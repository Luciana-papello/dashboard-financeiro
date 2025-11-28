from app import app, db
from models.nota_fiscal import NotaFiscal
from sqlalchemy import text

def resetar_tabela():
    print("☢️  ATENÇÃO: Apagando e recriando tabela de Notas Fiscais...")
    
    with app.app_context():
        try:
            # 1. Tenta apagar a tabela existente (DROP)
            # Usamos SQL direto para garantir que apague mesmo se o modelo estiver diferente
            try:
                db.session.execute(text("DROP TABLE IF EXISTS notas_fiscais"))
                db.session.commit()
                print("   ✅ Tabela antiga apagada.")
            except Exception as e:
                print(f"   ⚠️ Erro ao dropar (pode ignorar): {e}")

            # 2. Recria a tabela baseada no NOVO modelo do passo 1
            print("2️⃣  Criando nova tabela 'notas_fiscais'...")
            db.create_all()
            print("   ✅ Nova tabela criada com sucesso!")
            
        except Exception as e:
            print(f"   ❌ Erro fatal: {e}")

if __name__ == "__main__":
    resetar_tabela()