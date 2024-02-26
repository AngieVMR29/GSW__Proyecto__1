from flask import Flask,  render_template, request, redirect, url_for, session # pip install Flask
from flask_mysqldb import MySQL,MySQLdb # pip install Flask-MySQLdb
from os import path #pip install notify-py


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
    cur.execute("SELECT * FROM tip_usu")
    tipo = cur.fetchall()
    return render_template('/registrate.html')

@app.route('/iniciogsw')
def iniciogsw():
    return render_template('/inicios.html')

@app.route('/buscar', methods=['GET'])
def buscar():
    query = request.args.get('q')
    return render_template('resultados_busqueda.html', query=query, resultados=resultados)

if __name__ == '__main__':
    app.secret_key = "Hola1234."
    app.run(debug=True)