from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

from models import db, Usuario, Produtor, Lavoura, Documento
from utils import isolamento_produtor
from routes.auth import auth_bp
from routes.producer import producer_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agro_cafe.db'
app.config['UPLOAD_FOLDER'] = 'uploads/'
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(producer_bp, url_prefix='/produtor')

@app.route('/')
@login_required
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    produtor = None
    if current_user.role == 'PRODUTOR' and current_user.produtor:
        produtor = current_user.produtor
    return render_template('dashboard.html', produtor=produtor)

# ====== NOVAS ROTAS LAVOURA ======

@app.route('/lavouras')
@login_required
def list_lavouras():
    if current_user.role == 'PRODUTOR':
        produtor = Produtor.query.filter_by(usuario_id=current_user.id).first()
        if not produtor:
            abort(403)
        lavouras = Lavoura.query.filter_by(produtor_id=produtor.id).all()
    elif current_user.role == 'AGRONOMA':
        produtores = Produtor.query.filter_by(agronomist_id=current_user.id).all()
        produtor_ids = [p.id for p in produtores]
        lavouras = Lavoura.query.filter(Lavoura.produtor_id.in_(produtor_ids)).all()
    elif current_user.role == 'ADM':
        lavouras = Lavoura.query.all()
    else:
        abort(403)
    return render_template('lavoura/list.html', lavouras=lavouras)

@app.route('/lavoura/<int:id>')
@login_required
def detail_lavoura(id):
    lavoura = Lavoura.query.get_or_404(id)
    if not has_access_to_lavoura(lavoura):
        abort(403)
    documentos = Documento.query.filter_by(lavoura_id=id).all()
    return render_template('lavoura/detail.html', lavoura=lavoura, documentos=documentos)

@app.route('/lavoura/create', methods=['GET', 'POST'])
@login_required
def create_lavoura():
    if current_user.role not in ['PRODUTOR', 'ADM']:
        abort(403)
    produtor = None
    if current_user.role == 'PRODUTOR':
        produtor = Produtor.query.filter_by(usuario_id=current_user.id).first()
        if not produtor:
            abort(403)
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form.get('descricao')
        area = float(request.form['area'])
        produtor_id = request.form.get('produtor_id') if current_user.role == 'ADM' else produtor.id
        lavoura = Lavoura(nome=nome, descricao=descricao, area=area, produtor_id=produtor_id)
        db.session.add(lavoura)
        db.session.commit()
        flash('Lavoura criada com sucesso!')
        return redirect(url_for('list_lavouras'))
    produtores = Produtor.query.all() if current_user.role == 'ADM' else [produtor]
    return render_template('lavoura/create.html', produtores=produtores)

@app.route('/lavoura/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_lavoura(id):
    lavoura = Lavoura.query.get_or_404(id)
    if not has_access_to_lavoura(lavoura):
        abort(403)
    if request.method == 'POST':
        lavoura.nome = request.form['nome']
        lavoura.descricao = request.form.get('descricao')
        lavoura.area = float(request.form['area'])
        db.session.commit()
        flash('Lavoura atualizada com sucesso!')
        return redirect(url_for('detail_lavoura', id=id))
    return render_template('lavoura/edit.html', lavoura=lavoura)

@app.route('/lavoura/<int:id>/delete', methods=['POST'])
@login_required
def delete_lavoura(id):
    lavoura = Lavoura.query.get_or_404(id)
    if not has_access_to_lavoura(lavoura):
        abort(403)
    db.session.delete(lavoura)
    db.session.commit()
    flash('Lavoura excluída com sucesso!')
    return redirect(url_for('list_lavouras'))

def has_access_to_lavoura(lavoura):
    if current_user.role == 'ADM':
        return True
    elif current_user.role == 'PRODUTOR':
        produtor = Produtor.query.filter_by(usuario_id=current_user.id).first()
        return produtor and lavoura.produtor_id == produtor.id
    elif current_user.role == 'AGRONOMA':
        return lavoura.produtor.agronomist_id == current_user.id
    return False

@app.route('/lavoura/<int:id>/upload_documento', methods=['POST'])
@login_required
def upload_documento(id):
    lavoura = Lavoura.query.get_or_404(id)
    if not has_access_to_lavoura(lavoura):
        abort(403)
    if 'file' not in request.files:
        flash('Nenhum arquivo enviado')
        return redirect(url_for('detail_lavoura', id=id))

    file = request.files['file']
    if file.filename != '':
        filename = secure_filename(file.filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        documento = Documento(nome=filename, tipo=filename.split('.')[-1], caminho=file_path, lavoura_id=id)
        db.session.add(documento)
        db.session.commit()
        flash('Documento anexado com sucesso!')
    return redirect(url_for('detail_lavoura', id=id))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
