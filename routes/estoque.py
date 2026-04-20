from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from models import db, Produtor, Usuario
from models.estoque import (
    CategoriaEstoque, UnidadeMedida, Produto,
    MovimentacaoEstoque, SaldoEstoque, NotaFiscalEstoque,
    TipoMovimentacao
)
from utils import role_required
import logging

logger = logging.getLogger(__name__)
estoque_bp = Blueprint('estoque', __name__, url_prefix='/estoque')

# ============ HELPER FUNCTIONS ============

def get_papel(user):
    """Retorna o papel do usuário (compatível com campo 'role')"""
    return user.role

def verificar_acesso_estoque(produtor_id):
    """Verifica se o usuário tem acesso ao estoque do produtor"""
    papel = get_papel(current_user)
    if papel == 'ADM':
        return True
    if papel == 'PRODUTOR':
        produtor = Produtor.query.filter_by(usuario_id=current_user.id).first()
        return produtor and produtor.id == produtor_id
    if papel in ('AGRONOMA', 'AGRONOMO'):
        produtor = Produtor.query.get(produtor_id)
        return produtor and produtor.agronomist_id == current_user.id
    return False

def atualizar_saldo_estoque(produto_id):
    """Atualiza o saldo consolidado do produto baseado nas movimentações"""
    produto = Produto.query.get(produto_id)
    if not produto:
        return False

    saldo_atual = produto.calcular_saldo_atual()
    saldo_obj = SaldoEstoque.query.filter_by(produto_id=produto_id).first()

    if not saldo_obj:
        saldo_obj = SaldoEstoque(produto_id=produto_id, quantidade_atual=saldo_atual)
        db.session.add(saldo_obj)
    else:
        saldo_obj.quantidade_atual = saldo_atual

    saldo_obj.calcular_disponivel()
    db.session.commit()
    return True

# ============ ROTAS CATEGORIAS ============

@estoque_bp.route('/categorias', methods=['GET'])
@login_required
def listar_categorias():
    """Lista todas as categorias de estoque"""
    categorias = CategoriaEstoque.query.filter_by(ativo=True).all()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify([cat.to_dict() for cat in categorias])

    return render_template('estoque/categorias.html', categorias=categorias)

@estoque_bp.route('/categoria/criar', methods=['GET', 'POST'])
@login_required
def criar_categoria():
    """Cria uma nova categoria de estoque"""
    if get_papel(current_user) not in ('ADM', 'AGRONOMA'):
        flash('Acesso não autorizado.', 'error')
        return redirect(url_for('estoque.listar_categorias'))

    if request.method == 'POST':
        try:
            nome = request.form.get('nome', '').strip()
            descricao = request.form.get('descricao', '').strip()

            if not nome:
                flash('Nome da categoria é obrigatório.', 'error')
                return redirect(url_for('estoque.criar_categoria'))

            categoria_existente = CategoriaEstoque.query.filter_by(nome=nome).first()
            if categoria_existente:
                flash('Categoria com este nome já existe.', 'error')
                return redirect(url_for('estoque.criar_categoria'))

            categoria = CategoriaEstoque(nome=nome, descricao=descricao)
            db.session.add(categoria)
            db.session.commit()

            logger.info(f'Categoria criada: {nome} por {current_user.username}')
            flash('Categoria criada com sucesso!', 'success')
            return redirect(url_for('estoque.listar_categorias'))

        except Exception as e:
            db.session.rollback()
            logger.error(f'Erro ao criar categoria: {str(e)}')
            flash('Erro ao criar categoria.', 'error')
            return redirect(url_for('estoque.criar_categoria'))

    return render_template('estoque/criar_categoria.html')

# ============ ROTAS UNIDADES DE MEDIDA ============

@estoque_bp.route('/unidades', methods=['GET'])
@login_required
def listar_unidades():
    """Lista todas as unidades de medida"""
    unidades = UnidadeMedida.query.filter_by(ativo=True).all()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify([un.to_dict() for un in unidades])

    return render_template('estoque/unidades.html', unidades=unidades)

