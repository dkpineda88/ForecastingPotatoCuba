import os
from cgitb import html
from io import StringIO

from dns.asyncquery import https
from easygui import msgbox, boolbox
# from utils import generate_random_start, generate_from_seed
from flask import Blueprint, request, url_for, jsonify, make_response, Response
from flask import Flask, redirect, flash
from flask import render_template
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from html.parser import HTMLParser

from keras.utils import load_img
from markdown import markdown
from werkzeug.exceptions import abort
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
from tensorflow.keras.models import load_model

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
import numpy as np
import matplotlib.pyplot as plt
# from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.utils import img_to_array

plt.switch_backend('agg')
views = Blueprint("views", __name__)

import models
import psycopg2
import pdfkit
from forms import SignupForm, LoginForm, PlagaForm, HospedanteForm, PatogenoForm, MuestreoForm, PredicionFuturaForm

app = Flask(__name__)
app.config['SECRET_KEY'] = '7110c8ae51a4b5af97be6534caef90e4bb9bdcb3380af008f90b23a5d1616bf319bc298105da20fe'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://openpg:openpgpwd@localhost:5432/splagas'
app.config['IMAGE_UPLOADS'] = "static/upload/"
app.config['MODEL'] = "static/models/model_v1.h5"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
WKHTMLTOPDF_BIN_PATH = r'C:\Program Files\wkhtmltopdf'
PDF_DIR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'pdf')

# from flask_wkhtmltopdf import Wkhtmltopdf
#
# wkhtmltopdf = Wkhtmltopdf(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
Bootstrap(app)

db: SQLAlchemy = SQLAlchemy(app)

posts = []


@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html", num_posts=len(posts))


@app.route("/p/<string:slug>/")
def show_post(slug):
    return render_template("post_view.html", slug_title=slug)


@app.route("/admin/post/<int:post_id>/")
def post_form(post_id=None):
    return render_template("admin/post_form.html", post_id=post_id)


@app.route("/signup_form/", methods=["GET", "POST"])
def show_signup_form():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = SignupForm()
    error = None
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = form.password.data
        # Comprobamos que no hay ya un usuario con ese email
        user = models.User.get_by_email(email)
        if user is not None:
            error = f'El email {email} ya está siendo utilizado por otro usuario'
        else:
            # Creamos el usuario y lo guardamos
            user = models.User(name=name, email=email)
            user.set_password(password)
            user.save()
            # Dejamos al usuario logueado
            login_user(user, remember=True)
            next_page = request.args.get('next', None)
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('index')
            return redirect(next_page)
    return render_template("signup_form.html", form=form, error=error)


@login_manager.user_loader
def load_user(user_id):
    return models.User.get_by_id(int(user_id))


