from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
import os

app = Flask(__name__)
app.secret_key = 'ini_adalah_secret_key_rahasia'  # Wajib diisi!

# Buat folder materials jika belum ada
if not os.path.exists('static/materials'):
    os.makedirs('static/materials')

# Data kursus
courses = [
    {
        "id": 1, 
        "title": "Cloud", 
        "description": "Belajar konsep cloud dasar", 
        "duration": "4 minggu",
        "enroll_key": "cloud123",
        "materials": [
            {"id": 1, "title": "Bab 1 - Introduction to AWS", "file": "Modul 1 AWS.pdf"},
            {"id": 2, "title": "Bab 2 - Introduction to Database", "file": "Modul 2 Database.pdf"}
        ]
    },
    {
        "id": 2, 
        "title": "Bahasa Inggris III", 
        "description": "Kursus bahasa Inggris", 
        "duration": "6 minggu",
        "enroll_key": "english456",
        "materials": [
            {"id": 1, "title": "Modul 1 - Present Perfect Tense", "file": "PRESENT PERFECT TENSE.pdf"},
            {"id": 2, "title": "Modul 2 - Passive Voice", "file": "KALIMAT PASIF.pdf"}
        ]
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


@app.route('/view/<int:course_id>/<filename>')
def view_material(course_id, filename):
    if course_id not in session.get('enrolled_courses', []):
        flash('Anda harus enroll terlebih dahulu', 'error')
        return redirect(url_for('enroll', course_id=course_id))
    
    # Mengirim file sebagai attachment=False untuk preview di browser
    return send_from_directory(
        'static/materials', 
        filename, 
        as_attachment=False  # Ini yang membuat file dibuka di browser
    )

@app.route('/enroll/<int:course_id>', methods=['GET', 'POST'])
def enroll(course_id):
    course = next((c for c in courses if c['id'] == course_id), None)
    if not course:
        flash('Kursus tidak ditemukan', 'error')
        return redirect(url_for('show_courses'))
    
    if request.method == 'POST':
        if request.form.get('enroll_key') == course['enroll_key']:
            session.setdefault('enrolled_courses', []).append(course_id)
            flash('Enroll berhasil!', 'success')
            return redirect(url_for('course_materials', course_id=course_id))
        else:
            flash('Enroll key salah!', 'error')
    
    return render_template('enroll.html', course=course)

@app.route('/course/<int:course_id>/materials')
def course_materials(course_id):
    if course_id not in session.get('enrolled_courses', []):
        flash('Anda harus enroll terlebih dahulu', 'error')
        return redirect(url_for('enroll', course_id=course_id))
    
    course = next((c for c in courses if c['id'] == course_id), None)
    if not course:
        flash('Kursus tidak ditemukan', 'error')
        return redirect(url_for('show_courses'))
    
    return render_template('materials.html', course=course)

@app.route('/download/<int:course_id>/<filename>')
def download_material(course_id, filename):
    if course_id not in session.get('enrolled_courses', []):
        flash('Anda harus enroll terlebih dahulu', 'error')
        return redirect(url_for('enroll', course_id=course_id))
    
    try:
        return send_from_directory(
            'static/materials', 
            filename, 
            as_attachment=True
        )
    except FileNotFoundError:
        flash('File materi tidak ditemukan', 'error')
        return redirect(url_for('course_materials', course_id=course_id))

if __name__ == '__main__':
    app.run(debug=True, port=5000)