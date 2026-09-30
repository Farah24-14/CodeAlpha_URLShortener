from flask import Flask, request, jsonify, redirect, render_template
import sqlite3
import string
import secrets
from urllib.parse import urlparse

app = Flask(__name__)

DATABASE = "urls.db"


def get_connection():
    connection = sqlite3.connect(DATABASE)
    return connection


def init_db():
    connection = get_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_url TEXT NOT NULL,
            short_code TEXT UNIQUE NOT NULL
        )
    """)

    connection.commit()
    connection.close()


def generate_short_code(length=6):
    characters = string.ascii_letters + string.digits
    return "".join(secrets.choice(characters) for _ in range(length))


def is_valid_url(url):
    try:
        parsed_url = urlparse(url)

        return parsed_url.scheme in ("http", "https") and bool(parsed_url.netloc)

    except Exception:
        return False


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/shorten", methods=["POST"])
def shorten_url():

    data = request.get_json()

    if not data or "url" not in data:
        return jsonify({"error": "URL is required"}), 400

    original_url = data["url"].strip()

    if not is_valid_url(original_url):
        return jsonify({
            "error": "Please enter a valid URL starting with http:// or https://"
        }), 400

    connection = get_connection()

   
    while True:

        short_code = generate_short_code()

        existing = connection.execute(
            "SELECT id FROM urls WHERE short_code = ?",
            (short_code,)
        ).fetchone()

        if existing is None:
            break

    connection.execute(
        "INSERT INTO urls (original_url, short_code) VALUES (?, ?)",
        (original_url, short_code)
    )

    connection.commit()
    connection.close()

    return jsonify({
        "original_url": original_url,
        "short_code": short_code,
        "short_url": request.host_url + short_code
    })


@app.route("/<short_code>")
def redirect_url(short_code):

    connection = get_connection()

    result = connection.execute(
        "SELECT original_url FROM urls WHERE short_code = ?",
        (short_code,)
    ).fetchone()

    connection.close()

    if result is None:
        return "Short URL not found", 404

    return redirect(result[0])


if __name__ == "__main__":
    init_db()
    app.run(debug=True)