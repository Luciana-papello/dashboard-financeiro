import requests
import json
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError

class OmieService:
    def __init__(self):
        # Configuração das 3 empresas
        self.empresas = [
            {'nome': 'Empo', 'app_key': '5737037596290', 'app_secret': '6fd530379e7e36ca3253e6b0d994da9f'},
            {'nome': 'Papello', 'app_key': '5737236929424', 'app_secret': '0b0d8fbfbeb5a94eb3e8ff43d5baa951'},
            {'nome': 'RAO', 'app_key': '5737497595830', 'app_secret': '02ce8e7e9bde1e3e8a726613f693b31d'}
        ]
        # NOVO ENDPOINT: Consultar NF (ListarNF)
        self.url = "https://app.omie.com.br/api/v1/produtos/nfconsultar/"

    def sincronizar_ultimos_60_dias(self):
        """
        Busca notas (ListarNF) dos últimos 365 dias de todas as empresas
        """
        # Data limite para filtrar (1 ano atrás para garantir histórico)
        data_corte = datetime.now() - timedelta(days=365)
        # Formato Omie para filtro: dd/mm/aaaa
        data_inicial_str = data_corte.strftime("%d/%m/%Y")
        data_final_str = datetime.now().strftime("%d/%m/%Y") # Até hoje

        total_notas_processadas = 0
        meses_para_recalcular = set()

        print(f"\n🔄 --- INICIANDO SINCRONIZAÇÃO VIA 'ListarNF' ---")
        print(f"📅 Período: {data_inicial_str} até {data_final_str}")

        for empresa in self.empresas:
            print(f"\n🏢 Processando empresa: {empresa['nome']}...")
            pagina = 1
            continuar_buscando = True

            while continuar_buscando:
                payload = {
                    "call": "ListarNF",
                    "app_key": empresa['app_key'],
                    "app_secret": empresa['app_secret'],
                    "param": [{
                        "pagina": pagina,
                        "registros_por_pagina": 100,
                        "tpNF": "0", # 0 = Entrada (Compras), 1 = Saída
                        "apenas_importado_api": "N",
                        "ordenar_por": "DATA",
                        "dEmiInicial": data_inicial_str,
                        "dEmiFinal": data_final_str
                    }]
                }

                try:
                    response = requests.post(self.url, json=payload)
                    
                    # Verificação básica de status HTTP
                    if response.status_code != 200:
                        print(f"   ❌ Erro HTTP {response.status_code}: {response.text}")
                        break

                    data = response.json()

                    # Verifica se a lista veio (a chave no novo endpoint é 'nfCadastro')
                    if 'nfCadastro' not in data:
                        # Se não tem 'nfCadastro', pode ter acabado as páginas ou erro
                        if pagina == 1:
                            print(f"   ⚠️ Nenhuma nota encontrada ou erro na resposta: {data.keys()}")
                        break

                    notas_lista = data['nfCadastro']
                    if not notas_lista:
                        break

                    total_registros = data.get('total_de_registros', 0)
                    total_paginas = data.get('total_de_paginas', 0)
                    print(f"   -> Pág {pagina}/{total_paginas}: Processando {len(notas_lista)} notas...")

                    for nota_omie in notas_lista:
                        try:
                            # --- MAPEAMENTO DOS CAMPOS (NOVO JSON) ---
                            
                            # 1. Identificação e Data
                            ide = nota_omie.get('ide', {})
                            numero_nf = ide.get('nNF')
                            data_txt = ide.get('dEmi') # Ex: 14/11/2025
                            
                            if not data_txt: continue
                            
                            data_emissao = datetime.strptime(data_txt, "%d/%m/%Y")

                            # 2. Valores Totais
                            total_obj = nota_omie.get('total', {})
                            icms_tot = total_obj.get('ICMSTot', {})
                            valor_nf = float(icms_tot.get('vNF', 0))

                            # 3. Fornecedor (Destinatário Interno ou Emitente?)
                            # No endpoint ListarNF com tpNF=0 (Entrada), o emitente é o Fornecedor.
                            # Mas no seu JSON de exemplo, o 'nfDestInt' tem a Razão Social "ECO3".
                            # Vamos tentar pegar do emitente (quem vendeu) primeiro.
                            emitente = nota_omie.get('emit', {}) # Dados de quem emitiu a nota (Fornecedor)
                            destinatario = nota_omie.get('nfDestInt', {}) # Dados do cliente (Nossa empresa)
                            
                            # Se for nota de entrada, o fornecedor está no 'emit' (se existir) ou no cabeçalho
                            # O JSON que você mandou tem 'nfDestInt' com 'ECO3 DO BRASIL', que parece ser o fornecedor no seu exemplo.
                            # Vamos priorizar o campo que você indicou: 'cRazao'
                            fornecedor_nome = destinatario.get('cRazao') or emitente.get('xNome') or "Fornecedor Desconhecido"

                            # 4. Descrição (Primeiro produto)
                            detalhes = nota_omie.get('det', [])
                            descricao_produto = "Sem descrição"
                            if detalhes and len(detalhes) > 0:
                                prod = detalhes[0].get('prod', {})
                                descricao_produto = prod.get('xProd', 'Produto sem nome')
                                if len(detalhes) > 1:
                                    descricao_produto += " (+ outros itens)"

                            # 5. ID Único (Chave Externa)
                            compl = nota_omie.get('compl', {})
                            # Usamos nIdReceb (ID do Recebimento) ou nIdNF (ID da Nota)
                            # Se não tiver ID numérico, usamos a Chave de Acesso (cChaveNFe)
                            chave_unica = str(compl.get('nIdNF') or compl.get('nIdReceb') or compl.get('cChaveNFe') or f"{numero_nf}-{data_txt}")

                            # DEBUG VISUAL
                            # print(f"      NF: {numero_nf} | {data_txt} | R$ {valor_nf:.2f} | {fornecedor_nome}")

                            # Salvar e Contabilizar
                            mes_ref = data_emissao.month
                            ano_ref = data_emissao.year
                            meses_para_recalcular.add((mes_ref, ano_ref))

                            self._salvar_nota(
                                chave_unica=chave_unica,
                                numero=numero_nf,
                                fornecedor=fornecedor_nome,
                                valor=valor_nf,
                                data_emissao=data_emissao,
                                empresa=empresa['nome'],
                                mes=mes_ref,
                                ano=ano_ref,
                                descricao=descricao_produto
                            )
                            total_notas_processadas += 1

                        except Exception as e_item:
                            print(f"      ❌ Erro ao ler item da NF: {e_item}")
                            continue

                    # Controle de Paginação
                    if pagina >= total_paginas:
                        continuar_buscando = False
                    else:
                        pagina += 1

                except Exception as e:
                    print(f"❌ Erro de conexão/API na {empresa['nome']}: {str(e)}")
                    continuar_buscando = False

        # Recalcular saldos
        if total_notas_processadas > 0:
            self._recalcular_conta_95(meses_para_recalcular)
        else:
            print("\n⚠️ Nenhuma nota encontrada nos filtros especificados.")
        
        return {"status": "sucesso", "notas_processadas": total_notas_processadas}

    def _salvar_nota(self, chave_unica, numero, fornecedor, valor, data_emissao, empresa, mes, ano, descricao):
        from app import db
        from models.nota_fiscal import NotaFiscal
        
        # Verifica se já existe pelo ID único
        existe = NotaFiscal.query.filter_by(chave_externa=chave_unica).first()
        
        if existe:
            # Atualiza dados se mudou algo
            existe.valor = valor
            existe.fornecedor = fornecedor
            existe.data_emissao = data_emissao.date()
            existe.descricao = descricao
        else:
            nova_nota = NotaFiscal(
                chave_externa=chave_unica,
                numero=str(numero),
                descricao=descricao[:200], # Limita tamanho para não quebrar banco
                fornecedor=fornecedor[:200],
                valor=valor,
                data_emissao=data_emissao.date(),
                mes=mes,
                ano=ano,
                conta_id=95,
                categoria="Entrada NFe (API)",
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