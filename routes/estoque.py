from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db
from models_estoque import ProdutoEstoque, MovimentacaoEstoque

estoque_bp = Blueprint('estoque', __name__, url_prefix='/estoque')

@estoque_bp.route('/')
@login_required
def listar():
    produtos = ProdutoEstoque.query.all()
    return render_template('estoque/listar.html', produtos=produtos)

@estoque_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    if request.method == 'POST':
        nome = request.form.get('nome')
        categoria = request.form.get('categoria')
        quantidade = float(request.form.get('quantidade', 0))
        unidade = request.form.get('unidade_medida')
        preco = float(request.form.get('preco_unitario', 0))

        produto = ProdutoEstoque(
            nome=nome, 
            categoria=categoria, 
            quantidade_atual=quantidade, 
            unidade_medida=unidade,
            preco_unitario=preco,
            usuario_id=current_user.id
        )
        db.session.add(produto)
        
        # Cria movimentação inicial
        if quantidade > 0:
            mov = MovimentacaoEstoque(
                produto=produto,
                tipo='ENTRADA',
                quantidade=quantidade,
                observacao='Saldo Inicial',
                usuario_id=current_user.id
            )
            db.session.add(mov)
            
        db.session.commit()
        flash('Produto cadastrado no estoque!', 'success')
        return redirect(url_for('estoque.listar'))
    return render_template('estoque/novo.html')

@estoque_bp.route('/movimentar/<int:id>', methods=['GET', 'POST'])
@login_required
def movimentar(id):
    produto = ProdutoEstoque.query.get_or_404(id)
    if request.method == 'POST':
        tipo = request.form.get('tipo')
        quantidade = float(request.form.get('quantidade'))
        obs = request.form.get('observacao')

        if tipo == 'SAIDA' and quantidade > produto.quantidade_atual:
            flash('Estoque insuficiente!', 'danger')
            return redirect(url_for('estoque.movimentar', id=id))

        mov = MovimentacaoEstoque(
            produto_id=id,
            tipo=tipo,
            quantidade=quantidade,
            observacao=obs,
            usuario_id=current_user.id
        )
        
        if tipo == 'ENTRADA':
            produto.quantidade_atual += quantidade
        else:
            produto.quantidade_atual -= quantidade

        db.session.add(mov)
        db.session.commit()
        flash('Movimentação registrada!', 'success')
        return redirect(url_for('estoque.listar'))
    return render_template('estoque/movimentar.html', produto=produto)
