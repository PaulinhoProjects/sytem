from . import db
from datetime import datetime
from enum import Enum


class TipoMovimentacao(Enum):
    ENTRADA = "entrada"
    SAIDA = "saida"
    DEVOLUCAO = "devolucao"
    AJUSTE = "ajuste"

class UnidadeMedida(db.Model):
    __tablename__ = 'unidades_medida'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), unique=True, nullable=False)
    sigla = db.Column(db.String(10), unique=True, nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    produtos = db.relationship('Produto', backref='unidade_medida', lazy=True)
    
    def __repr__(self):
        return f'<UnidadeMedida {self.sigla}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'sigla': self.sigla,
            'descricao': self.descricao,
            'ativo': self.ativo
        }

class CategoriaEstoque(db.Model):
    __tablename__ = 'categorias_estoque'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    produtos = db.relationship('Produto', backref='categoria', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<CategoriaEstoque {self.nome}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'ativo': self.ativo
        }

class Produto(db.Model):
    __tablename__ = 'produtos_estoque'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    codigo_interno = db.Column(db.String(50), unique=True, nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias_estoque.id'), nullable=False)
    unidade_medida_id = db.Column(db.Integer, db.ForeignKey('unidades_medida.id'), nullable=False)
    quantidade_minima = db.Column(db.Float, default=0)
    quantidade_maxima = db.Column(db.Float, default=0)
    preco_unitario = db.Column(db.Float, default=0)
    descricao = db.Column(db.Text, nullable=True)
    fornecedor = db.Column(db.String(150), nullable=True)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    movimentacoes = db.relationship('MovimentacaoEstoque', backref='produto', lazy=True, cascade='all, delete-orphan')
    saldos = db.relationship('SaldoEstoque', backref='produto', lazy=True, cascade='all, delete-orphan', uselist=False)
    
    def __repr__(self):
        return f'<Produto {self.nome}>'
    
    def calcular_saldo_atual(self):
        """Calcula o saldo atual do produto baseado em movimentações"""
        saldo = 0
        movimentacoes = MovimentacaoEstoque.query.filter_by(produto_id=self.id).all()
        
        for mov in movimentacoes:
            if mov.tipo == TipoMovimentacao.ENTRADA.value:
                saldo += mov.quantidade
            elif mov.tipo == TipoMovimentacao.SAIDA.value:
                saldo -= mov.quantidade
            elif mov.tipo == TipoMovimentacao.DEVOLUCAO.value:
                saldo += mov.quantidade
            elif mov.tipo == TipoMovimentacao.AJUSTE.value:
                saldo += mov.quantidade  # Pode ser positivo ou negativo
        
        return max(0, saldo)  # Não pode ser negativo
    
    def status_estoque(self):
        """Retorna status do estoque: crítico, baixo, ok ou alto"""
        saldo = self.calcular_saldo_atual()
        
        if saldo <= self.quantidade_minima:
            return 'crítico'
        elif saldo <= (self.quantidade_minima * 1.5):
            return 'baixo'
        elif saldo >= self.quantidade_maxima:
            return 'alto'
        else:
            return 'ok'
    
    def valor_total_estoque(self):
        """Calcula o valor total do estoque deste produto"""
        saldo = self.calcular_saldo_atual()
        return saldo * self.preco_unitario
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'codigo_interno': self.codigo_interno,
            'categoria_id': self.categoria_id,
            'unidade_medida_id': self.unidade_medida_id,
            'quantidade_minima': self.quantidade_minima,
            'quantidade_maxima': self.quantidade_maxima,
            'preco_unitario': self.preco_unitario,
            'saldo_atual': self.calcular_saldo_atual(),
            'status': self.status_estoque(),
            'valor_total': self.valor_total_estoque(),
            'descricao': self.descricao,
            'fornecedor': self.fornecedor,
            'ativo': self.ativo
        }

class MovimentacaoEstoque(db.Model):
    __tablename__ = 'movimentacoes_estoque'
    
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos_estoque.id'), nullable=False)
    produtor_id = db.Column(db.Integer, db.ForeignKey('produtores.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # entrada, saida, devolucao, ajuste
    quantidade = db.Column(db.Float, nullable=False)
    observacao = db.Column(db.Text, nullable=True)
    numero_nf = db.Column(db.String(50), nullable=True)  # Número da Nota Fiscal
    data_movimentacao = db.Column(db.DateTime, default=datetime.utcnow)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    produtor = db.relationship('Produtor', backref='movimentacoes_estoque', foreign_keys=[produtor_id])
    usuario = db.relationship('Usuario', backref='movimentacoes_estoque', foreign_keys=[usuario_id])
    
    def __repr__(self):
        return f'<MovimentacaoEstoque {self.id}: {self.tipo} - {self.quantidade}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'produto_id': self.produto_id,
            'produto_nome': self.produto.nome if self.produto else None,
            'produtor_id': self.produtor_id,
            'usuario_id': self.usuario_id,
            'usuario_nome': self.usuario.nome_usuario if self.usuario else None,
            'tipo': self.tipo,
            'quantidade': self.quantidade,
            'observacao': self.observacao,
            'numero_nf': self.numero_nf,
            'data_movimentacao': self.data_movimentacao.isoformat() if self.data_movimentacao else None,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None
        }

class SaldoEstoque(db.Model):
    __tablename__ = 'saldos_estoque'
    
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos_estoque.id'), nullable=False, unique=True)
    quantidade_atual = db.Column(db.Float, default=0)
    quantidade_reservada = db.Column(db.Float, default=0)
    quantidade_disponivel = db.Column(db.Float, default=0)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SaldoEstoque Produto {self.produto_id}>'
    
    def calcular_disponivel(self):
        """Calcula quantidade disponível (atual - reservada)"""
        self.quantidade_disponivel = max(0, self.quantidade_atual - self.quantidade_reservada)
        return self.quantidade_disponivel
    
    def to_dict(self):
        return {
            'id': self.id,
            'produto_id': self.produto_id,
            'quantidade_atual': self.quantidade_atual,
            'quantidade_reservada': self.quantidade_reservada,
            'quantidade_disponivel': self.quantidade_disponivel,
            'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None
        }

class NotaFiscalEstoque(db.Model):
    __tablename__ = 'notas_fiscais_estoque'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_nf = db.Column(db.String(50), unique=True, nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # entrada ou saida
    fornecedor_id = db.Column(db.String(150), nullable=True)
    produtor_id = db.Column(db.Integer, db.ForeignKey('produtores.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    data_emissao = db.Column(db.Date, nullable=False)
    valor_total = db.Column(db.Float, default=0)
    descricao = db.Column(db.Text, nullable=True)
    arquivo_pdf = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default='pendente')  # pendente, processada, cancelada
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    produtor = db.relationship('Produtor', backref='notas_fiscais', foreign_keys=[produtor_id])
    usuario = db.relationship('Usuario', backref='notas_fiscais', foreign_keys=[usuario_id])
    
    def __repr__(self):
        return f'<NotaFiscalEstoque {self.numero_nf}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'numero_nf': self.numero_nf,
            'tipo': self.tipo,
            'fornecedor_id': self.fornecedor_id,
            'produtor_id': self.produtor_id,
            'usuario_id': self.usuario_id,
            'data_emissao': self.data_emissao.isoformat() if self.data_emissao else None,
            'valor_total': self.valor_total,
            'descricao': self.descricao,
            'status': self.status,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None
        }
