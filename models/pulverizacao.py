from . import db
from datetime import datetime
from enum import Enum

class StatusAplicacao(Enum):
    PLANEJADA = "planejada"
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDA = "concluida"
    CANCELADA = "cancelada"

class SeveridadePraga(Enum):
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"

class ProdutoPulverizacao(db.Model):
    __tablename__ = 'produtos_pulverizacao'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False, unique=True)
    ingrediente_ativo = db.Column(db.String(200), nullable=True)
    tipo = db.Column(db.String(50), nullable=False)  # inseticida, fungicida, herbicida, acaricida
    concentracao = db.Column(db.String(50), nullable=True)
    dose_recomendada = db.Column(db.String(50), nullable=True)
    unidade_dose = db.Column(db.String(20), default='ml')  # ml, g, L, kg
    fabricante = db.Column(db.String(150), nullable=True)
    registro_mapa = db.Column(db.String(50), nullable=True)
    periodo_carencia = db.Column(db.Integer, default=0)  # dias
    descricao = db.Column(db.Text, nullable=True)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<ProdutoPulverizacao {self.nome}>'

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'ingrediente_ativo': self.ingrediente_ativo,
            'tipo': self.tipo,
            'concentracao': self.concentracao,
            'dose_recomendada': self.dose_recomendada,
            'unidade_dose': self.unidade_dose,
            'fabricante': self.fabricante,
            'registro_mapa': self.registro_mapa,
            'periodo_carencia': self.periodo_carencia,
            'ativo': self.ativo
        }


class Praga(db.Model):
    __tablename__ = 'pragas'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False, unique=True)
    nome_cientifico = db.Column(db.String(200), nullable=True)
    tipo = db.Column(db.String(50), nullable=False)  # inseto, fungo, bacteria, virus, nematoide
    descricao = db.Column(db.Text, nullable=True)
    dano_potencial = db.Column(db.Text, nullable=True)
    metodos_controle = db.Column(db.Text, nullable=True)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Praga {self.nome}>'

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'nome_cientifico': self.nome_cientifico,
            'tipo': self.tipo,
            'descricao': self.descricao,
            'dano_potencial': self.dano_potencial,
            'metodos_controle': self.metodos_controle,
            'ativo': self.ativo
        }


