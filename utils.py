from functools import wraps
from flask import abort
from flask_login import current_user
from models import Produtor

def isolamento_produtor(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        produtor_id = kwargs.get('produtor_id')
        if produtor_id:
            produtor = Produtor.query.get(produtor_id)
            if not produtor or (current_user.role != 'ADM' and produtor.usuario_id != current_user.id):
                abort(403)  # Acesso negado
        return f(*args, **kwargs)
    return decorated_function