@estoque_bp.route('/unidade/criar', methods=['GET', 'POST'])
@login_required
def criar_unidade():
    """Cria uma nova unidade de medida"""
    if get_papel(current_user) != 'ADM':
        flash('Apenas administradores podem criar unidades.', 'error')
        return redirect(url_for('estoque.listar_unidades'))

    if request.method == 'POST':
        try:
            nome = request.form.get('nome', '').strip()
            sigla = request.form.get('sigla', '').strip().upper()
            descricao = request.form.get('descricao', '').strip()

            if not nome or not sigla:
                flash('Nome e sigla são obrigatórios.', 'error')
                return redirect(url_for('estoque.criar_unidade'))

            unidade_existente = UnidadeMedida.query.filter_by(sigla=sigla).first()
            if unidade_existente:
                flash('Unidade com esta sigla já existe.', 'error')
                return redirect(url_for('estoque.criar_unidade'))

            unidade = UnidadeMedida(nome=nome, sigla=sigla, descricao=descricao)
            db.session.add(unidade)
            db.session.commit()

            logger.info(f'Unidade criada: {sigla} por {current_user.username}')
            flash('Unidade criada com sucesso!', 'success')
            return redirect(url_for('estoque.listar_unidades'))

        except Exception as e:
            db.session.rollback()
            logger.error(f'Erro ao criar unidade: {str(e)}')
            flash('Erro ao criar unidade.', 'error')
            return redirect(url_for('estoque.criar_unidade'))

    return render_template('estoque/criar_unidade.html')

# ============ ROTAS PRODUTOS ============

@estoque_bp.route('/produtos', methods=['GET'])
@login_required
def listar_produtos():
    """Lista produtos de estoque com filtros"""
    page = request.args.get('page', 1, type=int)
    produtos = Produto.query.filter_by(ativo=True).paginate(page=page, per_page=10)
    return render_template('estoque/produtos.html', produtos=produtos)

@estoque_bp.route('/produto/criar', methods=['GET', 'POST'])
@login_required
def criar_produto():
    """Cria um novo produto de estoque"""
    if get_papel(current_user) not in ('ADM', 'AGRONOMA'):
        flash('Acesso não autorizado.', 'error')
        return redirect(url_for('estoque.listar_produtos'))

    categorias = CategoriaEstoque.query.filter_by(ativo=True).all()
    unidades = UnidadeMedida.query.filter_by(ativo=True).all()

    if request.method == 'POST':
        try:
            nome = request.form.get('nome', '').strip()
            codigo_interno = request.form.get('codigo_interno', '').strip()
            categoria_id = request.form.get('categoria_id', type=int)
            unidade_id = request.form.get('unidade_id', type=int)
            quantidade_minima = request.form.get('quantidade_minima', 0, type=float)
            quantidade_maxima = request.form.get('quantidade_maxima', 0, type=float)
            preco_unitario = request.form.get('preco_unitario', 0, type=float)
            fornecedor = request.form.get('fornecedor', '').strip()
            descricao = request.form.get('descricao', '').strip()

            if not all([nome, codigo_interno, categoria_id, unidade_id]):
                flash('Preencha todos os campos obrigatórios.', 'error')
                return redirect(url_for('estoque.criar_produto'))

            produto_existente = Produto.query.filter_by(codigo_interno=codigo_interno).first()
            if produto_existente:
                flash('Produto com este código já existe.', 'error')
                return redirect(url_for('estoque.criar_produto'))

            produto = Produto(
                nome=nome,
                codigo_interno=codigo_interno,
                categoria_id=categoria_id,
                unidade_medida_id=unidade_id,
                quantidade_minima=quantidade_minima,
                quantidade_maxima=quantidade_maxima,
                preco_unitario=preco_unitario,
                fornecedor=fornecedor,
                descricao=descricao
            )
            db.session.add(produto)
            db.session.flush()

            # Criar saldo inicial
            saldo = SaldoEstoque(produto_id=produto.id, quantidade_atual=0,
                                 quantidade_reservada=0, quantidade_disponivel=0)
            db.session.add(saldo)
            db.session.commit()

            logger.info(f'Produto criado: {nome} ({codigo_interno}) por {current_user.username}')
            flash('Produto criado com sucesso!', 'success')
            return redirect(url_for('estoque.listar_produtos'))

        except Exception as e:
            db.session.rollback()
            logger.error(f'Erro ao criar produto: {str(e)}')
            flash('Erro ao criar produto.', 'error')
            return redirect(url_for('estoque.criar_produto'))

    return render_template('estoque/criar_produto.html', categorias=categorias, unidades=unidades)

