from flask import Flask, render_template, url_for, redirect, request, flash, Blueprint, jsonify, session 
from psycopg2.extras import RealDictCursor
import os
import uuid
import psycopg2
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from Models.ModelUser import ModuleUser
from Models.entities.user import User

app = Flask(__name__)
csrf = CSRFProtect()

# Configuración secreta para sesiones
app.secret_key = "Secretomuysecreto"

#-------------------imagen-----------#
ruta_lonas = './app/static/img/uploads/lonas'

#------------- Configuración de inicio de sesión ----------#
Login_manager_app = LoginManager(app)

@Login_manager_app.user_loader
def load_user(idusuarios):
    return ModuleUser.get_by_id(get_db_connection(), idusuarios)
#------------------------imagen--------------------------#
def my_random_string(string_length=10):
    """Regresa una cadena aleatoria de la longitud de string_length."""
    random = str(uuid.uuid4())  # Convierte el formato UUID a una cadena de Python.
    random = random.upper()  # Hace todos los caracteres mayúsculas.
    random = random.replace("-", "")  # Remueve el separador UUID '-'.
    return random[0:string_length]  # Regresa la cadena aleatoria.

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER_LONAS'] = './app/static/img/uploads/lonas/'
app.config['UPLOAD_FOLDER_CARPAS'] = './app/static/img/uploads/carpas/'

if not os.path.exists(app.config['UPLOAD_FOLDER_LONAS']):
    os.makedirs(app.config['UPLOAD_FOLDER_LONAS'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Función para establecer conexión a la base de datos
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host='localhost',
            dbname='lonas',  # Cambiado de 'escuela' a 'lonas'
            port='5432',
            user=os.environ['DB_USERNAME'],
            password=os.environ['DB_PASSWORD']
        )
        return conn
    except psycopg2.Error as error:
        print(f"Error al conectar a la base de datos: {error}")
        return None

#---------------INICIO------------#

@app.route("/")
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM lona ORDER BY id_lona ASC;")
    lonas = cur.fetchall()
    cur.close()
    conn.close()
    titulo = "Panel de Administración"
    return render_template('index.html', titulo=titulo, lonas=lonas)

@app.route("/about-us")
def about_us():
    return render_template('about_us.html')

#--------------------- Paginador ----------------------#
def paginador(sql_count, sql_lim, in_page, per_pages):
    page = request.args.get('page', in_page, type=int)
    per_page = request.args.get('per_page', per_pages, type=int)
    
    offset = (page - 1) * per_page
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor) # type: ignore
    
    cursor.execute(sql_count)
    total_items = cursor.fetchone()['count']

    cursor.execute(sql_lim, (per_page, offset))
    items = cursor.fetchall()

    cursor.close()
    conn.close()

    total_pages = (total_items + per_page - 1) // per_page

    return items, page, per_page, total_items, total_pages

#---------------------CRUD DE USUARIO ----------------------#
@app.route('/formulario_usuario', methods=['GET', 'POST'])
@login_required
def formulario_usuario():
    if request.method == 'POST':
        name_user = request.form['Username']
        password_user = request.form['Password']

        if not name_user or not password_user:
            flash("Username y Password son requeridos.", 'error')
            return redirect(url_for('formulario_usuario'))

        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            try:
                # Verificar si el Username ya existe
                cur.execute('SELECT 1 FROM usuario WHERE "Username" = %s', (name_user,))
                if cur.fetchone():
                    flash("El Username ya existe.", 'error')
                    return redirect(url_for('formulario_usuario'))
                
                # Insertar en la tabla usuario y obtener el id del usuario creado
                cur.execute(
                    'INSERT INTO usuario ("Username", "Password") VALUES (%s, %s) RETURNING id_user',
                    (name_user, password_user)
                )
                id_user = cur.fetchone()[0]
                
                conn.commit()
                flash("Datos guardados correctamente", 'success')
                
                # Guardar el id_user en la sesión para usar como fk_usuario
                session['id_user'] = id_user
                
                # Redirigir al formulario de cliente
                return redirect(url_for('Cliente'))
                
            except psycopg2.Error as e:
                conn.rollback()
                flash(f"Error al guardar los datos: {e}", 'error')
            finally:
                cur.close()
                conn.close()
        else:
            flash("Error al conectar a la base de datos", 'error')
            return redirect(url_for('formulario_usuario'))
    return render_template('Crear_Usuario.html')


