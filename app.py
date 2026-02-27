from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = "cms_secret_key"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER



def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def home():
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('index.html', posts=posts)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == "admin" and password == "admin123":
            session['admin'] = True
            return redirect('/dashboard')
        else:
            error = "Invalid username or password. Please try again."

    return render_template('login.html', error=error)


@app.route('/dashboard')
def dashboard():
    if 'admin' not in session:
        return redirect('/login')

    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts ORDER BY id DESC').fetchall()
    conn.close()

    return render_template('dashboard.html', posts=posts)


@app.route('/add', methods=['GET', 'POST'])
def add_post():
    if 'admin' not in session:
        return redirect('/login')

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        image = request.files.get('image')

        image_name = ""

        if image and image.filename != "":
            image_name = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_name)
            image.save(image_path)

        conn = get_db_connection()
        conn.execute(
            'INSERT INTO posts (title, content, image) VALUES (?, ?, ?)',
            (title, content, image_name)
        )
        conn.commit()
        conn.close()

        return redirect('/dashboard')

    return render_template('add_post.html')


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_post(id):
    if 'admin' not in session:
        return redirect('/login')

    conn = get_db_connection()

    post = conn.execute(
        'SELECT * FROM posts WHERE id = ?', (id,)
    ).fetchone()

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        conn.execute(
            'UPDATE posts SET title = ?, content = ? WHERE id = ?',
            (title, content, id)
        )
        conn.commit()
        conn.close()

        return redirect('/dashboard')

    conn.close()
    return render_template('edit_post.html', post=post)

@app.route('/delete/<int:id>')
def delete_post(id):
    if 'admin' not in session:
        return redirect('/login')

    conn = get_db_connection()
    conn.execute('DELETE FROM posts WHERE id = ?', (id,))
    conn.commit()
    conn.close()

    return redirect('/dashboard')

@app.route('/post/<int:id>')
def post(id):
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (id,)).fetchone()
    conn.close()
    return render_template('post.html', post=post)


@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect('/login')


if __name__ == "__main__":
    app.run(debug=True)

