from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, abort, jsonify
import sqlite3, bcrypt, os, io, jwt, pyotp, qrcode, base64
from authlib.integrations.flask_client import OAuth
from utils import encrypt_file, decrypt_file, get_file_hash, sign_data
from functools import wraps
from datetime import datetime, timedelta, timezone

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['TEMPLATES_AUTO_RELOAD'] = True

# ======================================================
# الإعدادات العامة
# ======================================================
UPLOAD_FOLDER = 'uploads'
JWT_SECRET = os.environ.get('JWT_SECRET', 'jwt_dev_secret_2026') # في الإنتاج يُؤخذ من .env
JWT_ALGORITHM = 'HS256'
JWT_EXPIRY_HOURS = 2

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ======================================================
# Google OAuth
# ======================================================
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID', 'YOUR_GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET', 'YOUR_GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# ======================================================
# قاعدة البيانات
# ======================================================
def get_db():
    conn = sqlite3.connect('vault_system.db')
    conn.row_factory = sqlite3.Row
    return conn

# ======================================================
# JWT Helpers
# ======================================================
def generate_jwt(user_id, role_id, username):
    """إنشاء JWT token بعد تسجيل الدخول الناجح"""
    payload = {
        'user_id': user_id,
        'role_id': role_id,
        'username': username,
        'exp': datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS),
        'iat': datetime.now(timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_jwt(token):
    """فك تشفير والتحقق من JWT token"""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# ======================================================
# Decorators للحماية
# ======================================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("يرجى تسجيل الدخول للوصول لهذه الصفحة")
            return redirect(url_for('login'))
        # التحقق من صلاحية JWT
        token = session.get('jwt_token')
        if not token or not decode_jwt(token):
            session.clear()
            flash("⚠️ انتهت صلاحية جلستك، يرجى تسجيل الدخول مرة أخرى")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role_id') != 1:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@app.errorhandler(403)
def access_denied(error):
    return render_template('403.html'), 403

# ======================================================
# Routes: Auth
# ======================================================
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email    = request.form['email']
        password = request.form['password']

        # ======================================================
        # Password Policy Enforcement
        # ======================================================
        import re
        errors = []
        if len(password) < 8:
            errors.append("كلمة المرور يجب أن تكون 8 أحرف على الأقل")
        if not re.search(r'[A-Z]', password):
            errors.append("يجب أن تحتوي على حرف كبير واحد على الأقل (A-Z)")
        if not re.search(r'[a-z]', password):
            errors.append("يجب أن تحتوي على حرف صغير واحد على الأقل (a-z)")
        if not re.search(r'[0-9]', password):
            errors.append("يجب أن تحتوي على رقم واحد على الأقل (0-9)")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("يجب أن تحتوي على رمز خاص مثل !@#$%")

        if errors:
            for err in errors:
                flash("⚠️ " + err)
            return render_template('register.html', password_errors=errors)

        try:
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            db = get_db()
            db.execute('INSERT INTO users (username, email, password_hash, role_id) VALUES (?,?,?,3)',
                       (username, email, hashed))
            db.commit()
            db.close()
            flash("✅ تم إنشاء الحساب بنجاح، يمكنك الدخول الآن")
            return redirect(url_for('login'))
        except Exception as e:
            flash("❌ خطأ: اسم المستخدم أو البريد موجود بالفعل")
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        db.close()

        if user and user['password_hash'] != 'OAUTH_ACCOUNT':
            if bcrypt.checkpw(password.encode('utf-8'), user['password_hash']):
                # إذا كان المستخدم قد فعّل 2FA، نحوله لصفحة التحقق
                if user['two_factor_secret']:
                    session['pending_user_id'] = user['user_id']
                    session['pending_role_id'] = user['role_id']
                    session['pending_username'] = user['username']
                    return redirect(url_for('verify_2fa'))

                # تسجيل دخول كامل مع JWT
                token = generate_jwt(user['user_id'], user['role_id'], user['username'])
                session['user_id'] = user['user_id']
                session['role_id'] = user['role_id']
                session['user_name'] = user['username']
                session['jwt_token'] = token
                return redirect(url_for('dashboard'))

        flash('⚠️ البريد الإلكتروني أو كلمة المرور غير صحيحة')
    return render_template('login.html')

# ======================================================
# Routes: Google OAuth
# ======================================================
@app.route('/login/google')
def google_login():
    return google.authorize_redirect(url_for('authorize', _external=True))

@app.route('/authorize')
def authorize():
    token = google.authorize_access_token()
    user_info = google.get('userinfo').json()
    email = user_info['email']
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    if not user:
        db.execute('INSERT INTO users (username, email, password_hash, role_id) VALUES (?,?,?,3)',
                   (user_info['name'], email, 'OAUTH_ACCOUNT'))
        db.commit()
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

    jwt_token = generate_jwt(user['user_id'], user['role_id'], user['username'])
    session['user_id'] = user['user_id']
    session['role_id'] = user['role_id']
    session['user_name'] = user['username']
    session['jwt_token'] = jwt_token
    db.close()
    return redirect(url_for('dashboard'))

# ======================================================
# Routes: 2FA Setup
# ======================================================
@app.route('/setup-2fa')
@login_required
def setup_2fa():
    """صفحة إعداد المصادقة الثنائية"""
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE user_id = ?', (session['user_id'],)).fetchone()
    db.close()

    # إذا كان 2FA مفعّل بالفعل، نعرض صفحة الإلغاء بدل إعادة التوجيه
    if user['two_factor_secret']:
        return render_template('setup_2fa.html', already_enabled=True, qr_code=None, secret=None)

    # توليد سر جديد
    secret = pyotp.random_base32()
    session['temp_2fa_secret'] = secret

    # إنشاء رابط الـ OTP
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=session['user_name'],
        issuer_name='SecureVault'
    )

    # توليد QR Code كـ Base64 لعرضه مباشرة في HTML
    qr = qrcode.make(totp_uri)
    buffer = io.BytesIO()
    qr.save(buffer, format='PNG')
    qr_b64 = base64.b64encode(buffer.getvalue()).decode()

    return render_template('setup_2fa.html', already_enabled=False, qr_code=qr_b64, secret=secret)

