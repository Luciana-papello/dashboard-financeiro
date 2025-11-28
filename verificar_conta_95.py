from app import app, db
from models.nota_fiscal import NotaFiscal
from models.valor_mensal import ValorMensal
from sqlalchemy import func

def verificar_detalhado_por_mes():
    print("\n🔍 RELATÓRIO DE COMPRAS (NOTAS FISCAIS) - DETALHADO POR MÊS")
    print("=" * 60)

    with app.app_context():
        # 1. Buscar notas agrupadas por Ano, Mês e Empresa
        resultados = db.session.query(
            NotaFiscal.ano,
            NotaFiscal.mes,
            NotaFiscal.empresa,
            func.count(NotaFiscal.id),
            func.sum(NotaFiscal.valor)
        ).filter(NotaFiscal.conta_id == 95)\
        .group_by(NotaFiscal.ano, NotaFiscal.mes, NotaFiscal.empresa)\
        .order_by(NotaFiscal.ano, NotaFiscal.mes, NotaFiscal.empresa).all()

        if not resultados:
            print("   (Nenhuma nota fiscal encontrada no banco)")
            return

        # 2. Organizar os dados em um dicionário para facilitar a impressão
        # Estrutura: dados[ano][mes] = lista de empresas
        dados_organizados = {}
        
        for ano, mes, empresa, qtd, valor in resultados:
            chave = (ano, mes)
            if chave not in dados_organizados:
                dados_organizados[chave] = []
            
            dados_organizados[chave].append({
                'empresa': empresa if empresa else "Não Identificada",
                'qtd': qtd,
                'valor': valor if valor else 0.0
            })

        # 3. Imprimir Relatório
        total_geral_acumulado = 0.0
        
        # Iterar pelos meses ordenados
        for (ano, mes), lista_empresas in sorted(dados_organizados.items()):
            print(f"\n📅 {mes:02d}/{ano}")
            print("-" * 45)
            
            soma_mes_qtd = 0
            soma_mes_valor = 0.0
            
            for item in lista_empresas:
                # Ex: Empo: 83 notas R$ 10.000,00
                print(f"   🏢 {item['empresa']:<15}: {item['qtd']:>3} notas | R$ {item['valor']:,.2f}")
                
                soma_mes_qtd += item['qtd']
                soma_mes_valor += item['valor']
            
            print("-" * 45)
            print(f"   🔹 TOTAL MÊS    : {soma_mes_qtd:>3} notas | R$ {soma_mes_valor:,.2f}")
            
            total_geral_acumulado += soma_mes_valor

        print("\n" + "=" * 60)
        print(f"💰 TOTAL GERAL DE TODAS AS NOTAS: R$ {total_geral_acumulado:,.2f}")
        print("=" * 60)

        # 4. Comparação Rápida (Prova Real)
        print("\n⚖️  CONFERÊNCIA (NOTAS vs SALDO DA CONTA 95):")
        print(f"{'Mês/Ano':<10} | {'Total Notas':<15} | {'Saldo Conta 95':<15} | {'Diferença'}")
        print("-" * 60)

        valores_conta = ValorMensal.query.filter_by(conta_id=95).all()
        mapa_conta = {(v.ano, v.mes): v.valor for v in valores_conta}
        
        todos_meses = sorted(list(set(list(dados_organizados.keys()) + list(mapa_conta.keys()))))

        for ano, mes in todos_meses:
            # Soma das notas deste mês
            total_notas = sum(i['valor'] for i in dados_organizados.get((ano, mes), []))
            # Valor salvo na conta 95
            total_conta = mapa_conta.get((ano, mes), 0.0)
            
            diff = total_notas - total_conta
            status = "✅ OK" if abs(diff) < 0.01 else f"⚠️ {diff:,.2f}"
            
            if total_notas > 0 or total_conta > 0:
                print(f"{mes:02d}/{ano:<5} | R$ {total_notas:,.2f}    | R$ {total_conta:,.2f}    | {status}")

    print("\n")

if __name__ == "__main__":
    verificar_detalhado_por_mes()