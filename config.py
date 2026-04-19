import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'chave_secreta_padrao'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///gestao_cafe.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
