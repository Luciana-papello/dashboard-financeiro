import sqlite3

def corrigir_tabela_notas():
    print("🛠️ Iniciando correção do banco de dados...")
    
    # Conectar ao banco
    conn = sqlite3.connect('database/financeiro.db')
    cursor = conn.cursor()
    
    # ETAPA 1: Adicionar a coluna (sem a trava UNIQUE por enquanto)
    try:
        print("1️⃣ Tentando adicionar coluna 'chave_externa'...")
        cursor.execute("ALTER TABLE notas_fiscais ADD COLUMN chave_externa TEXT")
        print("   ✅ Coluna adicionada com sucesso!")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            print("   ⚠️ A coluna 'chave_externa' já existe. Pulando etapa.")
        else:
            print(f"   ❌ Erro na etapa 1: {e}")

    # ETAPA 2: Criar o índice UNIQUE separadamente (Isso o SQLite permite)
    try:
        print("2️⃣ Criando índice de proteção contra duplicidade...")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_notas_fiscais_chave_externa ON notas_fiscais(chave_externa)")
        print("   ✅ Índice criado com sucesso!")
    except Exception as e:
        print(f"   ❌ Erro na etapa 2: {e}")
            
    conn.commit()
    conn.close()
    print("🏁 Processo finalizado.")

if __name__ == "__main__":
    corrigir_tabela_notas()