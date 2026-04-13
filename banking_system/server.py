from flask import Flask, render_template, request, redirect, jsonify, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

rfid_last = ""

def db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template("login.html")

# ---------------- SIGNUP ----------------
@app.route('/signup')
def signup():
    return render_template("signup.html")

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    rfid = request.form['rfid']

    con = db()
    con.execute("INSERT INTO users(username,password,balance,rfid) VALUES(?,?,?,?)",
                (username, password, 1000, rfid))
    con.commit()
    con.close()

    return redirect('/')

# ---------------- LOGIN ----------------
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    con = db()
    user = con.execute("SELECT * FROM users WHERE username=? AND password=?",
                       (username, password)).fetchone()
    con.close()

    if user:
        session['username'] = username
        return render_template("dashboard.html",
                               username=user['username'],
                               balance=user['balance'])
    else:
        return "Login Failed"

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ---------------- DEPOSIT ----------------
@app.route('/deposit', methods=['POST'])
def deposit():
    data = request.json
    amount = int(data['amount'])
    username = session['username']

    con = db()
    user = con.execute("SELECT * FROM users WHERE username=?",
                       (username,)).fetchone()

    newbal = user['balance'] + amount

    con.execute("UPDATE users SET balance=? WHERE username=?",
                (newbal, username))
    con.commit()
    con.close()

    return jsonify({"balance": newbal})

# ---------------- WITHDRAW ----------------
@app.route('/withdraw', methods=['POST'])
def withdraw():
    global rfid_last

    data = request.json
    amount = int(data['amount'])
    username = session['username']

    con = db()
    user = con.execute("SELECT * FROM users WHERE username=?",
                       (username,)).fetchone()

    # 🚫 No scan yet
    if rfid_last == "":
        return jsonify({"status": "Scan Required"})

    # 🚫 Wrong RFID
    if user['rfid'].lower() != rfid_last.lower():
        rfid_last = ""
        return jsonify({"status": "RFID Failed"})

    # 🚫 Insufficient balance
    if user['balance'] < amount:
        rfid_last = ""
        return jsonify({"status": "Insufficient Balance"})

    # ✅ SUCCESS
    newbal = user['balance'] - amount

    con.execute("UPDATE users SET balance=? WHERE username=?",
                (newbal, username))
    con.commit()
    con.close()

    rfid_last = ""  # 🔥 RESET after use

    return jsonify({"status": "success", "balance": newbal})

# ---------------- RFID FROM ESP ----------------
@app.route('/rfid', methods=['POST'])
def rfid():
    global rfid_last
    rfid_last = request.json["uid"]
    print("RFID RECEIVED:", rfid_last)
    return jsonify({"status": "ok"})

# ---------------- GET RFID ----------------
@app.route('/get_rfid')
def get_rfid():
    global rfid_last
    return jsonify({"uid": rfid_last})

# ---------------- RESET RFID ----------------
@app.route('/reset_rfid')
def reset_rfid():
    global rfid_last
    rfid_last = ""
    return jsonify({"status": "cleared"})

# ---------------- RUN ----------------
app.run(host="0.0.0.0", port=5000, debug=True)