from models import db
from datetime import datetime

class Pulverizacao(db.Model):
    __tablename__ = 'pulverizacoes'
    id = db.Column(db.Integer, primary_key=True)
    lavoura_id = db.Column(db.Integer, db.ForeignKey('lavouras.id'), nullable=False)
    data_aplicacao = db.Column(db.DateTime, default=datetime.utcnow)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos_estoque.id'))
    dose_por_ha = db.Column(db.Float) # Ex: 2.5 kg/ha
    volume_calda = db.Column(db.Float) # Litros totais
    clima_condicao = db.Column(db.String(100)) # Sol, Nublado, etc
    responsavel_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))

    lavoura = db.relationship('Lavoura', backref='pulverizacoes')
    produto_estoque = db.relationship('ProdutoEstoque')

class CronogramaPulverizacao(db.Model):
    __tablename__ = 'cronograma_pulverizacoes'
    id = db.Column(db.Integer, primary_key=True)
    lavoura_id = db.Column(db.Integer, db.ForeignKey('lavouras.id'))
    data_prevista = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='PENDENTE') # PENDENTE, CONCLUIDO, CANCELADO
    descricao = db.Column(db.String(200))

    lavoura = db.relationship('Lavoura', backref='cronograma')
