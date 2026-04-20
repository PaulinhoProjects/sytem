from flask import Flask, render_template, redirect, url_for, abort
from flask_login import LoginManager, login_required, current_user
import os
from dotenv import load_dotenv

from models import db, Usuario, Lavoura, Producao
from models.alertas import Alerta, PredictaoProducao, ScoreLavoura

load_dotenv()

login_manager = LoginManager()


def create_app(config_name='development'):
    app = Flask(__name__)
    from config import config_by_name
    app.config.from_object(config_by_name[config_name])

    # Upload folder
    app.config.setdefault('UPLOAD_FOLDER', os.path.join(app.root_path, 'uploads'))

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    # ── Blueprints ──────────────────────────────────────────────────────────
    from routes.auth import auth_bp
    from routes.producer import producer_bp
    from routes.lavoura import lavoura_bp
    from routes.producao import producao_bp
    from routes.alertas import alertas_bp
    from routes.estoque import estoque_bp
    from routes.pulverizacao import pulverizacao_bp

    app.register_blueprint(auth_bp,        url_prefix='/auth')
    app.register_blueprint(producer_bp,    url_prefix='/produtor')
    app.register_blueprint(lavoura_bp)
    app.register_blueprint(producao_bp)
    app.register_blueprint(alertas_bp,     url_prefix='/alertas')
    app.register_blueprint(estoque_bp)     # já tem url_prefix='/estoque' definido no blueprint
    app.register_blueprint(pulverizacao_bp) # já tem url_prefix='/pulverizacao'

    # ── Core routes ─────────────────────────────────────────────────────────
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
            producoes = Producao.query.filter_by(
                produtor_id=produtor.id
            ).order_by(Producao.data_colheita.desc()).all()
            total_producao = sum(p.quantidade_kg for p in producoes)
            ultimas_producoes = producoes[:5]
        elif current_user.role in ['AGRONOMA', 'ADM']:
            total_lavouras = Lavoura.query.count()
            producoes = Producao.query.order_by(Producao.data_colheita.desc()).all()
            total_producao = sum(p.quantidade_kg for p in producoes)
            ultimas_producoes = producoes[:5]

        return render_template(
            'dashboard.html',
            produtor=produtor,
            total_lavouras=total_lavouras,
            total_producao=total_producao,
            ultimas_producoes=ultimas_producoes
        )

    @app.route('/relatorios')
    @login_required
    def relatorios():
        if current_user.role not in ['AGRONOMA', 'ADM']:
            abort(403)
        producoes = Producao.query.all()

        agg = {}
        for p in producoes:
            nome = p.lavoura.nome if p.lavoura else 'Sem lavoura'
            agg[nome] = agg.get(nome, 0) + p.quantidade_kg

        chart_labels = list(agg.keys())
        chart_data   = list(agg.values())

        return render_template(
            'relatorios.html',
            producoes=producoes,
            total_quantidade=sum(p.quantidade_kg for p in producoes),
            total_registros=len(producoes),
            chart_labels=chart_labels,
            chart_data=chart_data
        )

    # ── Create tables ───────────────────────────────────────────────────────
    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    app.run(debug=True)
