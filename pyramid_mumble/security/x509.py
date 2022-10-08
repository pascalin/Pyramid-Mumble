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


def import_pkcs12(data, dest_dir, password=None):
    parent_dir = "/".join(os.path.split(dest_dir)[:-1])
    if not os.path.isdir(dest_dir) and os.path.exists(parent_dir):
        os.makedirs(dest_dir)

    private_key, certificate, additional_certificates = serialization.pkcs12.load_key_and_certificates(data, password)
    key_path = os.path.join(dest_dir, "private_key.pem")
    cert_path = os.path.join(dest_dir, "certificate.pem")

    with open(key_path, 'wb') as privkey_file:
        privkey_file.write(private_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.TraditionalOpenSSL,
                        encryption_algorithm=serialization.NoEncryption(),
        ))
    with open(cert_path, 'wb') as certificate_file:
        certificate_file.write(certificate.public_bytes(serialization.Encoding.PEM))

    return (cert_path, key_path)

def export_pkcs12(user):
    cert = cryptography.x509.load_pem_x509_certificate(open(user.certificate, 'rb').read())
    key = serialization.load_pem_private_key(open(user.privkey, 'rb').read(), None)

    # p12 = serialization.pkcs12.serialize_key_and_certificates(
    #     bytes(user.email, encoding='utf8'), key, cert, cas=None, encryption_algorithm=serialization.NoEncryption(),
    # )

    return serialization.pkcs12.serialize_key_and_certificates(
        bytes(user.email, encoding='utf8'), key, cert, cas=None, encryption_algorithm=serialization.NoEncryption(),
    )