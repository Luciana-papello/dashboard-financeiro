from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from models import db
from models.conta import Conta
from models.valor_mensal import ValorMensal
from config import Config
import os

# Criar aplicação Flask
app = Flask(__name__)
app.config.from_object(Config)

# Inicializar banco de dados
db.init_app(app)

# Criar pasta database se não existir
os.makedirs(os.path.join(app.root_path, 'database'), exist_ok=True)

@app.route('/')
def index():
    """Rota principal - redireciona para dashboard"""
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    """Dashboard principal"""
    return render_template('dashboard.html')

@app.route('/entrada-dados')
def entrada_dados():
    """Tela de entrada de dados"""
    return render_template('entrada_dados.html')

@app.route('/balanco')
def balanco():
    """Tela de Balanço Patrimonial"""
    return render_template('balanco.html')

@app.route('/dre')
def dre():
    """Tela de DRE"""
    return render_template('dre.html')

@app.route('/capital-giro')
def capital_giro():
    """Tela de Capital de Giro"""
    return render_template('capital_giro.html')

# Função para popular o banco com as contas
def popular_contas():
    """Popula a tabela de contas com a estrutura inicial"""
    
    print("🔄 Verificando se as contas já existem...")
    
    # Se já existem contas, não precisa popular novamente
    if Conta.query.first():
        print("✅ Contas já existem no banco de dados!")
        return
    
    print("📝 Populando contas do Balanço Patrimonial...")
    
    # BALANÇO PATRIMONIAL
    contas_balanco = [
        # DISPONÍVEL
        (29, "CAIXINHA", "DISPONÍVEL", "Balanço", None, True),
        (30, "SICOOB", "DISPONÍVEL", "Balanço", None, True),
        (31, "BRB", "DISPONÍVEL", "Balanço", None, True),
        (32, "BANCO DO BRASIL", "DISPONÍVEL", "Balanço", None, True),
        (33, "IPAG", "DISPONÍVEL", "Balanço", None, True),
        (34, "SANTANDER", "DISPONÍVEL", "Balanço", None, True),
        (35, "BRADESCO", "DISPONÍVEL", "Balanço", None, True),
        (36, "SICOOB _ APLICAÇÃO", "DISPONÍVEL", "Balanço", None, True),
        (37, "TOTAL DISPONÍVEL", "DISPONÍVEL", "Balanço", "29+30+31+32+33+34+35+36", False),
        
        # CRÉDITOS
        (38, "DUPL. A RECEBER VENCIDAS", "CRÉDITOS", "Balanço", None, True),
        (39, "DUPLICATAS A RECEBER A VENCER", "CRÉDITOS", "Balanço", None, True),
        (40, "(-) PENDÊNCIAS JUDICIAIS", "CRÉDITOS", "Balanço", None, True),
        (41, "CIELO / REDE", "CRÉDITOS", "Balanço", None, True),
        (42, "ADIANTAMENTOS A EMPREGADOS", "CRÉDITOS", "Balanço", None, True),
        (43, "ADIANTAMENTOS A FORNECEDORES", "CRÉDITOS", "Balanço", None, True),
        (44, "IMPOSTOS A RECUPERAR", "CRÉDITOS", "Balanço", None, True),
        (45, "TOTAL CRÉDITOS", "CRÉDITOS", "Balanço", "38+39+40+41+42+43+44", False),
        
        # ESTOQUES
        (46, "MATERIA PRIMA", "ESTOQUES", "Balanço", None, True),
        (47, "TAMPAS", "ESTOQUES", "Balanço", None, True),
        (48, "PROD. EM ELABORAÇÃO ( 56 %)", "ESTOQUES", "Balanço", None, True),
        (49, "PRODUTOS ACABADOS ( 70%)", "ESTOQUES", "Balanço", None, True),
        (50, "COMPONENTES MAQUINAS SELAR", "ESTOQUES", "Balanço", None, True),
        (51, "TOTAL ESTOQUES", "ESTOQUES", "Balanço", "46+47+48+49+50", False),
        (52, "TOTAL DO ATIVO CIRCULANTE", "ESTOQUES", "Balanço", "37+45+51", False),
        
        # ATIVO NÃO CIRCULANTE
        (53, "MAQUINAS E EQUIP/VEÍCULOS", "ATIVO NÃO CIRCULANTE", "Balanço", None, True),
        (54, "MAQUINAS COMODATO", "ATIVO NÃO CIRCULANTE", "Balanço", None, True),
        (55, "CONSÓRCIOS", "ATIVO NÃO CIRCULANTE", "Balanço", None, True),
        (56, "TOTAL DO ATIVO NÃO CIRCULANTE", "ATIVO NÃO CIRCULANTE", "Balanço", "53+54+55", False),
        (57, "TOTAL DO ATIVO", "ATIVO NÃO CIRCULANTE", "Balanço", "52+56", False),
        
        # PASSIVO CIRCULANTE
        (58, "FORNECEDORES", "PASSIVO CIRCULANTE", "Balanço", None, True),
        (59, "CONTAS A PAGAR", "PASSIVO CIRCULANTE", "Balanço", None, True),
        (60, "SALÁRIOS A PAGAR", "PASSIVO CIRCULANTE", "Balanço", None, True),
        (61, "COMISSÕES A PAGAR", "PASSIVO CIRCULANTE", "Balanço", None, True),
        (62, "OBRIG.TRAB/PREV. (INSS,FGTS )", "PASSIVO CIRCULANTE", "Balanço", None, True),
        (63, "PARC. DE IMPOSTOS/ CONTRIBUIÇÕES", "PASSIVO CIRCULANTE", "Balanço", None, True),
        (64, "OBRIG. TRIBUT. (ISS,PIS,COFINS,IRRF,IRPJ)", "PASSIVO CIRCULANTE", "Balanço", None, True),
        (65, "FINANC. DE ATIVO CIRCULANTE", "PASSIVO CIRCULANTE", "Balanço", None, True),
        (66, "PROVISÃO P/ FÉRIAS", "PASSIVO CIRCULANTE", "Balanço", None, True),
        (67, "PROVISÃO P/ 13º SALARIO", "PASSIVO CIRCULANTE", "Balanço", None, True),
        (68, "CONSÓRCIO VEÍCULOS", "PASSIVO CIRCULANTE", "Balanço", None, True),
        (69, "FINANCIAMENTO DE ATIVO PERMANENTE", "PASSIVO CIRCULANTE", "Balanço", None, True),
        (70, "ANTECIPAÇÃO DE CLIENTES (SITE)", "PASSIVO CIRCULANTE", "Balanço", None, True),
        (71, "TOTAL DO PASSIVO CIRCULANTE", "PASSIVO CIRCULANTE", "Balanço", "58+59+60+61+62+63+64+65+66+67+68+69+70", False),
        
        # PASSIVO NÃO CIRCULANTE
        (72, "FINANC. DE ATIVO PERMANENTE ( CONSÓRCIOS)", "PASSIVO NÃO CIRCULANTE", "Balanço", None, True),
        (73, "FINANC. DE ATIVO CIRCULANTE", "PASSIVO NÃO CIRCULANTE", "Balanço", None, True),
        (74, "FINANCIAMENTO DE ATIVO PERMANENTE", "PASSIVO NÃO CIRCULANTE", "Balanço", None, True),
        (75, "PARC. DE IMPOSTOS", "PASSIVO NÃO CIRCULANTE", "Balanço", None, True),
        (76, "IMPOST A REGULARIZAR ( IPTU, ISS, PIS, COFINS)", "PASSIVO NÃO CIRCULANTE", "Balanço", None, True),
        (77, "CONTR. A REGULARIZAR ( INSS, FGTS,IRRF)", "PASSIVO NÃO CIRCULANTE", "Balanço", None, True),
        (78, "EMPRES. TERCEIRO (JULIO/SR.ROMEU/BENEDITO)", "PASSIVO NÃO CIRCULANTE", "Balanço", None, True),
        (79, "ENEL ENERGIA A REGULARIZAR", "PASSIVO NÃO CIRCULANTE", "Balanço", None, True),
        (80, "FCO - BANCO DO BRASIL (LOG)", "PASSIVO NÃO CIRCULANTE", "Balanço", None, True),
        (81, "TOTAL DO PASSIVO NÃO CIRCULANTE", "PASSIVO NÃO CIRCULANTE", "Balanço", "72+73+74+75+76+77+78+79+80", False),
        
        # LIQUIDEZ
        (82, "TOTAL DO PATRIMONIO LIQUIDO", "LIQUIDEZ", "Balanço", "57-71-81", False),
        (83, "TOTAL DO PASSIVO", "LIQUIDEZ", "Balanço", "71+81+82", False),
        (84, "LIQUIDEZ CORRENTE", "LIQUIDEZ", "Balanço", "52/71", False),
        (85, "LIQUIDEZ SECA", "LIQUIDEZ", "Balanço", "(52-51-42-43)/71", False),
        (86, "LIQUIDEZ IMEDIATA", "LIQUIDEZ", "Balanço", "37/71", False),
        (87, "CAPITAL CIRCULANTE", "LIQUIDEZ", "Balanço", "52-71", False),
    ]
    
    for id_conta, nome, categoria, tipo, formula, entrada_manual in contas_balanco:
        conta = Conta(
            id=id_conta,
            nome=nome,
            categoria=categoria,
            tipo=tipo,
            formula=formula,
            entrada_manual=entrada_manual
        )
        db.session.add(conta)
    
    print("📝 Populando contas da DRE...")
    
    # DRE
    contas_dre = [
        (1, "Receita Operacional", None, "DRE", None, True),
        (2, "Impostos Sobre Vendas", None, "DRE", None, True),
        (3, "Comissões Sobre Vendas", None, "DRE", None, True),
        (4, "Papeis e Cartões", None, "DRE", None, True),
        (5, "Chapas Offset", None, "DRE", None, True),
        (6, "Tintas e Vernizes", None, "DRE", None, True),
        (7, "Embalagem.(cxs/plast./strech/ fitas,)", None, "DRE", None, True),
        (8, "Industrialização de Terceiros", None, "DRE", None, True),
        (9, "Tampa Plástica/Peças Máquinas Selar", None, "DRE", None, True),
        (10, "Materia prima Indireta / Auxiliar", None, "DRE", None, True),
        (11, "Frete Matéria Prima", None, "DRE", None, True),
        (12, "Frete s/ Vendas", None, "DRE", None, True),
        (13, "Despesas Financeiras", None, "DRE", None, True),
        (14, "Marketing - Octadesck/Facebook/Google", None, "DRE", None, True),
        (15, "Custo Variável", None, "DRE", "2+3+4+5+6+7+8+9+10+11+12+13+14", False),
        (16, "Margem de Contribuição", None, "DRE", "1-15", False),
        (17, "Total Custo Fixo", None, "DRE", None, True),
        (18, "Resultado Operacional", None, "DRE", "16-17", False),
        (19, "Extorno da Despesa Financeira", None, "DRE", None, True),
        (20, "Extorno da Depreciação", None, "DRE", None, True),
        (21, "EBITDA", None, "DRE", "18+19+20", False),
        (22, "Receitas não Operacionais", None, "DRE", None, True),
        (23, "Despesas não Operacionais", None, "DRE", None, True),
        (24, "Pagamento de Imobilizações", None, "DRE", None, True),
        (25, "Parcelamento de Impostos", None, "DRE", None, True),
        (26, "Amortização de Emprestimos", None, "DRE", None, True),
        (27, "FLUXO CAIXA", None, "DRE", "18+22-23-24-25-26", False),
        (28, "FLUXO DE CAIXA LIVRE", None, "DRE", "ACUMULADO", False),
    ]
    
    for id_conta, nome, categoria, tipo, formula, entrada_manual in contas_dre:
        conta = Conta(
            id=id_conta,
            nome=nome,
            categoria=categoria,
            tipo=tipo,
            formula=formula,
            entrada_manual=entrada_manual
        )
        db.session.add(conta)
    
    print("📝 Populando contas de Capital de Giro...")
    
    # CAPITAL DE GIRO
    contas_capital_giro = [
        (88, "NECESSIDADE DE CAPITAL DE GIRO", "NCG", "Capital_Giro", "38+39+41+42+51+43", False),
        (89, "SUSTENTAÇÃO", "SUSTENTACAO", "Capital_Giro", "58+59+60+61+62+64+70", False),
        (90, "NECESSIDADE LÍQUIDA DE CAPITAL DE GIRO", "NCG_LIQUIDA", "Capital_Giro", "88-89", False),
        (91, "TESOURARIA", "TESOURARIA", "Capital_Giro", "90-37", False),
        (92, "DEFICIT A REGULARIZAR", "DEFICIT", "Capital_Giro", "61+95", False),
    ]
    
    for id_conta, nome, categoria, tipo, formula, entrada_manual in contas_capital_giro:
        conta = Conta(
            id=id_conta,
            nome=nome,
            categoria=categoria,
            tipo=tipo,
            formula=formula,
            entrada_manual=entrada_manual
        )
        db.session.add(conta)
    
    # Salvar todas as contas
    db.session.commit()
    print("✅ Contas populadas com sucesso!")

