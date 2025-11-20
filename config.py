import os

# Caminho base do projeto
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Configurações do aplicativo"""
    
    # Chave secreta para sessões (você pode mudar depois)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'chave-secreta-desenvolvimento-otm'
    
    # Configuração do banco de dados SQLite
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'database', 'financeiro.db')
    
    # Desabilita rastreamento de modificações (melhora performance)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Pasta de uploads (caso precise futuramente)
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max