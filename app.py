from flask import Flask, render_template, request, redirect, url_for, session, flash
import boto3
import pymysql
import os
import json

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default-key-if-missing')

# Ambil kredensial dari AWS Secrets Manager
def get_db_connection():
    secret_name = "eduapp/rds/credentials"
    region_name = "ap-southeast-1"

    session_boto = boto3.session.Session()
    client = session_boto.client(service_name='secretsmanager', region_name=region_name)

    get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    secret = json.loads(get_secret_value_response['SecretString'])

    connection = pymysql.connect(
        host=secret['host'],
        user=secret['username'],
        password=secret['password'],
        database=secret['dbname'],
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection

# Inisialisasi tabel materials jika belum ada
def init_db():
    conn = get_db_connection()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS materials (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    course_id INT NOT NULL,
                    title VARCHAR(255),
                    material_url VARCHAR(500)
                )
            """)
            conn.commit()

            # Tambahkan data dummy jika kosong
            cursor.execute("SELECT COUNT(*) as total FROM materials")
            if cursor.fetchone()['total'] == 0:
                cursor.executemany("""
                    INSERT INTO materials (course_id, title, material_url)
                    VALUES (%s, %s, %s)
                """, [
                    (1, "Modul 1 - Cloud", "https://dataeduapp.s3.ap-southeast-1.amazonaws.com/CLOUD_Modul1.pdf"),
                    (1, "Modul 2 - Cloud", "https://dataeduapp.s3.ap-southeast-1.amazonaws.com/CLOUD_Modul2.pdf"),
                    (2, "Modul 1 - Bahasa Inggris", "https://dataeduapp.s3.ap-southeast-1.amazonaws.com/INGGRIS_Modul1.pdf"),
                    (2, "Modul 2 - Bahasa Inggris", "https://dataeduapp.s3.ap-southeast-1.amazonaws.com/INGGRIS_Modul2.pdf")
                ])
                conn.commit()

# Data kursus dummy
courses = [
    {
        "id": 1,
        "title": "Cloud",
        "description": "Belajar konsep cloud dasar",
        "duration": "4 minggu",
        "enroll_key": "cloud123"
    },
    {
        "id": 2,
        "title": "Bahasa Inggris III",
        "description": "Kursus bahasa Inggris",
        "duration": "6 minggu",
        "enroll_key": "english456"
    }
]

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/courses')
def show_courses():
    return render_template('courses.html', courses=courses)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/enroll/<int:course_id>', methods=['GET', 'POST'])
def enroll(course_id):
    course = next((c for c in courses if c['id'] == course_id), None)
    if not course:
        flash('Kursus tidak ditemukan', 'error')
        return redirect(url_for('show_courses'))

    if request.method == 'POST':
        if request.form.get('enroll_key') == course['enroll_key']:
            enrolled = session.get('enrolled_courses', [])
            if course_id not in enrolled:
                enrolled.append(course_id)
                session['enrolled_courses'] = enrolled
            flash('Enroll berhasil!', 'success')
            return redirect(url_for('course_materials', course_id=course_id))
        else:
            flash('Enroll key salah!', 'error')

    return render_template('enroll.html', course=course)

# Ambil materi dari DB
def get_materials_from_db(course_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT id, title, material_url FROM materials WHERE course_id = %s"
            cursor.execute(sql, (course_id,))
            result = cursor.fetchall()
        return result
    finally:
        conn.close()

@app.route('/course/<int:course_id>/materials')
def course_materials(course_id):
    if course_id not in session.get('enrolled_courses', []):
        flash('Anda harus enroll terlebih dahulu', 'error')
        return redirect(url_for('enroll', course_id=course_id))

    course = next((c for c in courses if c['id'] == course_id), None)
    if not course:
        flash('Kursus tidak ditemukan', 'error')
        return redirect(url_for('show_courses'))

    materials = get_materials_from_db(course_id)
    return render_template('materials.html', course=course, materials=materials)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
