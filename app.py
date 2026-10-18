from flask import render_template

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
