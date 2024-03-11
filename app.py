from flask import Flask,  render_template, request, redirect, url_for, session, flash, send_file # pip install Flask
from flask_mysqldb import MySQL,MySQLdb # pip install Flask-MySQLdb
from random import sample
from generador import stringAleatorio
import os 
import time
from os import remove #Modulo
from os import path
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

def recibeFoto(file):
    print(file)
    basepath = os.path.dirname (__file__) #La ruta donde se encuentra el archivo actual
    filename = secure_filename(file.filename) 
    extension           = os.path.splitext(filename)[1]
    nuevoNombreFile     = stringAleatorio() + extension       
    upload_path = os.path.join (basepath, 'static/uploads', nuevoNombreFile) 
    file.save(upload_path)

    return nuevoNombreFile

@app.route('/')
def home():
    return render_template('/inicio.html')

@app.route('/404')
def not_found():
    return 'url no encontrada'

@app.route('/logout')
def logout():
    session.clear()
    time.sleep(5)
    return render_template('/inicio.html')

@app.route('/sobrenosotros')
def sobrenosotros():
    return render_template('/nosotros.html')

@app.route('/compras')
def compras():
    if 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (1, 2):
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM compra")
        compras = cur.fetchall()
        return render_template('administrador/publicacion/compras.html', compras = compras)
    elif 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (3, 4):
        flash('Inicie sesión como administrador')
        return redirect(url_for('iniciogsw'))
    else:
        flash('No has iniciado sesión')
        return redirect(url_for('iniciogsw'))

@app.route('/solicitudes')
def solicitudes():
    if 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (1, 2):
        persona_id = session['Id_Persona']
        flash('Inicie sesión como usuario')
        return redirect(url_for('iniciogsw'))
    elif 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (3, 4):
        return render_template('usuario/solicitudes.html')
    else:
        return render_template('/solicitudes.html')

@app.route('/miscompras')
def miscompras():
    if 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (1, 2):
        persona_id = session['Id_Persona']
        flash('Inicie sesión como usuario')
        return redirect(url_for('iniciogsw'))
    elif 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (3, 4):
        persona_id = session['Id_Persona']
        cur = mysql.connection.cursor()
        cur.execute('''
            SELECT compra.*, 
            GROUP_CONCAT(publicacion.Nombre_Publicacion SEPARATOR ', ') AS nombre_publicacion,
            CONCAT(comprador.Nombres, ' ', comprador.Apellidos) AS nombre_comprador,
            CONCAT(vendedor.Nombres, ' ', vendedor.Apellidos) AS nombre_vendedor
            FROM compra
            LEFT JOIN publicacion ON compra.publicacion = publicacion.id_publicacion
            LEFT JOIN persona AS comprador ON compra.comprador = comprador.Id_Persona
            LEFT JOIN persona AS vendedor ON publicacion.Propietario = vendedor.Id_Persona
            WHERE compra.comprador = %s
            GROUP BY compra.id_compra
            ''', (persona_id,))
        compras = cur.fetchall()
        cur.close()

        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM estados_compra')
        estados = cur.fetchall()
        cur.close()
        return render_template('usuario/miscompras.html', compras = compras, estados = estados)
    else:
        flash('Inicie sesión, no puede ingresar a está página')
        return redirect(url_for('iniciogsw'))


@app.route('/confirmar_compra/<string:id_compra>',methods=['GET','POST'])
def confirmar_compra(id_compra):
    if request.method == 'POST':
            estado = request.form['estado']
            compra_id = id_compra
            cur = mysql.connection.cursor()
            cur.execute(" INSERT INTO confirmar_compra (id_compra_fk,id_estado_fk) VALUES (%s,%s)",(compra_id,estado))
            cur.connection.commit()
            flash('Cambio de estado generado')
            cur.close() 
            return redirect(url_for('miscompras'))
    else:
        flash('Error')
        return redirect(url_for('miscompras'))



@app.route('/catalogo')
def catalogo():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM categoria")
    catalogo = cur.fetchall()

    cur = mysql.connection.cursor()
    cur.execute('''
        SELECT publicacion.*, GROUP_CONCAT(categoria.Nombre_de_Categoria SEPARATOR ', ') AS categoria,
        CONCAT(persona.Nombres, ' ', persona.Apellidos) AS persona
        FROM publicacion
        LEFT JOIN categoria ON publicacion.Categoria_Publicacion = categoria.ID_Categoria_de_Residuo
        LEFT JOIN persona ON publicacion.Propietario = persona.Id_Persona
        GROUP BY publicacion.id_publicacion
    ''')
    publicacion = cur.fetchall() 

    if 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (1, 2):
        persona_id = session['Id_Persona']
        flash('Inicie sesión como usuario')
        return redirect(url_for('iniciogsw'))
    elif 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (3, 4):
        return render_template('usuario/catalogo.html', catalogos = catalogo, publicaciones = publicacion)
    else:
        return render_template('/catalogo.html', catalogos = catalogo, publicaciones = publicacion)

