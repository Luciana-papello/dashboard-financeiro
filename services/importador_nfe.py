import pandas as pd
from datetime import datetime
from models import db
from models.nota_fiscal import NotaFiscal
from models.valor_mensal import ValorMensal

def importar_nfe(caminho_arquivo):
    """
    Importa notas fiscais de um arquivo Excel
    
    Args:
        caminho_arquivo: Caminho do arquivo Excel
        
    Returns:
        dict: Resultado da importação com sucesso/erro
    """
    try:
        # Ler Excel
        print(f"📂 Lendo arquivo: {caminho_arquivo}")
        df = pd.read_excel(caminho_arquivo)
        
        print(f"✅ Arquivo lido com sucesso! {len(df)} linhas encontradas")
        print(f"📋 Colunas disponíveis: {list(df.columns)}")
        
        # Mapear nomes de colunas (case-insensitive e com variações)
        colunas_mapeadas = {}
        for col in df.columns:
            col_lower = str(col).lower().strip()
            
            # Tipo da NF-e
            if 'tipo' in col_lower and 'nf' in col_lower:
                colunas_mapeadas['tipo_nfe'] = col
            # Data de Emissão
            elif 'data' in col_lower and 'emis' in col_lower:
                colunas_mapeadas['data_emissao'] = col
            # Valor da NF-e
            elif 'valor' in col_lower and 'nf' in col_lower:
                colunas_mapeadas['valor_nfe'] = col
            # Situação
            elif 'situa' in col_lower or 'status' in col_lower:
                colunas_mapeadas['situacao'] = col
            # Número da NF-e
            elif ('numero' in col_lower or 'número' in col_lower) and 'nf' in col_lower:
                colunas_mapeadas['numero_nfe'] = col
            # CNPJ/CPF
            elif 'cnpj' in col_lower or 'cpf' in col_lower:
                colunas_mapeadas['cnpj_cpf'] = col
            # Nome Fantasia
            elif 'fantasia' in col_lower:
                colunas_mapeadas['nome_fantasia'] = col
            # Categorias
            elif 'categoria' in col_lower:
                colunas_mapeadas['categorias'] = col
            # Razão Social
            elif 'razao' in col_lower or 'razão' in col_lower:
                colunas_mapeadas['razao_social'] = col
            # Valor do ICMS
            elif 'icms' in col_lower:
                colunas_mapeadas['valor_icms'] = col
            # Natureza da Operação
            elif 'natureza' in col_lower:
                colunas_mapeadas['natureza_operacao'] = col
            # Empresa
            elif col_lower == 'empresa':
                colunas_mapeadas['empresa'] = col
        
        print(f"🔍 Colunas mapeadas: {colunas_mapeadas}")
        
        # Validar colunas obrigatórias
        if 'tipo_nfe' not in colunas_mapeadas:
            return {
                'sucesso': False,
                'erro': 'Coluna "Tipo da NF-e" não encontrada. Colunas disponíveis: ' + ', '.join(df.columns)
            }
        
        if 'data_emissao' not in colunas_mapeadas:
            return {
                'sucesso': False,
                'erro': 'Coluna "Data de Emissão" não encontrada. Colunas disponíveis: ' + ', '.join(df.columns)
            }
        
        if 'valor_nfe' not in colunas_mapeadas:
            return {
                'sucesso': False,
                'erro': 'Coluna "Valor da NF-e" não encontrada. Colunas disponíveis: ' + ', '.join(df.columns)
            }
        
        # Filtrar apenas NF-e de Entrada
        df_filtrado = df[df[colunas_mapeadas['tipo_nfe']].astype(str).str.upper().str.contains('ENTRADA', na=False)]
        
        print(f"🔎 {len(df_filtrado)} NF-e de Entrada encontradas")
        
        if len(df_filtrado) == 0:
            return {
                'sucesso': False,
                'erro': 'Nenhuma NF-e de tipo "Entrada" encontrada na planilha'
            }
        
        # Processar cada linha
        total_importado = 0
        erros = []
        
        for idx, row in df_filtrado.iterrows():
            try:
                # Processar data
                data_emissao = _processar_data(row[colunas_mapeadas['data_emissao']])
                if not data_emissao:
                    erros.append(f"Linha {idx + 2}: Data inválida")
                    continue
                
                # Processar valor
                valor_nfe = _processar_valor(row[colunas_mapeadas['valor_nfe']])
                
                # Extrair mês e ano
                mes = data_emissao.month
                ano = data_emissao.year
                
                # Criar registro
                nf = NotaFiscal(
                    tipo_nfe='Entrada',
                    data_emissao=data_emissao,
                    situacao=str(row.get(colunas_mapeadas.get('situacao', ''), '')) if 'situacao' in colunas_mapeadas else None,
                    numero_nfe=str(row.get(colunas_mapeadas.get('numero_nfe', ''), '')) if 'numero_nfe' in colunas_mapeadas else None,
                    cnpj_cpf=str(row.get(colunas_mapeadas.get('cnpj_cpf', ''), '')) if 'cnpj_cpf' in colunas_mapeadas else None,
                    nome_fantasia=str(row.get(colunas_mapeadas.get('nome_fantasia', ''), '')) if 'nome_fantasia' in colunas_mapeadas else None,
                    valor_nfe=valor_nfe,
                    categorias=str(row.get(colunas_mapeadas.get('categorias', ''), '')) if 'categorias' in colunas_mapeadas else None,
                    razao_social=str(row.get(colunas_mapeadas.get('razao_social', ''), '')) if 'razao_social' in colunas_mapeadas else None,
                    valor_icms=str(row.get(colunas_mapeadas.get('valor_icms', ''), '')) if 'valor_icms' in colunas_mapeadas else None,
                    natureza_operacao=str(row.get(colunas_mapeadas.get('natureza_operacao', ''), '')) if 'natureza_operacao' in colunas_mapeadas else None,
                    empresa=str(row.get(colunas_mapeadas.get('empresa', ''), '')) if 'empresa' in colunas_mapeadas else None,
                    mes=mes,
                    ano=ano
                )
                
                db.session.add(nf)
                total_importado += 1
                
            except Exception as e:
                erros.append(f"Linha {idx + 2}: {str(e)}")
                continue
        
        # Salvar no banco
        db.session.commit()
        print(f"✅ {total_importado} NF-e salvas no banco")
        
        # Atualizar conta 95 (Compras)
        _atualizar_compras()
        
        return {
            'sucesso': True,
            'total_importado': total_importado,
            'erros': erros if erros else None,
            'mensagem': f"Importadas {total_importado} notas fiscais de entrada"
        }
        
    except Exception as e:
        print(f"❌ Erro na importação: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'sucesso': False,
            'erro': str(e)
        }


