import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from main import db
from sqlalchemy import Boolean, Column, ForeignKey
from sqlalchemy import DateTime, Integer, String, Text, Float
from sqlalchemy.orm import relationship


class Plaga(db.Model):
    __tablename__ = 'sv_plaga'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    nombre_cientifico = db.Column(db.String(80), unique=True, nullable=False)
    hospedante_id = db.Column(db.Integer, db.ForeignKey('sv_hospedante.id', ondelete='CASCADE'), nullable=False)
    hospedante = relationship("Hospedante", backref="Plaga")
    patogeno_id = db.Column(db.Integer, db.ForeignKey('sv_patogeno.id', ondelete='CASCADE'), nullable=False)
    patogeno = relationship("Patogeno", backref="Plaga")
    sintomatologia = db.Column(db.String, nullable=True)
    epidemiologia = db.Column(db.String, nullable=True)
    control = db.Column(db.String, nullable=True)
    otros_datos = db.Column(db.String, nullable=True)
    image = db.Column(db.String(255))

    def save(self):
        if not self.id:
            db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_by_id(id):
        return Plaga.query.get(id)

    def __repr__(self):
        return u'<{self.__class__.__name__}: {self.id}>'.format(self=self)


class Patogeno(db.Model):
    __tablename__ = 'sv_patogeno'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    plaga = relationship("Plaga", cascade="all, delete-orphan",
                         backref="Patogeno", lazy='dynamic')

    def save(self):
        if not self.id:
            db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_by_id(id):
        return Patogeno.query.get(id)

    def __repr__(self):
        return (u'<{self.__class__.__name__}: {self.id}>'.format(self=self))


class Hospedante(db.Model):
    __tablename__ = 'sv_hospedante'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    plaga = relationship("Plaga", cascade="all, delete-orphan",
                         backref="Hospedante", lazy='dynamic')

    def save(self):
        if not self.id:
            db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_by_id(id):
        return Hospedante.query.get(id)

    def __repr__(self):
        return u'<{self.__class__.__name__}: {self.id}>'.format(self=self)


class Muestreo(db.Model):
    __tablename__ = 'sv_muestreo'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    fecha = db.Column(db.DateTime(), default=datetime.datetime.now(), nullable=False)
    plaga_id = db.Column(db.Integer, db.ForeignKey('sv_plaga.id', ondelete='CASCADE'))
    plaga = relationship("Plaga", backref="Muestreo")
    provincia_id = db.Column(db.Integer, db.ForeignKey('sv_provincia.id', ondelete='CASCADE'))
    provincia = relationship("Provincia", backref="Muestreo")
    municipio_id = db.Column(db.Integer, db.ForeignKey('sv_municipio.id', ondelete='CASCADE'))
    municipio = relationship("Municipio", backref="Muestreo")
    latitud = db.Column(db.Float)
    longitud = db.Column(db.Float)
    observacion = db.Column(db.String(255))

    def save(self):
        if not self.id:
            db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_by_id(id):
        return Muestreo.query.get(id)

    def __repr__(self):
        return u'<{self.__class__.__name__}: {self.id}>'.format(self=self)
class PredicionFutura(db.Model):
    __tablename__ = 'sv_prediccion_futura'
    id = db.Column(db.Integer, primary_key=True)
    plaga_id = db.Column(db.Integer, db.ForeignKey('sv_plaga.id', ondelete='CASCADE'))
    plaga = relationship("Plaga", backref="PredicionFutura")
    provincia_id = db.Column(db.Integer, db.ForeignKey('sv_provincia.id', ondelete='CASCADE'))
    provincia = relationship("Provincia", backref="PredicionFutura")


    def save(self):
        if not self.id:
            db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_by_id(id):
        return PredicionFutura.query.get(id)

    def __repr__(self):
        return u'<{self.__class__.__name__}: {self.id}>'.format(self=self)

class Provincia(db.Model):
    __tablename__ = 'sv_provincia'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    # municipio_id = db.Column(db.Integer, db.ForeignKey('sv_municipio.id', ondelete='CASCADE'), nullable=False)
    municipio = relationship("Municipio", cascade="all, delete-orphan", backref="Provincia", lazy='dynamic')
    muestreo = relationship("Muestreo")

    def save(self):
        if not self.id:
            db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_by_id(id):
        return Provincia.query.get(id)

    def __repr__(self):
        return u'<{self.__class__.__name__}: {self.id}>'.format(self=self)


class Municipio(db.Model):
    __tablename__ = 'sv_municipio'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    provincia_id = db.Column(db.Integer, db.ForeignKey('sv_provincia.id', ondelete='CASCADE'), nullable=False)
    provincia = relationship("Provincia")
    muestreo = relationship("Muestreo")

    def save(self):
        if not self.id:
            db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_by_id(id):
        return Municipio.query.get(id)

    def __repr__(self):
        return u'<{self.__class__.__name__}: {self.id}>'.format(self=self)


class User(db.Model, UserMixin):
    __tablename__ = 'sv_user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(256), unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<User {self.email}>'

    def set_password(self, password):
        self.password = password

    def check_password(self, password):
        if self.password.strip() == password.strip():
            return True
        # return check_password_hash(self.password, password)

    def save(self):
        if not self.id:
            db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_by_id(id):
        return User.query.get(id)

    @staticmethod
    def get_by_email(email):
        return User.query.filter_by(email=email).first()
