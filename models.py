from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    produtor = db.relationship('Produtor', backref='user', uselist=False, cascade='all, delete-orphan', foreign_keys='Produtor.usuario_id')
    producoes = db.relationship('Producao', backref='usuario_rel', lazy=True)
    documentos = db.relationship('Documento', backref='usuario_rel', lazy=True)
    
    @property
    def is_admin(self): return self.role == 'ADM'
    @property
    def is_agronoma(self): return self.role == 'AGRONOMA'
    @property
    def is_produtor(self): return self.role == 'PRODUTOR'

class Produtor(db.Model):
    __tablename__ = 'produtores'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    farm_name = db.Column(db.String(150), nullable=True)
    location = db.Column(db.String(250), nullable=True)
    area_total = db.Column(db.Float)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    agronomist_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    agronomist = db.relationship('Usuario', foreign_keys=[agronomist_id])

class Lavoura(db.Model):
    __tablename__ = 'lavouras'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    area_plantada = db.Column(db.Float, nullable=False)
    variedade_cafe = db.Column(db.String(50))
    data_plantio = db.Column(db.Date)
    status = db.Column(db.String(20), default='Ativa')
    produtor_id = db.Column(db.Integer, db.ForeignKey('produtores.id'), nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    produtor = db.relationship('Produtor', backref=db.backref('lavouras', lazy=True))

class Producao(db.Model):
    __tablename__ = 'producoes'
    id = db.Column(db.Integer, primary_key=True)
    lavoura_id = db.Column(db.Integer, db.ForeignKey('lavouras.id'), nullable=False)
    produtor_id = db.Column(db.Integer, db.ForeignKey('produtores.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    data_colheita = db.Column(db.Date, nullable=False)
    quantidade_kg = db.Column(db.Float, nullable=False)
    qualidade = db.Column(db.String(50))
    observacoes = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    lavoura = db.relationship('Lavoura', backref=db.backref('producoes', lazy=True))
    produtor = db.relationship('Produtor', backref=db.backref('producoes', lazy=True))

class Documento(db.Model):
    __tablename__ = 'documentos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    caminho_arquivo = db.Column(db.String(255), nullable=False)
    lavoura_id = db.Column(db.Integer, db.ForeignKey('lavouras.id'), nullable=True)
    produtor_id = db.Column(db.Integer, db.ForeignKey('produtores.id'), nullable=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    lavoura = db.relationship('Lavoura', backref=db.backref('documentos', lazy=True))
    produtor = db.relationship('Produtor', backref=db.backref('documentos', lazy=True))