@app.route('/datosCliente', methods=['GET', 'POST'])
@login_required
def Cliente():
    if request.method == 'POST':
        Nombre = request.form['Nombre']
        Apellido_Pa = request.form['Apellido_paterno']
        Apellido_Ma = request.form['Apellido_materno']
        Direccion = request.form['Direccion']
        Estado = request.form['Estado']
        Municipio = request.form['Municipio']
        Telefono = request.form['Telefono']
        Correo = request.form['Email']

        # Obtener fk_usuario de la sesión
        fk_usuario = session.get('id_user')

        if not Nombre or not Apellido_Pa or not Apellido_Ma or not Direccion or not Estado or not Municipio or not Telefono or not Correo or not fk_usuario:
            flash("Todos los datos del cliente son requeridos.", 'error')
            return redirect(url_for('Cliente'))

        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            try:
                # Insertar en la tabla cliente
                cur.execute(
                    'INSERT INTO cliente ("Nombre", "Apellido_paterno", "Apellido_materno", "Direccion", "Estado", "Municipio", "Telefono", "Email", "fk_usuario") VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
                    (Nombre, Apellido_Pa, Apellido_Ma, Direccion, Estado, Municipio, Telefono, Correo, fk_usuario)
                )
                conn.commit()
                flash("Datos de cliente guardados correctamente", 'success')
                
                # Redirigir al índice o a la página correspondiente
                return redirect(url_for('index'))
                
            except psycopg2.Error as e:
                conn.rollback()
                flash(f"Error al guardar los datos del cliente en la base de datos: {e}", 'error')
            finally:
                cur.close()
                conn.close()
        else:
            flash("Error al conectar a la base de datos", 'error')
            return redirect(url_for('Cliente'))
        
        return render_template('formulario_cliente.html')
    
@app.route('/sideclienteInicio')
@login_required
def sideClienteInicio():
    return render_template('sideClienteInicio.html')

@app.route('/dashboardClienteMisDatos', methods=['GET', 'POST'])
@login_required
def dashboardClienteMisDatos():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT "id_cliente", "Nombre", "Apellido_paterno", "Apellido_materno", "Direccion", "Estado", "Municipio", "Telefono", "Email" FROM cliente ORDER BY id_cliente DESC LIMIT 1;')
    datos_cliente = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('sideclienteDatos.html', datos_cliente=datos_cliente)


@app.route('/Editar/Datos/Cliente/<int:id_cliente>', methods=['GET', 'POST'])
@login_required
def EditarDatosCliente(id_cliente):
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'GET':
        cur.execute('SELECT * FROM cliente WHERE id_cliente = %s', (id_cliente,))
        datos_cliente = cur.fetchone()
        cur.close()
        conn.close()
        if datos_cliente:
            return render_template('editarClienteDatos.html', datos_cliente=datos_cliente)
        else:
            flash('Cliente no encontrado', 'error')
            return redirect(url_for('dashboardClienteMisDatos'))

    elif request.method == 'POST':
        nombre = request.form['Nombre']
        apellido_pa = request.form['Apellido_paterno']
        apellido_ma = request.form['Apellido_materno']
        direccion = request.form['Direccion']
        estado = request.form['Estado']
        municipio = request.form['Municipio']
        telefono = request.form['Telefono']
        email = request.form['Email']

        try:
            cur.execute('UPDATE cliente SET "Nombre" = %s, "Apellido_paterno" = %s, "Apellido_materno" = %s, "Direccion" = %s, "Estado" = %s, "Municipio" = %s, "Telefono" = %s, "Email" = %s WHERE id_cliente = %s',
                        (nombre, apellido_pa, apellido_ma, direccion, estado, municipio, telefono, email, id_cliente))
            conn.commit()
            flash('Datos de cliente actualizados correctamente', 'success')
            return redirect(url_for('dashboardClienteMisDatos'))
        except psycopg2.Error as e:
            conn.rollback()
            flash(f"Error al actualizar datos del cliente: {e}", 'error')
            return redirect(url_for('EditarDatosCliente', id_cliente=id_cliente))
        finally:
            cur.close()
            conn.close()

