from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from models import db, Lavoura, Produtor, Documento
from flask import current_app

lavoura_bp = Blueprint('lavoura', __name__, url_prefix='/lavoura')

def has_access_to_lavoura(lavoura):
    if current_user.role == 'ADM': return True
    elif current_user.role == 'PRODUTOR':
        produtor = Produtor.query.filter_by(usuario_id=current_user.id).first()
        return produtor and lavoura.produtor_id == produtor.id
    elif current_user.role == 'AGRONOMA':
        return lavoura.produtor.agronomist_id == current_user.id
    return False

@lavoura_bp.route('/list')
@login_required
def list_lavouras():
    if current_user.role == 'PRODUTOR':
        produtor = Produtor.query.filter_by(usuario_id=current_user.id).first()
        if not produtor: abort(403)
        lavouras = Lavoura.query.filter_by(produtor_id=produtor.id).all()
    elif current_user.role == 'AGRONOMA':
        produtor_ids = [p.id for p in Produtor.query.filter_by(agronomist_id=current_user.id).all()]
        lavouras = Lavoura.query.filter(Lavoura.produtor_id.in_(produtor_ids)).all()
    elif current_user.role == 'ADM':
        lavouras = Lavoura.query.all()
    else: abort(403)
    return render_template('lavoura/list.html', lavouras=lavouras)

@lavoura_bp.route('/<int:id>')
@login_required
def detail_lavoura(id):
    lavoura = Lavoura.query.get_or_404(id)
    if not has_access_to_lavoura(lavoura): abort(403)
    documentos = Documento.query.filter_by(lavoura_id=id).all()
    return render_template('lavoura/detail.html', lavoura=lavoura, documentos=documentos)

@lavoura_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_lavoura():
    if current_user.role not in ['PRODUTOR', 'ADM']: abort(403)
    produtor = Produtor.query.filter_by(usuario_id=current_user.id).first() if current_user.role == 'PRODUTOR' else None
    if current_user.role == 'PRODUTOR' and not produtor: abort(403)
        
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form.get('descricao')
        area = float(request.form['area'])
        produtor_id = request.form.get('produtor_id') if current_user.role == 'ADM' else produtor.id
        lavoura = Lavoura(nome=nome, descricao=descricao, area_plantada=area, produtor_id=produtor_id)
        db.session.add(lavoura)
        db.session.commit()
        flash('Lavoura criada com sucesso!')
        return redirect(url_for('lavoura.list_lavouras'))
    
    produtores = Produtor.query.all() if current_user.role == 'ADM' else [produtor]
    return render_template('lavoura/create.html', produtores=produtores)

@lavoura_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_lavoura(id):
    lavoura = Lavoura.query.get_or_404(id)
    if not has_access_to_lavoura(lavoura): abort(403)
    if request.method == 'POST':
        lavoura.nome = request.form['nome']
        lavoura.descricao = request.form.get('descricao')
        lavoura.area_plantada = float(request.form['area'])
        db.session.commit()
        flash('Lavoura atualizada com sucesso!')
        return redirect(url_for('lavoura.detail_lavoura', id=id))
    return render_template('lavoura/edit.html', lavoura=lavoura)

@lavoura_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_lavoura(id):
    lavoura = Lavoura.query.get_or_404(id)
    if not has_access_to_lavoura(lavoura): abort(403)
    db.session.delete(lavoura)
    db.session.commit()
    flash('Lavoura excluída com sucesso!')
    return redirect(url_for('lavoura.list_lavouras'))

@lavoura_bp.route('/<int:id>/upload', methods=['POST'])
@login_required
def upload_documento(id):
    lavoura = Lavoura.query.get_or_404(id)
    if not has_access_to_lavoura(lavoura): abort(403)
    if 'file' not in request.files: return redirect(url_for('lavoura.detail_lavoura', id=id))
    file = request.files['file']
    if file.filename != '':
        filename = secure_filename(file.filename)
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        documento = Documento(nome=filename, tipo=filename.split('.')[-1], caminho_arquivo=file_path, lavoura_id=id, usuario_id=current_user.id)
        db.session.add(documento)
        db.session.commit()
        flash('Documento anexado com sucesso!')
    return redirect(url_for('lavoura.detail_lavoura', id=id))
