from models import db
from datetime import datetime

class ValorMensal(db.Model):
    """Modelo da tabela ValoresMensais - Armazena os valores de cada conta por mês"""
    
    __tablename__ = 'valores_mensais'
    
    # Colunas da tabela
    id = db.Column(db.Integer, primary_key=True)
    conta_id = db.Column(db.Integer, db.ForeignKey('contas.id'), nullable=False)
    mes = db.Column(db.Integer, nullable=False)  # 1 a 12
    ano = db.Column(db.Integer, nullable=False)
    valor = db.Column(db.Float, default=0.0)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Índice para melhorar performance nas consultas
    __table_args__ = (
        db.Index('idx_conta_mes_ano', 'conta_id', 'mes', 'ano'),
    )
    
    def __repr__(self):
        return f'<ValorMensal Conta:{self.conta_id} {self.mes}/{self.ano}: R${self.valor}>'
    
    def to_dict(self):
        """Converte o objeto em dicionário"""
        return {
            'id': self.id,
            'conta_id': self.conta_id,
            'mes': self.mes,
            'ano': self.ano,
            'valor': self.valor,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None
        }