@estoque_bp.route('/produto/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_produto(id):
    """Edita um produto existente"""
    if get_papel(current_user) not in ('ADM', 'AGRONOMA'):
        flash('Acesso não autorizado.', 'error')
        return redirect(url_for('estoque.listar_produtos'))

    produto = Produto.query.get_or_404(id)
    categorias = CategoriaEstoque.query.filter_by(ativo=True).all()
    unidades = UnidadeMedida.query.filter_by(ativo=True).all()

    if request.method == 'POST':
        try:
            produto.nome = request.form.get('nome', '').strip()
            produto.categoria_id = request.form.get('categoria_id', type=int)
            produto.unidade_medida_id = request.form.get('unidade_id', type=int)
            produto.quantidade_minima = request.form.get('quantidade_minima', type=float)
            produto.quantidade_maxima = request.form.get('quantidade_maxima', type=float)
            produto.preco_unitario = request.form.get('preco_unitario', type=float)
            produto.fornecedor = request.form.get('fornecedor', '').strip()
            produto.descricao = request.form.get('descricao', '').strip()
            produto.atualizado_em = datetime.utcnow()

            db.session.commit()
            logger.info(f'Produto atualizado: {produto.nome} por {current_user.username}')
            flash('Produto atualizado com sucesso!', 'success')
            return redirect(url_for('estoque.listar_produtos'))

        except Exception as e:
            db.session.rollback()
            logger.error(f'Erro ao atualizar produto: {str(e)}')
            flash('Erro ao atualizar produto.', 'error')

    return render_template('estoque/editar_produto.html', produto=produto,
                           categorias=categorias, unidades=unidades)

@estoque_bp.route('/produto/<int:id>/detalhes', methods=['GET'])
@login_required
def detalhes_produto(id):
    """Visualiza detalhes e histórico de movimentações de um produto"""
    produto = Produto.query.get_or_404(id)
    movimentacoes = MovimentacaoEstoque.query.filter_by(produto_id=id).order_by(
        MovimentacaoEstoque.data_movimentacao.desc()
    ).limit(50).all()
    saldo_obj = SaldoEstoque.query.filter_by(produto_id=id).first()

    return render_template(
        'estoque/detalhes_produto.html',
        produto=produto,
        movimentacoes=movimentacoes,
        saldo=saldo_obj
    )

# ============ ROTAS MOVIMENTAÇÕES ============

@estoque_bp.route('/movimentacao/criar', methods=['GET', 'POST'])
@login_required
def criar_movimentacao():
    """Cria uma nova movimentação de estoque"""
    papel = get_papel(current_user)

    if papel == 'PRODUTOR':
        produtor = Produtor.query.filter_by(usuario_id=current_user.id).first()
        if not produtor:
            flash('Nenhum produtor vinculado.', 'error')
            return redirect(url_for('dashboard'))
        produtores = [produtor]
    else:
        produtores = Produtor.query.all()

    produtos = Produto.query.filter_by(ativo=True).all()
    tipos_movimentacao = [tipo.value for tipo in TipoMovimentacao]

    if request.method == 'POST':
        try:
            produto_id = request.form.get('produto_id', type=int)
            produtor_id = request.form.get('produtor_id', type=int)
            tipo = request.form.get('tipo')
            quantidade = request.form.get('quantidade', type=float)
            observacao = request.form.get('observacao', '').strip()
            numero_nf = request.form.get('numero_nf', '').strip()

            if not all([produto_id, produtor_id, tipo, quantidade]):
                flash('Preencha todos os campos obrigatórios.', 'error')
                return redirect(url_for('estoque.criar_movimentacao'))

            if quantidade <= 0:
                flash('Quantidade deve ser maior que zero.', 'error')
                return redirect(url_for('estoque.criar_movimentacao'))

            if tipo not in tipos_movimentacao:
                flash('Tipo de movimentação inválido.', 'error')
                return redirect(url_for('estoque.criar_movimentacao'))

            if not verificar_acesso_estoque(produtor_id):
                flash('Você não tem acesso a este produtor.', 'error')
                return redirect(url_for('estoque.criar_movimentacao'))

            movimentacao = MovimentacaoEstoque(
                produto_id=produto_id,
                produtor_id=produtor_id,
                usuario_id=current_user.id,
                tipo=tipo,
                quantidade=quantidade,
                observacao=observacao,
                numero_nf=numero_nf
            )
            db.session.add(movimentacao)
            db.session.commit()

            atualizar_saldo_estoque(produto_id)

            logger.info(
                f'Movimentação criada: {tipo} de {quantidade} do produto {produto_id} por {current_user.username}'
            )
            flash('Movimentação registrada com sucesso!', 'success')
            return redirect(url_for('estoque.listar_movimentacoes'))

        except Exception as e:
            db.session.rollback()
            logger.error(f'Erro ao criar movimentação: {str(e)}')
            flash('Erro ao registrar movimentação.', 'error')
            return redirect(url_for('estoque.criar_movimentacao'))

    return render_template(
        'estoque/criar_movimentacao.html',
        produtos=produtos,
        produtores=produtores,
        tipos_movimentacao=tipos_movimentacao
    )

@estoque_bp.route('/movimentacoes', methods=['GET'])
@login_required
def listar_movimentacoes():
    """Lista todas as movimentações de estoque"""
    page = request.args.get('page', 1, type=int)
    papel = get_papel(current_user)

    if papel == 'PRODUTOR':
        produtor = Produtor.query.filter_by(usuario_id=current_user.id).first()
        if not produtor:
            flash('Nenhum produtor vinculado.', 'error')
            return redirect(url_for('dashboard'))
        movimentacoes = MovimentacaoEstoque.query.filter_by(
            produtor_id=produtor.id
        ).order_by(MovimentacaoEstoque.data_movimentacao.desc()).paginate(page=page, per_page=20)
    else:
        movimentacoes = MovimentacaoEstoque.query.order_by(
            MovimentacaoEstoque.data_movimentacao.desc()
        ).paginate(page=page, per_page=20)

    return render_template('estoque/movimentacoes.html', movimentacoes=movimentacoes)

# ============ DASHBOARD ESTOQUE ============

@estoque_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard_estoque():
    """Dashboard com resumo do estoque"""
    papel = get_papel(current_user)

    if papel == 'PRODUTOR':
        produtor = Produtor.query.filter_by(usuario_id=current_user.id).first()
        if not produtor:
            flash('Nenhum produtor vinculado.', 'error')
            return redirect(url_for('dashboard'))
        movimentacoes_recentes = MovimentacaoEstoque.query.filter_by(
            produtor_id=produtor.id
        ).order_by(MovimentacaoEstoque.data_movimentacao.desc()).limit(10).all()
    else:
        movimentacoes_recentes = MovimentacaoEstoque.query.order_by(
            MovimentacaoEstoque.data_movimentacao.desc()
        ).limit(10).all()

    produtos = Produto.query.filter_by(ativo=True).all()

    total_produtos = len(produtos)
    produtos_criticos = [p for p in produtos if p.status_estoque() == 'crítico']
    produtos_baixos = [p for p in produtos if p.status_estoque() == 'baixo']
    valor_total_estoque = sum(p.valor_total_estoque() for p in produtos)

    return render_template(
        'estoque/dashboard.html',
        total_produtos=total_produtos,
        produtos_criticos=len(produtos_criticos),
        produtos_baixos=len(produtos_baixos),
        valor_total_estoque=valor_total_estoque,
        movimentacoes_recentes=movimentacoes_recentes,
        produtos=produtos
    )

# ============ ROTAS LEGADAS (compatibilidade) ============

@estoque_bp.route('/', methods=['GET'])
@login_required
def listar():
    """Rota legada — redireciona para o dashboard de estoque"""
    return redirect(url_for('estoque.dashboard_estoque'))

@estoque_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    """Rota legada — redireciona para criar produto"""
    return redirect(url_for('estoque.criar_produto'))

@estoque_bp.route('/movimentar/<int:id>', methods=['GET', 'POST'])
@login_required
def movimentar(id):
    """Rota legada — redireciona para criar movimentação com produto pré-selecionado"""
    return redirect(url_for('estoque.criar_movimentacao', produto_id=id))

# ============ API (JSON) ============

@estoque_bp.route('/api/produto/<int:id>', methods=['GET'])
@login_required
def api_produto(id):
    """Retorna dados JSON de um produto"""
    produto = Produto.query.get_or_404(id)
    return jsonify(produto.to_dict())

@estoque_bp.route('/api/saldo/<int:produto_id>', methods=['GET'])
@login_required
def api_saldo(produto_id):
    """Retorna saldo atual de um produto"""
    saldo_obj = SaldoEstoque.query.filter_by(produto_id=produto_id).first()
    if saldo_obj:
        return jsonify(saldo_obj.to_dict())
    return jsonify({'error': 'Saldo não encontrado'}), 404

@estoque_bp.route('/api/categorias', methods=['GET'])
@login_required
def api_categorias():
    """Retorna categorias em JSON para selects dinâmicos"""
    categorias = CategoriaEstoque.query.filter_by(ativo=True).all()
    return jsonify([c.to_dict() for c in categorias])

@estoque_bp.route('/api/unidades', methods=['GET'])
@login_required
def api_unidades():
    """Retorna unidades de medida em JSON para selects dinâmicos"""
    unidades = UnidadeMedida.query.filter_by(ativo=True).all()
    return jsonify([u.to_dict() for u in unidades])