class OcorrenciaPraga(db.Model):
    __tablename__ = 'ocorrencias_pragas'

    id = db.Column(db.Integer, primary_key=True)
    lavoura_id = db.Column(db.Integer, db.ForeignKey('lavouras.id'), nullable=False)
    praga_id = db.Column(db.Integer, db.ForeignKey('pragas.id'), nullable=False)
    produtor_id = db.Column(db.Integer, db.ForeignKey('produtores.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    severidade = db.Column(db.String(20), nullable=False)  # baixa, media, alta, critica
    percentual_infestacao = db.Column(db.Float, default=0)
    data_deteccao = db.Column(db.Date, nullable=False)
    observacoes = db.Column(db.Text, nullable=True)
    foto_path = db.Column(db.String(255), nullable=True)
    resolvida = db.Column(db.Boolean, default=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    lavoura = db.relationship('Lavoura', backref='ocorrencias_pragas')
    praga = db.relationship('Praga', backref='ocorrencias')
    produtor = db.relationship('Produtor', backref='ocorrencias_pragas', foreign_keys=[produtor_id])
    usuario = db.relationship('Usuario', backref='ocorrencias_pragas', foreign_keys=[usuario_id])

    def __repr__(self):
        return f'<OcorrenciaPraga {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'lavoura_id': self.lavoura_id,
            'praga_id': self.praga_id,
            'praga_nome': self.praga.nome if self.praga else None,
            'produtor_id': self.produtor_id,
            'severidade': self.severidade,
            'percentual_infestacao': self.percentual_infestacao,
            'data_deteccao': self.data_deteccao.isoformat() if self.data_deteccao else None,
            'observacoes': self.observacoes,
            'resolvida': self.resolvida
        }


class CronogramaPulverizacao(db.Model):
    __tablename__ = 'cronograma_pulverizacoes'

    id = db.Column(db.Integer, primary_key=True)
    lavoura_id = db.Column(db.Integer, db.ForeignKey('lavouras.id'), nullable=False)
    produtor_id = db.Column(db.Integer, db.ForeignKey('produtores.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    data_planejada = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='planejada')  # planejada, em_andamento, concluida, cancelada
    observacoes = db.Column(db.Text, nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    lavoura = db.relationship('Lavoura', backref='cronogramas_pulverizacao')
    produtor = db.relationship('Produtor', backref='cronogramas_pulverizacao', foreign_keys=[produtor_id])
    usuario = db.relationship('Usuario', backref='cronogramas_pulverizacao', foreign_keys=[usuario_id])
    aplicacoes = db.relationship('AplicacaoPulverizacao', backref='cronograma', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<CronogramaPulverizacao {self.titulo}>'

    def to_dict(self):
        return {
            'id': self.id,
            'lavoura_id': self.lavoura_id,
            'produtor_id': self.produtor_id,
            'titulo': self.titulo,
            'descricao': self.descricao,
            'data_planejada': self.data_planejada.isoformat() if self.data_planejada else None,
            'status': self.status,
            'observacoes': self.observacoes
        }


class AplicacaoPulverizacao(db.Model):
    __tablename__ = 'aplicacoes_pulverizacao'

    id = db.Column(db.Integer, primary_key=True)
    cronograma_id = db.Column(db.Integer, db.ForeignKey('cronograma_pulverizacoes.id'), nullable=False)
    lavoura_id = db.Column(db.Integer, db.ForeignKey('lavouras.id'), nullable=False)
    produtor_id = db.Column(db.Integer, db.ForeignKey('produtores.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos_pulverizacao.id'), nullable=False)
    praga_id = db.Column(db.Integer, db.ForeignKey('pragas.id'), nullable=True)

    data_aplicacao = db.Column(db.Date, nullable=False)
    hora_inicio = db.Column(db.Time, nullable=True)
    hora_fim = db.Column(db.Time, nullable=True)

    quantidade_aplicada = db.Column(db.Float, nullable=False)  # na unidade do produto
    area_aplicada = db.Column(db.Float, nullable=False)  # hectares
    volume_calda = db.Column(db.Float, default=0)  # litros

    equipamento_utilizado = db.Column(db.String(150), nullable=True)
    condicoes_clima = db.Column(db.String(100), nullable=True)
    velocidade_vento = db.Column(db.String(20), nullable=True)
    temperatura = db.Column(db.Float, nullable=True)
    umidade = db.Column(db.Float, nullable=True)

    aplicador_nome = db.Column(db.String(150), nullable=True)
    epi_utilizado = db.Column(db.String(200), nullable=True)
    eficacia = db.Column(db.String(20), nullable=True)  # excelente, bom, regular, fraco
    observacoes = db.Column(db.Text, nullable=True)

    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    lavoura = db.relationship('Lavoura', backref='aplicacoes_pulverizacao')
    produtor = db.relationship('Produtor', backref='aplicacoes_pulverizacao', foreign_keys=[produtor_id])
    usuario = db.relationship('Usuario', backref='aplicacoes_pulverizacao', foreign_keys=[usuario_id])
    produto = db.relationship('ProdutoPulverizacao', backref='aplicacoes')
    praga = db.relationship('Praga', backref='aplicacoes')

    def __repr__(self):
        return f'<AplicacaoPulverizacao {self.id}: {self.data_aplicacao}>'

    def calcular_dias_carencia(self):
        """Calcula quantos dias faltam para o fim da carência"""
        if not self.produto or not self.data_aplicacao:
            return 0
        from datetime import date
        data_fim = self.data_aplicacao
        dias_passados = (date.today() - data_fim).days
        return max(0, self.produto.periodo_carencia - dias_passados)

    def to_dict(self):
        return {
            'id': self.id,
            'cronograma_id': self.cronograma_id,
            'lavoura_id': self.lavoura_id,
            'produto_id': self.produto_id,
            'produto_nome': self.produto.nome if self.produto else None,
            'data_aplicacao': self.data_aplicacao.isoformat() if self.data_aplicacao else None,
            'quantidade_aplicada': self.quantidade_aplicada,
            'area_aplicada': self.area_aplicada,
            'eficacia': self.eficacia
        }