from werkzeug.security import check_password_hash
from .entities.user import User

class ModuleUser:
    @classmethod
    def login(cls, db, correo, password):
        try:
            cur = db.cursor()
            sql = '''
                SELECT u.id_user, u.correo, u.password, u.rol, c.username
                FROM usuario u
                JOIN cliente c ON u.id_user = c.fk_usuario
                WHERE u.estado = true AND u.correo = %s
            '''
            cur.execute(sql, (correo,))
            row = cur.fetchone()

            if row is not None and check_password_hash(row[2], password):
                return User(row[0], row[1], row[2], None, row[3], row[4])  # Incluye username
            else:
                return None
        except Exception as ex:
            raise Exception(f"Error durante el inicio de sesión: {ex}")

    @classmethod
    def get_by_id(cls, db, id_user):
        try:
            cur = db.cursor()
            sql = '''
                SELECT u.id_user, u.correo, u.password, u.estado, u.rol, c.username
                FROM usuario u
                JOIN cliente c ON u.id_user = c.fk_usuario
                WHERE u.estado = true AND u.id_user = %s
            '''
            cur.execute(sql, (id_user,))
            row = cur.fetchone()

            if row is not None:
                return User(row[0], row[1], row[2], row[3], row[4], row[5])  # Incluye username
            else:
                return None
        except Exception as ex:
            raise Exception(f"Error al obtener usuario por ID: {ex}")



