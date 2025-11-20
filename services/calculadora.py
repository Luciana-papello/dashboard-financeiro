from models import db
from models.conta import Conta
from models.valor_mensal import ValorMensal
import re

class Calculadora:
    """Classe responsável por calcular todas as fórmulas das contas"""
    
    def __init__(self, mes, ano):
        self.mes = mes
        self.ano = ano
        self.valores_cache = {}
        
    def calcular_todas_contas(self):
        """Calcula todas as contas com fórmulas para o mês/ano"""
        print(f"\n🔢 Iniciando cálculos para {self.mes}/{self.ano}...")
        
        # Buscar todas as contas que têm fórmulas (entrada_manual = False)
        contas_calculadas = Conta.query.filter_by(entrada_manual=False).order_by(Conta.id).all()
        
        # Cache dos valores de entrada manual
        self._carregar_valores_cache()
        
        # Calcular cada conta
        total_calculadas = 0
        for conta in contas_calculadas:
            try:
                # Tratar fórmulas especiais
                if conta.formula == "ACUMULADO":
                    resultado = self._calcular_acumulado(conta.id)
                else:
                    resultado = self._calcular_formula(conta.formula)
                
                # Salvar resultado
                self._salvar_valor(conta.id, resultado)
                total_calculadas += 1
                
                print(f"✅ ID {conta.id} ({conta.nome}): R$ {resultado:,.2f}")
                
            except Exception as e:
                print(f"❌ Erro ao calcular ID {conta.id} ({conta.nome}): {str(e)}")
        
        print(f"\n✅ Total de contas calculadas: {total_calculadas}")
        return total_calculadas
    
    def _carregar_valores_cache(self):
        """Carrega todos os valores do mês/ano em cache"""
        valores = ValorMensal.query.filter_by(mes=self.mes, ano=self.ano).all()
        for valor in valores:
            self.valores_cache[valor.conta_id] = valor.valor
    
    def _obter_valor(self, conta_id):
        """Obtém o valor de uma conta do cache"""
        return self.valores_cache.get(conta_id, 0.0)
    
    def _calcular_formula(self, formula):
        """Calcula uma fórmula matemática substituindo IDs por valores"""
        if not formula:
            return 0.0
        
        # Substituir os IDs pelos valores
        formula_calculavel = formula
        
        # Encontrar todos os números (IDs) na fórmula
        ids_na_formula = re.findall(r'\d+', formula)
        
        for id_str in ids_na_formula:
            conta_id = int(id_str)
            valor = self._obter_valor(conta_id)
            
            # Substituir o ID pelo valor na fórmula
            # Usar regex para substituir apenas números completos (não partes de outros números)
            formula_calculavel = re.sub(
                r'\b' + id_str + r'\b', 
                str(valor), 
                formula_calculavel
            )
        
        # Avaliar a expressão matemática
        try:
            resultado = eval(formula_calculavel)
            return float(resultado) if resultado else 0.0
        except ZeroDivisionError:
            print(f"⚠️ Divisão por zero na fórmula: {formula}")
            return 0.0
        except Exception as e:
            print(f"⚠️ Erro ao calcular fórmula '{formula}': {str(e)}")
            return 0.0
    
    def _calcular_acumulado(self, conta_id):
        """Calcula o valor acumulado (ex: Fluxo de Caixa Livre)"""
        # Para ID 28 (FLUXO DE CAIXA LIVRE)
        # Fórmula: 28(mês anterior) + 27(mês atual)
        
        if conta_id == 28:
            # Buscar valor do mês anterior
            mes_anterior = self.mes - 1
            ano_anterior = self.ano
            
            if mes_anterior == 0:
                mes_anterior = 12
                ano_anterior -= 1
            
            valor_mes_anterior = ValorMensal.query.filter_by(
                conta_id=28,
                mes=mes_anterior,
                ano=ano_anterior
            ).first()
            
            acumulado_anterior = valor_mes_anterior.valor if valor_mes_anterior else 0.0
            
            # Buscar valor do ID 27 (FLUXO CAIXA) do mês atual
            fluxo_caixa_atual = self._obter_valor(27)
            
            # Retornar acumulado
            return acumulado_anterior + fluxo_caixa_atual
        
        return 0.0
    
    def _salvar_valor(self, conta_id, valor):
        """Salva o valor calculado no banco de dados"""
        # Verificar se já existe
        valor_existente = ValorMensal.query.filter_by(
            conta_id=conta_id,
            mes=self.mes,
            ano=self.ano
        ).first()
        
        if valor_existente:
            valor_existente.valor = valor
        else:
            novo_valor = ValorMensal(
                conta_id=conta_id,
                mes=self.mes,
                ano=self.ano,
                valor=valor
            )
            db.session.add(novo_valor)
        
        # Atualizar cache
        self.valores_cache[conta_id] = valor
        
        # Commit
        db.session.commit()


def calcular_mes(mes, ano):
    """Função auxiliar para calcular um mês específico"""
    calculadora = Calculadora(mes, ano)
    return calculadora.calcular_todas_contas()