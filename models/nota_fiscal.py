from app import db

class NotaFiscal(db.Model):
    __tablename__ = 'notas_fiscais'

    id = db.Column(db.Integer, primary_key=True)
    chave_externa = db.Column(db.String(100), unique=True, nullable=True) # ID Único do Omie
    
    # Campos simplificados para bater com o serviço
    numero = db.Column(db.String(50))
    descricao = db.Column(db.String(200))
    fornecedor = db.Column(db.String(200))
    valor = db.Column(db.Float)
    data_emissao = db.Column(db.Date)
    
    mes = db.Column(db.Integer)
    ano = db.Column(db.Integer)
    
    conta_id = db.Column(db.Integer, db.ForeignKey('contas.id'))
    categoria = db.Column(db.String(100))
    
    # Campo para saber de qual empresa veio (Empo, Papello, RAO)
    empresa = db.Column(db.String(50)) 

    def __repr__(self):
        return f'<NotaFiscal {self.numero} - R$ {self.valor}>'