@app.route('/confirm-2fa', methods=['POST'])
@login_required
def confirm_2fa():
    """تأكيد إعداد 2FA بواسطة إدخال الكود"""
    code = request.form.get('code', '').strip()
    secret = session.get('temp_2fa_secret')

    if not secret:
        flash("❌ حدث خطأ، يرجى البدء من جديد")
        return redirect(url_for('setup_2fa'))

    totp = pyotp.TOTP(secret)
    if totp.verify(code):
        db = get_db()
        db.execute('UPDATE users SET two_factor_secret = ? WHERE user_id = ?',
                   (secret, session['user_id']))
        db.commit()
        db.close()
        session.pop('temp_2fa_secret', None)
        flash("🔐 تم تفعيل المصادقة الثنائية بنجاح!")
        return redirect(url_for('dashboard'))
    else:
        flash("❌ الكود غير صحيح، يرجى المحاولة مجدداً")
        return redirect(url_for('setup_2fa'))

@app.route('/disable-2fa', methods=['POST'])
@login_required
def disable_2fa():
    """إلغاء تفعيل 2FA"""
    db = get_db()
    db.execute('UPDATE users SET two_factor_secret = NULL WHERE user_id = ?', (session['user_id'],))
    db.commit()
    db.close()
    flash("⚠️ تم إلغاء تفعيل المصادقة الثنائية")
    return redirect(url_for('dashboard'))

