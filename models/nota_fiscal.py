from models import db
from datetime import datetime

class NotaFiscal(db.Model):
    """Modelo da tabela NotasFiscais - Armazena dados de NF-e de entrada"""
    
    __tablename__ = 'notas_fiscais'
    
    # Colunas da tabela
    id = db.Column(db.Integer, primary_key=True)
    tipo_nfe = db.Column(db.String(50))  # 'Entrada' ou 'Saída'
    data_emissao = db.Column(db.Date)
    situacao = db.Column(db.String(100))
    numero_nfe = db.Column(db.String(50))
    cnpj_cpf = db.Column(db.String(20))
    nome_fantasia = db.Column(db.String(200))
    valor_nfe = db.Column(db.Float)
    categorias = db.Column(db.String(200))
    razao_social = db.Column(db.String(200))
    valor_icms = db.Column(db.String(100))
    natureza_operacao = db.Column(db.String(200))
    empresa = db.Column(db.String(200))
    mes = db.Column(db.Integer)  # Extraído da data_emissao
    ano = db.Column(db.Integer)  # Extraído da data_emissao
    data_importacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Índice para melhorar performance
    __table_args__ = (
        db.Index('idx_mes_ano_tipo', 'mes', 'ano', 'tipo_nfe'),
    )
    
    def __repr__(self):
        return f'<NotaFiscal {self.numero_nfe}: R${self.valor_nfe}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tipo_nfe': self.tipo_nfe,
            'data_emissao': self.data_emissao.isoformat() if self.data_emissao else None,
            'numero_nfe': self.numero_nfe,
            'valor_nfe': self.valor_nfe,
            'mes': self.mes,
            'ano': self.ano
        }