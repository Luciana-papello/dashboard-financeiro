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
        
        # --- TRAVA DE SEGURANÇA ---
        # Impede recálculo de anos anteriores a 2025 para proteger dados históricos
        if self.ano < 2025:
            print(f"🔒 Ano {self.ano} é histórico/fixo. Cálculos automáticos ignorados.")
            return 0
        # --------------------------

        print(f"\n🔢 Iniciando cálculos para {self.mes}/{self.ano}...")
        
        # Buscar todas as contas que têm fórmulas (entrada_manual = False)
        contas_calculadas = Conta.query.filter_by(entrada_manual=False).order_by(Conta.id).all()
        
        # Cache dos valores de entrada manual
        self._carregar_valores_cache()
        
        # Calcular cada conta
        
        total_calculadas = 0
        for conta in contas_calculadas:
            try:
                resultado = None

                # --- NOVO: Valores Fixos para Jan-Abr/2025 (IDs 27 e 28) ---
                if self.ano == 2025:
                    if conta.id == 27: # FLUXO DE CAIXA
                        if self.mes == 1: resultado = -808491.83
                        elif self.mes == 2: resultado = -97556.96
                        elif self.mes == 3: resultado = -135813.53
                        elif self.mes == 4: resultado = -128647.21
                    elif conta.id == 28: # FLUXO DE CAIXA LIVRE (ACUMULADO)
                        if self.mes == 1: resultado = -418423.17
                        elif self.mes == 2: resultado = -515980.13
                        elif self.mes == 3: resultado = -605324.75
                        elif self.mes == 4: resultado = -733971.96
                # -----------------------------------------------------------

                # Se não foi definido acima (resultado é None), calcula normalmente
                if resultado is None:
                    if conta.formula == "ACUMULADO":
                        resultado = self._calcular_acumulado(conta.id)
                    elif conta.formula == "ACUMULADO_ANUAL":
                        resultado = self._calcular_acumulado_anual(conta.id)    
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
        
        try:
            # Abordagem: split por operadores, substituir tokens inteiros, rejuntar
            import re
            
            # Preservar a fórmula original
            formula_original = str(formula)
            
            # Dividir a fórmula em tokens (números e operadores)
            # Match: números (inteiros ou decimais) ou operadores
            tokens = re.findall(r'\d+\.?\d*|\+|\-|\*|\/|\(|\)', formula_original)
            
            # Criar dicionário de substituições
            substituicoes = {}
            for token in tokens:
                # Se o token é um número inteiro (sem ponto decimal)
                if token.isdigit():
                    conta_id = int(token)
                    # Buscar valor da conta
                    valor = self._obter_valor(conta_id)
                    substituicoes[token] = str(valor)
            
            # Reconstruir fórmula substituindo apenas tokens completos
            nova_formula = []
            for token in tokens:
                if token in substituicoes:
                    nova_formula.append(substituicoes[token])
                else:
                    nova_formula.append(token)
            
            # Juntar com espaços para clareza
            formula_calculavel = ' '.join(nova_formula)
            
            # Avaliar
            resultado = eval(formula_calculavel)
            return float(resultado) if resultado else 0.0
            
        except ZeroDivisionError:
            print(f"⚠️ Divisão por zero na fórmula: {formula}")
            return 0.0
        except SyntaxError as e:
            print(f"⚠️ Erro de sintaxe na fórmula '{formula}'")
            print(f"   DEBUG: {formula_calculavel}")
            return 0.0
        except Exception as e:
            print(f"⚠️ Erro ao calcular fórmula '{formula}': {type(e).__name__}: {str(e)}")
            return 0.0
    
    def _calcular_acumulado(self, conta_id):
        """Calcula o valor acumulado (ex: Fluxo de Caixa Livre)"""
        # Para ID 28 (FLUXO DE CAIXA LIVRE)
        # Fórmula: 28(mês anterior) + 27(mês atual)
        
        if conta_id == 28:
            # --- NOVO: Regra de Exceção para Saldo Inicial (Jan/2025) ---
            if self.mes == 1 and self.ano == 2025:
                return -418423.17
            # -----------------------------------------------------------

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
    def _calcular_acumulado_anual(self, conta_id):
        """
        Calcula o acumulado anual (soma de janeiro até o mês atual)
        Usado para: ID 101 - Receita Acumulada Anual
        Fórmula: Soma de ID 1 (Receita Operacional) de Jan até mês atual
        """
        
        if conta_id == 101:  # Receita Acumulada Anual
            acumulado = 0.0
            
            # Somar receita de janeiro até o mês atual
            for mes_iter in range(1, self.mes + 1):
                # Buscar receita operacional (ID 1) do mês
                receita = ValorMensal.query.filter_by(
                    conta_id=1,
                    mes=mes_iter,
                    ano=self.ano
                ).first()
                
                if receita:
                    acumulado += receita.valor
            
            return acumulado
        
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