@app.route('/verify-2fa', methods=['GET', 'POST'])
def verify_2fa():
    """التحقق من كود 2FA أثناء تسجيل الدخول"""
    if 'pending_user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE user_id = ?', (session['pending_user_id'],)).fetchone()
        db.close()

        if user and user['two_factor_secret']:
            totp = pyotp.TOTP(user['two_factor_secret'])
            if totp.verify(code):
                token = generate_jwt(user['user_id'], user['role_id'], user['username'])
                session['user_id'] = session.pop('pending_user_id')
                session['role_id'] = session.pop('pending_role_id')
                session['user_name'] = session.pop('pending_username')
                session['jwt_token'] = token
                return redirect(url_for('dashboard'))

        flash("❌ كود التحقق غير صحيح")
    return render_template('verify_2fa.html')

# ======================================================
# Routes: Documents
# ======================================================
@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    if session['role_id'] == 1:
        docs = db.execute('SELECT d.*, u.username FROM documents d JOIN users u ON d.owner_id = u.user_id ORDER BY d.upload_date DESC').fetchall()
    else:
        docs = db.execute('SELECT * FROM documents WHERE owner_id = ? ORDER BY upload_date DESC', (session['user_id'],)).fetchall()
    
    # إحصائيات
    total_docs = len(docs)
    db.close()
    return render_template('dashboard.html', docs=docs, total_docs=total_docs)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename != '':
            data = file.read()
            f_hash = get_file_hash(data)
            signature = sign_data(data)
            encrypted_data = encrypt_file(data)
            file_size = len(data)

            path = os.path.join(UPLOAD_FOLDER, file.filename)
            with open(path, 'wb') as f:
                f.write(encrypted_data)

            db = get_db()
            db.execute(
                'INSERT INTO documents (owner_id, file_name, encrypted_file_path, file_hash, digital_signature, file_size) VALUES (?,?,?,?,?,?)',
                (session['user_id'], file.filename, path, f_hash, signature, file_size)
            )
            db.commit()
            db.close()
            flash("✅ تم تشفير المستند ورفعه بنجاح")
            return redirect(url_for('dashboard'))
        else:
            flash("⚠️ يرجى اختيار ملف صحيح")
    return render_template('upload.html')

@app.route('/verify')
@login_required
def verify():
    db = get_db()
    if session['role_id'] == 1:
        docs = db.execute('SELECT d.*, u.username FROM documents d JOIN users u ON d.owner_id = u.user_id').fetchall()
    else:
        docs = db.execute('SELECT * FROM documents WHERE owner_id = ?', (session['user_id'],)).fetchall()
    db.close()
    return render_template('verify.html', docs=docs)

@app.route('/download/<int:doc_id>')
@login_required
def download(doc_id):
    db = get_db()
    doc = db.execute('SELECT * FROM documents WHERE doc_id = ?', (doc_id,)).fetchone()
    db.close()

    if not doc:
        abort(404)
    if session['role_id'] != 1 and doc['owner_id'] != session['user_id']:
        abort(403)

    try:
        with open(doc['encrypted_file_path'], 'rb') as f:
            decrypted_data = decrypt_file(f.read())
        if get_file_hash(decrypted_data) != doc['file_hash']:
            return "⚠️ تنبيه أمني: تم اكتشاف تلاعب في سلامة الملف!", 403
        return send_file(io.BytesIO(decrypted_data), download_name=doc['file_name'], as_attachment=True)
    except Exception as e:
        flash("❌ حدث خطأ أثناء معالجة الملف")
        return redirect(url_for('dashboard'))

@app.route('/delete/<int:doc_id>', methods=['POST'])
@login_required
def delete_document(doc_id):
    """حذف مستند مع التحقق من الصلاحية"""
    db = get_db()
    doc = db.execute('SELECT * FROM documents WHERE doc_id = ?', (doc_id,)).fetchone()

    if not doc:
        db.close()
        abort(404)

    # فقط المالك أو Admin يمكنه الحذف
    if session['role_id'] != 1 and doc['owner_id'] != session['user_id']:
        db.close()
        abort(403)

    # حذف الملف الفعلي من القرص
    try:
        if os.path.exists(doc['encrypted_file_path']):
            os.remove(doc['encrypted_file_path'])
    except Exception:
        pass  # استمر حتى لو فشل حذف الملف

    # حذف السجل من قاعدة البيانات
    db.execute('DELETE FROM documents WHERE doc_id = ?', (doc_id,))
    db.commit()
    db.close()

    flash(f"🗑️ تم حذف المستند '{doc['file_name']}' بنجاح")
    return redirect(url_for('dashboard'))

