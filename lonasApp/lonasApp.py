from flask import Flask, request, url_for, redirect, render_template

app = Flask(__name__)

# Primera ruta
@app.route('/')
def index():
    return render_template('Layout.html')

# Ruta hola
@app.route('/hola')
def hola():
    return "Hola mundo"

if __name__ == '__main__':
    app.run(debug=True)
