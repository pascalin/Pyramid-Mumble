import datetime
import os
import tempfile

import cryptography
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
# from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def get_user_cert_and_key(user, password=None, tmp_dir=None):
    if not tmp_dir:
        tmp_dir = tempfile.mkdtemp()
    key_path = os.path.join(tmp_dir, f"{user.email}_key.pem")
    if user.privkey:
        try:
            with open(user.privkey, "rb") as privkey:
                if password:
                    key = serialization.load_pem_private_key(privkey.read(), password)
                    with open(key_path, "wb") as f:
                        f.write(key.private_bytes(
                            encoding=serialization.Encoding.PEM,
                            format=serialization.PrivateFormat.TraditionalOpenSSL,
                            encryption_algorithm=serialization.NoEncryption(),
                        ))
                    return (user.certificate, key_path)
        except ValueError:
            return None
        except TypeError:
            raise
        return (user.certificate, user.privkey)


def generate_selfsigned_cert(user, key=None, size=2048, password=None, dest_dir=None):
    """Generates self-signed certificate for a hostname, and optional IP addresses."""

    if not dest_dir:
        dest_dir = tempfile.mkdtemp()

    crt_path = os.path.join(dest_dir, f"{user.email}_cert.pem")
    key_path = os.path.join(dest_dir, f"{user.email}_key.pem")

    # Generate our key
    if key is None:
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=size,
            # backend=default_backend(),
        )

    # Write our key to disk for safe keeping
    if password:
        encryption_algorithm = serialization.BestAvailableEncryption(password)
    else:
        encryption_algorithm = serialization.NoEncryption()
    with open(key_path, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=encryption_algorithm,
        ))

    subject = issuer = cryptography.x509.Name([
        cryptography.x509.NameAttribute(NameOID.COUNTRY_NAME, user.country),
        cryptography.x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, user.state),
        cryptography.x509.NameAttribute(NameOID.LOCALITY_NAME, ''),
        cryptography.x509.NameAttribute(NameOID.ORGANIZATION_NAME, user.organization),
        cryptography.x509.NameAttribute(NameOID.COMMON_NAME, user.realname),
    ])

    cert = cryptography.x509.CertificateBuilder().subject_name(subject).issuer_name(issuer).public_key(key.public_key()).serial_number(cryptography.x509.random_serial_number()).not_valid_before(datetime.datetime.utcnow()).not_valid_after(
    # Our certificate will be valid for 10 years
    datetime.datetime.utcnow() + datetime.timedelta(days=10*365)
    ).add_extension(
        cryptography.x509.SubjectAlternativeName([
            #x509.DNSName(u"localhost"),
            # cryptography.x509.NameAttribute(NameOID.EMAIL_ADDRESS, user.email),
            cryptography.x509.RFC822Name(user.email)
        ]),
        critical=False,
    # Sign our certificate with our private key
    ).sign(key, hashes.SHA256())

    # Write our certificate out to disk.
    with open(crt_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    return (crt_path, key_path)