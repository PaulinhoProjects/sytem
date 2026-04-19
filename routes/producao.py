from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from datetime import datetime
from models import db, Producao, Lavoura

producao_bp = Blueprint('producao', __name__, url_prefix='/producao')

@producao_bp.route('/list')
@login_required
def listar_producao():
    if current_user.role == 'PRODUTOR' and current_user.produtor:
        producoes = Producao.query.filter_by(produtor_id=current_user.produtor.id).all()
    elif current_user.role in ['AGRONOMA', 'ADM']:
        producoes = Producao.query.all()
    else: producoes = []
    return render_template('producao/listar.html', producoes=producoes)

@producao_bp.route('/nova', methods=['GET', 'POST'])
@login_required
def nova_producao():
    if current_user.role not in ['PRODUTOR', 'ADM']: abort(403)
    if request.method == 'POST':
        lavoura_id, data_colheita, quantidade_kg = request.form.get('lavoura_id'), request.form.get('data_colheita'), request.form.get('quantidade_kg')
        if not all([lavoura_id, data_colheita, quantidade_kg]):
            flash('Campos obrigatórios não preenchidos.', 'error')
            return redirect(request.url)
        lavoura = Lavoura.query.get(lavoura_id)
        producao = Producao(
            lavoura_id=lavoura_id,
            produtor_id=current_user.produtor.id if current_user.role == 'PRODUTOR' else lavoura.produtor_id,
            usuario_id=current_user.id,
            data_colheita=datetime.strptime(data_colheita, '%Y-%m-%d').date(),
            quantidade_kg=float(quantidade_kg),
            qualidade=request.form.get('qualidade'),
            observacoes=request.form.get('observacoes')
        )
        db.session.add(producao)
        db.session.commit()
        flash('Produção registrada com sucesso!', 'success')
        return redirect(url_for('producao.listar_producao'))
    
    lavouras = Lavoura.query.filter_by(produtor_id=current_user.produtor.id).all() if current_user.role == 'PRODUTOR' else Lavoura.query.all()
    return render_template('producao/nova.html', lavouras=lavouras)

@producao_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_producao(id):
    producao = Producao.query.get_or_404(id)
    if current_user.role not in ['PRODUTOR', 'ADM'] or (current_user.role == 'PRODUTOR' and producao.produtor_id != current_user.produtor.id):
        abort(403)
    if request.method == 'POST':
        producao.data_colheita = datetime.strptime(request.form.get('data_colheita'), '%Y-%m-%d').date()
        producao.quantidade_kg = float(request.form.get('quantidade_kg'))
        producao.qualidade = request.form.get('qualidade')
        producao.observacoes = request.form.get('observacoes')
        db.session.commit()
        flash('Produção atualizada com sucesso.', 'success')
        return redirect(url_for('producao.listar_producao'))
    return render_template('producao/editar.html', producao=producao)

@producao_bp.route('/<int:id>/visualizar')
@login_required
def visualizar_producao(id):
    producao = Producao.query.get_or_404(id)
    return render_template('producao/visualizar.html', producao=producao)
