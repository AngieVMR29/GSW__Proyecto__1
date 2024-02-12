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
    return render_template("./usuario/inicio.html")    


@app.route('/login')
def login():
    return render_template("./login/login.html")
    
    
@app.route('/inicio')
def inicio():
    return render_template("./comprador/inicio.html")


if __name__ == '__main__':
    app.run(debug=True)