@app.route('/login_form', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = models.User.get_by_email(form.email.data)
        if user is not None and user.check_password(form.password.data):
            print("entro usuario")
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('index')
            return redirect(next_page)
    return render_template('login_form.html', form=form)


#
# @app.route('/plagas_new', methods=['GET', 'POST'])
# @login_required
# def upload_file():
#     form = PlagaForm()
#     if request.method == 'POST':
#         file = request.files['img']
#         filename = secure_filename(file.filename)
#         file.save(os.path.join(app.config['IMAGE_UPLOADS'], filename))
#         img = os.path.join(app.config['IMAGE_UPLOADS'], filename)
#         return render_template('plagas_new.html', img=img,form=form)
#     return render_template('plagas_new.html',form=form)


# @app.route('/perfil/<username>', methods=["get","post"])
# def perfil(username):
#     from models import User
# 	user=User.query.filter_by(username=username).first()
# 	if user is None:
# 		abort(404)
#
# 	form=formUsuario(request.form,obj=user)
# 	del form.password
# 	if form.validate_on_submit():
# 		form.populate_obj(user)
# 		db.session.commit()
# 		return redirect(url_for("inicio"))
#
# 	return render_template("usuarios_new.html",form=form,perfil=True)


@app.route('/muestreo/plagas_list', methods=['GET', 'POST'])
@app.route('/plagas_list', methods=['GET', 'POST'])
@app.route('/plagas_list/<id>', methods=['GET', 'POST'])
def plagaslist():
    from models import Plaga, Hospedante, Patogeno
    hospedantes = Hospedante.query.all()
    patogenos = Patogeno.query.all()
    plagas = Plaga.query.all()
    return render_template("plagas_list.html", plaga=plagas, hospedantes=hospedantes, patogenos=patogenos)


@app.route('/plagas_edit/<int:id>', methods=['GET', 'POST'])
@login_required
def plagas_edit(id):
    from models import Plaga, Hospedante, Patogeno
    # connection = postgres.connect('splagas.db')
    pl = Plaga.query.get(id)
    if pl is None:
        abort(404)
    form = PlagaForm(request.form, obj=pl)
    form.hospedante_id.choices = [(c.id, c.nombre) for c in Hospedante.query.all()[0:]]
    patogeno = [(c.id, c.nombre) for c in Patogeno.query.all()[0:]]
    form.patogeno_id.choices = patogeno
    if form.validate_on_submit():
        if form.photo.data:
            if pl.image:
                os.remove(app.root_path + "/static/upload/" + pl.image)
            try:
                f = form.photo.data
                nombre_fichero = secure_filename(f.filename)
                f.save(app.root_path + "/static/upload/" + nombre_fichero)
            except:
                nombre_fichero = ""
        else:
            nombre_fichero = pl.image
        pl.image = nombre_fichero

        sql = 'update sv_plaga set patogeno_id = %s, nombre = %s ' \
              ', nombre_cientifico= %s,hospedante_id= %s,sintomatologia= %s,' \
              ' epidemiologia= %s, control= %s, otros_datos= %s, image= %s' \
              ' where id=%s'

        updated_rows = 0
        try:
            connection = psycopg2.connect(
                host="localhost",
                database="splagas",
                user='openpg',
                password='openpgpwd')
            cur = connection.cursor()

            pat = form.patogeno_id.data
            nombre = form.nombre.data
            nombre_cientifico = form.nombre_cientifico.data
            hospedante_id = form.hospedante_id.data
            sintomatologia = form.sintomatologia.data
            epidemiologia = form.epidemiologia.data
            control = form.control.data
            otros_datos = form.otros_datos.data

            cur.execute(sql, (pat, nombre, nombre_cientifico, hospedante_id,
                              sintomatologia, epidemiologia, control, otros_datos, nombre_fichero, id))
            # get the number of updated rows
            updated_rows = cur.rowcount
            # Commit the changes to the database
            connection.commit()
            # Close communication with the PostgreSQL database
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if connection is not None:
                connection.close()

        flash('Plaga editada: ' + str(pl.patogeno_id), 'info')
        # msgbox(msg="Plaga editada satisfactoriamente", ok_button='Aceptar', image=Non¨¨e, title='Editar plaga')
        return redirect(url_for("plagaslist"))

    return render_template("plagas_edit.html", form=form, values_pl=pl)


@app.route('/plagas_new', methods=['GET', 'POST'])
@login_required
def plagas_new():
    from models import Plaga, Hospedante, Patogeno
    form = PlagaForm()
    form.hospedante_id.choices = [(c.id, c.nombre) for c in Hospedante.query.all()[0:]]
    patogeno = [(c.id, c.nombre) for c in Patogeno.query.all()[0:]]
    form.patogeno_id.choices = patogeno
    if form.validate_on_submit():
        art = Plaga()
        try:
            f = form.photo.data
            nombre_fichero = secure_filename(f.filename)
            f.save(app.root_path + "/static/upload/" + nombre_fichero)
        except:
            nombre_fichero = ""
        form.populate_obj(art)
        art.image = nombre_fichero
        db.session.add(art)
        db.session.commit()
        db.session.close()
        msgbox(msg='Plaga añadida satisfactoriamente', ok_button='Aceptar', image=None, title='Editar plaga')
        return redirect(url_for("plagaslist"))
    else:
        return render_template('plagas_new.html', form=form)


@app.route('/plagas_list/delete/<id>', methods=["get", "post"])
@login_required
def plagas_delete(id):
    from models import Plaga
    from main import db
    art = Plaga.query.get(id)
    if art is None:
        abort(404)
    form = boolbox(msg="¿Estás seguro que deseas eliminar?", title="Título", choices=['Si', 'No'])
    if form:
        try:
            if art.image:
                os.remove(app.root_path + "/static/upload/" + art.image)
            db.session.delete(art)
            db.session.commit()
            db.session.close()
            flash('Plaga eliminada satisfactoriamente')
        except Exception as e:
            msgbox(msg=e, ok_button='Aceptar', image=None, title='Eliminar plaga')
        return redirect(url_for("plagaslist"))
    else:
        return redirect(url_for("plagaslist"))


@app.route('/hospedantes_list', methods=['GET', 'POST'])
def hospedanteslist():
    from models import Hospedante
    hospedantes = Hospedante.query.all()
    form = HospedanteForm()
    return render_template("hospedantes_list.html", form=form, hospedante=hospedantes)


@app.route('/hospedantes/new', methods=['GET', 'POST'])
@login_required
def hospedantes_new():
    from models import Hospedante
    form = HospedanteForm()
    if form.validate_on_submit():
        art = Hospedante()
        form.populate_obj(art)
        db.session.add(art)
        db.session.commit()
        db.session.close()
        flash('Hospedante añadido satisfactoriamente')
        return redirect(url_for("hospedanteslist"))
    else:
        return render_template('hospedanteslist.html', form=form)


@app.route('/hospedantes_list/<id>/edit', methods=['GET', 'POST'])
def hospedantes_edit(id):
    from models import Hospedante
    pl = Hospedante.query.get(id)
    if pl is None:
        abort(404)
    form = HospedanteForm(request.form, obj=pl)
    if form.validate_on_submit():
        form.populate_obj(pl)
        db.session.commit()
        db.session.close()
        msgbox(msg='Hospedante editado satisfactoriamente', ok_button='Aceptar', image=None, title='Editar hospedante')
        return redirect(url_for("hospedantesedit"))
    return render_template("hospedantes_list.html", form=form)


@app.route('/hospedantes_list/delete/<id>', methods=["get", "post"])
@login_required
def hospedantes_delete(id):
    from models import Hospedante
    from main import db
    art = Hospedante.query.get(id)
    if art is None:
        abort(404)
    form = boolbox(msg="¿Estás seguro que deseas eliminar?", title="Título", choices=['Si', 'No'])
    if form:
        try:
            # if art.photo != "":
            #    os.remove(app.root_path + "/static/upload/" + art.photo)
            db.session.delete(art)
            db.session.commit()
            db.session.close()
            flash('Hospedante eliminado satisfactoriamente')
        except Exception as e:
            msgbox(msg=e, ok_button='Aceptar', image=None, title='Eliminar hospedante')
        return redirect(url_for("hospedanteslist"))
    else:
        return redirect(url_for("hospedanteslist"))


@app.route('/patogenos_list', methods=['GET', 'POST'])
def patogenoslist():
    from models import Patogeno
    patogenos = Patogeno.query.all()
    form = PatogenoForm()
    return render_template("patogenos_list.html", form=form, patogenos=patogenos)


@app.route('/patogenos/new', methods=['GET', 'POST'])
@login_required
def patogenos_new():
    from models import Patogeno
    form = PatogenoForm()
    if form.validate_on_submit():
        art = Patogeno()
        form.populate_obj(art)
        db.session.add(art)
        db.session.commit()
        db.session.close()
        flash('Patógeno añadido satisfactoriamente')
        return redirect(url_for("patogenoslist"))
    else:
        return render_template('patogenos_list.html', form=form)


@app.route('/patogenos_list/delete/<id>', methods=["get", "post"])
@login_required
def patogenos_delete(id):
    from models import Patogeno
    from main import db
    art = Patogeno.query.get(id)
    if art is None:
        abort(404)
    form = boolbox(msg="¿Estás seguro que deseas eliminar?", title="Título", choices=['Si', 'No'])
    if form:
        try:
            # if art.photo != "":
            #    os.remove(app.root_path + "/static/upload/" + art.photo)
            db.session.delete(art)
            db.session.commit()
            db.session.close()
            flash('Patógeno eliminado satisfactoriamente')
        except Exception as e:
            msgbox(msg=e, ok_button='Aceptar', image=None, title='Eliminar patógeno')
        return redirect(url_for("patogenoslist"))
    else:
        return redirect(url_for("patogenoslist"))


@app.route("/pdf_plagas", methods=["get", "post"])
def pdfplagas():
    # config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
    from models import Plaga, Hospedante, Patogeno
    hospedantes = Hospedante.query.all()
    patogenos = Patogeno.query.all()
    plagas = Plaga.query.all()

    return render_template(
        "pdf_plagas.html",
        hospedantes=hospedantes, patogenos=patogenos, plagas=plagas)

    # pdfkit.from_string(html, 'out.pdf',configuration=config)
    # response = make_response(pdf)
    # response.headers["Content-Type"] = "application/pdf"
    # response.headers["Content-Disposition"] = "inline; filename=output.pdf"
    # return html


def to_pdf():
    read_password = app.config.get('READ_PASSWORD')

    input_filename = 'resume.md'
    output_filename = 'resume.pdf'

    with open(input_filename, 'r') as stream:
        html_text = markdown(stream.read(), output_format='html4')
    # render the html template
    output = render_template('pdf_template.html',
                             title=app.config.get('TITLE'),
                             sub_title=app.config.get('SUB_TITLE'),
                             content=html_text)

    # generate pdf file
    pdfkit.from_string(output, output_filename, options=app.config.get('PDF_OPTIONS'), )

    # return send_from_directory(app.config.get('UPLOAD_FOLDER'),
    #                            'resume.pdf', as_attachment=True)


@app.route("/generar_pdf", methods=["get", "post"])
def generar_pdf():
    import pdfkit
    # Get the HTML output
    out = render_template("index2.html")
    pdf = pdfkit.from_string(out, False)
    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = "inline; filename=output.pdf"
    return response
    #     # PDF options
    # options = {
    #         "orientation": "landscape",
    #         "page-size": "A4",
    #         "margin-top": "1.0cm",
    #         "margin-right": "1.0cm",
    #         "margin-bottom": "1.0cm",
    #         "margin-left": "1.0cm",
    #         "encoding": "UTF-8",
    #     }
    #
    #     # Build PDF from HTML
    #
    #
    #     # Download the PDF
    # return Response(pdf, mimetype="application/pdf")
    # import send_files
    # try:
    #     return send_files('/sample.pdf',
    #                      attachment_filename='ohhey.pdf')
    # except Exception as e:
    #     return str(e)

    # from flask import render_template_string
    #
    # path_to_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
    # #
    # # # Define path to HTML file
    # path_to_file = 'pdf_plagas.html'    #
    # # # Point pdfkit configuration to wkhtmltopdf.exe
    # render = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)
    # #
    # # # Convert HTML file to PDF
    # pdf=pdfkit.from_string(path_to_file, output_path='sample.pdf', configuration=render)
    # # response = make_response(pdf)
    # # response.headers["Content-Type"] = "application/pdf"
    # # response.headers["Content-Disposition"] = "inline; filename=output.pdf"
    #
    # return render_template_string(pdf)


@app.route("/plagasexp", methods=["get", "post"])
def plagasexp():
    from flask import make_response
    try:
        config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
        pdf = pdfkit.from_url('Shaurya Stackoverflow', 'SOF.pdf', configuration=config)
        response = make_response(pdf)
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = "inline; filename=output.pdf"
        return response
    except Exception as e:
        print(e)


@app.route('/muestreo_list', methods=['GET', 'POST'])
def muestreolist():
    from models import Muestreo
    muestreolist = Muestreo.query.all()
    plagas = models.Plaga.query.all()
    form = MuestreoForm()
    return render_template("muestreo_list.html", plagas=plagas, form=form, muestreo=muestreolist)


@app.route('/muestreo/new', methods=['GET', 'POST'])
@login_required
def muestreo_new():
    from models import Muestreo, Plaga, Provincia, Municipio
    form = MuestreoForm()
    form.plaga_id.choices = [(c.id, c.nombre) for c in Plaga.query.all()]
    form.provincia_id.choices = [(c.id, c.nombre) for c in Provincia.query.all()[0:]]
    pr = Provincia.query.first()
    form.municipio_id.choices = [(c.id, c.nombre) for c in Municipio.query.filter_by(id=pr.id).all()[0:]]
    if request.method == 'POST':
        art = Muestreo()
        form.populate_obj(art)
        db.session.add(art)
        db.session.commit()
        db.session.close()
        flash('Muestreo añadido satisfactoriamente')
        return redirect(url_for("muestreolist"))
    else:
        return render_template('muestreo_new.html', form=form)


@app.route('/muestreo/new/municipio/<get_municipio>')
@login_required
def municipioporprovincia(get_municipio):
    state = models.Municipio.query.filter_by(provincia_id=get_municipio).all()
    stateArray = []
    for city in state:
        stateObj = {}
        stateObj['id'] = city.id
        stateObj['nombre'] = city.nombre
        stateArray.append(stateObj)
        print(city.nombre)
    return jsonify({'municipioprovincia': stateArray})


@app.route('/muestreo_list/delete/<id>', methods=["get", "post"])
@login_required
def muestreo_delete(id):
    from models import Muestreo
    from main import db
    art = Muestreo.query.get(id)
    if art is None:
        abort(404)
    form = boolbox(msg="¿Estás seguro que deseas eliminar?", title="Título", choices=['Si', 'No'])
    if form:
        try:
            # if art.photo != "":
            #    os.remove(app.root_path + "/static/upload/" + art.photo)
            db.session.delete(art)
            db.session.commit()
            db.session.close()
            flash('Muestreo eliminado satisfactoriamente')
        except Exception as e:
            msgbox(msg=e, ok_button='Aceptar', image=None, title='Eliminar patógeno')
        return redirect(url_for("muestreolist"))
    else:
        return redirect(url_for(",uestreolist"))


##############################################
model = load_model(app.config['MODEL'])
class_names = ['Tizón Temprano', 'Tizón Tardío', 'Sano']


def predict_save(img):
    my_image = load_img(app.config['IMAGE_UPLOADS'] + img, target_size=(128, 128))
    my_image = img_to_array(my_image)
    my_image = np.expand_dims(my_image, 0)

    out = np.round(model.predict(my_image)[0], 2)
    fig = plt.figure(figsize=(8, 5))
    plt.barh(class_names,
             [1, 1, 1],
             edgecolor='gray',
             linewidth=2,
             color='white',
             height=0.5)
    plt.barh(class_names,
             out,
             color='lightgray',
             height=0.5)

    for index, value in enumerate(out):
        plt.text(value / 2, index, f"{100 * value:.2f}%", fontsize=13, fontweight='bold')

    plt.xticks([])
    plt.yticks([0, 1, 2], labels=class_names, fontweight='bold', fontsize=14)
    name = app.config['IMAGE_UPLOADS'] + 'pred_img.png'
    fig.savefig(name, bbox_inches='tight')
    return out


# from jinja2 import Markup
from jinja2.utils import markupsafe

from pyecharts import options as opts
from pyecharts.charts import Bar


def bar_base(input_img) -> Bar:
    eje_y = predict_save(input_img)
    array = []

    for index, value in enumerate(eje_y):
        if index != 1:
            array.append(round(100 * value))
    for index, value in enumerate(eje_y):
        if index == 1:
            array.append(round(100 * value))
    print(array)
    c = (
        Bar()
        .add_xaxis(class_names)
        .add_yaxis("Porciento de probabilidad", array, color='#2E9AFE', category_gap="20%")
        .set_global_opts(title_opts=opts.TitleOpts(title="Probabilidad acorde al modelo"))
    )
    return c


@app.route("/clasificador", methods=["get", "post"])
def clasificar_plaga():
    if request.method == "POST":
        try:
            file = request.files['file']
            input_img = secure_filename(file.filename)
            file.save(app.config['IMAGE_UPLOADS'] + input_img)
            # f = file.data
            # f.save(app.root_path + "/static/upload/" + input_img)
        except:
            nombre_fichero = ""

        var_aux = 0
        out = predict_save(input_img)
        if np.argmax(out) == 2:
            var_aux = 1
        if np.argmax(out) == 1:
            var_aux = 2
        pred = class_names[var_aux]
        c = bar_base(input_img)
        var = markupsafe.Markup(c.render_embed())

        return render_template('clasificador.html', out=var, pred=pred, input_img=input_img, pred_img='pred_img.png')
    return render_template('clasificador.html')


def result_weather_tizon_tardio(lat, lon, elev):
    from datetime import datetime, date, timedelta
    import matplotlib.pyplot as plt
    import pandas as pd
    from meteostat import Point, Daily, Hourly, Stations

    # Set time period hourly
    today = date.today()
    ayer = today - timedelta(1)
    start = datetime(ayer.year, ayer.month, ayer.day)
    end = datetime(today.year, today.month, today.day, 23, 59)

    print(lat)

    # Create Point for Vancouver, BC
    location = Point(lat, lon, elev)

    # Get daily data for 2018
    data_daily = Daily(location, start, end)
    data = Hourly(location, start, end)
    data = data.fetch()
    df = pd.DataFrame(
        {
            "latitude": [lat],
            "longitude": [lon],
            "altitude": [elev],
            "start": start,
            "end": end,
        }
    )
    data = []
    data_humidity = []

    for index, row in df.iterrows():
        point = Point(row['latitude'], row['longitude'])

        daily_data = Daily(point, start, end)
        daily_data = daily_data.fetch()
        data_hourly = Hourly(point, start, end)
        data_hourly = data_hourly.fetch()

        data.append(daily_data)
        data_humidity.append(data_hourly)

    # Concatenate the data from all locations into a single dataframe
    result = pd.concat(data)
    resultH = pd.concat(data_humidity)
    result_humidity = resultH['rhum']

    print(result)
    print(result_humidity)

    # print(data_daily)
    # print(data)
    var_color = 'green'
    return var_color

    # Plot line chart including average, minimum and maximum temperature
    # data.plot(y=['tavg', 'tmin', 'tmax'])
    # plt.show()


def result_temp_openweather(lat, lon, elev):
    print("aqui")
    import requests

    api_key = '4f05590c556c818cb3b2d076038c5693'

    url = f'http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}'

    response = requests.get(url)
    print(response.status_code)
    if response.status_code == 200:
        data = response.json()
        print(data['main']['temp_max'])
        temp_max = round((float(data['main']['temp_max']) - 273.15), 2)
        temp_min = round((float(data['main']['temp_min']) - 273.15), 2)
        temp_med = round((float(data['main']['temp']) - 273.15), 2)
        humidity = data['main']['humidity']
        # humidity_min = data['main']['humidity']['min']
        print(humidity)
        if temp_min >= 11 and humidity >= 84 and temp_max <= 25 and 16 <= temp_med <= 21:
            var_color = 'red'
        elif 8 <= temp_min < 11 and 25 <= temp_max <= 28 and humidity >= 75:
            var_color = 'orange'
        elif (temp_min < 8 and 24 >= temp_max >= 14 and humidity >= 70) \
                or (temp_min < 8 and 33 >= temp_max >= 28 and humidity >= 70):
            var_color = 'yellow'
        else:
            var_color = 'green'
        return var_color


def result_temp_openweather_temprano(lat, lon, elev):
    import requests

    api_key = '4f05590c556c818cb3b2d076038c5693'

    url = f'http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}'

    response = requests.get(url)
    print(response.status_code)
    if response.status_code == 200:
        data = response.json()
        temp_max = round((float(data['main']['temp_max']) - 273.15), 2)
        temp_min = round((float(data['main']['temp_min']) - 273.15), 2)
        temp_med = round((float(data['main']['temp']) - 273.15), 2)
        humidity = data['main']['humidity']
        # rainfall = data['rain']['1h']
        # print(rainfall)
        if temp_min >= 18 and humidity >= 77 and 31 >= temp_max >= 26:
            var_color = 'red'
        elif temp_min >= 15 and 31 >= temp_max >= 26 and humidity >= 73 and 25 >= temp_med >= 23:
            var_color = 'orange'
        elif (temp_min < 15 and 24 >= temp_max < 26 and humidity >= 75) \
                or (temp_min >= 10 and 33 >= temp_max >= 28 and 73 >= humidity >= 70):
            var_color = 'yellow'
        else:
            var_color = 'green'
        return var_color


def result_temperatura(Lat, Long):
    import pandas as pd
    from datetime import datetime
    import matplotlib.pyplot as plt
    from meteostat import Point, Monthly, Stations

    # Set time period
    start = datetime(2023, 12, 14)
    end = datetime(2023, 12, 22)

    # Create Point for
    tpr = Point(Lat, Long)

    # Get monthly data for 2022
    data = Monthly(tpr, start, end)
    data = data.fetch()
    temperatura = data['tavg']
    humedad = data['wspd']
    # data.plot(y=['tavg', 'tmin', 'tmax'])
    # plt.show()
    print(data['tavg'])
    print(humedad)


def obtener_coordenadas():
    from geopy.geocoders import Nominatim
    loc = Nominatim(user_agent="GetLoc")
    getLoc = loc.geocode("Paris")
    print("entre a bainoa")
    print(getLoc.address)


def descripcion_color(color):
    if color == 'yellow':
        return 'Resistence'
    elif color == 'orange':
        return 'Alert'
    elif color == 'red':
        return 'Critic'
    else:
        return 'Unlikely'


@app.route("/prediccion", methods=["get", "post"])
def prediccion_tizon_tardio():
    var_color = 'green'
    var_descripcion = 'No probable'

    # obtener_coordenadas()

    # La antigua Habana
    import folium
    from folium.plugins import MiniMap

    # cuba_mayabeque = folium.Map(location=[21.521757, -77.781167], zoom_start=8)

    cuba_mayabeque = folium.Map(location=[22.7833, -82.15], zoom_start=8)

    # Bainoa
    var_color = result_temp_openweather(23.0177246, -81.9412061, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[23.0177246, -81.9412061], popup='Bainoa(Jaruco)').add_to(cuba_mayabeque)
    folium.Circle(location=[23.0177246, -81.9412061], color=var_color, fill_color='red', radius=40, weight=20,
                  tooltip=var_descripcion).add_to(cuba_mayabeque)
    # # Artemisa
    var_color = result_temp_openweather(22.8, -82.75, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[22.8, -82.75], popup='Artemisa').add_to(cuba_mayabeque)
    folium.Circle(location=[22.8, -82.75], color=var_color, fill_color='red', radius=40, weight=20,
                  tooltip=var_descripcion).add_to(cuba_mayabeque)
    # # Guira de Melena
    var_color = result_weather_tizon_tardio(22.7833, -82.825167, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[22.7833, -82.825167], popup='Guira de Melena').add_to(cuba_mayabeque)
    folium.Circle(location=[22.7833, -82.825167], color=var_color, fill_color='red', radius=40, weight=20,
                  tooltip=var_descripcion).add_to(cuba_mayabeque)

    # Batabanó
    var_color = result_temp_openweather(22.7167, -82.2833, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[22.7167, -82.2833], popup='Batabanó').add_to(cuba_mayabeque)
    folium.Circle(location=[22.7167, -82.2833], color=var_color, fill_color='red', radius=40, weight=20,
                  tooltip=var_descripcion).add_to(cuba_mayabeque)

    # Melena del Sur
    var_color = result_temp_openweather(22.7667, -82.1333, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[22.7667, -82.1333], popup='Melena del Sur').add_to(cuba_mayabeque)
    folium.Circle(location=[22.7667, -82.1333], color=var_color, fill_color='red', radius=40, weight=20,
                  tooltip=var_descripcion).add_to(cuba_mayabeque)

    # Bauta
    var_color = result_temp_openweather(22.9667, -82.5333, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[22.9667, -82.5333], popup='Bauta').add_to(cuba_mayabeque)
    folium.Circle(location=[22.9667, -82.5333], color=var_color, fill_color='red', radius=40, weight=20,
                  tooltip=var_descripcion).add_to(cuba_mayabeque)

    # Tapaste
    var_color = result_temp_openweather(23.0167, -82.1333, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[23.0167, -82.1333], popup='Tapaste(San Jose)').add_to(cuba_mayabeque)
    folium.Circle(location=[23.0167, -82.1333], color=var_color, fill_color='red', radius=40, weight=20,
                  fill_opacity=0.5, tooltip=var_descripcion).add_to(cuba_mayabeque)

    # Nueva Paz
    var_color = result_temp_openweather(22.7633, -81.7581, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[22.7633, -81.7581], popup='Nueva Paz').add_to(cuba_mayabeque)
    folium.Circle(location=[22.7633, -81.7581], color=var_color, fill_color='red', radius=40, weight=20,
                  fill_opacity=0.5, tooltip=var_descripcion).add_to(cuba_mayabeque)

    # Quivican
    var_color = result_temp_openweather(22.8247, -82.3558, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[22.8247, -82.3558], popup='Quivican').add_to(cuba_mayabeque)
    folium.Circle(location=[22.8247, -82.3558], color=var_color, fill_color='red', radius=40, weight=20,
                  fill_opacity=0.5, tooltip=var_descripcion).add_to(cuba_mayabeque)

    # Madruga
    var_color = result_temp_openweather(22.9164, -81.8569, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[22.9164, -81.8569], popup='Madruga').add_to(cuba_mayabeque)
    folium.Circle(location=[22.9164, -81.8569], color=var_color, fill_color='red', radius=40, weight=20,
                  fill_opacity=0.5, tooltip=var_descripcion).add_to(cuba_mayabeque)

    # ######VILLA CLARA
    # # Saua La Grande
    var_color = result_temp_openweather(22.8167, -80.0833, 22)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[22.8167, -80.0833], popup='Saua La Grande').add_to(cuba_mayabeque)
    folium.Circle(location=[22.8167, -80.0833], color=var_color, fill_color='red', radius=40, weight=20,
                  tooltip=var_descripcion).add_to(cuba_mayabeque)

    # El Yabu
    var_color = result_temp_openweather(22.4333, -79.9833, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[22.4333, -79.9833], popup='El Yabu (Santa Clara)').add_to(cuba_mayabeque)
    folium.Circle(location=[22.4333, -79.9833], color=var_color, fill_color='red', radius=40, weight=20,
                  fill_opacity=0.5, tooltip=var_descripcion).add_to(cuba_mayabeque)

    # # Caibarien
    var_color = result_temp_openweather(22.5167, -79.45, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[22.5167, -79.45], popup='Caibarien').add_to(cuba_mayabeque)
    folium.Circle(location=[22.5167, -79.45], color=var_color, fill_color='red', radius=40, weight=20,
                  tooltip=var_descripcion).add_to(cuba_mayabeque)

    # # Remedios
    var_color = result_temp_openweather(22.4922, -79.5456, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[22.4922, -79.5456], popup='Remedios').add_to(cuba_mayabeque)
    folium.Circle(location=[22.4922, -79.5456], color=var_color, fill_color='red', radius=40, weight=20,
                  tooltip=var_descripcion).add_to(cuba_mayabeque)

    # # Santo Domingo
    var_color = result_temp_openweather(22.5836, -80.2383, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[22.5836, -80.2383], popup='Santo Domingo').add_to(cuba_mayabeque)
    folium.Circle(location=[22.5836, -80.2383], color=var_color, fill_color='red', radius=40, weight=20,
                  tooltip=var_descripcion).add_to(cuba_mayabeque)

    # # Quemado de Guines
    var_color = result_temp_openweather(22.8094, -80.27928, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[22.8094, -80.27928], popup='Quemado de Güines').add_to(cuba_mayabeque)
    folium.Circle(location=[22.8094, -80.27928], color=var_color, fill_color='red', radius=40, weight=20,
                  tooltip=var_descripcion).add_to(cuba_mayabeque)
    #

    # ##CIEGO DE AVILA###
    # # Camilo Cienfuegos
    var_color = result_temp_openweather(22.15, -78.75, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[22.15, -78.75], popup='Camilo Cienfuegos').add_to(cuba_mayabeque)
    folium.Circle(location=[22.15, -78.75], color=var_color, fill_color='red', radius=40, weight=20,
                  tooltip=var_descripcion).add_to(cuba_mayabeque)
    #
    # # Jucaro
    var_color = result_temp_openweather(21.6167, -78.85, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[21.6167, -78.85], popup='Jucaro').add_to(cuba_mayabeque)
    folium.Circle(location=[21.6167, -78.85], color=var_color, fill_color='red', radius=40, weight=20,
                  fill_opacity=0.5, tooltip=var_descripcion).add_to(cuba_mayabeque)
    #
    # # Venezuela
    var_color = result_temp_openweather(21.7833, -78.7833, 26)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[21.7833, -78.7833], popup='Venezuela').add_to(cuba_mayabeque)
    folium.Circle(location=[21.7833, -78.7833], color=var_color, fill_color='red', radius=40, weight=20,
                  fill_opacity=0.5, tooltip=var_descripcion).add_to(cuba_mayabeque)
    #
    # # Majagua
    var_color = result_temp_openweather(21.9244, -78.9906, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[21.9244, -78.9906], popup='Majagua').add_to(cuba_mayabeque)
    folium.Circle(location=[21.9244, -78.9906], color=var_color, fill_color='red', radius=40, weight=20,
                  fill_opacity=0.5, tooltip=var_descripcion).add_to(cuba_mayabeque)

    # # Primero de Enero
    var_color = result_temp_openweather(21.9453, -78.4189, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[21.9453, -78.4189], popup='Primero de Enero').add_to(cuba_mayabeque)
    folium.Circle(location=[21.9453, -78.4189], color=var_color, fill_color='red', radius=40, weight=20,
                  fill_opacity=0.5, tooltip=var_descripcion).add_to(cuba_mayabeque)

    # # Ceballos
    var_color = result_temp_openweather(21.9494, -78.7405, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[21.9494, -78.7405], popup='Ceballos(Ciro Redondo)').add_to(cuba_mayabeque)
    folium.Circle(location=[21.9494, -78.7405], color=var_color, fill_color='red', radius=40, weight=20,
                  fill_opacity=0.5, tooltip=var_descripcion).add_to(cuba_mayabeque)

    # # Ciego de Ávila
    var_color = result_temp_openweather(21.8405, -78.7589, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[21.8405, -78.7589], popup='Ciego de Ávila').add_to(cuba_mayabeque)
    folium.Circle(location=[21.8405, -78.7589], color=var_color, fill_color='red', radius=40, weight=20,
                  fill_opacity=0.5, tooltip=var_descripcion).add_to(cuba_mayabeque)

    # # Baraguá
    var_color = result_temp_openweather(21.6822, -78.6244, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[21.6822, -78.6244], popup='Baraguá').add_to(cuba_mayabeque)
    folium.Circle(location=[21.6822, -78.6244], color=var_color, fill_color='red', radius=40, weight=20,
                  fill_opacity=0.5, tooltip=var_descripcion).add_to(cuba_mayabeque)

    folium.TileLayer('stamenterrain').add_to(cuba_mayabeque)
    minimap = MiniMap(tile_layer='stamenterrain')
    cuba_mayabeque.add_child(minimap)

    return render_template('prediccion.html', resultado=cuba_mayabeque._repr_html_())