@app.route('/EliminarMisDatos/<int:id_cliente>', methods=['GET', 'POST'], endpoint='EliminarDatosCliente')
@login_required
def deleteDataUser(id_cliente):
    conn = get_db_connection()
    if request.method == 'POST':
        if conn:
            cur = conn.cursor()
            try:
                # Obtener el cliente
                cur.execute("SELECT * FROM cliente WHERE id_cliente = %s", (id_cliente,))
                datos_cliente = cur.fetchone()

                if datos_cliente:
                    # Obtener el usuario relacionado (verifica el índice correcto para fk_usuario)
                    cur.execute("SELECT * FROM usuario WHERE Username = %s", (datos_cliente[0],))  # suposicion que Username es el primer campo
                    datos_usuario = cur.fetchone()

                    # Eliminar cliente y usuario
                    cur.execute("DELETE FROM cliente WHERE id_cliente = %s", (id_cliente,))
                    cur.execute("DELETE FROM usuario WHERE Username = %s", (datos_cliente[0],))

                    conn.commit()
                    flash('Datos de cliente y usuario eliminados correctamente', 'success')
                    return redirect(url_for('index'))
                else:
                    flash('No se encontraron datos para el cliente especificado', 'error')
                    return redirect(url_for('dashboardClienteMisDatos'))

            except psycopg2.Error as e:
                conn.rollback()
                flash(f"Error al eliminar los datos del cliente: {e}", 'error')
            finally:
                cur.close()
                conn.close()
        else:
            flash('Error al conectar a la base de datos', 'error')
            return redirect(url_for('dashboardClienteMisDatos'))

    return render_template('eliminar_datos_usuario.html', id_cliente=id_cliente)
#---------------------- CRUD DE LONAS ---------------------#
@app.route("/dashboard/lonas")
@login_required
def lonas_dashboard():
    titulo = "Lonas"
    sql_count = 'SELECT COUNT(*) FROM lona;'
    sql_lim = 'SELECT id_lona, color, cantidad, precio_renta, ancho, largo, unidad_medida FROM lona ORDER BY id_lona DESC LIMIT %s OFFSET %s;'
    paginado = paginador(sql_count, sql_lim, 1, 5)
    return render_template('lonas.html',
                            titulo=titulo,
                            lonas=paginado[0],
                            page=paginado[1],
                            per_page=paginado[2],
                            total_items=paginado[3],
                            total_pages=paginado[4])

@app.route("/dashboard/lonas/formulario")
@login_required
def lona_formulario():
    titulo = "Formulario de Lonas"
    return render_template('lonas_formulario.html', titulo=titulo)

@app.route("/dashboard/lonas/crear", methods=['GET', 'POST'])
@login_required
def lona_crear():
    if request.method == 'POST':
        color = request.form['color']
        cantidad = request.form['cantidad']
        precio_renta = request.form['precio_renta']
        ancho = request.form['ancho']
        largo = request.form['largo']
        imagen = request.files['Foto']

        if imagen and allowed_file(imagen.filename):
            cadena_aleatoria = my_random_string(10)
            filename = secure_filename(f"lona_{cadena_aleatoria}_{imagen.filename}")
            file_path = os.path.join(app.config['UPLOAD_FOLDER_LONAS'], filename)
            if os.path.exists(file_path):
                flash('Error: ¡Un archivo con el mismo nombre ya existe! Intente renombrar su archivo.')
                return redirect(url_for('lonas_dashboard'))
            imagen.save(file_path)

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('INSERT INTO lona (color, cantidad, precio_renta, ancho, largo, unidad_medida, filename) '
                        'VALUES (%s, %s, %s, %s, %s, %s, %s)',
                        (color, cantidad, precio_renta, ancho, largo, 'metros', filename))
            conn.commit()
            cur.close()
            conn.close()
            flash('¡Lona agregada exitosamente!', 'success')
            return redirect(url_for('lonas_dashboard'))
        else:
            flash('Error: ¡Extensión de archivo inválida! Intente con una imagen válida PNG, JPG o JPEG.')
            return redirect(url_for('lona_formulario'))
    return redirect(url_for('lona_formulario'))

