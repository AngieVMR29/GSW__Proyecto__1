from flask import Flask,  render_template, request, redirect, url_for, session, flash, send_file # pip install Flask
from flask_mysqldb import MySQL,MySQLdb # pip install Flask-MySQLdb
from random import sample
from generador import stringAleatorio
import os 
import time
from os import remove #Modulo
from os import path
from werkzeug.utils import secure_filename 


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
        cur.execute('''
            SELECT compra.*, 
            GROUP_CONCAT(publicacion.Nombre_Publicacion SEPARATOR ', ') AS nombre_publicacion,
            CONCAT(comprador.Nombres, ' ', comprador.Apellidos) AS nombre_comprador,
            CONCAT(vendedor.Nombres, ' ', vendedor.Apellidos) AS nombre_vendedor
            FROM compra
            LEFT JOIN publicacion ON compra.publicacion = publicacion.id_publicacion
            LEFT JOIN persona AS comprador ON compra.comprador = comprador.Id_Persona
            LEFT JOIN persona AS vendedor ON publicacion.Propietario = vendedor.Id_Persona
            GROUP BY compra.id_compra
            ''')
        compras = cur.fetchall()
        cur.close()
        return render_template('administrador/publicacion/compras.html', compras = compras)
    elif 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (3, 4):
        flash('Inicie sesión como administrador')
        return redirect(url_for('iniciogsw'))
    else:
        flash('No has iniciado sesión')
        return redirect(url_for('iniciogsw'))

@app.route('/solicitudes', methods = ['GET','POST'])
def solicitudes():
    if 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (1, 2):
        persona_id = session['Id_Persona']
        cur = mysql.connection.cursor()
        cur.execute('''
            SELECT solicitudes.*, GROUP_CONCAT(persona.Nombres, ' ', persona.Apellidos) AS persona
            FROM solicitudes
            LEFT JOIN persona ON solicitudes.Solicitante = persona.Id_Persona
            GROUP BY solicitudes.id_solicitudes
            ''')
        solicitudes = cur.fetchall() 
        return render_template('administrador/solicitudes/solicitudes.html', solicitudes = solicitudes)
    elif 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (3, 4):
        persona_id = session['Id_Persona']
        if request.method == 'POST':
            Solicitante = persona_id
            asunto_solicitud = request.form['asunto_solicitud']
            Descripcion_Solicitud = request.form['Descripcion_Solicitud']
            cur = mysql.connection.cursor()
            cur.execute(" INSERT INTO solicitudes (Solicitante,asunto_solicitud,Descripcion_Solicitud,Estado_Solicitudes) VALUES (%s,%s,%s,%s)",(Solicitante,asunto_solicitud,Descripcion_Solicitud,True))
            cur.connection.commit()
            flash('Solicitud enviada con exito')
            return redirect(url_for('missolicitudes'))
        else:
            return render_template('usuario/solicitudes.html')
    else:
        flash('Por favor inicie sesión para realizar las solicitudes')
        return redirect(url_for('iniciogsw'))
    
@app.route('/respuesta/<string:id_solicitudes>', methods=['GET', 'POST'])
def respuesta(id_solicitudes):
    if 'email' in session and 'Id_Persona' in session and 'rol' in session:
        if session['rol'] in (1, 2):
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM respuestas WHERE id_solicitud = %s", (id_solicitudes,))
            respuesta_existente = cur.fetchone()
            if respuesta_existente:
                flash('Esta solicitud ya tiene una respuesta.')
                return redirect(url_for('solicitudes'))
            if request.method == 'POST':
                persona_id = session['Id_Persona']
                administrador = persona_id
                id_solicitud = id_solicitudes
                respuesta = request.form['respuesta']
                cur = mysql.connection.cursor()
                cur.execute("INSERT INTO respuestas (administrador, id_solicitud, respuesta, estado_respuesta) VALUES (%s, %s, %s, %s)", (administrador, id_solicitud, respuesta, True))
                cur.connection.commit()
                cur.execute("UPDATE solicitudes SET Estado_Solicitudes = %s WHERE id_solicitudes = %s", (False, id_solicitud,))
                mysql.connection.commit()
                flash('Respondió correctamente la solicitud') 
                return redirect(url_for('solicitudes'))

            else:
                id_solicitud = id_solicitudes
                cur = mysql.connection.cursor()
                cur.execute('''
                    SELECT solicitudes.*, GROUP_CONCAT(persona.Nombres, ' ', persona.Apellidos) AS persona
                    FROM solicitudes
                    LEFT JOIN persona ON solicitudes.Solicitante = persona.Id_Persona
                    GROUP BY solicitudes.id_solicitudes
                ''')
                solicitudes = cur.fetchall()
                return render_template('administrador/solicitudes/respuestas.html', solicitudes=solicitudes, id_solicitud= id_solicitud)
        else:
            flash('No tiene permisos para ingresar a esta sección')
            return redirect(url_for('iniciogsw'))
    else:
        flash('Por favor inicie sesión para realizar las solicitudes')
        return redirect(url_for('iniciogsw'))


