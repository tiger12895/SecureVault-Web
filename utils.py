import hashlib
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# مفتاح التشفير المتماثل (AES) - يجب أن يكون 16 أو 24 أو 32 بايت
# ملحوظة: في المشاريع الحقيقية يتم تخزين هذا المفتاح في بيئة آمنة
AES_KEY = b'sixteen_byte_key' 

# 1. تشفير الملف باستخدام AES-256
def encrypt_file(data):
    # إنشاء IV (Initialization Vector) عشوائي لكل عملية تشفير
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(AES_KEY), modes.CFB(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    return iv + encryptor.update(data) + encryptor.finalize()

# 2. فك التشفير
def decrypt_file(encrypted_data):
    # استخراج أول 16 بايت (الـ IV)
    iv = encrypted_data[:16]
    actual_encrypted_data = encrypted_data[16:]
    cipher = Cipher(algorithms.AES(AES_KEY), modes.CFB(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    return decryptor.update(actual_encrypted_data) + decryptor.finalize()

# 3. حساب الـ Hash (SHA-256) للتأكد من الـ Integrity
def get_file_hash(data):
    return hashlib.sha256(data).hexdigest()

# 4. التوقيع الرقمي (Authenticity)
# هنا بنعمل توقيع رقمي "محاكاة" عن طريق دمج الداتا مع مفتاح سري وتشفيرهم بالهاش
def sign_data(data):
    server_secret = "PROJECT_SECRET_2026" # مفتاح سري خاص بالسيرفر
    # التوقيع هو هاش يجمع بين محتوى الملف وسر السيرفر
    signature = hashlib.sha256((data.hex() + server_secret).encode()).hexdigest()
    return signature