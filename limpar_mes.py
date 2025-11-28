from app import app, db
from models.valor_mensal import ValorMensal
from models.nota_fiscal import NotaFiscal

def limpar_dados_mes():
    print("\n🧹 --- FERRAMENTA DE LIMPEZA DE DADOS ---")
    
    try:
        mes = int(input("Digite o número do MÊS para limpar (1-12): "))
        ano = int(input("Digite o ANO (ex: 2024): "))
        
        confirmacao = input(f"⚠️ Tem certeza que deseja APAGAR TUDO de {mes}/{ano}? (S/N): ")
        
        if confirmacao.upper() != 'S':
            print("Cancelado.")
            return

        with app.app_context():
            # 1. Remove Valores Mensais (DRE, Balanço, Cálculos)
            num_valores = ValorMensal.query.filter_by(mes=mes, ano=ano).delete()
            
            # 2. Remove Notas Fiscais (se houver)
            num_nfe = NotaFiscal.query.filter_by(mes=mes, ano=ano).delete()
            
            db.session.commit()
            
            print(f"\n✅ SUCESSO!")
            print(f"🗑️  Foram apagados {num_valores} registros financeiros.")
            print(f"🗑️  Foram apagadas {num_nfe} notas fiscais.")
            print(f"📅 O mês {mes}/{ano} agora está vazio no banco de dados.")

    except ValueError:
        print("❌ Erro: Digite apenas números inteiros.")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

if __name__ == "__main__":
    limpar_dados_mes()