def _processar_data(valor):
    """Processa diferentes formatos de data"""
    if pd.isna(valor):
        return None
    
    # Se já é datetime
    if isinstance(valor, datetime):
        return valor
    
    # Se é string
    valor_str = str(valor).strip()
    
    # Tentar formato DD/MM/YYYY
    try:
        return datetime.strptime(valor_str, '%d/%m/%Y')
    except:
        pass
    
    # Tentar formato YYYY-MM-DD
    try:
        return datetime.strptime(valor_str, '%Y-%m-%d')
    except:
        pass
    
    # Tentar formato DD-MM-YYYY
    try:
        return datetime.strptime(valor_str, '%d-%m-%Y')
    except:
        pass
    
    return None


def _processar_valor(valor):
    """Processa e limpa valores monetários"""
    if pd.isna(valor):
        return 0.0
    
    # Se já é número
    if isinstance(valor, (int, float)):
        return float(valor)
    
    # Se é string, limpar
    valor_str = str(valor).strip()
    
    # Remover símbolo de moeda
    valor_str = valor_str.replace('R$', '').replace('$', '').strip()
    
    # Contar vírgulas e pontos
    qtd_virgulas = valor_str.count(',')
    qtd_pontos = valor_str.count('.')
    
    # Determinar formato
    if qtd_virgulas > 0 and qtd_pontos > 0:
        # Formato misto - detectar qual é decimal
        pos_virgula = valor_str.rfind(',')
        pos_ponto = valor_str.rfind('.')
        
        if pos_virgula > pos_ponto:
            # Formato brasileiro: 1.234.567,89
            valor_str = valor_str.replace('.', '').replace(',', '.')
        else:
            # Formato americano: 1,234,567.89
            valor_str = valor_str.replace(',', '')
    
    elif qtd_virgulas > 0:
        # Só vírgulas - formato brasileiro
        valor_str = valor_str.replace('.', '').replace(',', '.')
    
    # Converter para float
    try:
        return float(valor_str)
    except:
        return 0.0


def _atualizar_compras():
    """Atualiza a conta 95 (Compras) com base nas NF-e"""
    print("\n💰 Atualizando conta Compras (ID 95)...")
    
    # Buscar todos os meses/anos com NF-e de entrada
    meses_anos = db.session.query(
        NotaFiscal.mes,
        NotaFiscal.ano
    ).filter_by(tipo_nfe='Entrada').distinct().all()
    
    for mes, ano in meses_anos:
        # Somar valores do mês
        total = db.session.query(
            db.func.sum(NotaFiscal.valor_nfe)
        ).filter_by(
            tipo_nfe='Entrada',
            mes=mes,
            ano=ano
        ).scalar() or 0.0
        
        # Atualizar ou criar valor mensal
        valor_existente = ValorMensal.query.filter_by(
            conta_id=95,
            mes=mes,
            ano=ano
        ).first()
        
        if valor_existente:
            valor_existente.valor = total
        else:
            novo_valor = ValorMensal(
                conta_id=95,
                mes=mes,
                ano=ano,
                valor=total
            )
            db.session.add(novo_valor)
        
        db.session.commit()
        print(f"✅ {mes}/{ano}: R$ {total:,.2f}")
    
    print("✅ Conta Compras atualizada!")