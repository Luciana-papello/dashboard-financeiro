from app import app, db
from models.nota_fiscal import NotaFiscal
from models.valor_mensal import ValorMensal

def limpar_tudo():
    print("🧹 Iniciando limpeza de dados de Compras (Notas e Conta 95)...")
    
    with app.app_context():
        try:
            # 1. Apagar todas as Notas Fiscais
            num_notas = db.session.query(NotaFiscal).delete()
            print(f"   🗑️  {num_notas} notas fiscais removidas.")

            # 2. Apagar os valores mensais da conta 95 (Compras)
            # Assim, quando você subir a planilha, ele vai criar do zero
            num_valores = db.session.query(ValorMensal).filter_by(conta_id=95).delete()
            print(f"   🗑️  {num_valores} registros mensais da conta 95 removidos.")

            db.session.commit()
            print("\n✨ Limpeza concluída com sucesso! O banco está pronto para nova importação.")
            
        except Exception as e:
            db.session.rollback()
            print(f"   ❌ Erro ao limpar: {e}")

if __name__ == "__main__":
    limpar_tudo()