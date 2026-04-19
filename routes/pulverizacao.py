from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Lavoura
from models_estoque import ProdutoEstoque
from models_pulverizacao import Pulverizacao, CronogramaPulverizacao
from datetime import datetime

pulverizacao_bp = Blueprint('pulverizacao', __name__, url_prefix='/pulverizacao')

@pulverizacao_bp.route('/')
@login_required
def listar():
    aplicacoes = Pulverizacao.query.order_by(Pulverizacao.data_aplicacao.desc()).all()
    return render_template('pulverizacao/listar.html', aplicacoes=aplicacoes)

@pulverizacao_bp.route('/nova', methods=['GET', 'POST'])
@login_required
def nova():
    lavouras = Lavoura.query.all()
    produtos = ProdutoEstoque.query.filter(ProdutoEstoque.categoria == 'Defensivo').all()
    
    if request.method == 'POST':
        lavoura_id = request.form.get('lavoura_id')
        produto_id = request.form.get('produto_id')
        dose = float(request.form.get('dose_por_ha'))
        volume = float(request.form.get('volume_calda'))
        clima = request.form.get('clima')

        nova_app = Pulverizacao(
            lavoura_id=lavoura_id,
            produto_id=produto_id,
            dose_por_ha=dose,
            volume_calda=volume,
            clima_condicao=clima,
            responsavel_id=current_user.id
        )
        
        # Abater do estoque se necessário (opcional - lógica de negócio)
        db.session.add(nova_app)
        db.session.commit()
        flash('Pulverização registrada com sucesso!', 'success')
        return redirect(url_for('pulverizacao.listar'))
        
    return render_template('pulverizacao/nova.html', lavouras=lavouras, produtos=produtos)

@pulverizacao_bp.route('/cronograma')
@login_required
def cronograma():
    itens = CronogramaPulverizacao.query.order_by(CronogramaPulverizacao.data_prevista.asc()).all()
    return render_template('pulverizacao/cronograma.html', itens=itens)