@app.route("/prediccion_temprano", methods=["get", "post"])
def prediccion_tizon_temprano():
    # La antigua Habana
    import folium
    from folium.plugins import MiniMap

    # cuba_mayabeque = folium.Map(location=[21.521757, -77.781167], zoom_start=8)

    cuba_mayabeque = folium.Map(location=[22.7833, -82.15], zoom_start=8)

    # Bainoa
    var_color = result_temp_openweather_temprano(23.0177246, -81.9412061, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[23.0177246, -81.9412061], popup='Bainoa(Jaruco)').add_to(cuba_mayabeque)
    folium.Circle(location=[23.0177246, -81.9412061], color=var_color, fill_color='red', radius=40, weight=20,
                  tooltip=var_descripcion).add_to(cuba_mayabeque)
    # # Artemisa
    var_color = result_temp_openweather_temprano(22.8, -82.75, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[22.8, -82.75], popup='Artemisa').add_to(cuba_mayabeque)
    folium.Circle(location=[22.8, -82.75], color=var_color, fill_color='red', radius=40, weight=20,
                  tooltip=var_descripcion).add_to(cuba_mayabeque)
    # # Guira de Melena
    var_color = result_temp_openweather_temprano(22.7833, -82.825167, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[22.7833, -82.825167], popup='Guira de Melena').add_to(cuba_mayabeque)
    folium.Circle(location=[22.7833, -82.825167], color=var_color, fill_color='red', radius=40, weight=20,
                  tooltip=var_descripcion).add_to(cuba_mayabeque)

    # Batabanó
    var_color = result_temp_openweather_temprano(22.7167, -82.2833, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[22.7167, -82.2833], popup='Batabanó').add_to(cuba_mayabeque)
    folium.Circle(location=[22.7167, -82.2833], color=var_color, fill_color='red', radius=40, weight=20,
                  tooltip=var_descripcion).add_to(cuba_mayabeque)

    # Melena del Sur
    var_color = result_temp_openweather_temprano(22.7667, -82.1333, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[22.7667, -82.1333], popup='Melena del Sur').add_to(cuba_mayabeque)
    folium.Circle(location=[22.7667, -82.1333], color=var_color, fill_color='red', radius=40, weight=20,
                  tooltip=var_descripcion).add_to(cuba_mayabeque)

    # Bauta
    var_color = result_temp_openweather_temprano(22.9667, -82.5333, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[22.9667, -82.5333], popup='Bauta').add_to(cuba_mayabeque)
    folium.Circle(location=[22.9667, -82.5333], color=var_color, fill_color='red', radius=40, weight=20,
                  tooltip=var_descripcion).add_to(cuba_mayabeque)

    # Tapaste
    var_color = result_temp_openweather_temprano(23.0167, -82.1333, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[23.0167, -82.1333], popup='Tapaste(San Jose)').add_to(cuba_mayabeque)
    folium.Circle(location=[23.0167, -82.1333], color=var_color, fill_color='red', radius=40, weight=20,
                  fill_opacity=0.5, tooltip=var_descripcion).add_to(cuba_mayabeque)

    # Nueva Paz
    var_color = result_temp_openweather_temprano(22.7633, -81.7581, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[22.7633, -81.7581], popup='Nueva Paz').add_to(cuba_mayabeque)
    folium.Circle(location=[22.7633, -81.7581], color=var_color, fill_color='red', radius=40, weight=20,
                  fill_opacity=0.5, tooltip=var_descripcion).add_to(cuba_mayabeque)

    # Quivican
    var_color = result_temp_openweather_temprano(22.8247, -82.3558, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[22.8247, -82.3558], popup='Quivican').add_to(cuba_mayabeque)
    folium.Circle(location=[22.8247, -82.3558], color=var_color, fill_color='red', radius=40, weight=20,
                  fill_opacity=0.5, tooltip=var_descripcion).add_to(cuba_mayabeque)

    # Madruga
    var_color = result_temp_openweather_temprano(22.9164, -81.8569, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[22.9164, -81.8569], popup='Madruga').add_to(cuba_mayabeque)
    folium.Circle(location=[22.9164, -81.8569], color=var_color, fill_color='red', radius=40, weight=20,
                  fill_opacity=0.5, tooltip=var_descripcion).add_to(cuba_mayabeque)

    # ######VILLA CLARA
    # # Saua La Grande
    var_color = result_temp_openweather_temprano(22.8167, -80.0833, 22)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[22.8167, -80.0833], popup='Saua La Grande').add_to(cuba_mayabeque)
    folium.Circle(location=[22.8167, -80.0833], color=var_color, fill_color='red', radius=40, weight=20,
                  tooltip=var_descripcion).add_to(cuba_mayabeque)

    # El Yabu
    var_color = result_temp_openweather_temprano(22.4333, -79.9833, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[22.4333, -79.9833], popup='El Yabu (Santa Clara)').add_to(cuba_mayabeque)
    folium.Circle(location=[22.4333, -79.9833], color=var_color, fill_color='red', radius=40, weight=20,
                  fill_opacity=0.5, tooltip=var_descripcion).add_to(cuba_mayabeque)

    # # Caibarien
    var_color = result_temp_openweather_temprano(22.5167, -79.45, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[22.5167, -79.45], popup='Caibarien').add_to(cuba_mayabeque)
    folium.Circle(location=[22.5167, -79.45], color=var_color, fill_color='red', radius=40, weight=20,
                  tooltip=var_descripcion).add_to(cuba_mayabeque)

    # # Remedios
    var_color = result_temp_openweather_temprano(22.4922, -79.5456, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[22.4922, -79.5456], popup='Remedios').add_to(cuba_mayabeque)
    folium.Circle(location=[22.4922, -79.5456], color=var_color, fill_color='red', radius=40, weight=20,
                  tooltip=var_descripcion).add_to(cuba_mayabeque)

    # # Santo Domingo
    var_color = result_temp_openweather_temprano(22.5836, -80.2383, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[22.5836, -80.2383], popup='Santo Domingo').add_to(cuba_mayabeque)
    folium.Circle(location=[22.5836, -80.2383], color=var_color, fill_color='red', radius=40, weight=20,
                  tooltip=var_descripcion).add_to(cuba_mayabeque)

    # # Quemado de Guines
    var_color = result_temp_openweather_temprano(22.8094, -80.27928, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[22.8094, -80.27928], popup='Quemado de Güines').add_to(cuba_mayabeque)
    folium.Circle(location=[22.8094, -80.27928], color=var_color, fill_color='red', radius=40, weight=20,
                  tooltip=var_descripcion).add_to(cuba_mayabeque)
    #

    # ##CIEGO DE AVILA###
    # # Camilo Cienfuegos
    var_color = result_temp_openweather_temprano(22.15, -78.75, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[22.15, -78.75], popup='Camilo Cienfuegos').add_to(cuba_mayabeque)
    folium.Circle(location=[22.15, -78.75], color=var_color, fill_color='red', radius=40, weight=20,
                  tooltip=var_descripcion).add_to(cuba_mayabeque)
    #
    # # Jucaro
    var_color = result_temp_openweather_temprano(21.6167, -78.85, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[21.6167, -78.85], popup='Jucaro').add_to(cuba_mayabeque)
    folium.Circle(location=[21.6167, -78.85], color=var_color, fill_color='red', radius=40, weight=20,
                  fill_opacity=0.5, tooltip=var_descripcion).add_to(cuba_mayabeque)
    #
    # # Venezuela
    var_color = result_temp_openweather_temprano(21.7833, -78.7833, 26)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[21.7833, -78.7833], popup='Venezuela').add_to(cuba_mayabeque)
    folium.Circle(location=[21.7833, -78.7833], color=var_color, fill_color='red', radius=40, weight=20,
                  fill_opacity=0.5, tooltip=var_descripcion).add_to(cuba_mayabeque)
    #
    # # Majagua
    var_color = result_temp_openweather_temprano(21.9244, -78.9906, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[21.9244, -78.9906], popup='Majagua').add_to(cuba_mayabeque)
    folium.Circle(location=[21.9244, -78.9906], color=var_color, fill_color='red', radius=40, weight=20,
                  fill_opacity=0.5, tooltip=var_descripcion).add_to(cuba_mayabeque)

    # # Primero de Enero
    var_color = result_temp_openweather_temprano(21.9453, -78.4189, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[21.9453, -78.4189], popup='Primero de Enero').add_to(cuba_mayabeque)
    folium.Circle(location=[21.9453, -78.4189], color=var_color, fill_color='red', radius=40, weight=20,
                  fill_opacity=0.5, tooltip=var_descripcion).add_to(cuba_mayabeque)

    # # Ceballos
    var_color = result_temp_openweather_temprano(21.9494, -78.7405, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[21.9494, -78.7405], popup='Ceballos(Ciro Redondo)').add_to(cuba_mayabeque)
    folium.Circle(location=[21.9494, -78.7405], color=var_color, fill_color='red', radius=40, weight=20,
                  fill_opacity=0.5, tooltip=var_descripcion).add_to(cuba_mayabeque)

    # # Ciego de Ávila
    var_color = result_temp_openweather_temprano(21.8405, -78.7589, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[21.8405, -78.7589], popup='Ciego de Ávila').add_to(cuba_mayabeque)
    folium.Circle(location=[21.8405, -78.7589], color=var_color, fill_color='red', radius=40, weight=20,
                  fill_opacity=0.5, tooltip=var_descripcion).add_to(cuba_mayabeque)

    # # Baraguá
    var_color = result_temp_openweather_temprano(21.6822, -78.6244, 0)
    var_descripcion = descripcion_color(var_color)
    folium.Marker(location=[21.6822, -78.6244], popup='Baraguá').add_to(cuba_mayabeque)
    folium.Circle(location=[21.6822, -78.6244], color=var_color, fill_color='red', radius=40, weight=20,
                  fill_opacity=0.5, tooltip=var_descripcion).add_to(cuba_mayabeque)

    folium.TileLayer('stamenterrain').add_to(cuba_mayabeque)
    minimap = MiniMap(tile_layer='stamenterrain')
    cuba_mayabeque.add_child(minimap)

    return render_template('prediccion.html', resultado=cuba_mayabeque._repr_html_())