@app.route('/missolicitudes')
def missolicitudes():
    if 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (1, 2):
        persona_id = session['Id_Persona']
        flash('Inicie sesión como usuario')
        return redirect(url_for('iniciogsw'))
    elif 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (3, 4):
        persona_id = session['Id_Persona']
        cur = mysql.connection.cursor()
        cur.execute('''
        SELECT solicitudes.*, 
               GROUP_CONCAT(persona.Nombres, ' ', persona.Apellidos) AS persona,
               respuestas.respuesta AS respuesta
        FROM solicitudes
        LEFT JOIN persona ON solicitudes.Solicitante = persona.Id_Persona
        LEFT JOIN respuestas ON solicitudes.id_solicitudes = respuestas.id_solicitud
        WHERE solicitudes.Solicitante = %s
        GROUP BY solicitudes.id_solicitudes
        ''', (persona_id,))
        solicitudes = cur.fetchall()
        print(solicitudes)

        return render_template('usuario/missolicitudes.html', solicitudes = solicitudes)
    else:
        flash('Por favor inicie sesión para realizar las solicitudes')
        return redirect(url_for('iniciogsw'))


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
            CONCAT(vendedor.Nombres, ' ', vendedor.Apellidos) AS nombre_vendedor,
            publicacion.Foto1_Publicacion AS foto1_publicacion
            FROM compra
            LEFT JOIN publicacion ON compra.publicacion = publicacion.id_publicacion
            LEFT JOIN persona AS comprador ON compra.comprador = comprador.Id_Persona
            LEFT JOIN persona AS vendedor ON publicacion.Propietario = vendedor.Id_Persona
            WHERE compra.comprador = %s
            GROUP BY compra.id_compra
    ''', (persona_id,))
        compras = cur.fetchall()
        cur.close()

        return render_template('usuario/miscompras.html', compras = compras)
    else:
        flash('Inicie sesión, no puede ingresar a está página')
        return redirect(url_for('iniciogsw'))

@app.route('/mispublicaciones')
def mispublicaciones():
    if 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (1, 2):
        persona_id = session['Id_Persona']
        flash('Inicie sesión como usuario')
        return redirect(url_for('iniciogsw'))
    elif 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (3, 4):
        persona_id = session['Id_Persona']
        cur = mysql.connection.cursor()
        cur.execute('''
            SELECT publicacion.*, GROUP_CONCAT(categoria.Nombre_de_Categoria SEPARATOR ', ') AS categoria,
            CONCAT(persona.Nombres, ' ', persona.Apellidos) AS persona
            FROM publicacion
            LEFT JOIN categoria ON publicacion.Categoria_Publicacion = categoria.ID_Categoria_de_Residuo
            LEFT JOIN persona ON publicacion.Propietario = persona.Id_Persona
            WHERE publicacion.Propietario = %s
            GROUP BY publicacion.id_publicacion
            ''', (persona_id,))
        publicacion = cur.fetchall()  
        cur.close()

        return render_template('usuario/mispublicaciones.html', publicaciones = publicacion)
    else:
        flash('Inicie sesión, no puede ingresar a está página')
        return redirect(url_for('iniciogsw'))
    
@app.route('/eliminarpublicacion/<string:id_publicacion>')
def eliminarpublicacion(id_publicacion):
        if 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (3, 4):
            
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM compra WHERE publicacion = %s", (id_publicacion,))
            compra_existente = cur.fetchone()
            cur.close()

            if compra_existente:
                flash('Este producto no se puede eliminar, tiene una compra pendiente.')
                return redirect(url_for('mispublicaciones'))
            else:
                cur = mysql.connection.cursor()
                cur.execute('DELETE FROM publicacion WHERE id_publicacion = %s',(id_publicacion,))
                cur.connection.commit()
                flash('Publicación eliminada con exito')
                return redirect(url_for('mispublicaciones'))
        elif 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (1, 2):
            flash('No tienes permisos para ingresar a esta página.')
            return redirect(url_for('iniciogsw'))
        else:
            flash('No has iniciado sesión.')
            return redirect(url_for('iniciogsw'))


@app.route('/confirmar_compra/<string:id_compra>',methods=['GET','POST'])
def confirmar_compra(id_compra):
    if request.method == 'POST':
        estado = request.form['estado']
        compra_id = id_compra
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT estado_Compra FROM compra WHERE id_compra = %s", (compra_id,))
        compra = cur.fetchone()
        cur.close()
        
        if compra and compra['estado_Compra'] == True:
            cur = mysql.connection.cursor()
            cur.execute("""UPDATE compra SET 
                            estado_Compra = %s
                            WHERE id_compra = %s
                        """, (estado, compra_id,))
            mysql.connection.commit()
            flash('Cambio de estado generado')
            cur.close()
            return redirect(url_for('miscompras'))
        else:
            flash('La compra ya ha sido completada y no se puede cambiar su estado.')
            return redirect(url_for('miscompras'))

@app.route('/enviar_mensaje', methods=['POST'])
def enviar_mensaje():
        if 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (3, 4):
            if request.method == 'POST':
                id_compra = request.form['id_compra']
                mensaje = request.form['mensaje']
                cur = mysql.connection.cursor()
                cur.execute("SELECT estado_Compra FROM compra WHERE id_compra = %s", (id_compra,))
                compra = cur.fetchone()
                cur.close()
        
                if compra and compra['estado_Compra']:
                    cur = mysql.connection.cursor()
                    cur.execute("INSERT INTO chat (compra, mensaje, estado_mensaje) VALUES (%s, %s, %s)", (id_compra, mensaje, True))
                    mysql.connection.commit()
                    cur.close()

                    flash('Su mensaje fue enviado con exito')
                    return redirect(url_for('miscompras'))
            id_compra = request.form.get('id_compra') 
            if id_compra:
                cur = mysql.connection.cursor()
                cur.execute("SELECT mensaje FROM chat WHERE compra = %s", (id_compra,))
                mensajes = cur.fetchall()
                cur.close()
                print(mensajes)
                return render_template('usuario/miscompras.html', mensajes=mensajes)

        elif 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (1, 2):
            flash('No tienes permisos para ingresar a esta página.')
            return redirect(url_for('iniciogsw'))
        else:
            flash('No has iniciado sesión.')
            return redirect(url_for('iniciogsw'))



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
        cur = mysql.connection.cursor()
        cur.execute('''
    SELECT publicacion.*, GROUP_CONCAT(categoria.Nombre_de_Categoria SEPARATOR ', ') AS categoria,
    CONCAT(persona.Nombres, ' ', persona.Apellidos) AS persona,
    CONCAT(vendedor.Telefono, ' ') AS vendedor,
    vendedor.Direccion AS direccion_vendedor
    FROM publicacion
    LEFT JOIN categoria ON publicacion.Categoria_Publicacion = categoria.ID_Categoria_de_Residuo
    LEFT JOIN persona AS vendedor ON publicacion.Propietario = vendedor.Id_Persona
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

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM compra WHERE publicacion = %s", (producto_id,))
        compra_existente = cur.fetchone()
        cur.close()

        if compra_existente:
            flash('Este producto no está disponible para comprar.')
            return redirect(url_for('miscompras'))

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
    

