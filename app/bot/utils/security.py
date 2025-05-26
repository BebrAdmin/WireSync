import secrets
import string

def generate_password(length=32):
    alphabet = string.ascii_letters + "-"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_api_token(length=64):
    alphabet = string.ascii_letters + "-!@#$"
    return ''.join(secrets.choice(alphabet) for _ in range(length))