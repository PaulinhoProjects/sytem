from functools import wraps
from flask import abort
from flask_login import current_user, login_required

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return abort(401)
            if current_user.papel not in roles:
                return abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