@app.route('/comprar/<int:producto_id>',methods=['GET','POST'])
def comprar(producto_id):
    if 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (3, 4):
        cur = mysql.connection.cursor()
        cur.execute('''
            SELECT publicacion.*, GROUP_CONCAT(categoria.Nombre_de_Categoria SEPARATOR ', ') AS categoria,
            CONCAT(persona.Nombres, ' ', persona.Apellidos) AS persona
            FROM publicacion
            LEFT JOIN categoria ON publicacion.Categoria_Publicacion = categoria.ID_Categoria_de_Residuo
            LEFT JOIN persona ON publicacion.Propietario = persona.Id_Persona
            WHERE publicacion.id_publicacion = %s
            GROUP BY publicacion.id_publicacion
            ''', (producto_id,))
        producto = cur.fetchone()
        cur.close()

        persona_id = session['Id_Persona']
        cur = mysql.connection.cursor()
        cur.execute('''
            SELECT persona.*, GROUP_CONCAT(roles.Nombre_Rol SEPARATOR ', ') AS roles,
            GROUP_CONCAT(tipo_documento.Tipo_de_documento SEPARATOR ', ') AS tipo_documento
            FROM persona
            LEFT JOIN asignacion_roles ON persona.Id_Persona = asignacion_roles.id_Persona1_FK
            LEFT JOIN roles ON asignacion_roles.id_roles_fk = roles.Id_Roles
            LEFT JOIN tipo_documento ON persona.Tipo_Doc = tipo_documento.Id_Tipo_de_Documento
            WHERE persona.Id_Persona = %s
            GROUP BY persona.Id_Persona
            ''', (persona_id,))
        persona = cur.fetchone() 
        cur.close() 

        if request.method == 'POST':
            publicacion = producto_id
            comprador = persona_id
            cur = mysql.connection.cursor()
            cur.execute(" INSERT INTO compra (publicacion,comprador,estado_compra) VALUES (%s,%s,%s)",(publicacion,comprador,True))
            cur.connection.commit()
            return redirect(url_for('miscompras'))
        return render_template('usuario/comprar.html', producto=producto, persona = persona)
    elif 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (1, 2):
        flash('Inicie sesión como usuario')
        return redirect(url_for('iniciogsw'))
    else:
        flash('Inicie sesión como usuario')
        return redirect(url_for('iniciogsw'))

