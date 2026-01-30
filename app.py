from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import requests
import os

app = Flask(__name__)

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
    os.path.join(basedir, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Define Book model


class Book(db.Model):
    __tablename__ = 'book'

    id = db.Column(db.Integer, primary_key=True)
    ol_key = db.Column(db.String(255), unique=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    year = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return f'<Book {self.title}>'


# Create tables when app starts
with app.app_context():
    db.create_all()


@app.route('/health')
def health():
    try:
        db.session.execute(text('SELECT 1'))
        return jsonify({"status": "ok", "db": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "error", "db": "error"}), 500


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/search')
def search():
    """Search for books from Open Library API."""
    query = request.args.get('q', '').strip()

    if not query:
        return redirect(url_for('index'))

    results = []
    error = False

    try:
        response = requests.get(
            'https://openlibrary.org/search.json',
            params={'q': query},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            docs = data.get('docs', [])

            for doc in docs[:20]:
                book_data = {
                    'key': doc.get('key', ''),
                    'title': doc.get('title', 'Unknown Title'),
                    'author': ', '.join(doc.get('author_name', ['Unknown Author'])),
                    'year': doc.get('first_publish_year', None)
                }
                results.append(book_data)
        else:
            error = True
    except Exception as e:
        error = True

    if error or not results:
        return render_template('search.html', results=[], error=True)

    return render_template('search.html', results=results, error=False)


@app.route('/add', methods=['POST'])
def add_book():
    ol_key = request.form.get('ol_key', '').strip()
    title = request.form.get('title', '').strip()
    author = request.form.get('author', '').strip()
    year = request.form.get('year', '')
    if not ol_key or not title or not author:
        return redirect(url_for('index'))
    try:
        year = int(year) if year else None
    except (ValueError, TypeError):
        year = None
    existing_book = Book.query.filter_by(ol_key=ol_key).first()
    if existing_book:
        return redirect(url_for('books'))
    new_book = Book(
        ol_key=ol_key,
        title=title,
        author=author,
        year=year
    )
    db.session.add(new_book)
    db.session.commit()
    return redirect(url_for('books'))


@app.route('/books')
def books():
    all_books = Book.query.all()
    return render_template('books.html', books=all_books)


@app.route('/books/delete/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        return jsonify({"status": "error"}), 404
    db.session.delete(book)
    db.session.commit()
    return jsonify({"status": "ok"}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
