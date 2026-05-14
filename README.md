<div align="center">

<img src="https://img.shields.io/badge/SecureVault-v2.0-6374ff?style=for-the-badge&logo=shield&logoColor=white"/>

# 🔒 SecureVault
### Secure Document Vault System

**A full-stack secure web application for encrypted document management**  
*Final Year Project — Data Integrity and Authentication — 2026*

<br/>

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.1.0-000000?style=flat-square&logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=flat-square&logo=sqlite&logoColor=white)
![AES-256](https://img.shields.io/badge/Encryption-AES--256-22d98a?style=flat-square)
![JWT](https://img.shields.io/badge/Auth-JWT-6374ff?style=flat-square)
![OAuth](https://img.shields.io/badge/OAuth-Google-EA4335?style=flat-square&logo=google&logoColor=white)
![2FA](https://img.shields.io/badge/2FA-TOTP-ffb830?style=flat-square)
![HTTPS](https://img.shields.io/badge/Protocol-HTTPS-00e5c0?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

<br/>

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Security Features](#-security-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Environment Variables](#-environment-variables)
- [Pages & Routes](#-pages--routes)
- [RBAC Permissions](#-rbac-permissions)
- [MITM Demonstration](#-mitm-demonstration)
- [API Reference](#-api-reference)
- [Screenshots](#-screenshots)

---

## 🌐 Overview

**SecureVault** is a secure web-based document management platform that simulates a real-world enterprise security system. Users can securely upload, store, download, and verify digital documents with multiple layers of protection.

The system applies modern security concepts including:

- 🔐 **Confidentiality** → AES-256 file encryption
- 🔗 **Integrity** → SHA-256 hash verification
- ✍️ **Authenticity** → Digital signatures
- 🛡️ **Authentication** → JWT + OAuth + 2FA
- 👥 **Authorization** → Role-Based Access Control (RBAC)
- 🌐 **Secure Transport** → HTTPS/TLS

---

## 🛡️ Security Features

| Feature | Technology | Details |
|---------|-----------|---------|
| Password Hashing | `bcrypt` | Adaptive hashing with automatic salt |
| Password Policy | Regex + Live UI | 8+ chars, uppercase, lowercase, digit, special char |
| Session Auth | `PyJWT` HS256 | 2-hour expiring tokens |
| Google OAuth 2.0 | `Authlib` | Authorization Code flow |
| Two-Factor Auth | `pyotp` TOTP | RFC 6238, 30-second codes + QR Code |
| File Encryption | `AES-256-CFB` | Random IV per file via `cryptography` library |
| Integrity Check | `SHA-256` | Computed at upload, verified at download |
| Digital Signature | HMAC-SHA256 | Server-signed proof of origin |
| Access Control | RBAC | 3 roles: Admin, Manager, User |
| Secure Transport | HTTPS/TLS | Self-signed cert (production: Let's Encrypt) |

---

## 🧰 Tech Stack

```
Backend   →  Python 3 + Flask 3.1
Database  →  SQLite (via sqlite3)
Auth      →  bcrypt · PyJWT · pyotp · Authlib
Crypto    →  cryptography (AES-256-CFB) · hashlib (SHA-256)
Frontend  →  Custom dark theme HTML/CSS (no frameworks)
2FA       →  pyotp + qrcode[pil]
HTTPS     →  pyOpenSSL (ssl_context='adhoc')
```

---

## 📁 Project Structure

```
SecureVault/
│
├── app.py                  ← Flask app — all routes & logic
├── utils.py                ← encrypt_file, decrypt_file, get_file_hash, sign_data
├── init_db.py              ← Database schema & initialization
├── requirements.txt        ← Python dependencies
├── .env                    ← Environment variables (NOT committed)
├── .gitignore
│
├── uploads/                ← Encrypted files (auto-created)
├── vault_system.db         ← SQLite database (auto-created)
│
└── templates/
    ├── layout.html         ← Base dark theme template
    ├── login.html          ← Login + Google OAuth
    ├── register.html       ← Register + live password strength meter
    ├── dashboard.html      ← Files list + JWT viewer + stats
    ├── upload.html         ← Drag-and-drop upload
    ├── verify.html         ← SHA-256 integrity verification
    ├── metadata.html       ← File security details (hash, signature, CIA)
    ├── setup_2fa.html      ← QR code + TOTP enrollment
    ├── verify_2fa.html     ← 6-digit code entry with countdown timer
    ├── admin.html          ← User management + RBAC matrix
    └── 403.html            ← Access denied page
```

---

## ⚡ Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/tiger12895/SecureVault-Web.git
cd SecureVault-Web
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Linux / Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
pip install pyOpenSSL qrcode[pil] Pillow
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret_here
JWT_SECRET=your_strong_random_jwt_secret
SERVER_SECRET=your_strong_random_server_secret
```

> 💡 Generate strong secrets:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

### 5. Initialize the Database

```bash
python init_db.py
```

Expected output:
```
✅ Database and tables created/updated successfully!
```

### 6. Run the Application

```bash
python app.py
```

Expected output:
```
* Running on https://127.0.0.1:5000
* Debug mode: on
```

### 7. Open in Browser

```
https://127.0.0.1:5000
```

> ⚠️ The browser will show a security warning for the self-signed certificate.  
> Click **Advanced → Proceed to 127.0.0.1** to continue.

### 8. Create Your First Admin Account

Register a normal account, then run:

```bash
python -c "
import sqlite3
conn = sqlite3.connect('vault_system.db')
conn.execute(\"UPDATE users SET role_id=1 WHERE email='your@email.com'\")
conn.commit()
conn.close()
print('✅ Admin role assigned!')
"
```

---

## 🔑 Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID | `123456.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | Google OAuth Client Secret | `GOCSPX-xxxxxxxxxxxx` |
| `JWT_SECRET` | Secret key for signing JWT tokens | `a3f8c2d1e4b5...` (32+ chars) |
| `SERVER_SECRET` | Secret key for digital signatures | `b9d2e3f4a5c6...` (32+ chars) |

> 🔒 Never commit `.env` to GitHub — it's listed in `.gitignore`

### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → **APIs & Services** → **Credentials**
3. Create **OAuth 2.0 Client ID** → Web application
4. Add to **Authorized redirect URIs**:
   ```
   https://127.0.0.1:5000/authorize
   ```

---

## 🗺️ Pages & Routes

| Page | URL | Access | Description |
|------|-----|--------|-------------|
| Login | `GET /login` | Public | Email/password + Google OAuth |
| Register | `GET /register` | Public | Account creation with password strength meter |
| Dashboard | `GET /dashboard` | 🔐 Auth | File list, stats, JWT viewer |
| Upload | `GET /upload` | 🔐 Auth | Drag-and-drop + AES-256 encryption |
| Integrity Check | `GET /verify` | 🔐 Auth | SHA-256 hash verification |
| Document Metadata | `GET /metadata/<id>` | 🔐 Auth | Hash, signature, CIA triad details |
| Setup 2FA | `GET /setup-2fa` | 🔐 Auth | QR code enrollment for TOTP |
| Verify 2FA | `POST /verify-2fa` | Pending | 6-digit code during login |
| Admin Panel | `GET /admin` | 👑 Admin | User management + role assignment |
| Download | `GET /download/<id>` | 🔐 Auth | Decrypt + integrity check before download |
| Delete File | `POST /delete/<id>` | 🔐 Auth | Permanent file deletion |
| JWT API | `GET /api/verify-token` | Token | Demo endpoint for JWT validation |
| Delete User | `POST /admin/delete-user/<id>` | 👑 Admin | Remove user + all their documents |

---

## 👥 RBAC Permissions

| Permission | 👑 Admin | 🔷 Manager | 👤 User |
|-----------|---------|-----------|--------|
| Upload documents | ✅ | ✅ | ✅ |
| Download own documents | ✅ | ✅ | ✅ |
| Delete own documents | ✅ | ✅ | ✅ |
| Integrity verification | ✅ | ✅ | ✅ |
| View **all** documents | ✅ | ✅ | ❌ |
| Download others' files | ✅ | ✅ | ❌ |
| Access admin panel | ✅ | ❌ | ❌ |
| Manage users & roles | ✅ | ❌ | ❌ |
| Delete users | ✅ | ❌ | ❌ |

---

## 🕵️ MITM Demonstration

This project includes a Wireshark-based demonstration of why HTTPS is critical.

### HTTP — Credentials Exposed ⚠️

Running the app without SSL and capturing traffic with Wireshark on the loopback interface reveals login credentials in plain text:

```
POST /login HTTP/1.1
Content-Type: application/x-www-form-urlencoded

email=user%40gmail.com&password=MyPassword123
```

> Any attacker on the network can read credentials directly — no decryption needed.

### HTTPS — Encrypted ✅

With `ssl_context='adhoc'` enabled, the same request appears as unreadable TLS-encrypted data:

```
RSL / TLS Application Data
[Encrypted binary data — unreadable]
```

### Switch Between Modes

```python
# HTTPS (default — use this)
app.run(debug=True, ssl_context='adhoc')

# HTTP (only for Wireshark demo)
app.run(debug=True, host='0.0.0.0', port=5000)
```

---

## 📡 API Reference

### `GET /api/verify-token`

Verifies a JWT token. For demonstration purposes.

**Request:**
```http
GET /api/verify-token
Authorization: Bearer <your_jwt_token>
```

**Response (valid):**
```json
{
  "valid": true,
  "payload": {
    "user_id": 1,
    "role_id": 1,
    "username": "admin",
    "exp": 1748000000,
    "iat": 1747993600
  }
}
```

**Response (invalid/expired):**
```json
{
  "valid": false,
  "error": "Token expired or invalid"
}
```

---

## 🖼️ Screenshots

> Add screenshots of your running application here.

| Login Page | Dashboard | Admin Panel |
|-----------|-----------|-------------|
| ![login]() | ![dashboard]() | ![admin]() |

| 2FA Setup | Upload | Integrity Check |
|-----------|--------|-----------------|
| ![2fa]() | ![upload]() | ![verify]() |

---

## 🚨 Common Issues

| Error | Fix |
|-------|-----|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `ssl_context` error | Run `pip install pyOpenSSL` |
| `No module named 'qrcode'` | Run `pip install qrcode[pil] Pillow` |
| `vault_system.db not found` | Run `python init_db.py` |
| Browser HTTPS warning | Click **Advanced → Proceed** (self-signed cert) |
| Google OAuth error | Add `https://127.0.0.1:5000/authorize` to redirect URIs |

---

## 📦 Dependencies

```
Flask==3.1.0
bcrypt==4.2.1
PyJWT==2.10.1
pyotp==2.9.0
qrcode[pil]==8.0
cryptography==44.0.1
Authlib==1.3.0
python-dotenv==1.1.0
pyOpenSSL
Pillow
```

---

## 📄 License

This project is licensed under the MIT License.

---

<div align="center">

**🔒 SecureVault** — Built with security in mind

*Abdelrhman Ahmed Mohamed 👨🏼‍💻👨🫰🏼🐯*

</div>
