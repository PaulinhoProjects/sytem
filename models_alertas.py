from models import db
from datetime import datetime

class Alerta(db.Model):
    __tablename__ = 'alertas'
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)
    severidade = db.Column(db.String(20), nullable=False)
    produtor_id = db.Column(db.Integer, nullable=False)
    lavoura_id = db.Column(db.Integer, nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    resolvido = db.Column(db.Boolean, default=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_resolucao = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<Alerta {self.id}: {self.tipo} - {self.severidade}>'

    def to_dict(self):
        return {
            'id': self.id,
            'tipo': self.tipo,
            'severidade': self.severidade,
            'produtor_id': self.produtor_id,
            'lavoura_id': self.lavoura_id,
            'mensagem': self.mensagem,
            'resolvido': self.resolvido,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_resolucao': self.data_resolucao.isoformat() if self.data_resolucao else None
        }

class PredictaoProducao(db.Model):
    __tablename__ = 'predictao_producao'
    id = db.Column(db.Integer, primary_key=True)
    lavoura_id = db.Column(db.Integer, nullable=False)
    mes_previsto = db.Column(db.String(20), nullable=False)
    quantidade_estimada = db.Column(db.Float, nullable=False)
    confianca = db.Column(db.Float, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<PredictaoProducao {self.id}: {self.mes_previsto}>'

    def to_dict(self):
        return {
            'id': self.id,
            'lavoura_id': self.lavoura_id,
            'mes_previsto': self.mes_previsto,
            'quantidade_estimada': self.quantidade_estimada,
            'confianca': self.confianca,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None
        }

class ScoreLavoura(db.Model):
    __tablename__ = 'score_lavoura'
    id = db.Column(db.Integer, primary_key=True)
    lavoura_id = db.Column(db.Integer, nullable=False)
    data_calculo = db.Column(db.DateTime, default=datetime.utcnow)
    score_saude = db.Column(db.Float, nullable=False)
    tendencia = db.Column(db.String(20), nullable=False)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<ScoreLavoura {self.id}: {self.score_saude}>'

    def to_dict(self):
        return {
            'id': self.id,
            'lavoura_id': self.lavoura_id,
            'data_calculo': self.data_calculo.isoformat() if self.data_calculo else None,
            'score_saude': self.score_saude,
            'tendencia': self.tendencia,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None
        }