@app.route('/eliminar_compra/<int:compra_id>')
def eliminar_compra(compra_id):
    if 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (3, 4):

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM compra WHERE id_compra = %s AND comprador = %s", (compra_id, session['Id_Persona']))
        compra = cur.fetchone()
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM compra WHERE id_compra = %s", (compra_id,))
        mysql.connection.commit()
        flash('Compra eliminada con éxito.')
        cur.close()

        return redirect(url_for('miscompras'))
    else:
        flash('Inicie sesión como usuario.')
        return redirect(url_for('iniciogsw'))



@app.route('/registrogsw', methods=["GET", "POST"])
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
        if 'foto' in request.files:
            file = request.files['foto']
            nuevoNombreFile = recibeFoto(file)

        Password = request.form['Password']
        direccion = request.form['direccion']

        cur.execute("SELECT * FROM persona WHERE Email = %s", (Email,))
        existing_user = cur.fetchone()
        if existing_user:
            flash('El correo electrónico ya está registrado. Por favor, inicie sesión.')
            return redirect(url_for('iniciogsw'))

        cur.execute("INSERT INTO persona (Nombres, Apellidos, Tipo_Doc, Documento, Email, Telefono, Password, foto, direccion, estado) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (Nombres, Apellidos, Tipo_Doc, Documento, Email, Telefono, Password, nuevoNombreFile, direccion, True))
        cur.connection.commit()

        id_persona = cur.lastrowid

        cur.execute("INSERT INTO asignacion_roles (id_roles_fk, id_Persona1_FK) VALUES (3, %s), (4, %s)", (id_persona, id_persona))
        cur.connection.commit()

    return render_template('/registrate.html', tipos=tipo)


@app.route('/iniciogsw', methods=['POST', 'GET'])
def iniciogsw():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM persona WHERE Email = %s", (email,))
        persona = cur.fetchone()

        if persona:
            if password == persona["Password"]:
                session['email'] = persona['Email']
                Id_Persona = persona['Id_Persona']

                cur.execute("SELECT * FROM asignacion_roles WHERE id_Persona1_FK = %s", (Id_Persona,))
                rol_persona = cur.fetchone()

                if rol_persona:
                    session['rol'] = rol_persona['id_roles_fk']
                    session['Id_Persona'] = Id_Persona

                    if rol_persona['id_roles_fk'] in (1, 2):
                        return redirect(url_for('administrador'))
                    elif rol_persona['id_roles_fk'] in (3, 4):
                        return redirect(url_for('usuario'))
                else:
                    flash('No se encontró el rol asociado al usuario')
                    return render_template("inicios.html")
            else:
                flash('Contraseña incorrecta')
                return render_template("inicios.html")
        else:
            flash('No existe el usuario con este correo electrónico')
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
    if 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (1, 2):
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

            cur.execute("SELECT * FROM persona WHERE Email = %s", (Email,))
            existing_user = cur.fetchone()
            if existing_user:
                flash('El correo electrónico ya está registrado. Por favor, inicie sesión.')
                return redirect(url_for('iniciogsw'))

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
    elif 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (3, 4):
        flash('No tienes permisos para ingresar a esta página.')
        return redirect(url_for('iniciogsw'))
    else:
        flash('No has iniciado sesión.')
        return redirect(url_for('iniciogsw'))

    return render_template('administrador/usuarios/crearusuario.html',  tipos = tipo, roles = roles)

    

@app.route('/eliminar/<string:id>')
def eliminar_persona(id):
        if 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (1, 2):
            cur = mysql.connection.cursor()
            cur.execute("DELETE FROM asignacion_roles WHERE id_Persona1_FK = %s", (id,))
            cur.execute('DELETE FROM persona WHERE Id_Persona = %s',(id,))
            cur.connection.commit()
        
            flash('Persona eliminada exitosamente')
            return redirect(url_for('basedeusuarios'))
        elif 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (3, 4):
            flash('No tienes permisos para ingresar a esta página.')
            return redirect(url_for('iniciogsw'))
        else:
            flash('No has iniciado sesión.')
            return redirect(url_for('iniciogsw'))


@app.route('/editar/<string:id>', methods=['GET','POST'])
def editar_persona(id):
    if 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (1, 2):
        if request.method == 'GET':
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM persona WHERE Id_Persona = %s", (id,))
            usuario = cur.fetchone() 

            if usuario:
                return render_template('administrador/usuarios/editarusuario.html', usuario=usuario, id_usuario=id)
            else:
                flash('El usuario no existe')
                return redirect(url_for('basedeusuarios'))
        elif request.method == 'POST':
            Nombres = request.form['Nombres']
            Apellidos = request.form['Apellidos']
            Tipo_Doc = request.form['tipo']
            Documento = request.form['Documento']
            Email = request.form['Email']
            Telefono = request.form['Telefono']
            
            if 'foto' in request.files:
                file = request.files['foto']
                if file.filename != '':
                    nuevoNombreFile = recibeFoto(file) 

            direccion = request.form['direccion']

            cur = mysql.connection.cursor()
            cur.execute("""UPDATE persona SET 
                Nombres = %s,
                Apellidos = %s,
                Tipo_Doc = %s,
                Documento = %s,
                Email = %s,
                Telefono = %s,
                direccion = %s
                WHERE Id_Persona = %s""",
                (Nombres, Apellidos, Tipo_Doc, Documento, Email, Telefono, direccion, id))
            mysql.connection.commit()
            flash('Actualización de datos exitosa')
            return redirect(url_for('basedeusuarios'))
        else:
                return redirect(url_for('basedeusuarios'))
    elif 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (3, 4):
        if request.method == 'GET':
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM persona WHERE Id_Persona = %s", (id,))
            usuario = cur.fetchone() 
            if usuario:
                return render_template('usuario/editaru.html', usuarios=usuario, id_usuario=id)
            else:
                flash('El usuario no existe')
                return redirect(url_for('basedeusuarios'))
        elif request.method == 'POST':
            Nombres = request.form['Nombres']
            Apellidos = request.form['Apellidos']
            Tipo_Doc = request.form['tipo']
            Documento = request.form['Documento']
            Email = request.form['Email']
            Telefono = request.form['Telefono']
            
            if 'foto' in request.files:
                file = request.files['foto']
                if file.filename != '':
                    nuevoNombreFile = recibeFoto(file) 

            direccion = request.form['direccion']

            cur = mysql.connection.cursor()
            cur.execute("""UPDATE persona SET 
                Nombres = %s,
                Apellidos = %s,
                Tipo_Doc = %s,
                Documento = %s,
                Email = %s,
                Telefono = %s,
                direccion = %s
                WHERE Id_Persona = %s""",
                (Nombres, Apellidos, Tipo_Doc, Documento, Email, Telefono, direccion, id))
            mysql.connection.commit()
            flash('Actualización de datos exitosa')
            return redirect(url_for('perfilu'))
        else:
            flash('No has iniciado sesión.')
            return redirect(url_for('iniciogsw'))

@app.route('/cambiar_contraseña', methods=['GET', 'POST'])
def cambiar_contraseña():
    if 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (3, 4):
        if request.method == 'POST':
            cur = mysql.connection.cursor()
            cur.execute("SELECT Password FROM persona WHERE Id_Persona = %s", (session['Id_Persona'],))
            usuario = cur.fetchone()
            if usuario and usuario['Password'] == request.form['contraseña_actual']:
                nueva_contraseña = request.form['nueva_contraseña']
                cur.execute("UPDATE persona SET Password = %s WHERE Id_Persona = %s", (nueva_contraseña, session['Id_Persona']))
                mysql.connection.commit()
                flash('Contraseña actualizada correctamente')
                return redirect(url_for('perfilu')) 
            else:
                flash('La contraseña actual es incorrecta')
                return render_template('usuario/cambiar.html')
        else:
            return render_template('usuario/cambiar.html')
    else:
        flash('Por favor, inicie sesión para cambiar la contraseña')
        return redirect(url_for('iniciogsw'))
    
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


@app.route('/categorias', methods=['GET','POST'])
def categorias():
    if 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (1, 2):
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM categoria')
        categoria = cur.fetchall()
        if request.method == 'POST':
            Nombre_de_Categoria = request.form['Nombre_de_Categoria']
            Estado_Categoria = True
            cur.execute(" INSERT INTO categoria (Nombre_de_Categoria,Estado_Categoria) VALUES (%s,%s)",(Nombre_de_Categoria,Estado_Categoria))
            cur.connection.commit()
        return render_template('administrador/publicacion/categoria.html', categorias= categoria)
    elif 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (3, 4):
            flash('No tienes permisos para ingresar a esta página.')
            return redirect(url_for('iniciogsw'))
    else:
        flash('No has iniciado sesión.')
        return redirect(url_for('iniciogsw'))

@app.route('/eliminarcategorias/<string:id>')
def eliminarcategorias(id):
    if 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (1, 2):
        cur = mysql.connection.cursor()
        cur.execute('DELETE FROM categoria WHERE ID_Categoria_de_Residuo = %s',(id,))
        cur.connection.commit()
        return redirect(url_for('categorias'))
    elif 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (3, 4):
        flash('No tienes permisos para ingresar a esta página.')
        return redirect(url_for('iniciogsw'))
    else:
        flash('No has iniciado sesión.')
        return redirect(url_for('iniciogsw'))

@app.route('/usuario', methods=['GET','POST'])
def usuario():
    if 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (3, 4):
        return render_template('usuario/usuario.html')
    elif 'email' in session and 'Id_Persona' in session and 'rol' in session and session['rol'] in (1, 2):
        flash('No tienes permisos para ingresar a esta página.')
        return redirect(url_for('iniciogsw'))
    else:
        flash('No has iniciado sesión.')
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
    return '<h1>Seguimos trabajando para ti, este apartado aún no se encuentra disponible</h1>'

if __name__ == '__main__':
    app.secret_key = "Hola1234."
    app.run(debug=True)