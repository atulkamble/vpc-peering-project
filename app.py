import os
import pymysql
from flask import Flask, render_template, request, redirect, url_for, abort

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024

def get_db():
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.getenv("DB_NAME", "university"),
        connect_timeout=5,
        read_timeout=10,
        write_timeout=10,
        cursorclass=pymysql.cursors.DictCursor
    )

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def home():
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name, email, course FROM students ORDER BY id DESC LIMIT 100")
            students = cursor.fetchall()
        return render_template("index.html", students=students)
    finally:
        conn.close()

@app.post("/add")
def add_student():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    course = request.form.get("course", "").strip()
    if not name or not email or not course or max(map(len, (name, email, course))) > 255:
        abort(400)
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO students (name, email, course) VALUES (%s, %s, %s)", (name, email, course))
        conn.commit()
    finally:
        conn.close()
    return redirect(url_for("home"), code=303)
