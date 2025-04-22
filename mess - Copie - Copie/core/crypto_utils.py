import os
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes

def generate_keys(username):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    client_dir = f'clients/{username}'
    os.makedirs(client_dir, exist_ok=True)

    with open(f'{client_dir}/private_key.pem', 'wb') as f:
        f.write(private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption()
        ))

    public_pem = public_key.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return public_pem.decode()

def load_private_key(username):
    path = f'clients/{username}/private_key.pem'
    with open(path, 'rb') as f:
        return serialization.load_pem_private_key(f.read(), password=None)

def encrypt_message(public_key_pem, message):
    public_key = serialization.load_pem_public_key(public_key_pem.encode())
    return public_key.encrypt(
        message.encode(),
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )

def decrypt_message(private_key, encrypted_message):
    return private_key.decrypt(
        encrypted_message,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    ).decode()