@app.route('/dashboard/lonas/editar/<string:id>')
@login_required
def lona_editar(id):
    titulo = "Editar Lona"
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM lona WHERE id_lona=%s', (id,))
    lona = cur.fetchone()
    cur.close()
    conn.close()
    if lona:
        return render_template('lonas_editar.html', titulo=titulo, lona=lona)
    else:
        flash('Lona no encontrada', 'danger')
        return redirect(url_for('lonas_dashboard'))

@app.route('/dashboard/lonas/actualizar/<string:id>', methods=['POST'])
@login_required
def lona_actualizar(id):
    color = request.form['color']
    cantidad = request.form['cantidad']
    precio_renta = request.form['precio_renta']
    ancho = request.form['ancho']
    largo = request.form['largo']

    conn = get_db_connection()
    cur = conn.cursor()
    sql = "UPDATE lona SET color=%s, cantidad=%s, precio_renta=%s, ancho=%s, largo=%s WHERE id_lona=%s"
    valores = (color, cantidad, precio_renta, ancho, largo, id)
    
    cur.execute(sql, valores)
    conn.commit()
    cur.close()
    conn.close()

    flash('¡Lona modificada exitosamente!', 'success')
    return redirect(url_for('lonas_dashboard'))


@app.route('/dashboard/lonas/actualizar/foto/<string:id>', methods=['POST'])
@login_required
def lonas_actualizar_foto(id):
    if request.method == 'POST':
        imagen = request.files['Foto']
        foto_anterior = request.form['anterior']
        foto_anterior_path = os.path.join(ruta_lonas, foto_anterior) if foto_anterior else None
        editado = datetime.now()

        if imagen and allowed_file(imagen.filename):
            cadena_aleatoria = my_random_string(10)
            filename = cadena_aleatoria + "_" + secure_filename(imagen.filename)
            file_path = os.path.join(ruta_lonas, filename)

            if os.path.exists(file_path):
                flash('Error: ¡Un archivo con el mismo nombre ya existe! Intente renombrar su archivo.')
                return redirect(url_for('lonas_dashboard'))

            imagen.save(file_path)

            conn = get_db_connection()
            cur = conn.cursor()
            sql = "UPDATE lona SET imagen = %s WHERE id_lona = %s"
            values = (filename, id)
            cur.execute(sql, values)
            conn.commit()
            cur.close()
            conn.close()

            if foto_anterior_path and os.path.exists(foto_anterior_path):
                os.remove(foto_anterior_path)

            flash('¡Foto de lona actualizada exitosamente!', 'success')
            return redirect(url_for('lona_editar', id=id))
        else:
            flash('Error: ¡Extensión de archivo inválida! Intente con una imagen válida PNG, JPG o JPEG.')
            return redirect(url_for('lona_editar', id=id))

    return redirect(url_for('lonas_dashboard'))

