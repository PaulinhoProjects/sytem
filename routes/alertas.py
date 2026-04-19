from flask import Blueprint, render_template, abort, send_file, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, Produtor
from models_alertas import Alerta
from ml_alertas import MLAlertas
from export_pdf import RelatorioGerador
from datetime import datetime, timedelta

alertas_bp = Blueprint('alertas', __name__)

@alertas_bp.route('/dashboard')
@login_required
def dashboard_agronomico():
    if current_user.role not in ['AGRONOMA', 'ADM']: abort(403)
    
    alertas = Alerta.query.filter_by(resolvido=False).order_by(Alerta.data_criacao.desc()).all()
    return render_template('dashboard_agronomico.html', alertas=alertas)

@alertas_bp.route('/gerar_pdf')
@login_required
def gerar_pdf():
    if current_user.role not in ['AGRONOMA', 'ADM']: abort(403)
    
    gerador = RelatorioGerador(db)
    inicio = datetime.utcnow() - timedelta(days=90)
    fim = datetime.utcnow() + timedelta(days=60) # Inclui previsoes futuras
    
    pdf_buffer = gerador.gerar_relatorio_producao(inicio, fim)
    return send_file(pdf_buffer, as_attachment=True, download_name='Relatorio_Producao_SaaS_Agro.pdf', mimetype='application/pdf')

@alertas_bp.route('/run_ml_job')
@login_required
def run_ml_job():
    if current_user.role not in ['AGRONOMA', 'ADM']: abort(403)
    ml = MLAlertas(db)
    
    alertas_totais = 0
    produtores = Produtor.query.all()
    for prod in produtores:
        alertas_totais += ml.processar_alertas_produtor(prod.id)
        
    flash(f'Inteligência Artificial concluída. {alertas_totais} novos insights/anomalias processados no sistema.', 'success')
    return redirect(url_for('alertas.dashboard_agronomico'))
