from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    produtor = db.relationship('Produtor', backref='user', uselist=False, cascade='all, delete-orphan', foreign_keys='Produtor.usuario_id')

class Produtor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    farm_name = db.Column(db.String(150), nullable=True)
    location = db.Column(db.String(250), nullable=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    agronomist_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    agronomist = db.relationship('Usuario', foreign_keys=[agronomist_id])

class Lavoura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    area = db.Column(db.Float, nullable=False)  # em hectares
    variedade_cafe = db.Column(db.String(50))
    produtor_id = db.Column(db.Integer, db.ForeignKey('produtor.id'), nullable=False)
    produtor = db.relationship('Produtor', backref=db.backref('lavouras', lazy=True))

class Producao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lavoura_id = db.Column(db.Integer, db.ForeignKey('lavoura.id'), nullable=False)
    produtor_id = db.Column(db.Integer, db.ForeignKey('produtor.id'), nullable=False)
    data_colheita = db.Column(db.Date, nullable=False)
    quantidade_kg = db.Column(db.Float, nullable=False)
    qualidade = db.Column(db.String(50))
    observacoes = db.Column(db.Text)
    lavoura = db.relationship('Lavoura', backref=db.backref('producoes', lazy=True))
    produtor = db.relationship('Produtor', backref=db.backref('producoes', lazy=True))

class Documento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    caminho = db.Column(db.String(255), nullable=False)
    lavoura_id = db.Column(db.Integer, db.ForeignKey('lavoura.id'), nullable=True)
    produtor_id = db.Column(db.Integer, db.ForeignKey('produtor.id'), nullable=True)
    lavoura = db.relationship('Lavoura', backref=db.backref('documentos', lazy=True))
    produtor = db.relationship('Produtor', backref=db.backref('documentos', lazy=True))
