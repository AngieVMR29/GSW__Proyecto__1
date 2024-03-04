from flask import Flask,  render_template, request, redirect, url_for, session, flash # pip install Flask
from flask_mysqldb import MySQL,MySQLdb # pip install Flask-MySQLdb
from random import sample
from generador import stringAleatorio
import os
import base64
from werkzeug.utils import secure_filename 
from notifypy import Notify


app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads/'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'greensoftworld'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.static_folder = 'static'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
mysql = MySQL(app)

ALLOWED_EXTENSIONS = set(['png','jpg','jpeg','gif'])

@app.route('/')
def home():
    return render_template('/inicio.html')

@app.route('/404')
def not_found():
    return 'url no encontrada'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/registrogsw', methods = ["GET", "POST"])
def registrogsw():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM tipo_documento")
    tipo = cur.fetchall()
    print(tipo)

    return render_template('/registrate.html', tipos = tipo)


@app.route('/iniciogsw', methods =['POST', 'GET'])
def iniciogsw():
    notificacion = Notify()
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM persona WHERE Email = %s AND Password = %s",(email, password,))
        persona = cur.fetchone()

        if persona:
            if password == persona["Password"]:
                session['email'] = persona['Email']
                Id_Persona = persona['Id_Persona']

                cur = mysql.connection.cursor()
                cur.execute("SELECT * FROM asignacion_roles WHERE id_Persona1_FK = %s",(Id_Persona,))
                persona = cur.fetchone()

                if persona['id_roles_fk'] == 1 or persona['id_roles_fk'] == 2:
                    return redirect(url_for('administrador'))
                elif persona['id_roles_fk'] == 3 or persona['id_roles_fk'] == 4:
                    return redirect(url_for('usuario'))
            else:
                notificacion.title = "Datos incorrectos, valida nuevamente"
                notificacion.message="Correo o contraseña no valida"
                notificacion.send()
                return render_template("inicios.html")
        else:
            notificacion.title = "Error de Acceso"
            notificacion.message="No existe el usuario"
            notificacion.send()
            return render_template("inicios.html")
    return render_template('/inicios.html')

@app.route('/administrador', methods=['GET','POST'])
def administrador():
    return render_template('administrador/administrador.html')

@app.route('/basedeusuarios')
def basedeusuarios():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM persona')
    personas = cur.fetchall()
    fotos_codificadas = []
    
    for persona in personas:
        foto = persona['foto']
        foto_codificada = base64.b64encode(foto).decode('utf-8')
        fotos_codificadas.append(foto_codificada)

    datos = zip(personas, fotos_codificadas)
    print(fotos_codificadas)
    return render_template('administrador/usuarios/basedeusuarios.html', datos=datos)


@app.route('/crearusuario', methods=['GET','POST'])
def crear_persona():

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM tipo_documento")
    tipo = cur.fetchall()
    
    if request.method == 'POST':
        Nombres = request.form['Nombres']
        Apellidos = request.form['Apellidos']
        Tipo_Doc = request.form['tipo']
        Documento = request.form['Documento']
        Email = request.form['Email']
        if 'file' not in request.files:
            flash('no file part')
        file = request.files['foto']
        if file.filename == '':
            flash('imagen no se ha seleccionado')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            ruta = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(ruta)
            flash('exit')

        Password = request.form['Password']
        direccion = request.form['direccion']

        cur = mysql.connection.cursor()
        cur.execute(" INSERT INTO persona (Nombres, Apellidos,Tipo_Doc, Documento, Email, Password, foto, direccion, estado) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",(Nombres, Apellidos,Tipo_Doc, Documento, Email, Password,file,direccion,True))
        cur.connection.commit()

        flash('Persona creada exitosamente')
        return redirect(url_for('basedeusuarios'))
    return render_template('administrador/usuarios/crearusuario.html',  tipos = tipo)
    
    

@app.route('/eliminar/<string:id>')
def eliminar_persona(id):
        cur = mysql.connection.cursor()
        cur.execute('DELETE FROM persona WHERE Id_Persona = %s',(id,))
        cur.connection.commit()
        flash('Persona eliminada exitosamente')
        return redirect(url_for('basedeusuarios'))


@app.route('/editar/<string:id>', methods=['GET','POST'])
def editar_persona(id):
    if request.method == 'POST':
        Nombres = request.form['Nombres']
        Apellidos = request.form['Apellidos']
        Documento = request.form['Documento']
        Email = request.form['Email']
        Password = request.form['Password']

        cur = mysql.connection.cursor()
        cur.execute("""UPDATE persona SET 
                Nomres = %s, 
                Apellidos = %s, 
                Documento = %s, 
                Email= %s, 
                Password = %s
                WHERE Id_Persona = %s
                """,(Nombres, Apellidos, Documento, Email, Password,))
        flash('Actualización de datos exitosa')
        return redirect(url_for('basedeusuarios'))
    
@app.route('/basedepublicaciones', methods=['GET','POST'])
def basedepublicaciones():
    return render_template('administrador/administrador.html')

@app.route('/categorias', methods=['GET','POST'])
def categorias():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM categoria')
    categoria = cur.fetchall()
    if request.method == 'POST':
        Nombre_de_Categoria = request.form['Nombre_de_Categoria']
        Estado_Categoria = True
        cur.execute(" INSERT INTO categoria (Nombre_de_Categoria,Estado_Categoria) VALUES (%s,%s)",(Nombre_de_Categoria,Estado_Categoria))
        cur.connection.commit()
    return render_template('administrador/publicacion/categoria.html', categorias= categoria)

@app.route('/eliminarcategorias/<string:id>')
def eliminarcategorias(id):
        cur = mysql.connection.cursor()
        cur.execute('DELETE FROM categoria WHERE ID_Categoria_de_Residuo = %s',(id,))
        cur.connection.commit()
        return redirect(url_for('categorias'))


@app.route('/usuario', methods=['GET','POST'])
def usuario():
    return render_template('usuario/usuario.html')


@app.route('/buscar', methods=['GET','POST'])
def buscar():
    query = request.args.get('q')
    return render_template('resultados_busqueda.html', query=query, resultados=resultados)

if __name__ == '__main__':
    app.secret_key = "Hola1234."
    app.run(debug=True)