import pandas as pd
from datetime import datetime
from sqlalchemy.exc import IntegrityError

class ImportadorNfeManual:
    def processar_arquivo(self, file_storage):
        # Importações tardias para evitar erro circular
        from app import db
        from models.nota_fiscal import NotaFiscal
        from models.valor_mensal import ValorMensal

        try:
            # Ler o arquivo Excel
            df = pd.read_excel(file_storage)
            
            # Limpar nomes das colunas (remover espaços extras)
            df.columns = df.columns.str.strip()
            
            notas_processadas = 0
            meses_para_recalcular = set()

            for index, row in df.iterrows():
                try:
                    # Extrair dados da linha
                    numero = str(row['Numero NF']).strip()
                    fornecedor = str(row['Fornecedor']).strip()
                    valor = float(row['Valor'])
                    
                    # Tratamento da Data
                    data_raw = row['Data Emissao']
                    if isinstance(data_raw, str):
                        data_emissao = datetime.strptime(data_raw, "%d/%m/%Y").date()
                    else:
                        data_emissao = data_raw.date() # Já é um objeto datetime do Excel

                    descricao = str(row.get('Descricao', f'NF {numero} - {fornecedor}'))
                    empresa = str(row.get('Empresa', 'Manual'))

                    # Gerar uma chave única artificial para evitar duplicidade
                    # Ex: MANUAL_12345_FORNECEDORX
                    chave_unica = f"MANUAL_{numero}_{fornecedor.replace(' ', '').upper()}"

                    # Verificar se já existe
                    existe = NotaFiscal.query.filter_by(chave_externa=chave_unica).first()

                    mes = data_emissao.month
                    ano = data_emissao.year
                    meses_para_recalcular.add((mes, ano))

                    if existe:
                        # Atualiza dados existentes
                        existe.valor = valor
                        existe.data_emissao = data_emissao
                    else:
                        # Cria nova nota
                        nova_nota = NotaFiscal(
                            chave_externa=chave_unica,
                            numero=numero,
                            descricao=descricao,
                            fornecedor=fornecedor,
                            valor=valor,
                            data_emissao=data_emissao,
                            mes=mes,
                            ano=ano,
                            conta_id=95, # ID 95 = Compras
                            categoria="Importação Manual",
                            empresa=empresa
                        )
                        db.session.add(nova_nota)
                    
                    notas_processadas += 1

                except Exception as e:
                    print(f"⚠️ Erro na linha {index + 2}: {e}")
                    continue # Pula para a próxima linha se der erro nessa

            # Salva as notas
            db.session.commit()

            # Recalcula os totais da conta 95
            self._recalcular_conta_95(meses_para_recalcular)

            return {"sucesso": True, "qtd": notas_processadas}

        except Exception as e:
            return {"sucesso": False, "erro": str(e)}

    def _recalcular_conta_95(self, meses_set):
        from app import db
        from models.nota_fiscal import NotaFiscal
        from models.valor_mensal import ValorMensal

        print("🧮 Recalculando totais da Conta 95 (Importação Manual)...")
        
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
        
        db.session.commit()