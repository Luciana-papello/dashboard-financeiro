import pandas as pd
from models import db
from models.conta import Conta
from models.valor_mensal import ValorMensal
from datetime import datetime
import re

class ImportadorExcel:
    """Classe para importar dados de planilhas Excel"""
    
    def __init__(self, caminho_arquivo):
        self.caminho = caminho_arquivo
        self.erros = []
        self.sucessos = 0
        
    def importar(self):
        """Importa todos os dados do Excel"""
        print(f"\n📥 Iniciando importação de {self.caminho}...")
        
        try:
            # Ler todas as abas do Excel
            excel_file = pd.ExcelFile(self.caminho)
            
            print(f"📋 Abas encontradas: {excel_file.sheet_names}")
            
            # Processar cada aba
            for aba in excel_file.sheet_names:
                if aba.upper() in ['BALANCO_PATRIMONIAL', 'BALANÇO_PATRIMONIAL', 'BALANCO']:
                    self._processar_aba(excel_file, aba, 'Balanço')
                elif aba.upper() in ['DRE', 'DEMONSTRACAO']:
                    self._processar_aba(excel_file, aba, 'DRE')
            
            # Salvar no banco
            db.session.commit()
            
            print(f"\n✅ Importação concluída!")
            print(f"✅ {self.sucessos} valores importados com sucesso")
            
            if self.erros:
                print(f"⚠️ {len(self.erros)} erros encontrados:")
                for erro in self.erros[:10]:  # Mostrar só os 10 primeiros
                    print(f"   - {erro}")
            
            return {
                'sucesso': True,
                'total_importado': self.sucessos,
                'total_erros': len(self.erros),
                'erros': self.erros
            }
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro na importação: {str(e)}")
            return {
                'sucesso': False,
                'erro': str(e)
            }
    
    def _processar_aba(self, excel_file, nome_aba, tipo_conta):
        """Processa uma aba específica"""
        print(f"\n📄 Processando aba: {nome_aba} (Tipo: {tipo_conta})")
        
        # Ler a aba
        df = pd.read_excel(excel_file, sheet_name=nome_aba)
        
        # Validar estrutura
        if 'ID' not in df.columns or 'CONTA' not in df.columns:
            self.erros.append(f"Aba '{nome_aba}': Colunas 'ID' e 'CONTA' são obrigatórias")
            return
        
        # Identificar colunas de meses (formato: MES/ANO)
        colunas_meses = [col for col in df.columns if self._eh_coluna_mes(col)]
        
        if not colunas_meses:
            self.erros.append(f"Aba '{nome_aba}': Nenhuma coluna de mês encontrada (formato: JAN/2024)")
            return
        
        print(f"   📅 Encontradas {len(colunas_meses)} colunas de meses")
        
        # Processar cada linha
        for idx, row in df.iterrows():
            try:
                conta_id = int(row['ID'])
                
                # Verificar se a conta existe
                conta = Conta.query.get(conta_id)
                if not conta:
                    self.erros.append(f"ID {conta_id} não existe no banco de dados")
                    continue
                
                # Verificar se é conta de entrada manual
                if not conta.entrada_manual:
                    continue  # Pular contas calculadas
                
                # Processar cada mês
                for coluna_mes in colunas_meses:
                    mes, ano = self._extrair_mes_ano(coluna_mes)
                    
                    if mes and ano:
                        valor_bruto = row[coluna_mes]
                        
                        # LIMPEZA ROBUSTA DO VALOR
                        valor = self._limpar_valor(valor_bruto)
                        
                        # Salvar no banco
                        self._salvar_valor(conta_id, mes, ano, valor)
                        self.sucessos += 1
                        
            except Exception as e:
                self.erros.append(f"Linha {idx + 2}: {str(e)}")

    def _limpar_valor(self, valor_bruto):
        """Limpa e converte valor para float, removendo caracteres inválidos"""
        # Se for NaN ou None, retornar 0
        if pd.isna(valor_bruto) or valor_bruto is None:
            return 0.0
        
        # Se já for número, retornar
        if isinstance(valor_bruto, (int, float)):
            return float(valor_bruto)
        
        # Se for string, limpar
        if isinstance(valor_bruto, str):
            # Remover espaços
            valor_limpo = valor_bruto.strip()
            
            # Remover separadores de milhar (vírgulas, pontos, espaços)
            # Assumindo formato brasileiro: 1.234.567,89 ou americano: 1,234,567.89
            
            # Contar vírgulas e pontos
            num_virgulas = valor_limpo.count(',')
            num_pontos = valor_limpo.count('.')
            
            # Se tem vírgula no final, é decimal brasileiro
            if ',' in valor_limpo and valor_limpo.rfind(',') > valor_limpo.rfind('.'):
                # Formato brasileiro: 1.234,56
                valor_limpo = valor_limpo.replace('.', '').replace(',', '.')
            else:
                # Formato americano ou só números: 1,234.56 ou 1234.56
                valor_limpo = valor_limpo.replace(',', '')
            
            # Remover qualquer outro caractere não numérico (exceto - e .)
            valor_limpo = ''.join(c for c in valor_limpo if c.isdigit() or c in '.-')
            
            # Tentar converter
            try:
                return float(valor_limpo) if valor_limpo else 0.0
            except (ValueError, AttributeError):
                print(f"⚠️ Não foi possível converter valor: '{valor_bruto}' -> '{valor_limpo}'")
                return 0.0
        
        # Se não conseguiu processar, retornar 0
        return 0.0            
    
    def _eh_coluna_mes(self, nome_coluna):
        """Verifica se a coluna é uma coluna de mês"""
        if not isinstance(nome_coluna, str):
            return False
        
        # Padrão: MES/ANO (ex: JAN/2024, JANEIRO/2024, 01/2024)
        padrao = r'(JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ|JANEIRO|FEVEREIRO|MARÇO|ABRIL|MAIO|JUNHO|JULHO|AGOSTO|SETEMBRO|OUTUBRO|NOVEMBRO|DEZEMBRO|\d{1,2})/\d{4}'
        
        return bool(re.search(padrao, nome_coluna.upper()))
    
    def _extrair_mes_ano(self, nome_coluna):
        """Extrai mês e ano do nome da coluna"""
        nome_upper = nome_coluna.upper()
        
        # Dicionário de meses
        meses = {
            'JAN': 1, 'JANEIRO': 1,
            'FEV': 2, 'FEVEREIRO': 2,
            'MAR': 3, 'MARÇO': 3, 'MARCO': 3,
            'ABR': 4, 'ABRIL': 4,
            'MAI': 5, 'MAIO': 5,
            'JUN': 6, 'JUNHO': 6,
            'JUL': 7, 'JULHO': 7,
            'AGO': 8, 'AGOSTO': 8,
            'SET': 9, 'SETEMBRO': 9,
            'OUT': 10, 'OUTUBRO': 10,
            'NOV': 11, 'NOVEMBRO': 11,
            'DEZ': 12, 'DEZEMBRO': 12
        }
        
        # Buscar padrão MES/ANO
        match = re.search(r'([A-Z]+|\d{1,2})/(\d{4})', nome_upper)
        
        if match:
            mes_str = match.group(1)
            ano = int(match.group(2))
            
            # Converter mês
            if mes_str.isdigit():
                mes = int(mes_str)
            else:
                mes = meses.get(mes_str)
            
            return mes, ano
        
        return None, None
    
    def _salvar_valor(self, conta_id, mes, ano, valor):
        """Salva ou atualiza um valor no banco"""
        # Verificar se já existe
        valor_existente = ValorMensal.query.filter_by(
            conta_id=conta_id,
            mes=mes,
            ano=ano
        ).first()
        
        if valor_existente:
            valor_existente.valor = valor
            valor_existente.data_atualizacao = datetime.utcnow()
        else:
            novo_valor = ValorMensal(
                conta_id=conta_id,
                mes=mes,
                ano=ano,
                valor=valor
            )
            db.session.add(novo_valor)


def importar_excel(caminho_arquivo):
    """Função auxiliar para importar Excel"""
    importador = ImportadorExcel(caminho_arquivo)
    return importador.importar()