import base64, os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend

def generate_aes_key_iv():
    key = os.urandom(32)  # AES 256
    iv = os.urandom(16)
    return key, iv

def aes_encrypt(data, key, iv):
    padder = sym_padding.PKCS7(128).padder()
    padded_data = padder.update(data) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    return encryptor.update(padded_data) + encryptor.finalize()

def aes_decrypt(ciphertext, key, iv):
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = sym_padding.PKCS7(128).unpadder()
    return unpadder.update(padded_data) + unpadder.finalize()

def rsa_encrypt_key(key, public_key_pem):
    public_key = serialization.load_pem_public_key(public_key_pem.encode(), backend=default_backend())
    return public_key.encrypt(key, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))

def rsa_decrypt_key(encrypted_key, private_key):
    return private_key.decrypt(encrypted_key, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))

def encrypt_image_base64_hybrid(image_data, public_key_pem):
    key, iv = generate_aes_key_iv()
    encrypted_data = aes_encrypt(image_data, key, iv)
    encrypted_key = rsa_encrypt_key(key, public_key_pem)
    encrypted_iv = rsa_encrypt_key(iv, public_key_pem)
    return base64.b64encode(encrypted_key).decode() + "||" + base64.b64encode(encrypted_iv).decode() + "||" + base64.b64encode(encrypted_data).decode()

def decrypt_image_base64_hybrid(encrypted_str, private_key):
    encrypted_key_b64, encrypted_iv_b64, encrypted_data_b64 = encrypted_str.split("||")
    encrypted_key = base64.b64decode(encrypted_key_b64)
    encrypted_iv = base64.b64decode(encrypted_iv_b64)
    encrypted_data = base64.b64decode(encrypted_data_b64)
    key = rsa_decrypt_key(encrypted_key, private_key)
    iv = rsa_decrypt_key(encrypted_iv, private_key)
    return aes_decrypt(encrypted_data, key, iv)

def encrypt_binary_hybrid(data_bytes, public_key_pem):
    key, iv = generate_aes_key_iv()
    ciphertext = aes_encrypt(data_bytes, key, iv)
    encrypted_key = rsa_encrypt_key(key, public_key_pem)
    encrypted_iv = rsa_encrypt_key(iv, public_key_pem)
    return ciphertext, encrypted_key, encrypted_iv

def decrypt_binary_hybrid(ciphertext, encrypted_key, encrypted_iv, private_key):
    key = rsa_decrypt_key(encrypted_key, private_key)
    iv = rsa_decrypt_key(encrypted_iv, private_key)
    return aes_decrypt(ciphertext, key, iv)

