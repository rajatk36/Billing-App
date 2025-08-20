
from flask import Flask, jsonify, request, session, g
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import hashlib
import secrets
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from functools import wraps
from pathlib import Path
import json

# Firebase Admin
import firebase_admin
from firebase_admin import auth as fb_auth, credentials as fb_credentials

# Load .env from the server directory explicitly
ENV_PATH = Path(__file__).with_name('.env')
load_dotenv(dotenv_path=str(ENV_PATH))

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
CORS(app, supports_credentials=True)

# Session configuration (not used for auth anymore but kept for compatibility)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True

# Initialize Firebase Admin (robust init with explicit projectId)
try:
    if not firebase_admin._apps:
        cred = None
        cred_path = os.environ.get('FIREBASE_APPLICATION_CREDENTIALS')
        cred_inline = os.environ.get('FIREBASE_CREDENTIALS_JSON')
        project_id = os.environ.get('FIREBASE_PROJECT_ID') or os.environ.get('GOOGLE_CLOUD_PROJECT')
        options = {'projectId': project_id} if project_id else None
        
        print(f"[Firebase Admin] Using project_id={project_id}")
       
        print(f"[Firebase Admin] Using FIREBASE_APPLICATION_CREDENTIALS={cred_path}")
        print(f"[Firebase Admin] Inline JSON present={bool(cred_inline)}")
        if cred_inline:
            try:
                cred_data = json.loads(cred_inline)
                cred = fb_credentials.Certificate(cred_data)
                firebase_admin.initialize_app(cred, options)
                print("✅ Firebase Admin initialized with inline JSON credentials")
            except Exception as e:
                print(f"⚠️ Inline JSON credentials failed: {e}")
                raise
        elif cred_path and os.path.exists(cred_path):
            cred = fb_credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, options)
            print("✅ Firebase Admin initialized with service account certificate")
        else:
            try:
                cred = fb_credentials.ApplicationDefault()
                firebase_admin.initialize_app(cred, options)
                print("✅ Firebase Admin initialized with Application Default Credentials")
            except Exception:
                # Last resort: initialize without explicit credentials (may work on GCP)
                firebase_admin.initialize_app(options)
                print("✅ Firebase Admin initialized with options only (no explicit credentials)")
except Exception as e:
    print(f"⚠️ Firebase Admin initialization failed: {e}")


# --- Connection pooling helpers ---
POOL_CREATED = False
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "1"))  # default to 1 to respect low connection caps
print(f"[DB] Using pool_size={DB_POOL_SIZE}")

