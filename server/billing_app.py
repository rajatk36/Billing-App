
from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
app = Flask(__name__)
CORS(app)  

def create_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="keep_coding",  
            database="billing_db"
        )
        if connection.is_connected():
            print(" Connected to MySQL database successfully.")
            return connection
    except Error as e:
        print(f" Error while connecting to MySQL: {e}")
    return None 


@app.route("/db", methods=["GET"])
def db_check():
    conn = create_connection()
    if conn:
        conn.close()
        return jsonify({"status": "success", "message": "Connected to MySQL database successfully."})
    else:
        return jsonify({"status": "error", "message": "Failed to connect to MySQL database."}), 500


@app.route("/get_bills", methods=["GET"])
def get_bills():
    conn = create_connection()
    if conn is None:
        return jsonify({
            "status": "error",
            "message": "Failed to connect to database. Please check your MySQL server, credentials, and database name.",
            "hint": "Ensure MySQL is running and connection details in billing_app.py are correct."
        }), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT b.id, c.name, c.contact, c.email, b.amount, b.date
            FROM bills b
            JOIN customers c ON b.customer_id = c.id
        """)
        bills = cursor.fetchall()
        return jsonify(bills)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route("/add_bill", methods=["POST"])
def add_bill():
    data = request.json
    name, contact, email, amount = data["name"], data["contact"], data["email"], data["amount"]

    conn = create_connection()
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO customers (name, contact, email) VALUES (%s, %s, %s)", (name, contact, email))
    customer_id = cursor.lastrowid

    cursor.execute("INSERT INTO bills (customer_id, amount) VALUES (%s, %s)", (customer_id, amount))
    
    conn.commit()
    conn.close()
    return jsonify({"message": "Bill added successfully"}), 201


@app.route("/update_bill/<int:bill_id>", methods=["PUT"])
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
        cursor = conn.cursor()
    
        cursor.execute("UPDATE bills SET amount = %s WHERE id = %s", (amount, bill_id))
        
        cursor.execute("SELECT customer_id FROM bills WHERE id = %s", (bill_id,))
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
                query = f"UPDATE customers SET {', '.join(update_fields)} WHERE id = %s"
                update_values.append(customer_id)
                cursor.execute(query, tuple(update_values))
        conn.commit()
        return jsonify({"message": "Bill updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route("/delete_bill/<int:bill_id>", methods=["DELETE"])
def delete_bill(bill_id):
    conn = create_connection()
    cursor = conn.cursor()

    try:
        # 1. Get customer_id from the bill
        cursor.execute("SELECT customer_id FROM bills WHERE id = %s", (bill_id,))
        result = cursor.fetchone()

        if not result:
            return jsonify({"message": "Bill not found"}), 404

        customer_id = result[0]

        # 2. Delete the bill
        cursor.execute("DELETE FROM bills WHERE id = %s", (bill_id,))

        # 3. Check if the customer has any more bills
        cursor.execute("SELECT COUNT(*) FROM bills WHERE customer_id = %s", (customer_id,))
        bill_count = cursor.fetchone()[0]

        # 4. If no more bills, delete the customer
        if bill_count == 0:
            cursor.execute("DELETE FROM customers WHERE id = %s", (customer_id,))

        conn.commit()
        return jsonify({"message": "Bill deleted successfully"}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        conn.close()

if __name__ == "__main__":
    app.run(debug=True)