import io
import base64


def fig_to_base64(fig):
    img = io.BytesIO()
    fig.savefig(img, format='png',
                bbox_inches='tight')
    img.seek(0)

    return base64.b64encode(img.getvalue())


def clasification_tizontardio(temp_min, temp_max, temp_med, humidity, rainfall):
    probabilidad = 0
    if (temp_min >= 11 and humidity >= 84 and temp_max <= 25 and rainfall >= 0.1) \
            or (temp_min >= 11 and humidity >= 84 and temp_max <= 25 and 16 <= temp_med <= 21):
        probabilidad = 100
    elif (temp_min >= 8 and 16 <= temp_max <= 28 and humidity >= 75) \
            or (temp_min >= 11 and humidity >= 84 and temp_max <= 25):
        probabilidad = 80
    elif (temp_min < 8 and 24 >= temp_max >= 14 and humidity >= 70) \
            or (temp_min < 8 and 33 >= temp_max >= 28 and humidity >= 70):
        probabilidad = 50
    else:
        probabilidad = 20
    return probabilidad


def clasification_tizontemprano(temp_max, temp_min, temp_med, humidity, rainfall):
    probabilidad = 0
    if temp_min >= 18 and humidity >= 77 and 31 >= temp_max >= 26 and rainfall >= 0.5:
        probabilidad = 100
    elif (temp_min >= 15 and 31 >= temp_max >= 26 and humidity >= 73 and 25 >= temp_med >= 23) \
            or (temp_min >= 18 and humidity >= 77 and 31 >= temp_max >= 26):
        probabilidad = 80
    elif (temp_min < 15 and 24 >= temp_max < 26 and humidity >= 75) \
            or (temp_min >= 10 and 33 >= temp_max >= 28 and 73 >= humidity >= 70):
        probabilidad = 50
    else:
        probabilidad = 20
    return probabilidad


