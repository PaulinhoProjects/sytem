from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Produtor
from forms import ProducerForm

producer_bp = Blueprint('producer', __name__)

@producer_bp.route('/cadastrar', methods=['GET', 'POST'])
@login_required
def register_producer():
    form = ProducerForm()
    if form.validate_on_submit():
        new_produtor = Produtor(
            name=form.name.data, 
            farm_name=form.farm_name.data,
            location=form.location.data,
            usuario_id=form.user_id.data
        )
        db.session.add(new_produtor)
        db.session.commit()
        flash('Produtor cadastrado com sucesso!')
        return redirect(url_for('producer.list_producers'))
    return render_template('register_producer.html', form=form)

@producer_bp.route('/listar')
@login_required
def list_producers():
    if current_user.role == 'ADM':
        producers = Produtor.query.all()
    else:
        producers = Produtor.query.filter_by(usuario_id=current_user.id).all()
    return render_template('list_producers.html', producers=producers)
