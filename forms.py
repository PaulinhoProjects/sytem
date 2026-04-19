from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo

class LoginForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Entrar')

class RegisterForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmar Senha', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Papel', choices=[('PRODUTOR', 'Produtor'), ('AGRONOMA', 'Agrônoma'), ('ADM', 'Administrador')], validators=[DataRequired()])
    submit = SubmitField('Cadastrar')

class ProducerForm(FlaskForm):
    name = StringField('Nome do Produtor', validators=[DataRequired()])
    farm_name = StringField('Nome da Fazenda', validators=[DataRequired()])
    location = StringField('Localização', validators=[DataRequired()])
    user_id = IntegerField('ID do Usuário Vinculado', validators=[DataRequired()])
    submit = SubmitField('Cadastrar')