# ============================================
# ROTAS DA API
# ============================================

@app.route('/api/contas-entrada-manual')
def api_contas_entrada_manual():
    """Retorna todas as contas de entrada manual"""
    contas = Conta.query.filter_by(entrada_manual=True).order_by(Conta.id).all()
    return jsonify([conta.to_dict() for conta in contas])

@app.route('/api/valores/<int:mes>/<int:ano>')
def api_valores(mes, ano):
    """Retorna os valores de um mês/ano específico"""
    valores_db = ValorMensal.query.filter_by(mes=mes, ano=ano).all()
    
    # Criar dicionário {conta_id: valor}
    valores = {}
    for v in valores_db:
        valores[v.conta_id] = v.valor
    
    return jsonify(valores)

@app.route('/api/contas-balanco')
def api_contas_balanco():
    """Retorna todas as contas do Balanço Patrimonial"""
    contas = Conta.query.filter_by(tipo='Balanço').order_by(Conta.id).all()
    return jsonify([conta.to_dict() for conta in contas])

@app.route('/api/salvar-dados', methods=['POST'])
def api_salvar_dados():
    """Salva os dados do formulário e executa os cálculos"""
    try:
        dados = request.get_json()
        mes = dados['mes']
        ano = dados['ano']
        valores = dados['valores']
        
        # Salvar cada valor de entrada manual
        for conta_id, valor in valores.items():
            conta_id = int(conta_id)
            valor = float(valor)
            
            # Verificar se já existe
            valor_existente = ValorMensal.query.filter_by(
                conta_id=conta_id,
                mes=mes,
                ano=ano
            ).first()
            
            if valor_existente:
                # Atualizar
                valor_existente.valor = valor
            else:
                # Criar novo
                novo_valor = ValorMensal(
                    conta_id=conta_id,
                    mes=mes,
                    ano=ano,
                    valor=valor
                )
                db.session.add(novo_valor)
        
        db.session.commit()
        
        # EXECUTAR OS CÁLCULOS
        from services.calculadora import calcular_mes
        total_calculadas = calcular_mes(int(mes), int(ano))
        
        return jsonify({
            'success': True, 
            'message': f'Dados salvos! {total_calculadas} contas calculadas automaticamente.'
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao salvar dados: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/contas-dre')
def api_contas_dre():
    """Retorna todas as contas da DRE"""
    contas = Conta.query.filter_by(tipo='DRE').order_by(Conta.id).all()
    return jsonify([conta.to_dict() for conta in contas])

if __name__ == '__main__':
    with app.app_context():
        # Criar todas as tabelas
        print("🔨 Criando banco de dados...")
        db.create_all()
        print("✅ Banco de dados criado!")
        
        # Popular as contas
        popular_contas()
        
        print("\n🚀 Iniciando servidor Flask...")
        print("📍 Acesse: http://127.0.0.1:5000")
        print("🛑 Para parar: Ctrl + C\n")
    
    app.run(debug=True)