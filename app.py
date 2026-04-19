from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Usuario, Produtor
from utils import isolamento_produtor
from routes.auth import auth_bp
from routes.producer import producer_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agro_cafe.db'
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
