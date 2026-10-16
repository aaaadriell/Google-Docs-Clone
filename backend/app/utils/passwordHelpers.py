import bcrypt

# Hash password using bcrypt
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(plain_passord: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_passord.encode('utf-8'), hashed_password.encode('utf-8'))