def create_connection():
    global POOL_CREATED
    try:
        connect_args = dict(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            port=os.getenv("DB_PORT"),
            pool_name="app_pool",
        )
        if not POOL_CREATED:
            connect_args["pool_size"] = DB_POOL_SIZE
            connect_args["pool_reset_session"] = True
        conn = mysql.connector.connect(**connect_args)
        POOL_CREATED = True
        if conn.is_connected():
            return conn
    except Error as e:
        # Retry once without pool size in case pool already exists
        try:
            conn = mysql.connector.connect(
                host=os.getenv("DB_HOST"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                database=os.getenv("DB_NAME"),
                port=os.getenv("DB_PORT"),
                pool_name="app_pool",
            )
            if conn.is_connected():
                return conn
        except Exception:
            pass
        print(f" Error while connecting to MySQL: {e}")
    return None


def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def ensure_users_table_has_firebase_uid():
    """Add firebase_uid column to users table if missing"""
    conn = create_connection()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'users' AND COLUMN_NAME = 'firebase_uid'
        """, (os.getenv("DB_NAME"),))
        exists = cursor.fetchone()[0] > 0
        if not exists:
            cursor.execute("ALTER TABLE users ADD COLUMN firebase_uid VARCHAR(128) UNIQUE")
            conn.commit()
            print("✅ Added firebase_uid column to users table")
    except Exception as e:
        print(f"⚠️ Could not ensure firebase_uid column: {e}")
    finally:
        conn.close()


def create_users_table():
    """Create users table if it doesn't exist"""
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            print("Users table created/verified successfully")
        except Exception as e:
            print(f"Error creating users table: {e}")
        finally:
            conn.close()
    # Ensure firebase_uid column exists
    ensure_users_table_has_firebase_uid()


def create_user_tables(user_id, conn=None):
    """Create user-specific customer and bill tables using provided conn if given."""
    print(f"Creating tables for user {user_id}...")
    own_conn = False
    if conn is None:
        conn = create_connection()
        own_conn = True
    if conn:
        try:
            cursor = conn.cursor()

            customers_table = f"customers_{user_id}"
            bills_table = f"bills_{user_id}"

            print(f"Creating table: {customers_table}")
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {customers_table} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    contact VARCHAR(255),
                    email VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            print(f"Creating table: {bills_table}")
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {bills_table} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    customer_id INT NOT NULL,
                    amount DECIMAL(10,2) NOT NULL,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES {customers_table}(id) ON DELETE CASCADE
                )
            """)

            if own_conn:
                conn.commit()
            print(f"✅ User tables created/verified for user {user_id}")
        except Exception as e:
            if own_conn and conn:
                conn.rollback()
            print(f"❌ Error creating user tables: {e}")
            raise e
        finally:
            if own_conn and conn:
                conn.close()
    else:
        print(f"❌ Failed to connect to database for user {user_id}")
        raise Exception("Database connection failed")


# --- Users/table helpers (accept shared conn) ---

def get_or_create_sql_user(firebase_uid: str, email: str, conn=None) -> int:
    """Return SQL users.id for given firebase_uid, creating row if needed, using shared conn when provided."""
    own_conn = False
    if conn is None:
        conn = create_connection()
        own_conn = True
    if not conn:
        raise Exception("Database connection failed")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE firebase_uid = %s", (firebase_uid,))
        row = cursor.fetchone()
        if row:
            return row[0]
        placeholder = hash_password("firebase")
        cursor.execute(
            "INSERT INTO users (email, password_hash, firebase_uid) VALUES (%s, %s, %s)",
            (email, placeholder, firebase_uid),
        )
        if own_conn:
            conn.commit()
        user_id = cursor.lastrowid
        print(f"✅ Created SQL user {user_id} for Firebase uid {firebase_uid}")
        return user_id
    finally:
        if own_conn and conn:
            conn.close()


# Cache of provisioned user_ids to avoid repeated ensure work
PROVISIONED_USERS = set()


def provision_user_with_conn(conn, firebase_uid: str, email: str) -> int:
    """With an existing conn, map/create SQL user and ensure per-user tables; cache to avoid repeats."""
    cursor = conn.cursor()
    # Map/create user
    cursor.execute("SELECT id FROM users WHERE firebase_uid = %s", (firebase_uid,))
    row = cursor.fetchone()
    if row:
        user_id = row[0]
    else:
        placeholder = hash_password("firebase")
        cursor.execute(
            "INSERT INTO users (email, password_hash, firebase_uid) VALUES (%s, %s, %s)",
            (email, placeholder, firebase_uid),
        )
        user_id = cursor.lastrowid
        print(f"✅ Created SQL user {user_id} for Firebase uid {firebase_uid}")
    # Ensure tables only once per process lifetime
    if user_id not in PROVISIONED_USERS:
        cursor.execute(f"SHOW TABLES LIKE 'customers_{user_id}'")
        customers_exists = cursor.fetchone()
        cursor.execute(f"SHOW TABLES LIKE 'bills_{user_id}'")
        bills_exists = cursor.fetchone()
        if not customers_exists or not bills_exists:
            create_user_tables(user_id, conn=conn)
        PROVISIONED_USERS.add(user_id)
    return user_id


# --- Auth middleware uses ONE shared connection ---

def require_firebase_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing Authorization Bearer token"}), 401
        id_token = auth_header.split(' ', 1)[1].strip()
        # Only wrap token verification in try/except so route errors are not misreported as auth errors
        try:
            decoded = fb_auth.verify_id_token(id_token)
        except fb_auth.InvalidIdTokenError as e:
            return jsonify({"error": f"Invalid token: {str(e)}"}), 401
        except Exception as e:
            return jsonify({"error": f"Auth processing error: {str(e)}"}), 500

        firebase_uid = decoded.get('uid')
        email = decoded.get('email', '')
        if not firebase_uid:
            return jsonify({"error": "Invalid token"}), 401
        # Only attach firebase identity here; DB work happens inside endpoints with one connection
        g.firebase_uid = firebase_uid
        g.user_email = email
        return f(*args, **kwargs)
    return wrapper


# Create users table on startup (and ensure firebase_uid column)
create_users_table()


@app.route("/check-auth", methods=["GET"])
@require_firebase_auth
def check_auth():
    # Open one connection and provision user
    conn = create_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        user_id = provision_user_with_conn(conn, g.firebase_uid, g.user_email)
        conn.commit()
        return jsonify({
            "authenticated": True,
            "user": {"id": user_id, "email": g.user_email}
        }), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route("/db", methods=["GET"])
def db_check():
    conn = create_connection()
    if conn:
        conn.close()
        return jsonify({"status": "success", "message": "Connected to MySQL database successfully."})
    else:
        return jsonify({"status": "error", "message": "Failed to connect to MySQL database."}), 500


@app.route("/get_bills", methods=["GET"])
@require_firebase_auth
def get_bills():
    conn = create_connection()
    if conn is None:
        return jsonify({"status": "error", "message": "Failed to connect to database."}), 500
    try:
        user_id = provision_user_with_conn(conn, g.firebase_uid, g.user_email)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"""
            SELECT b.id, c.name, c.contact, c.email, b.amount, b.date
            FROM bills_{user_id} b
            JOIN customers_{user_id} c ON b.customer_id = c.id
        """)
        bills = cursor.fetchall()
        return jsonify(bills)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route("/add_bill", methods=["POST"])
@require_firebase_auth
def add_bill():
    data = request.json
    name, contact, email, amount = data["name"], data["contact"], data["email"], data["amount"]
    conn = create_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        user_id = provision_user_with_conn(conn, g.firebase_uid, g.user_email)
        cursor = conn.cursor()
        cursor.execute(f"INSERT INTO customers_{user_id} (name, contact, email) VALUES (%s, %s, %s)", (name, contact, email))
        customer_id = cursor.lastrowid
        cursor.execute(f"INSERT INTO bills_{user_id} (customer_id, amount) VALUES (%s, %s)", (customer_id, amount))
        conn.commit()
        return jsonify({"message": "Bill added successfully"}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route("/update_bill/<int:bill_id>", methods=["PUT"])
@require_firebase_auth
def update_bill(bill_id):
    data = request.json
    amount = data.get("amount")
    name = data.get("name")
    contact = data.get("contact")
    email = data.get("email")
    conn = create_connection()
    if conn is None:
        return jsonify({"error": "Failed to connect to database"}), 500
    try:
        user_id = provision_user_with_conn(conn, g.firebase_uid, g.user_email)
        cursor = conn.cursor()
        cursor.execute(f"UPDATE bills_{user_id} SET amount = %s WHERE id = %s", (amount, bill_id))
        cursor.execute(f"SELECT customer_id FROM bills_{user_id} WHERE id = %s", (bill_id,))
        result = cursor.fetchone()
        if result:
            customer_id = result[0]
            update_fields = []
            update_values = []
            if name:
                update_fields.append("name = %s")
                update_values.append(name)
            if contact:
                update_fields.append("contact = %s")
                update_values.append(contact)
            if email:
                update_fields.append("email = %s")
                update_values.append(email)
            if update_fields:
                query = f"UPDATE customers_{user_id} SET {', '.join(update_fields)} WHERE id = %s"
                update_values.append(customer_id)
                cursor.execute(query, tuple(update_values))
        conn.commit()
        return jsonify({"message": "Bill updated successfully"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route("/delete_bill/<int:bill_id>", methods=["DELETE"])
@require_firebase_auth
def delete_bill(bill_id):
    conn = create_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        user_id = provision_user_with_conn(conn, g.firebase_uid, g.user_email)
        cursor = conn.cursor()
        cursor.execute(f"SELECT customer_id FROM bills_{user_id} WHERE id = %s", (bill_id,))
        result = cursor.fetchone()
        if not result:
            return jsonify({"message": "Bill not found"}), 404
        customer_id = result[0]
        cursor.execute(f"DELETE FROM bills_{user_id} WHERE id = %s", (bill_id,))
        cursor.execute(f"SELECT COUNT(*) FROM bills_{user_id} WHERE customer_id = %s", (customer_id,))
        bill_count = cursor.fetchone()[0]
        if bill_count == 0:
            cursor.execute(f"DELETE FROM customers_{user_id} WHERE id = %s", (customer_id,))
        conn.commit()
        return jsonify({"message": "Bill deleted successfully"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route("/admin/view-all-data", methods=["GET"])
@require_firebase_auth
def view_all_users_data():
    """Admin endpoint to view all users' billing data. NOTE: Secure with admin checks in production."""
    conn = create_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, email FROM users ORDER BY id")
        users = cursor.fetchall()
        all_data = []
        for user in users:
            uid = user['id']
            user_email = user['email']
            cursor.execute(f"SHOW TABLES LIKE 'customers_{uid}'")
            customers_table_exists = cursor.fetchone()
            cursor.execute(f"SHOW TABLES LIKE 'bills_{uid}'")
            bills_table_exists = cursor.fetchone()
            if customers_table_exists and bills_table_exists:
                cursor.execute(f"""
                    SELECT 
                        {uid} as user_id,
                        '{user_email}' as user_email,
                        c.id AS customer_id,
                        c.name AS customer_name,
                        c.contact AS customer_contact,
                        c.email AS customer_email,
                        b.id AS bill_id,
                        b.amount,
                        b.date AS bill_date
                    FROM customers_{uid} c
                    LEFT JOIN bills_{uid} b ON c.id = b.customer_id
                    ORDER BY c.id, b.date DESC
                """)
                all_data.extend(cursor.fetchall())
        return jsonify({
            "total_users": len(users),
            "total_records": len(all_data),
            "data": all_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route("/user-stats", methods=["GET"])
@require_firebase_auth
def get_user_stats():
    conn = create_connection()
    if conn is None:
        return jsonify({"error": "Failed to connect to database"}), 500
    try:
        user_id = provision_user_with_conn(conn, g.firebase_uid, g.user_email)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"SELECT COUNT(*) as customer_count FROM customers_{user_id}")
        customer_count = cursor.fetchone()['customer_count']
        cursor.execute(f"SELECT COUNT(*) as bill_count FROM bills_{user_id}")
        bill_count = cursor.fetchone()['bill_count']
        cursor.execute(f"SELECT SUM(amount) as total_amount FROM bills_{user_id}")
        total_amount_result = cursor.fetchone()['total_amount']
        total_amount = float(total_amount_result) if total_amount_result else 0
        return jsonify({
            "customer_count": customer_count,
            "bill_count": bill_count,
            "total_amount": total_amount
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route("/delete-account", methods=["DELETE"])
@require_firebase_auth
def delete_account():
    """Delete user from Firebase + MySQL (user table, bills, customers)."""
    conn = create_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor()
        
        # Use g instead of request.user
        uid = g.firebase_uid
        email = g.user_email

        # 1️⃣ Delete user from Firebase
        fb_auth.delete_user(uid)

        # 2️⃣ Get user_id from MySQL users table (use firebase_uid for reliability)
        cursor.execute("SELECT id FROM users WHERE firebase_uid = %s", (uid,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"error": "User not found in MySQL"}), 404
        user_id = user[0]

        # 3️⃣ Drop user-specific tables
        cursor.execute(f"DROP TABLE IF EXISTS bills_{user_id}")
        cursor.execute(f"DROP TABLE IF EXISTS customers_{user_id}")
        

        # 4️⃣ Delete user from MySQL users table
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()

        return jsonify({"success": True, "message": "Account deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


if __name__ == "__main__":
    app.run(debug=True)
