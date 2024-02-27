from flask import Flask,  render_template, request, redirect, url_for, session # pip install Flask
from flask_mysqldb import MySQL,MySQLdb # pip install Flask-MySQLdb
from os import path #pip install notify-py
from notifypy import Notify


app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'greensoftworld'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

@app.route('/')
def home():
    return render_template('/inicio.html')

@app.route('/registrogsw', methods = ["GET", "POST"])
def registrogsw():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM tipo_documento")
    tipo = cur.fetchall()

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM roles")
    interes = cur.fetchall()
    cur.close()
    return render_template('/registrate.html')


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

@app.route('/basedeusuarios', methods=['GET','POST'])
def basedeusuarios():
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM persona')
        persona = cur.fetchall()
        print(persona)
        return render_template('administrador/basedeusuarios.html', personas = persona)

@app.route('/basedepublicaciones', methods=['GET','POST'])
def basedepublicaciones():
    return render_template('administrador/administrador.html')

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