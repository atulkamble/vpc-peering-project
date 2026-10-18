import os
import pymysql
from flask import Flask, render_template, request, redirect
from dotenv import load_dotenv

load_dotenv("/var/www/html/.env")

app = Flask(__name__)

def get_db():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "webapp"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME", "university"),
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route("/")
def home():
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM students ORDER BY id DESC")
            students = cursor.fetchall()
        return render_template("index.html", students=students)
    finally:
        conn.close()

@app.route("/add", methods=["POST"])
def add_student():
    name = request.form["name"]
    email = request.form["email"]
    course = request.form["course"]

    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO students (name, email, course) VALUES (%s, %s, %s)",
                (name, email, course)
            )
        conn.commit()
    finally:
        conn.close()

    return redirect("/")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
