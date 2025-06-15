from flask import Flask, render_template, request, session, redirect, url_for, send_file, Response, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import csv
from io import StringIO
from persona_agent import PersonaAgent, brightdata_wiki_tool
from dotenv import load_dotenv
import time
import requests
import openai
from multi_agent_system import create_multi_agent_system

try:
    import google.generativeai as genai
    GOOGLE_GENAI_AVAILABLE = True
except ModuleNotFoundError:
    GOOGLE_GENAI_AVAILABLE = False

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-key")

DB_PATH = 'users.db'

# --- User Auth and DB Setup ---
def init_user_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            role TEXT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')
init_user_db()

def get_user_id() -> int | None:
    return session.get('user_id')

def save_message(role: str, message: str) -> None:
    user_id = get_user_id()
    if user_id:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                'INSERT INTO chat_history (user_id, role, message) VALUES (?, ?, ?)',
                (user_id, role, message)
            )

def load_history() -> list[tuple[str, str]]:
    user_id = get_user_id()
    if user_id:
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.execute(
                'SELECT role, message FROM chat_history WHERE user_id=? ORDER BY timestamp ASC',
                (user_id,)
            )
            return cur.fetchall()
    return []

def get_agent() -> PersonaAgent:
    if not hasattr(g, 'agent'):
        user_id = session.get("user_id", "demo_user")
        if not hasattr(g, 'user_agents'):
            g.user_agents = {}
        if user_id not in g.user_agents:
            g.user_agents[user_id] = PersonaAgent(user_id)
        g.agent = g.user_agents[user_id]
    return g.agent

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = generate_password_hash(password)
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute(
                    'INSERT INTO users (username, password_hash) VALUES (?, ?)',
                    (username, password_hash)
                )
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists.', 'danger')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.execute(
                'SELECT id, password_hash FROM users WHERE username=?',
                (username,)
            )
            user = cur.fetchone()
        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            session['username'] = username
            return redirect(url_for('chat'))
        else:
            flash('Invalid credentials.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

MODEL_NAME_PRO = "models/gemini-pro"
MODEL_NAME_FLASH = "models/gemini-1.5-flash"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def ask_openai(prompt: str, model: str = "gpt-3.5-turbo") -> str:
    openai.api_key = OPENAI_API_KEY
    try:
        response = openai.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error with OpenAI API: {e}"

@app.route("/", methods=["GET", "POST"])
def chat():
    if not get_user_id():
        return redirect(url_for('login'))
    agent = get_agent()
    chat_history = load_history()
    if request.method == "POST":
        user_input = request.form["message"]
        response = ask_openai(user_input)
        save_message('user', user_input)
        save_message('agent', response)
        return redirect(url_for("chat"))
    return render_template("chat.html", chat_history=chat_history)

@app.route("/reset")
def reset():
    user_id = get_user_id()
    if user_id:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('DELETE FROM chat_history WHERE user_id=?', (user_id,))
    return redirect(url_for("chat"))

@app.route("/export_chat")
def export_chat():
    user_id = get_user_id()
    if not user_id:
        return redirect(url_for('login'))
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            'SELECT role, message FROM chat_history WHERE user_id=? ORDER BY timestamp ASC',
            (user_id,)
        )
        chat_history = cur.fetchall()
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(["role", "message"])
    for role, msg in chat_history:
        writer.writerow([role, msg])
    si.seek(0)
    return send_file(
        StringIO(si.getvalue()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='chat_history.csv'
    )

def stream_agent_response(user_query: str):
    response = search_and_summarize(user_query)
    for token in response.split():
        yield token + ' '
        time.sleep(0.05)

@app.route("/stream_chat", methods=["POST"])
def stream_chat():
    user_input = request.form["message"]
    return Response(stream_agent_response(user_input), mimetype='text/plain')

@app.route('/profile')
def profile():
    if not get_user_id():
        return redirect(url_for('login'))
    user_id = get_user_id()
    username = session.get('username')
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            'SELECT id, username, ROWID, datetime((SELECT MIN(timestamp) FROM chat_history WHERE user_id=?), "localtime") FROM users WHERE id=?',
            (user_id, user_id)
        )
        user = cur.fetchone()
    registered = user[3] if user and user[3] else 'N/A'
    is_admin = (username == 'admin')
    return render_template('profile.html', username=username, user_id=user_id, registered=registered, is_admin=is_admin)

@app.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    if not get_user_id():
        return redirect(url_for('login'))
    user_id = get_user_id()
    username = session.get('username')
    if request.method == 'POST':
        new_username = request.form['username']
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute('UPDATE users SET username=? WHERE id=?', (new_username, user_id))
            session['username'] = new_username
            flash('Profile updated!', 'success')
        except sqlite3.IntegrityError:
            flash('Username already exists.', 'danger')
        return redirect(url_for('profile'))
    return render_template('edit_profile.html', username=username)

@app.route('/admin/users')
def admin_users():
    if session.get('username') != 'admin':
        return redirect(url_for('login'))
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute('SELECT id, username FROM users')
        users = cur.fetchall()
    return render_template('admin_users.html', users=users)

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id: int):
    if session.get('username') != 'admin':
        return redirect(url_for('login'))
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('DELETE FROM users WHERE id=?', (user_id,))
        conn.execute('DELETE FROM chat_history WHERE user_id=?', (user_id,))
    flash('User deleted.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/chats')
def admin_chats():
    if session.get('username') != 'admin':
        return redirect(url_for('login'))
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            'SELECT u.username, c.role, c.message, c.timestamp FROM chat_history c JOIN users u ON c.user_id = u.id ORDER BY c.timestamp DESC LIMIT 100'
        )
        chats = cur.fetchall()
    return render_template('admin_chats.html', chats=chats)

def search_brightdata(query: str) -> str:
    api_key = os.getenv("BRIGHTDATA_API_KEY")
    dataset_id = os.getenv("BRIGHTDATA_DATASET_ID")
    url = f"https://api.brightdata.com/dca/{dataset_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {"query": query}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        return f"Error with BrightData API: {e}"

def search_and_summarize(query: str) -> str:
    raw_web_data = search_brightdata(query)
    summary = ask_openai(f"Summarize this information: {raw_web_data}")
    return summary

@app.route("/multi_agent_chat", methods=["POST"])
def multi_agent_chat():
    user_input = request.form.get("message")
    if not user_input:
        return {"error": "No message provided."}, 400
    manager = create_multi_agent_system()
    user_message = json.dumps({"role": "user", "content": user_input})
    result = manager.receive(user_message)
    return result, 200, {'Content-Type': 'application/json'}

if __name__ == "__main__":
    app.run(debug=True)
