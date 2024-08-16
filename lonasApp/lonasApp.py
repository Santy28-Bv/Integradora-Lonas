from flask import Flask, render_template, url_for, redirect, request, flash, Blueprint, jsonify, session 
from psycopg2.extras import RealDictCursor, DictCursor
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
ruta_lonas ='./LonasApp/static/img/uploads/lonas'
ruta_carpas='./LonasApp/static/img/uploads/carpas'
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
app.config['UPLOAD_FOLDER_LONAS'] = './lonasApp/static/img/uploads/lonas/'
app.config['UPLOAD_FOLDER_CARPAS'] = './lonasApp/static/img/uploads/carpas/'

if not os.path.exists(app.config['UPLOAD_FOLDER_LONAS']):
    os.makedirs(app.config['UPLOAD_FOLDER_LONAS'])
    
if not os.path.exists(app.config['UPLOAD_FOLDER_CARPAS']):
    os.makedirs(app.config['UPLOAD_FOLDER_CARPAS'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

## Función para obtener la conexión a la base de datos
def get_db_connection():
    try:
        conn = psycopg2.connect(host='localhost',
                                dbname='lonas',
                                user=os.environ['DB_USER'],
                                password=os.environ['DB_PASSWORD'])
        return conn
    except psycopg2.Error as error:
        print(f"Error al conectar a la base de datos: {error}")
        return None


#---------------INICIO------------#

@app.route("/")
def index():
  
    return render_template('index.html')

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
def formulario_usuario():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        correo = request.form['correo']
        password = generate_password_hash(request.form['password'])

        if not correo or not password:
            flash("Correo y password son requeridos.", 'error')
            return redirect(url_for('formulario_usuario'))

        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            try:
                # Verificar si el correo ya existe
                cur.execute('SELECT 1 FROM usuario WHERE "correo" = %s', (correo,))
                if cur.fetchone():
                    flash("El correo ya existe.", 'error')
                    return redirect(url_for('formulario_usuario'))
                
                # Insertar en la tabla usuario y obtener el id del usuario creado
                cur.execute(
                    'INSERT INTO usuario ("correo", "password") VALUES (%s, %s) RETURNING id_user',
                    (correo, password)
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

def Cliente():
    if current_user.is_authenticated:
        # Redirigir a una página diferente si el usuario ya está autenticado
        return redirect(url_for('index'))
    if request.method == 'POST':
        # Obtener los datos del formulario
        Nombre = request.form.get('nombre')
        Apellido_Pa = request.form.get('apellido_paterno')
        Apellido_Ma = request.form.get('apellido_materno')
        Direccion = request.form.get('direccion')
        Estado = request.form.get('estado')
        Municipio = request.form.get('municipio')
        Telefono = request.form.get('telefono')
        Usuario = request.form.get('username')

        # Obtener fk_usuario de la sesión
        fk_usuario = session.get('id_user')

        # Verificar si algún dato falta
        if not Nombre or not Apellido_Pa or not Apellido_Ma or not Direccion or not Estado or not Municipio or not Telefono or not Usuario or not fk_usuario:
            flash("Todos los datos del cliente son requeridos.", 'error')
            return redirect(url_for('Cliente'))

        # Conexión a la base de datos
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            try:
                # Insertar en la tabla cliente (ajustar la sintaxis según tu base de datos)
                cur.execute(
                    'INSERT INTO cliente (nombre, apellido_paterno, apellido_materno, direccion, estado, municipio, telefono, username, fk_usuario) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
                    (Nombre, Apellido_Pa, Apellido_Ma, Direccion, Estado, Municipio, Telefono, Usuario, fk_usuario)
                )
                conn.commit()
                flash("Datos de cliente guardados correctamente", 'success')

                # Redirigir al índice o a la página correspondiente
                return redirect(url_for('index'))

            except Exception as e:
                conn.rollback()
                flash(f"Error al guardar los datos del cliente en la base de datos: {e}", 'error')
            finally:
                cur.close()
                conn.close()
        else:
            flash("Error al conectar a la base de datos", 'error')
            return redirect(url_for('Cliente'))

    # Renderizar el template del formulario
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
        nombre = request.form['nombre']
        apellido_pa = request.form['apellido_paterno']
        apellido_ma = request.form['apellido_materno']
        direccion = request.form['direccion']
        estado = request.form['estado']
        municipio = request.form['municipio']
        telefono = request.form['telefono']
        username = request.form['username']

        try:
            cur.execute('UPDATE cliente SET "nombre" = %s, "apellido_paterno" = %s, "apellido_materno" = %s, "direccion" = %s, "estado" = %s, "municipio" = %s, "telefono" = %s, "email" = %s WHERE id_cliente = %s',
                        (nombre, apellido_pa, apellido_ma, direccion, estado, municipio, telefono, username, id_cliente))
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
    if current_user.rol == 'admin':

        titulo = "Lonas"
        sql_count = 'SELECT COUNT(*) FROM lona;'
        sql_lim = 'SELECT id_lona, color, cantidad, precio_renta, medidas FROM lona ORDER BY id_lona DESC LIMIT %s OFFSET %s;'
        paginado = paginador(sql_count, sql_lim, 1, 5)
        return render_template('lonas.html',
                                titulo=titulo,
                                lonas=paginado[0],
                                page=paginado[1],
                                per_page=paginado[2],
                                total_items=paginado[3],
                                total_pages=paginado[4])
    else:
                return render_template('index.html')
    
@app.route("/dashboard/lonas/formulario")
@login_required
def lona_formulario():
    if current_user.rol == 'admin':
            titulo = "Formulario de Lonas"
            return render_template('lonas_formulario.html', titulo=titulo)
    else:
           return render_template('index.html')


@app.route("/dashboard/lonas/crear", methods=['GET', 'POST'])
@login_required
def lona_crear():
    if current_user.rol == 'admin':
        if request.method == 'POST':
            color = request.form['color']
            cantidad = request.form.get('cantidad', type=int)
            precio_renta = request.form.get('precio_renta', type=float)
            medidas = request.form.get('medidas')
            imagen = request.files.get('Foto')

            if imagen and allowed_file(imagen.filename):
                cadena_aleatoria = my_random_string(10)
                filename = secure_filename(f"lona_{cadena_aleatoria}_{imagen.filename}")
                file_path = os.path.join(app.config['UPLOAD_FOLDER_LONAS'], filename)
                
                # Verifica si el archivo ya existe antes de guardarlo
                if os.path.exists(file_path):
                    flash('Error: ¡Un archivo con el mismo nombre ya existe! Intente renombrar su archivo.')
                    return redirect(url_for('lona_formulario'))

                imagen.save(file_path)
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute('INSERT INTO lona (color, cantidad, precio_renta, medidas, imagen) '
                            'VALUES (%s, %s, %s, %s, %s)',
                            (color, cantidad, precio_renta, medidas, filename))
                conn.commit()
                cur.close()
                conn.close()
                flash('¡Lona agregada exitosamente!', 'success')
                return redirect(url_for('lonas_dashboard'))
            else:
                flash('Error: ¡Extensión de archivo inválida! Intente con una imagen válida PNG, JPG o JPEG.')
                return redirect(url_for('lona_formulario'))
        return render_template('lona_formulario.html')
    else:
        return redirect(url_for('index'))


@app.route('/dashboard/lonas/editar/<string:id>')
@login_required
def lona_editar(id):
    if current_user.rol == 'admin':
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
    else:
           return redirect(url_for('index'))


@app.route('/dashboard/lonas/actualizar/<string:id>', methods=['POST'])
@login_required
def lona_actualizar(id):
    if current_user.rol == 'admin':
        color = request.form['color']
        cantidad = request.form.get('cantidad', type=int)
        precio_renta = request.form.get('precio_renta', type=float)
        medidas = request.form.get('medidas')
        conn = get_db_connection()
        cur = conn.cursor()
        sql = "UPDATE lona SET color=%s, cantidad=%s, precio_renta=%s, medidas=%s WHERE id_lona=%s"
        valores = (color, cantidad, precio_renta, medidas, id)

        cur.execute(sql, valores)
        conn.commit()
        cur.close()
        conn.close()

        flash('¡Lona modificada exitosamente!', 'success')
        return redirect(url_for('lonas_dashboard'))
    else:
         return redirect(url_for('index'))

@app.route('/dashboard/lonas/actualizar/foto/<string:id>', methods=['POST'])
@login_required
def lonas_actualizar_foto(id):
    if current_user.rol == 'admin':   
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
    else:
        return redirect(url_for('index'))


@app.route("/dashboard/lonas/eliminar/<string:id>", methods=['POST'])
@login_required
def lona_eliminar(id):
    if current_user.rol == 'admin':
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('DELETE FROM lona WHERE id_lona = %s', (id,))
        conn.commit()
        cur.close()
        conn.close()

        flash('¡Lona eliminada exitosamente!', 'success')
        return redirect(url_for('lonas_dashboard'))
    else:
       return redirect(url_for('index'))

#---------------CRUD CARPAS---------------#

@app.route("/dashboard/carpas")
@login_required
def carpas_dashboard():
    if current_user.rol == 'admin':
        titulo = "carpas"
        sql_count = 'SELECT COUNT(*) FROM carpa;'
        sql_lim = 'SELECT id_carpa, color, cantidad, precio_renta, medidas FROM carpa ORDER BY id_carpa DESC LIMIT %s OFFSET %s;'
        paginado = paginador(sql_count, sql_lim, 1, 5)
        
        return render_template('carpas.html',
                               titulo=titulo,
                               carpas=paginado[0],
                               page=paginado[1],
                               per_page=paginado[2],
                               total_items=paginado[3],
                               total_pages=paginado[4])
    else:
        return redirect(url_for('index'))
    

@app.route("/dashboard/carpas/formulario", methods=['GET', 'POST'])
@login_required
def carpas_formulario():
    if current_user.rol == 'admin':
        titulo = "Formulario de Carpas"
        return render_template('carpas_formulario.html', titulo=titulo)
    else:
        return redirect(url_for('index'))

@app.route("/dashboard/carpas/crear", methods=['GET', 'POST'])
@login_required
def carpas_crear():
    if current_user.rol == 'admin':   
        if request.method == 'POST':
            color = request.form['color']
            cantidad = request.form['cantidad']
            precio_renta = request.form['precio_renta']
            medidas = request.form['medidas']

            conn = get_db_connection()
            cur = conn.cursor()

            try:
                cur.execute('INSERT INTO carpa (color, cantidad, precio_renta, medidas) VALUES (%s, %s, %s, %s)',
                            (color, cantidad, precio_renta, medidas))
                conn.commit()
                flash('¡Carpa agregada exitosamente!', 'success')
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                flash('Error: Ya existe una carpa con este ID.', 'danger')
            finally:
                cur.close()
                conn.close()
            return redirect(url_for('carpas_dashboard'))
        return redirect(url_for('carpas_formulario'))
    else:        
        return redirect(url_for('index'))


@app.route('/dashboard/carpas/editar/<int:id>')
@login_required
def carpas_editar(id):

    if current_user.rol == 'admin':
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
    else:
        return redirect(url_for('index'))



@app.route('/dashboard/carpas/actualizar/<int:id>', methods=['POST'])
@login_required
def carpas_actualizar(id):
    if current_user.rol == 'admin':
        color = request.form['color']
        cantidad = request.form['cantidad']
        precio_renta = request.form['precio_renta']
        medidas = request.form['medidas']

        conn = get_db_connection()
        cur = conn.cursor()
        sql = "UPDATE carpa SET color = %s, cantidad = %s, precio_renta = %s, medidas = %s WHERE id_carpa = %s"
        valores = (color, cantidad, precio_renta, medidas, id)
        
        cur.execute(sql, valores)
        conn.commit()
        cur.close()
        conn.close()

        flash('¡Carpa modificada exitosamente!', 'success')
        return redirect(url_for('carpas_dashboard'))
    else:
        return redirect(url_for('index'))

@app.route("/dashboard/carpas/eliminar/<string:id>", methods=['POST'])
@login_required
def carpas_eliminar(id):
    if current_user.rol == 'admin':
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('DELETE FROM carpa WHERE id_carpa = %s', (id,))
        conn.commit()
        cur.close()
        conn.close()

        flash('¡Carpa eliminada exitosamente!', 'success')
        return redirect(url_for('carpas_dashboard'))
    else:   
        return redirect(url_for('index'))

#-------------APARTADO LOGIN---------------------------#

@app.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index')) 
    return render_template('login.html')

@app.route('/loguear', methods=['POST'])
def loguear():
    if request.method == 'POST':
        correo = request.form.get('correo')
        password = request.form.get('password')
        
        print(f"Datos recibidos: correo={correo}, password={password}")

        if not correo or not password:
            print("Correo o contraseña vacíos.")
            flash('Correo y/o contraseña incorrectos.')
            return redirect(url_for('login'))
        
        loged_user = ModuleUser.login(get_db_connection(), correo, password)
        
        print(f"Loged_user: {loged_user}")

        if loged_user:
            login_user(loged_user)
            flash(f'Bienvenido, {loged_user.username}!')
            return redirect(url_for('index'))  
        else:
            flash('Correo y/o contraseña incorrectos.')
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))






#------------------RENTAR O SOLICITAR--------------#
@app.route('/rentar_lonas', methods=['GET', 'POST'])
@login_required
def rentar_lonas():
    if request.method == 'POST':
        try:
            # Captura de datos del formulario
            fecha_inicio = datetime.strptime(request.form['fecha_inicio'], '%Y-%m-%d')
            fecha_fin = datetime.strptime(request.form['fecha_fin'], '%Y-%m-%d')
            metodo_pago = request.form['metodo_de_pago']
            medidas = request.form['medidas']
            color = request.form['color']
            correo_cliente = current_user.correo

            print("Datos capturados del formulario:")
            print(f"Fecha Inicio: {fecha_inicio}, Fecha Fin: {fecha_fin}, Método de Pago: {metodo_pago}")
            print(f"Medidas: {medidas}, Color: {color}, Correo Cliente: {correo_cliente}")

            # Establecer conexión a la base de datos
            conn = get_db_connection()
            cur = conn.cursor()

            # Verificar disponibilidad de la lona
            cur.execute("SELECT cantidad, id_lona, precio_renta FROM lona WHERE medidas = %s AND color = %s", (medidas, color))
            result = cur.fetchone()
            print("Resultado de la consulta de disponibilidad de lona:", result)

            if result is None or result[0] <= 0:
                flash('La lona solicitada no está disponible.', 'error')
                return redirect(url_for('rentar_lonas'))

            cantidad, id_lona, precio_renta = result
            print(f"Cantidad disponible: {cantidad}, ID Lona: {id_lona}, Precio Renta: {precio_renta}")

            # Recuperar el id_cliente basado en el correo del cliente
            cur.execute("SELECT id_cliente FROM cliente JOIN usuario ON cliente.fk_usuario = usuario.id_user WHERE usuario.correo = %s", (correo_cliente,))
            id_cliente = cur.fetchone()
            print("Resultado de la consulta del ID del cliente:", id_cliente)

            if id_cliente is None:
                flash('No se encontró el cliente asociado a este correo.', 'error')
                return redirect(url_for('rentar_lonas'))

            id_cliente = id_cliente[0]
            print(f"ID Cliente: {id_cliente}")

            # Calcular el costo total
            dias_alquiler = (fecha_fin - fecha_inicio).days
            recargo = 0
            if fecha_fin.date() > datetime.now().date():  # Convertir fecha_fin a date
                recargo = (fecha_fin.date() - datetime.now().date()).days * 300

            total = precio_renta + recargo

            # Insertar los datos en la tabla alquila (sin color y medidas)
            cur.execute("""
                INSERT INTO alquila (fk_cliente, fk_lona, fecha_inicio, fecha_fin, estatus, metodo_de_pago, total)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id_alquila;
            """, (id_cliente, id_lona, fecha_inicio, fecha_fin, 'En proceso', metodo_pago, total))

            id_alquila = cur.fetchone()
            print(f"ID de la nueva solicitud de alquiler: {id_alquila}")

            # Actualizar la cantidad de lonas disponibles
            cur.execute("UPDATE lona SET cantidad = cantidad - 1 WHERE id_lona = %s", (id_lona,))
            print(f"Cantidad de lona actualizada para ID Lona: {id_lona}")

            conn.commit()
            flash('Solicitud realizada con éxito.', 'success')

        except Exception as e:
            print(f"Error durante la ejecución: {e}")
            conn.rollback()
            flash(f'Error al realizar la solicitud: {e}', 'error')

        finally:
            cur.close()
            conn.close()

    return render_template('rentar_lonas.html')


@app.route('/rentar_carpas')
@login_required
def rentar_carpas():
    return render_template('rentar_carpas.html')

#------------------VISTAS DE PEDIDOS--------------#
@app.route('/dashboard/pedidos/lonas')
@login_required
def pedidos_lonas():
    if current_user.rol == 'admin':
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        sql_count = 'SELECT COUNT(*) FROM vista_pedidos_lona;'
        sql_lim = 'SELECT * FROM vista_pedidos_lona ORDER BY id_alquila ASC LIMIT %s OFFSET %s;'

        paginado = paginador(sql_count, sql_lim, page, per_page)
        
        # Imprime los datos para ver qué está obteniendo
        print("Datos obtenidos: ", paginado[0])
        print("Página actual: ", paginado[1])
        print("Registros por página: ", paginado[2])
        print("Total de registros: ", paginado[3])
        print("Total de páginas: ", paginado[4])

        return render_template(
            'pedidos_lonas.html',
            titulo="Pedidos de Lonas",
            dato=paginado[0],
            page=paginado[1],
            per_page=paginado[2],
            total_items=paginado[3],
            total_pages=paginado[4]
        )
@app.route('/update_status/<int:id>', methods=['POST'])
def update_status(id):
    try:
        estatus = request.form['estatus']
    except KeyError:
        return "El campo 'estatus' no se encontró en la solicitud", 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Obtener el estatus actual del registro
        cur.execute("SELECT estatus FROM alquila WHERE id_alquila = %s", (id,))
        current_status = cur.fetchone()

        if current_status is None:
            flash('Registro no encontrado.', 'error')
            return redirect(url_for('pedidos_lonas'))

        current_status = current_status[0]

        # Si el estatus cambia a 'Devuelta', actualizamos el estatus primero
        if estatus == 'Devuelta' and current_status != 'Devuelta':
            # Actualizar el estatus a 'Devuelta'
            cur.execute("""
                UPDATE alquila
                SET estatus = %s
                WHERE id_alquila = %s;
            """, (estatus, id))
            conn.commit()
            flash('Estado actualizado a "Devuelta". Ahora confirme si desea eliminar el registro.', 'warning')

            # Redirigir para confirmar la eliminación
            return redirect(url_for('confirm_delete', id=id))

        else:
            # Actualizar el estatus normalmente
            cur.execute("""
                UPDATE alquila
                SET estatus = %s
                WHERE id_alquila = %s;
            """, (estatus, id))
            conn.commit()
            flash('Estado actualizado con éxito.', 'success')

    except Exception as e:
        print(f"Error durante la actualización: {e}")
        conn.rollback()
        flash(f'Error al actualizar el estado: {e}', 'error')

    finally:
        cur.close()
        conn.close()

    return redirect(url_for('pedidos_lonas'))


@app.route('/confirm_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def confirm_delete(id):
    if request.method == 'POST':
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # Recuperar los datos del alquiler para obtener la lona asociada
            cur.execute("SELECT fk_lona FROM alquila WHERE id_alquila = %s", (id,))
            alquiler = cur.fetchone()

            if alquiler is None:
                flash('No se encontró el alquiler.', 'error')
                return redirect(url_for('pedidos_lonas'))

            id_lona = alquiler[0]

            # Actualizar la cantidad de lonas disponibles
            cur.execute("UPDATE lona SET cantidad = cantidad + 1 WHERE id_lona = %s", (id_lona,))
            print(f"Cantidad de lona actualizada para ID Lona: {id_lona}")

            # Eliminar el registro de alquiler
            cur.execute("DELETE FROM alquila WHERE id_alquila = %s", (id,))
            print(f"Registro de alquiler con ID {id} eliminado.")

            conn.commit()
            flash('Lona devuelta y cantidad actualizada con éxito.', 'success')

        except Exception as e:
            print(f"Error durante la ejecución: {e}")
            conn.rollback()
            flash(f'Error al devolver la lona: {e}', 'error')

        finally:
            cur.close()
            conn.close()

        return redirect(url_for('pedidos_lonas'))

    # Renderizar la página de confirmación
    return render_template('confirm_delete.html', id=id)



@app.route('/dashboard/pedidos/carpas')
def pedidoscarpa():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM alquiladores_datos ORDER BY id_alquila ASC;")
    datos = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('pedidos_carpa.html',  dato=datos)




@app.route('/Contactanos')
def conocenos():
    return render_template('Conocenos.html')



#------------------PAGINA DE ERROR Y PUERTO--------------#

def pagina_no_encontrada(error):
    return render_template('404.html')
def acceso_no_autorizado(error):
 return render_template('401.html')#----------------------------------------------


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


        #correr aplicacion       python LonasApp\LonasApp.py run
