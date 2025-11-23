import os

from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Obtener clave de encriptación
# NOTA: En producción, esto DEBE venir de variables de entorno.
# Si no existe, generamos una temporal para desarrollo.
# (Esto evita que falle en local si no configuraste el .env)
_KEY = os.getenv("ENCRYPTION_SECRET_KEY", Fernet.generate_key().decode())
_CIPHER = Fernet(_KEY.encode() if isinstance(_KEY, str) else _KEY)


def encrypt_aes256(content: str) -> bytes:
    """
    Encripta una cadena de texto usando Fernet (AES-256).

    Cumple con la RN16: Encriptación de Código Fuente en reposo.

    Args:
        content: El texto plano (código fuente) a encriptar.

    Returns:
        bytes: El contenido encriptado listo para almacenar en BD.

    Raises:
        ValueError: Si el contenido es nulo o vacío.
    """
    if not content:
        raise ValueError("El contenido a encriptar no puede estar vacío")

    return _CIPHER.encrypt(content.encode("utf-8"))


def decrypt_aes256(encrypted_content: bytes) -> str:
    """
    Desencripta bytes almacenados para recuperar el texto original.

    Args:
        encrypted_content: Los bytes encriptados recuperados de la BD.

    Returns:
        str: El código fuente original en texto plano.
    """
    if not encrypted_content:
        return ""

    return _CIPHER.decrypt(encrypted_content).decode("utf-8")
