from functools import wraps
from flask import abort
from flask_login import current_user, login_required

def role_required(*roles):
    """Decorator para exigir papéis específicos."""
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def produtor_required(f):
    """Decorator para exigir que o usuário tenha produtor vinculado."""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not hasattr(current_user, 'produtor') or not current_user.produtor:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def has_access_lavoura(lavoura, user=current_user):
    """Verifica se o usuário tem acesso à lavoura."""
    if user.is_admin:
        return True
    if user.is_produtor:
        return lavoura.produtor_id == user.produtor.id
    if user.is_agronoma:
        return lavoura.produtor.agronomist_id == user.id
    return False

def has_access_producao(producao, user=current_user):
    """Verifica se o usuário tem acesso à produção."""
    if user.is_admin:
        return True
    if user.is_produtor:
        return producao.produtor_id == user.produtor.id
    if user.is_agronoma:
        return producao.produtor.agronomist_id == user.id
    return False