@app.route('/metadata/<int:doc_id>')
@login_required
def document_metadata(doc_id):
    """عرض metadata تفصيلية للمستند"""
    db = get_db()
    if session['role_id'] == 1:
        doc = db.execute(
            'SELECT d.*, u.username FROM documents d JOIN users u ON d.owner_id = u.user_id WHERE d.doc_id = ?',
            (doc_id,)
        ).fetchone()
    else:
        doc = db.execute(
            'SELECT * FROM documents WHERE doc_id = ? AND owner_id = ?',
            (doc_id, session['user_id'])
        ).fetchone()
    db.close()

    if not doc:
        abort(404)

    return render_template('metadata.html', doc=doc)

# ======================================================
# API Route: JWT Verification Endpoint (للتوثيق)
# ======================================================
@app.route('/api/verify-token', methods=['GET'])
def api_verify_token():
    """endpoint يُظهر كيف يعمل JWT - للعرض التوضيحي"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({'valid': False, 'error': 'No token provided'}), 401

    token = auth_header.split(' ')[1]
    payload = decode_jwt(token)
    if payload:
        return jsonify({'valid': True, 'payload': payload}), 200
    return jsonify({'valid': False, 'error': 'Token expired or invalid'}), 401

# ======================================================
# Routes: Admin
# ======================================================
@app.route('/admin')
@login_required
@admin_only
def admin_panel():
    db = get_db()
    users = db.execute('SELECT u.*, r.role_name FROM users u JOIN roles r ON u.role_id = r.role_id').fetchall()
    db.close()
    return render_template('admin.html', users=users)


@app.route('/admin/change-role', methods=['POST'])
@login_required
@admin_only
def change_role():
    """Admin: تغيير دور مستخدم"""
    user_id = request.form.get('user_id')
    role_id  = request.form.get('role_id')
    if user_id and role_id:
        db = get_db()
        db.execute('UPDATE users SET role_id = ? WHERE user_id = ?', (role_id, user_id))
        db.commit()
        db.close()
        flash("تم تحديث صلاحية المستخدم بنجاح")
    return redirect(url_for('admin_panel'))


@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@login_required
@admin_only
def delete_user(user_id):
    """Admin: حذف مستخدم — لا يمكن حذف نفسك"""
    if user_id == session['user_id']:
        flash("❌ لا يمكنك حذف حسابك الخاص")
        return redirect(url_for('admin_panel'))

    db = get_db()
    user = db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
    if not user:
        db.close()
        abort(404)

    # حذف مستندات المستخدم من القرص
    docs = db.execute('SELECT * FROM documents WHERE owner_id = ?', (user_id,)).fetchall()
    for doc in docs:
        try:
            if os.path.exists(doc['encrypted_file_path']):
                os.remove(doc['encrypted_file_path'])
        except Exception:
            pass

    # حذف مستنداته من DB
    db.execute('DELETE FROM documents WHERE owner_id = ?', (user_id,))
    # حذف المستخدم
    db.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
    db.commit()
    db.close()

    flash(f"🗑️ تم حذف المستخدم '{user['username']}' وجميع مستنداته")
    return redirect(url_for('admin_panel'))

@app.route('/logout')
def logout():
    session.clear()
    flash("👋 تم تسجيل الخروج بنجاح")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, ssl_context='adhoc')

# ======================================================
# Route: Admin Change Role (appended)
# ======================================================
