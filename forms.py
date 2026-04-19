from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, FloatField, DateField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange

class LoginForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Entrar')

class RegisterForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired(), Length(min=3, max=150)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Senha', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Papel', choices=[('PRODUTOR', 'Produtor'), ('AGRONOMA', 'Agrônoma'), ('ADM', 'Administrador')], validators=[DataRequired()])
    submit = SubmitField('Cadastrar')

class ProducerForm(FlaskForm):
    name = StringField('Nome do Produtor', validators=[DataRequired(), Length(max=150)])
    farm_name = StringField('Nome da Fazenda', validators=[DataRequired(), Length(max=150)])
    location = StringField('Localização', validators=[Length(max=250)])
    user_id = IntegerField('ID do Usuário', validators=[DataRequired()])
    submit = SubmitField('Cadastrar Produtor')

class LavouraForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired(), Length(max=150)])
    descricao = TextAreaField('Descrição', validators=[Length(max=500)])
    area_plantada = FloatField('Área Plantada (ha)', validators=[DataRequired(), NumberRange(min=0.01)])
    produtor_id = IntegerField('ID do Produtor', validators=[DataRequired()])
    submit = SubmitField('Salvar Lavoura')

class ProducaoForm(FlaskForm):
    lavoura_id = IntegerField('ID da Lavoura', validators=[DataRequired()])
    data_colheita = DateField('Data da Colheita', validators=[DataRequired()], format='%Y-%m-%d')
    quantidade_kg = FloatField('Quantidade (kg)', validators=[DataRequired(), NumberRange(min=0)])
    qualidade = StringField('Qualidade', validators=[Length(max=50)])
    observacoes = TextAreaField('Observações')
    submit = SubmitField('Salvar Produção')

class DocumentoForm(FlaskForm):
    nome = StringField('Nome do Documento', validators=[DataRequired()])
    tipo = SelectField('Tipo', choices=[('contrato', 'Contrato'), ('relatorio', 'Relatório'), ('foto', 'Foto'), ('outro', 'Outro')], validators=[DataRequired()])
    caminho_arquivo = StringField('Caminho do Arquivo', validators=[DataRequired()])
    lavoura_id = IntegerField('ID da Lavoura (opcional)')
    produtor_id = IntegerField('ID do Produtor (opcional)')
    submit = SubmitField('Salvar Documento')