@app.route("/dashboard/lonas/eliminar/<string:id>", methods=['POST'])
@login_required
def lona_eliminar(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM lona WHERE id_lona = %s', (id,))
    conn.commit()
    cur.close()
    conn.close()

    flash('¡Lona eliminada exitosamente!', 'success')
    return redirect(url_for('lonas_dashboard'))

#---------------CRUD CARPAS---------------#

@app.route("/dashboard/carpas")
@login_required
def carpas_dashboard():
    titulo = "carpas"
    sql_count = 'SELECT COUNT(*) FROM carpa;'
    sql_lim = 'SELECT id_carpa, color, cantidad, precio_renta, ancho, largo FROM carpa ORDER BY id_carpa DESC LIMIT %s OFFSET %s;'
    paginado = paginador(sql_count, sql_lim, 1, 5)
    return render_template('carpas.html',
                        titulo=titulo,
                        carpas=paginado[0],
                        page=paginado[1],
                        per_page=paginado[2],
                        total_items=paginado[3],
                        total_pages=paginado[4])

@app.route("/dashboard/carpas/formulario")
@login_required
def carpas_formulario():
    titulo = "Formulario de Carpas"
    return render_template('carpas_formulario.html', titulo = titulo)

@app.route("/dashboard/carpas/crear", methods=['GET', 'POST'])
@login_required
def carpas_crear():
    if request.method == 'POST':
        color = request.form['color']
        cantidad = request.form['cantidad']
        precio_renta = request.form['precio_renta']
        ancho = request.form['ancho']
        largo = request.form['largo']

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('INSERT INTO carpa (color, cantidad, precio_renta, ancho, largo)'
                    'VALUES ( %s, %s, %s, %s, %s)',
                    (color, cantidad, precio_renta, ancho, largo))
        
        conn.commit()
        cur.close()
        conn.close()
        flash('¡Carpa agregada exitosamente!', 'success')
        return redirect(url_for('carpas_dashboard'))
    return redirect(url_for('carpas_formulario'))

@app.route('/dashboard/carpas/editar/<int:id>')
@login_required
def carpas_editar(id):
    titulo = "Editar Carpa"
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM carpa WHERE id_carpa = %s', (id,))
    carpa = cur.fetchone()
    cur.close()
    conn.close()
    if carpa:
        return render_template('carpas_editar.html', titulo = titulo, carpa = carpa)
    else:
        flash('Carpa no encontrada', 'danger')
        return redirect(url_for('carpas_dashboard'))


@app.route('/dashboard/carpas/actualizar/<int:id>', methods=['POST'])
def carpas_actualizar(id):
    color = request.form['color']
    cantidad = request.form['cantidad']
    precio_renta = request.form['precio_renta']
    ancho = request.form['ancho']
    largo = request.form['largo']

    conn = get_db_connection()
    cur = conn.cursor()
    sql = "UPDATE carpa SET color = %s, cantidad = %s, precio_renta = %s, ancho = %s, largo = %s WHERE id_carpa = %s"
    valores = (color, cantidad, precio_renta, ancho, largo, id)
    
    cur.execute(sql, valores)
    conn.commit()
    cur.close()
    conn.close()

    flash('¡Carpa modificada exitosamente!', 'success')
    return redirect(url_for('carpas_dashboard'))

@app.route("/dashboard/carpas/eliminar/<string:id>", methods=['POST'])
@login_required
def carpas_eliminar(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM carpa WHERE id_carpa = %s', (id,))
    conn.commit()
    cur.close()
    conn.close()

    flash('¡Carpa eliminada exitosamente!', 'success')
    return redirect(url_for('carpas_dashboard'))

#-------------APARTADO LOGIN---------------------------#
@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/loguear', methods=['POST'])
def loguear():
    if request.method == 'POST':
        Username = request.form['Username']
        Password = request.form['Password']
        user = User(0, Username, Password, None)
        loged_user = ModuleUser.login(get_db_connection(), user)
        print(loged_user)
        if loged_user is not None:
            if loged_user.password:
                login_user(loged_user)
                return redirect(url_for('lonas_dashboard'))
            else:
                flash('Nombre de usuario y/o Contraseña incorrecta.')
                return render_template('login.html')
        else:
            flash('Nombre de usuario y/o Contraseña incorrecta.')
            return render_template('login.html')
    else:
        flash('Nombre de usuario y/o Contraseña incorrecta.')
        return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))
#------------------PAGINA DE ERROR Y PUERTO--------------#

def pagina_no_encontrada(error):
    return render_template('404.html')

def acceso_no_autorizado(error):
    return redirect(url_for('login'))

if __name__ == '__main__':
    csrf.init_app(app)
    app.register_error_handler(404,pagina_no_encontrada)
    app.register_error_handler(401,acceso_no_autorizado)
    app.run(debug=True, port=5000)
    
    #activar entorno         vistual.venv\Scripts\activate
    #correr aplicacion       python app\app.py run
    #                        flask --app app\app.py run 
    
    
