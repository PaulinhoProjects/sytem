from flask import Blueprint, render_template
from flask_login import login_required, current_user
from routes.decorators import role_required

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    return render_template('dashboard.html', titulo='Painel Inicial')

@main_bp.route('/dashboard/produtor')
@role_required('PRODUTOR')
def dashboard_produtor():
    return render_template(
        'dashboard.html',
        titulo='Dashboard do Produtor',
        perfil='PRODUTOR'
    )

@main_bp.route('/dashboard/agronoma')
@role_required('AGRONOMA', 'ADM')
def dashboard_agronoma():
    return render_template(
        'dashboard.html',
        titulo='Dashboard da Agrônoma',
        perfil='AGRONOMA'
    )

@main_bp.route('/dashboard/adm')
@role_required('ADM')
def dashboard_adm():
    return render_template(
        'dashboard.html',
        titulo='Dashboard ADM',
        perfil='ADM'
    )
