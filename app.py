from flask import Flask, render_template, redirect, url_for, abort
from flask_login import LoginManager, login_required, current_user
import os

from models import db, Usuario, Lavoura, Producao
from routes.auth import auth_bp
from routes.producer import producer_bp
from routes.lavoura import lavoura_bp
from routes.producao import producao_bp

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
app.register_blueprint(lavoura_bp)
app.register_blueprint(producao_bp)

@app.route('/')
@login_required
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    produtor = current_user.produtor if current_user.role == 'PRODUTOR' else None
    total_lavouras = 0
    total_producao = 0
    ultimas_producoes = []
    
    if current_user.role == 'PRODUTOR' and produtor:
        lavouras = Lavoura.query.filter_by(produtor_id=produtor.id).all()
        total_lavouras = len(lavouras)
        producoes = Producao.query.filter_by(produtor_id=produtor.id).order_by(Producao.data_colheita.desc()).all()
        total_producao = sum(p.quantidade_kg for p in producoes)
        ultimas_producoes = producoes[:5]
    elif current_user.role in ['AGRONOMA', 'ADM']:
        total_lavouras = Lavoura.query.count()
        producoes = Producao.query.order_by(Producao.data_colheita.desc()).all()
        total_producao = sum(p.quantidade_kg for p in producoes)
        ultimas_producoes = producoes[:5]
        
    return render_template('dashboard.html', 
                           produtor=produtor,
                           total_lavouras=total_lavouras,
                           total_producao=total_producao,
                           ultimas_producoes=ultimas_producoes)

@app.route('/relatorios')
@login_required
def relatorios():
    if current_user.role not in ['AGRONOMA', 'ADM']: abort(403)
    producoes = Producao.query.all()
    return render_template('relatorios.html', producoes=producoes, total_quantidade=sum(p.quantidade_kg for p in producoes), total_registros=len(producoes))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
