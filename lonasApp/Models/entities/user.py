from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin

class User(UserMixin):
    
    def __init__(self, id_user, correo, password, estado, rol, username) -> None:
        self.id_user = id_user
        self.correo = correo
        self.password = password
        self.estado = estado
        self.rol = rol
        self.username = username 
            
    def get_id(self):
        return str(self.id_user)

    @classmethod
    def check_password(cls, hashed_password, password):
        return check_password_hash(hashed_password, password)

    @classmethod
    def generate_password_hash(cls, password):
        return generate_password_hash(password)
