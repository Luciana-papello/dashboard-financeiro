from models import db

class Conta(db.Model):
    """Modelo da tabela Contas - Define a estrutura de cada conta financeira"""
    
    __tablename__ = 'contas'
    
    # Colunas da tabela
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    categoria = db.Column(db.String(100), nullable=True)
    tipo = db.Column(db.String(50), nullable=False)  # "Balanço", "DRE", "Capital_Giro", "EBITDA"
    formula = db.Column(db.String(500), nullable=True)
    entrada_manual = db.Column(db.Boolean, default=True)
    
    # Relacionamento com ValoresMensais
    valores = db.relationship('ValorMensal', backref='conta', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Conta {self.id}: {self.nome}>'
    
    def to_dict(self):
        """Converte o objeto em dicionário"""
        return {
            'id': self.id,
            'nome': self.nome,
            'categoria': self.categoria,
            'tipo': self.tipo,
            'formula': self.formula,
            'entrada_manual': self.entrada_manual
        }