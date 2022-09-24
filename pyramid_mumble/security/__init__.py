import bcrypt
import secrets
import string


def hash_password(pw):
    pwhash = bcrypt.hashpw(pw.encode('utf8'), bcrypt.gensalt())
    return pwhash.decode('utf8')


def check_password(pw, hashed_pw):
    expected_hash = hashed_pw.encode('utf8')
    return bcrypt.checkpw(pw.encode('utf8'), expected_hash)


def random_password(length=12, hashed=False):
    password = ''.join((secrets.choice(string.ascii_letters + string.digits) for i in range(2)))
    password = password + ''.join((secrets.choice(string.ascii_letters + string.digits + string.punctuation) for i in range(length-4)))
    password = password + ''.join((secrets.choice(string.ascii_letters + string.digits) for i in range(2)))
    if hashed:
        return hash_password(password)
    return password


def random_string(length=10):
    rstring = ''.join((secrets.choice(string.ascii_letters + string.digits) for i in range(length)))
    return rstring