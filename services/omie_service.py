import requests
import json
from datetime import datetime
from sqlalchemy.exc import IntegrityError

class OmieService:
    def __init__(self):
        self.empresas = [
            {'nome': 'Empo', 'app_key': '5737037596290', 'app_secret': '6fd530379e7e36ca3253e6b0d994da9f'},
            {'nome': 'Papello', 'app_key': '5737236929424', 'app_secret': '0b0d8fbfbeb5a94eb3e8ff43d5baa951'},
            {'nome': 'RAO', 'app_key': '5737497595830', 'app_secret': '02ce8e7e9bde1e3e8a726613f693b31d'}
        ]
        self.url = "https://app.omie.com.br/api/v1/produtos/recebimentonfe/"

    def sincronizar_por_periodo(self, data_inicio_iso, data_fim_iso):
        """
        Busca notas (ListarRecebimentos) no período selecionado.
        Recebe datas no formato ISO (YYYY-MM-DD) do HTML e converte para Omie (DD/MM/YYYY).
        """
        # Converter datas para formato Omie
        dt_ini_obj = datetime.strptime(data_inicio_iso, "%Y-%m-%d")
        dt_fim_obj = datetime.strptime(data_fim_iso, "%Y-%m-%d")
        
        dt_ini_omie = dt_ini_obj.strftime("%d/%m/%Y")
        dt_fim_omie = dt_fim_obj.strftime("%d/%m/%Y")

        total_notas_processadas = 0
        meses_para_recalcular = set()

        print(f"\n🔄 --- INICIANDO SINCRONIZAÇÃO ({dt_ini_omie} a {dt_fim_omie}) ---")

        for empresa in self.empresas:
            print(f"\n🏢 Processando empresa: {empresa['nome']}...")
            pagina = 1
            continuar_buscando = True

            while continuar_buscando:
                payload = {
                    "call": "ListarRecebimentos",
                    "app_key": empresa['app_key'],
                    "app_secret": empresa['app_secret'],
                    "param": [{
                        "nPagina": pagina,
                        "nRegistrosPorPagina": 100,
                        "cEtapa": "60", # Concluída
                        "cExibirDetalhes": "S", # Traz os itens
                        "dtEmissaoDe": dt_ini_omie,
                        "dtEmissaoAte": dt_fim_omie
                    }]
                }

                try:
                    response = requests.post(self.url, json=payload)
                    data = response.json()

                    # Verifica se acabou a paginação ou deu erro
                    if 'recebimentos' not in data:
                        if pagina == 1:
                            print(f"   ⚠️ Nenhuma nota encontrada neste período.")
                        break

                    notas = data['recebimentos']
                    total_paginas = data.get('nTotalPaginas', 1)
                    
                    print(f"   -> Pág {pagina}/{total_paginas}: Analisando {len(notas)} registros...")

                    for rec in notas:
                        try:
                            # 1. Filtro de Operação (CRÍTICO)
                            info = rec.get('infoCadastro', {})
                            operacao = info.get('cOperacao')
                            
                            if operacao != "21":
                                # Pula se não for operação de compra/entrada padrão
                                continue

                            # 2. Dados do Cabeçalho
                            cabec = rec.get('cabec', {})
                            numero_nf = cabec.get('cNumeroNFe')
                            fornecedor = cabec.get('cNome')
                            valor_nf = float(cabec.get('nValorNFe', 0))
                            data_txt = cabec.get('dEmissaoNFe')
                            chave_unica = str(cabec.get('nIdReceb')) # ID único do Recebimento

                            if not data_txt: continue
                            data_emissao = datetime.strptime(data_txt, "%d/%m/%Y")

                            # 3. Concatenação das Descrições
                            itens = rec.get('itensRecebimento', [])
                            descricoes_lista = []
                            
                            for item in itens:
                                item_cabec = item.get('itensCabec', {})
                                desc_prod = item_cabec.get('cDescricaoProduto')
                                if desc_prod:
                                    descricoes_lista.append(desc_prod)
                            
                            if descricoes_lista:
                                descricao_final = " + ".join(descricoes_lista)
                            else:
                                descricao_final = "Descrição não disponível"

                            # Limitar tamanho para não estourar banco (opcional, mas seguro)
                            if len(descricao_final) > 200:
                                descricao_final = descricao_final[:197] + "..."

                            # DEBUG
                            print(f"      ✅ Importando: NF {numero_nf} | R$ {valor_nf:.2f} | {descricao_final[:30]}...")

                            # 4. Salvar
                            mes_ref = data_emissao.month
                            ano_ref = data_emissao.year
                            meses_para_recalcular.add((mes_ref, ano_ref))

                            self._salvar_nota(
                                chave_unica=chave_unica,
                                numero=numero_nf,
                                fornecedor=fornecedor,
                                valor=valor_nf,
                                data_emissao=data_emissao,
                                empresa=empresa['nome'],
                                mes=mes_ref,
                                ano=ano_ref,
                                descricao=descricao_final
                            )
                            total_notas_processadas += 1

                        except Exception as e_item:
                            print(f"      ❌ Erro ao processar item: {e_item}")
                            continue

                    if pagina >= total_paginas:
                        continuar_buscando = False
                    else:
                        pagina += 1

                except Exception as e:
                    print(f"❌ Erro de conexão na {empresa['nome']}: {str(e)}")
                    continuar_buscando = False

        if total_notas_processadas > 0:
            self._recalcular_conta_95(meses_para_recalcular)
        
        return {"status": "sucesso", "notas_processadas": total_notas_processadas}

    def _salvar_nota(self, chave_unica, numero, fornecedor, valor, data_emissao, empresa, mes, ano, descricao):
        from app import db
        from models.nota_fiscal import NotaFiscal
        
        existe = NotaFiscal.query.filter_by(chave_externa=chave_unica).first()
        
        if existe:
            existe.valor = valor
            existe.fornecedor = fornecedor
            existe.data_emissao = data_emissao.date()
            existe.descricao = descricao
        else:
            nova_nota = NotaFiscal(
                chave_externa=chave_unica,
                numero=str(numero),
                descricao=descricao,
                fornecedor=fornecedor,
                valor=valor,
                data_emissao=data_emissao.date(),
                mes=mes,
                ano=ano,
                conta_id=95,
                categoria="Entrada NFe (Omie)",
                empresa=empresa
            )
            db.session.add(nova_nota)
        
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

    def _recalcular_conta_95(self, meses_set):
        from app import db
        from models.nota_fiscal import NotaFiscal
        from models.valor_mensal import ValorMensal
        
        print("🧮 Recalculando totais da Conta 95...")
        for mes, ano in meses_set:
            total = db.session.query(db.func.sum(NotaFiscal.valor))\
                .filter(NotaFiscal.conta_id == 95, NotaFiscal.mes == mes, NotaFiscal.ano == ano)\
                .scalar() or 0.0
            
            registro = ValorMensal.query.filter_by(conta_id=95, mes=mes, ano=ano).first()
            if registro:
                registro.valor = total
            else:
                novo = ValorMensal(conta_id=95, mes=mes, ano=ano, valor=total)
                db.session.add(novo)
            
            print(f"   -> {mes}/{ano}: Total atualizado para R$ {total:,.2f}")
        
        db.session.commit()