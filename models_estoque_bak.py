from models import db
from datetime import datetime

class ProdutoEstoque(db.Model):
    __tablename__ = 'produtos_estoque'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    categoria = db.Column(db.String(50)) # Fertilizante, Defensivo, Ferramenta
    quantidade_atual = db.Column(db.Float, default=0.0)
    unidade_medida = db.Column(db.String(20)) # kg, litros, un
    preco_unitario = db.Column(db.Float, default=0.0)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

class MovimentacaoEstoque(db.Model):
    __tablename__ = 'movimentacoes_estoque'
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos_estoque.id'))
    tipo = db.Column(db.String(10)) # ENTRADA ou SAIDA
    quantidade = db.Column(db.Float, nullable=False)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    observacao = db.Column(db.Text)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))

    produto = db.relationship('ProdutoEstoque', backref='movimentacoes')
