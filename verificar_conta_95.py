from app import app
from models.valor_mensal import ValorMensal

def verificar_saldo():
    print("\n🔍 Verificando saldo da Conta 95 (Compras) no banco de dados...")
    print("-" * 40)
    
    with app.app_context():
        # Busca ordenado por Ano e Mês
        valores = ValorMensal.query.filter_by(conta_id=95)\
            .order_by(ValorMensal.ano, ValorMensal.mes).all()
        
        if not valores:
            print("   (Nenhum dado encontrado. A conta está vazia)")
        
        total_geral = 0
        for v in valores:
            print(f"   📅 {v.mes:02d}/{v.ano} | R$ {v.valor:,.2f}")
            total_geral += v.valor
            
        print("-" * 40)
        print(f"   💰 TOTAL GERAL ACUMULADO: R$ {total_geral:,.2f}\n")

if __name__ == "__main__":
    verificar_saldo()