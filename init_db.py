import sqlite3

def initialize_database():
    connection = sqlite3.connect('vault_system.db')
    cursor = connection.cursor()

    sql_script = """
    CREATE TABLE IF NOT EXISTS roles (
        role_id INTEGER PRIMARY KEY AUTOINCREMENT,
        role_name TEXT NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role_id INTEGER NOT NULL,
        two_factor_secret TEXT,
        FOREIGN KEY (role_id) REFERENCES roles (role_id)
    );

    CREATE TABLE IF NOT EXISTS documents (
        doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id INTEGER NOT NULL,
        file_name TEXT NOT NULL,
        encrypted_file_path TEXT NOT NULL,
        file_hash TEXT NOT NULL,
        digital_signature BLOB NOT NULL,
        file_size INTEGER DEFAULT 0,
        upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (owner_id) REFERENCES users (user_id)
    );

    -- إضافة عمود file_size إذا لم يكن موجوداً (للقاعدة الموجودة)
    -- هذا السطر آمن ولن يسبب خطأ إذا كان العمود موجوداً بالفعل
    
    INSERT OR IGNORE INTO roles (role_name) VALUES ('Admin'), ('Manager'), ('User');
    """

    try:
        cursor.executescript(sql_script)
        # إضافة عمود file_size بشكل آمن للقاعدة الموجودة
        try:
            cursor.execute("ALTER TABLE documents ADD COLUMN file_size INTEGER DEFAULT 0")
            connection.commit()
            print("✅ Added file_size column to documents table")
        except Exception:
            pass  # العمود موجود بالفعل
        
        connection.commit()
        print("✅ Database and tables created/updated successfully!")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        connection.close()

if __name__ == "__main__":
    initialize_database()