def calcular_Pday(temp_max, temp_min, temp_med):
    p = 0
    pdays = 0
    if 21 >= temp_med >= 7:
        p = 10 * (1 - (((temp_med - 21) ** 2) / 196))
    elif 30 >= temp_med > 21:
        p = 10 * (1 - (((temp_med - 21) ** 2) / 81))

    pdays1 = 5 * p * temp_min
    pdays2= 8 * p*(((2 * temp_min) + temp_max) / 3)
    pdays3 = 8 * p*((2 * temp_max + temp_min) / 3)
    pdays4 = 3 * p * temp_max
    pdays = (pdays1+pdays2+pdays3+pdays4)/ 24
    return round(pdays, 2)


def clasif_Pdays(pday):
    clasif="Unlikely"
    if 200 < pday <= 258:
        clasif="Resistence"
    elif 258<pday<300:
        clasif= "Alert"
    elif pday>=300:
        clasif = "Crtic"
    return clasif


@app.route("/prediccion_futura", methods=["get", "post"])
def prediccion_futura_mayabeque():
    import pandas as pd
    import cufflinks as cf
    pd.options.plotting.backend = "plotly"
    from datetime import datetime
    import matplotlib.pyplot as plt
    from models import PredicionFutura, Plaga, Provincia, Municipio
    form = PredicionFuturaForm()
    form.plaga_id.choices = [(c.id, c.nombre) for c in Plaga.query.all()[5:7]]
    form.provincia_id.choices = [(c.id, c.nombre) for c in Provincia.query.all()[0:]]
    pr = Provincia.query.first()
    if request.method == 'POST':
        art = PredicionFutura()
        archivo = 'climaData/climaMayabeque.xlsx'
        if form.provincia_id.data == 3:
            archivo = 'climaData/climaVillaClara.xlsx'
        elif form.provincia_id.data == 4:
            archivo = 'climaData/climaCiegoAvila.xlsx'
            print(form.provincia_id.data)
        read_excel = pd.read_excel(archivo, sheet_name='Hoja1', skiprows=[1],
                                   names=['Fecha', 'Temp. Max', 'Temp. Min', 'Temp. Media', 'Humedad relativa',
                                          'Prcipitaciones'])
        df = pd.DataFrame(read_excel)

        ejex, ejey, ejexF, ejeyF, ejexM, ejeyM, ejePday, ejePdayF,ejePdayM, color, ysticks, ysticksF, ysticksM = [], [], [],[], [], [], [], [], [], [], [], [], []
        url_pday, url_marzo = "", ""

        for i, row in df.iterrows():
            date = row['Fecha']
            temp_min = row['Temp. Min']
            temp_max = row['Temp. Max']
            temp_med = row['Temp. Media']
            humidity = row['Humedad relativa']
            rainfall = row['Prcipitaciones']
            current_date = datetime.strptime(str(date), "%Y-%m-%d %H:%M:%S")
            if current_date.year == form.year.data and temp_min and temp_max and humidity and (
                    current_date.month == 1 or current_date.month == 2 or current_date.month == 3):
                if form.plaga_id.data == 26:
                    probabilidad = clasification_tizontardio(temp_max, temp_min, temp_med, humidity, rainfall)
                    pdays=-1
                else:
                    probabilidad = clasification_tizontemprano(temp_max, temp_min, temp_med, humidity, rainfall)
                    pdays = calcular_Pday(temp_max, temp_min, temp_med)
                if probabilidad == 100:
                    var_color = '#FF0000'
                    estado = 'Critic'
                elif probabilidad == 80:
                    var_color = '#FFA500'
                    estado = 'Alert'
                elif probabilidad == 50:
                    var_color = '#FFFF00'
                    estado = 'Resistence'
                else:
                    var_color = '#6B8E23'
                    estado = 'Unlikely'
                newfecha = current_date.day
                if current_date.month == 1:
                    ejex.append(newfecha)
                    ejey.append(probabilidad)
                    ejePday.append(pdays)
                    ysticks.append(estado)
                    color.append(var_color)
                    dfJ = pd.DataFrame({'day': ejex, 'state': ejey, 'est': ysticks})
                    dataPdays = pd.DataFrame({'day': ejex, 'pday': ejePday})
                    # plt.figure(figsize=(5.5, 4))
                    # plt.plot(dfJ['day'], dfJ['state'], marker="o")
                    # plt.yticks(dfJ['state'], ysticks)
                    # plt.xlabel("Days")  # add X-axis label
                    # plt.ylabel("Probable states")  # add Y-axis label
                    # plt.title("January")
                    # plt.savefig('static/upload/plot_enero.png')
                    #url_enero = 'static/upload/plot_enero.png'

                elif current_date.month == 2:
                    ejexF.append(newfecha)
                    ejeyF.append(probabilidad)
                    ejePdayF.append(pdays)
                    color.append(var_color)
                    ysticksF.append(estado)
                    dfF = pd.DataFrame({'day': ejexF, 'state': ejeyF, 'est': ysticksF})
                    dataPdaysF = pd.DataFrame({'day': ejexF, 'pday': ejePdayF})
                    # plt.figure(figsize=(5.5, 4))
                    # plt.plot(dfF['day'], dfF['state'], marker="o")
                    # plt.yticks(dfF['state'], ysticksF)
                    # plt.xlabel("Days")  # add X-axis label
                    # plt.ylabel("Probable states")  # add Y-axis label
                    # plt.title("February")
                    # plt.savefig('static/upload/plot_febrero.png')
                    #url_febrero = 'static/upload/plot_febrero.png'
                elif current_date.month == 3:
                    ejexM.append(newfecha)
                    ejeyM.append(probabilidad)
                    ejePdayM.append(pdays)
                    ysticksM.append(estado)
                    dfM = pd.DataFrame({'day': ejexM, 'state': ejeyM, 'est': ysticksM})
                    dataPdaysM = pd.DataFrame({'day': ejexM, 'pday': ejePdayM})
                    #
                    # plt.figure(figsize=(5.5, 4))
                    # plt.plot(dfM['day'], dfM['state'], marker="o")
                    # plt.xlabel("Days")  # add X-axis label
                    # plt.yticks(dfM['state'], ysticksM)
                    # plt.ylabel("Probable states")  # add Y-axis label
                    # plt.title("March")
                    # plt.savefig('static/upload/plot_marzo.png')
                    # url_marzo = 'static/upload/plot_marzo.png'

        # dt = pd.concat([dfJ, dfF,dfM], axis=1)
        plt.figure(figsize=(10.5, 6))
        plt.plot(dfJ['day'], dfJ['state'], marker="o", label='January')
        plt.yticks(dfJ['state'], dfJ['est'])
        plt.plot(dfF['day'], dfF['state'], marker="o", label='February')
        # plt.yticks(dfF['state'], dfF['est'])
        plt.plot(dfM['day'], dfM['state'], marker="o", label='March')

        frames_st = [dfJ['state'], dfF['state'], dfM['state']]
        result_st = pd.concat(frames_st)

        frames = [dfJ['est'], dfF['est'], dfM['est']]
        result = pd.concat(frames)

        plt.yticks(result_st, result)
        plt.legend()
        plt.xlabel("Days")  # add X-axis label
        # plt.yticks(dfM['state'], ysticksM)
        plt.ylabel("Probable states")  # add Y-axis label
        plt.savefig('static/upload/plot_marzo.png')
        url_marzo = 'static/upload/plot_marzo.png'

        #figura de pdays
        # dt = pd.concat([dfJ, dfF,dfM], axis=1)
        if pdays!=-1:
          plt.figure(figsize=(10.5, 6))
          plt.plot(dataPdays['day'], dataPdays['pday'], marker="o", label='January')
          plt.plot(dataPdaysF['day'], dataPdaysF['pday'], marker="o", label='February')
          plt.plot(dataPdaysM['day'], dataPdaysM['pday'], marker="o", label='March')


          plt.legend()
          plt.xlabel("Days")  # add X-axis label
        # plt.yticks(dfM['state'], ysticksM)
          plt.ylabel("PDays")  # add Y-axis label
          plt.savefig('static/upload/plot_pday.png')
          url_pday = 'static/upload/plot_pday.png'

        # df1 = pd.DataFrame(dt['day'], columns=dt['mes'],values='state')
        # print(df1)
        # dt.pivot(index='day',columns='mes',values='state')
        # df1.plot()

        return render_template('prediccion_futura.html', input_pday=url_pday,
                               input_marzo=url_marzo, form=form)
    else:
        return render_template('prediccion_futura.html', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


if __name__ == "__main__":
    db.create_all()
    app.run(host='0.0.0.0',
            debug=True,
            port=8080)
    db.session.close()
