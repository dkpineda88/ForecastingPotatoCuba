from flask_wtf import FlaskForm
from wtforms import Form, StringField, SubmitField, PasswordField, BooleanField, IntegerField, SelectField, \
    TextAreaField, validators, FileField, DateField,FloatField
from wtforms.validators import DataRequired, Email, Length, EqualTo


class SignupForm(FlaskForm):
    name = StringField('Nombre', validators=[DataRequired(), Length(max=64)])
    password = PasswordField('Contraseña', validators=[DataRequired(), EqualTo('password2',
                                                                               message='Las contraseñas deben coincidir')])
    password2 = PasswordField('Repite Contraseña', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Registrar')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember_me = BooleanField('Recuérdame')
    submit = SubmitField('Login')


class PlagaForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    nombre_cientifico = StringField('Nombre científico', validators=[DataRequired()])
    hospedante_id = SelectField('Hospedante', coerce=int, choices=[])
    patogeno_id = SelectField('Patógeno', coerce=int)
    sintomatologia = TextAreaField('Sintomatología')
    epidemiologia = TextAreaField('Epidemiología y Ciclo')
    control = TextAreaField('Control')
    otros_datos = TextAreaField('Otros datos')
    photo = FileField('Selecciona imagen:')
    submit = SubmitField('Aceptar')


class HospedanteForm(FlaskForm):
    nombre = StringField("Nombre:"
                         )
    submit = SubmitField('Enviar')


class PatogenoForm(FlaskForm):
    nombre = StringField("Nombre:"
                         )
    submit = SubmitField('Enviar')


class MuestreoForm(FlaskForm):
    nombre = StringField('Nombre del experto', validators=[DataRequired()])
    fecha = DateField('Fecha', validators=[DataRequired()])
    plsi = BooleanField('Encontró plaga?')
    plaga_id = SelectField('Plaga', coerce=int, choices=[])
    provincia_id = SelectField('Provincia', coerce=int, choices=[])
    municipio_id = SelectField('Municipio', coerce=int, choices=[])
    latitud = FloatField('Latitud')
    longitud = FloatField('Longitud')
    observacion = TextAreaField('Observaciones')
    submit = SubmitField('Aceptar')


class ProvinciaForm(FlaskForm):
    nombre = StringField('Provincia', validators=[DataRequired()])
    submit = SubmitField('Aceptar')


class MunicipioForm(FlaskForm):
    nombre = StringField('Municipio', validators=[DataRequired()])
    provincia_id = SelectField('Provincia', coerce=int, choices=[])
    submit = SubmitField('Aceptar')

class PredicionFuturaForm(FlaskForm):
    plaga_id = SelectField('Pest', coerce=int, choices=[])
    provincia_id = SelectField('Province', coerce=int, choices=[])
    year = IntegerField('Year', default=2024)
    submit = SubmitField('Aceptar')


class FormSINO(FlaskForm):
    si = SubmitField('Si')
    no = SubmitField('No')


class FormClasificar(FlaskForm):
    photo = FileField('Selecciona imagen:')
    submit = SubmitField("Enter")