@app.route('/registrogsw', methods = ["GET", "POST"])
def registrogsw():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM tipo_documento")
    tipo = cur.fetchall()

    if request.method == 'POST':
        Nombres = request.form['Nombres']
        Apellidos = request.form['Apellidos']
        Tipo_Doc = request.form['tipo']
        Documento = request.form['Documento']
        Email = request.form['Email']
        Telefono = request.form['Telefono']
        if(request.files['foto'] !=''):
            file     = request.files['foto'] #recibiendo el archivo
            nuevoNombreFile = recibeFoto(file) 

        Password = request.form['Password']
        direccion = request.form['direccion']

        cur = mysql.connection.cursor()
        cur.execute(" INSERT INTO persona (Nombres, Apellidos,Tipo_Doc, Documento, Email,Telefono, Password, foto, direccion, estado) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(Nombres, Apellidos,Tipo_Doc, Documento, Email,Telefono, Password,nuevoNombreFile,direccion,True))
        cur.connection.commit()

        cur.execute("SELECT LAST_INSERT_ID()")
        id_persona = cur.fetchone()['LAST_INSERT_ID()']

        cur.execute("INSERT INTO asignacion_roles (id_roles_fk, id_Persona1_FK) VALUES (3, %s), (4, %s)", (id_persona, id_persona))
        cur.connection.commit()

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
                Id_Persona  = persona['Id_Persona']

                cur = mysql.connection.cursor()
                cur.execute("SELECT * FROM asignacion_roles WHERE id_Persona1_FK = %s",(Id_Persona,))
                persona = cur.fetchone()

                if persona['id_roles_fk'] == 1 or persona['id_roles_fk'] == 2:
                    session['rol'] = persona['id_roles_fk']
                    session['Id_Persona'] = Id_Persona
                    return redirect(url_for('administrador'))
                elif persona['id_roles_fk'] == 3 or persona['id_roles_fk'] == 4:
                    session['rol'] = persona['id_roles_fk']
                    session['Id_Persona'] = Id_Persona
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

@app.route('/administrador')
def administrador():
    if 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (1, 2):
        persona_id = session['Id_Persona']
        return render_template('administrador/administrador.html')
    elif 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (3, 4):
        flash('No tienes permisos para ingresar a esta página.')
        return redirect(url_for('iniciogsw'))
    else:
        flash('No has iniciado sesión.')
        return redirect(url_for('iniciogsw'))
    
@app.route('/perfiladministrador')
def perfila():
        if 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (1, 2):
            persona_id = session['Id_Persona']
            cur = mysql.connection.cursor()
            cur.execute('''
            SELECT persona.*, GROUP_CONCAT(roles.Nombre_Rol SEPARATOR ', ') AS roles,
            GROUP_CONCAT(tipo_documento.Tipo_de_documento SEPARATOR ', ') AS tipo_documento
            FROM persona
            LEFT JOIN asignacion_roles ON persona.Id_Persona = asignacion_roles.id_Persona1_FK
            LEFT JOIN roles ON asignacion_roles.id_roles_fk = roles.Id_Roles
            LEFT JOIN tipo_documento ON persona.Tipo_Doc = tipo_documento.Id_Tipo_de_Documento
            WHERE persona.Id_Persona = %s
            GROUP BY persona.Id_Persona
            ''', (persona_id,))
            persona = cur.fetchone() 
            cur.close() 
            print(persona)
            return render_template('administrador/perfil.html', persona= persona)
        elif 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (3, 4):
            flash('No tienes permisos para ingresar a esta página.')
            return redirect(url_for('iniciogsw'))
        else:
            flash('No has iniciado sesión.')
            return redirect(url_for('iniciogsw'))


@app.route('/basedeusuarios')
def basedeusuarios():
    if 'email' in session and 'Id_Persona' in session and 'rol' in session:
        if session['rol'] in (1, 2):
            cur = mysql.connection.cursor()
            cur.execute('''
                SELECT persona.*, GROUP_CONCAT(roles.Nombre_Rol SEPARATOR ', ') AS roles,
                GROUP_CONCAT(tipo_documento.Tipo_de_documento SEPARATOR ', ') AS tipo_documento
                FROM persona
                LEFT JOIN asignacion_roles ON persona.Id_Persona = asignacion_roles.id_Persona1_FK
                LEFT JOIN roles ON asignacion_roles.id_roles_fk = roles.Id_Roles
                LEFT JOIN tipo_documento ON persona.Tipo_Doc = tipo_documento.Id_Tipo_de_Documento
                GROUP BY persona.Id_Persona
            ''')
            personas = cur.fetchall()
            cur.close()
            return render_template('administrador/usuarios/basedeusuarios.html', personas=personas)
        else:
            flash('No tienes permisos para acceder a esta página.')
            return redirect(url_for('inicio')) 
    else:
        flash('No has iniciado sesión.')
        return redirect(url_for('iniciogsw')) 



@app.route('/crearusuario', methods=['GET','POST'])
def crear_persona():

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM tipo_documento")
    tipo = cur.fetchall()

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM roles")
    roles = cur.fetchall()
    
    if request.method == 'POST':
        Nombres = request.form['Nombres']
        Apellidos = request.form['Apellidos']
        Tipo_Doc = request.form['tipo']
        Documento = request.form['Documento']
        Email = request.form['Email']
        Telefono = request.form['Telefono']
        if(request.files['foto'] !=''):
            file     = request.files['foto'] #recibiendo el archivo
            nuevoNombreFile = recibeFoto(file) 

        Password = request.form['Password']
        direccion = request.form['direccion']
        roles = request.form.getlist('roles[]')

        cur = mysql.connection.cursor()
        cur.execute(" INSERT INTO persona (Nombres, Apellidos,Tipo_Doc, Documento, Email,Telefono, Password, foto, direccion, estado) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(Nombres, Apellidos,Tipo_Doc, Documento, Email,Telefono, Password,nuevoNombreFile,direccion,True))
        cur.connection.commit()

        cur.execute("SELECT LAST_INSERT_ID()")
        id_persona = cur.fetchone()['LAST_INSERT_ID()']

        for role in roles:
                cur.execute("INSERT INTO asignacion_roles (id_Persona1_FK, id_roles_fk) VALUES (%s, %s)", (id_persona, role))
                mysql.connection.commit()

        
        flash('Persona creada exitosamente')
        return redirect(url_for('basedeusuarios'))
    return render_template('administrador/usuarios/crearusuario.html',  tipos = tipo, roles = roles)

    

@app.route('/eliminar/<string:id>')
def eliminar_persona(id):
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM asignacion_roles WHERE id_Persona1_FK = %s", (id,))
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
    if 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (1, 2):
        cur = mysql.connection.cursor()
        cur.execute('''
            SELECT publicacion.*, GROUP_CONCAT(categoria.Nombre_de_Categoria SEPARATOR ', ') AS categoria,
            CONCAT(persona.Nombres, ' ', persona.Apellidos) AS persona
            FROM publicacion
            LEFT JOIN categoria ON publicacion.Categoria_Publicacion = categoria.ID_Categoria_de_Residuo
            LEFT JOIN persona ON publicacion.Propietario = persona.Id_Persona
            GROUP BY publicacion.id_publicacion
            ''')
        publicacion = cur.fetchall()        
        return render_template('administrador/publicacion/basedepublicacion.html', publicaciones= publicacion)
    elif 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (3, 4):
        flash('No tienes permisos para ingresar a esta página.')
        return redirect(url_for('iniciogsw'))
    else:
        flash('No has iniciado sesión.')
        return redirect(url_for('iniciogsw'))

@app.route('/eliminarpublicacion/<string:id>')
def eliminarpublicacion(id):
        cur = mysql.connection.cursor()
        cur.execute('DELETE FROM publicacion WHERE id_publicacion = %s',(id,))
        cur.connection.commit()
        flash('Publicación eliminada con exito')
        return redirect(url_for('basedepublicaciones'))

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
    if 'email' in session and 'rol' in session and session['rol'] in (3, 4):
        return render_template('usuario/usuario.html')
    else:
        return redirect(url_for('iniciogsw'))

@app.route('/perfilu')
def perfilu():
        if 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (3, 4):
            persona_id = session['Id_Persona']
            print(persona_id)
            cur = mysql.connection.cursor()
            cur.execute('''
            SELECT persona.*, GROUP_CONCAT(roles.Nombre_Rol SEPARATOR ', ') AS roles,
            GROUP_CONCAT(tipo_documento.Tipo_de_documento SEPARATOR ', ') AS tipo_documento
            FROM persona
            LEFT JOIN asignacion_roles ON persona.Id_Persona = asignacion_roles.id_Persona1_FK
            LEFT JOIN roles ON asignacion_roles.id_roles_fk = roles.Id_Roles
            LEFT JOIN tipo_documento ON persona.Tipo_Doc = tipo_documento.Id_Tipo_de_Documento
            WHERE persona.Id_Persona = %s
            GROUP BY persona.Id_Persona
            ''', (persona_id,))
            persona = cur.fetchone() 
            cur.close() 
            print(persona)
            return render_template('usuario/perfilu.html', persona= persona)
        elif 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (1, 2):
            flash('No tienes permisos para ingresar a esta página.')
            return redirect(url_for('iniciogsw'))
        else:
            flash('No has iniciado sesión.')
            return redirect(url_for('iniciogsw'))

@app.route('/crearpublicacion', methods=['GET','POST'])
def crearpublicacion():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM categoria")
    categoria = cur.fetchall()

    if 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (3, 4):
        if request.method == 'POST':
            Nombre_Publicacion = request.form['Nombre_Publicacion']
            Descripcion_Publicacion = request.form['Descripcion_Publicacion'] 
            if(request.files['Foto1_Publicacion'] !=''):
                file = request.files['Foto1_Publicacion'] 
                nuevoNombreFile1 = recibeFoto(file) 
            if(request.files['Foto2_Publicacion'] !=''):
                file = request.files['Foto2_Publicacion'] 
                nuevoNombreFile2 = recibeFoto(file) 
            if(request.files['Foto3_Publicacion'] !=''):
                file = request.files['Foto3_Publicacion'] #recibiendo el archivo
                nuevoNombreFile3 = recibeFoto(file)
            Categoria_Publicacion = request.form['Categoria_Publicacion'] 
            Precio = request.form['Precio'] 
            Propietario = session['Id_Persona']
            Estado_p = True
            cur = mysql.connection.cursor()
            cur.execute(" INSERT INTO publicacion (Nombre_Publicacion, Descripcion_Publicacion,Foto1_Publicacion, Foto2_Publicacion, Foto3_Publicacion, Categoria_Publicacion, Precio, Propietario, Estado_Publicacion) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",(Nombre_Publicacion, Descripcion_Publicacion,nuevoNombreFile1, nuevoNombreFile2, nuevoNombreFile3, Categoria_Publicacion, Precio, Propietario, Estado_p))
            cur.connection.commit()
            flash('Producto agregado con exito')
            return render_template('usuario/crearpublicacion.html')
    else:
        return redirect(url_for('iniciogsw'))

    return render_template('usuario/crearpublicacion.html', categorias = categoria)


@app.route('/buscar', methods=['GET','POST'])
def buscar():
    query = request.args.get('q')
    return render_template('resultados_busqueda.html', query=query, resultados=resultados)

if __name__ == '__main__':
    app.secret_key = "Hola1234."
    app.run(debug=True)