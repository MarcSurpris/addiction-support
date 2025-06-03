from flask import Flask, render_template, request, redirect, url_for
import requests
from dotenv import load_dotenv
import os
from flask_sqlalchemy import SQLAlchemy
from models import db, Entry

load_dotenv()
XAI_API_KEY = os.getenv("XAI_API_KEY")
if not XAI_API_KEY:
    raise ValueError("XAI_API_KEY environment variable not set")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///entries.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()

def get_xai_response(user_input):
    messages = [
        {"role": "system", "content": (
            "You are a compassionate addiction support assistant. "
            "Respond in a calm, supportive, and empathetic tone. "
            "Avoid giving medical advice. Always suggest professional help if needed."
        )},
        {"role": "user", "content": user_input}
    ]
    headers = {
        "Authorization": f"Bearer {XAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "grok-3",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 150
    }
    try:
        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        response_data = response.json()
        return response_data["choices"][0]["message"]["content"].strip()
    except requests.exceptions.RequestException as e:
        print("xAI API Error:", e)
        if e.response is not None:
            print("Response body:", e.response.text)
        return "I'm sorry, I'm having trouble responding right now. If you're struggling, please reach out to a professional for support."

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        addiction_type = request.form.get("addiction_type")
        description = request.form.get("description")

        user_input = f"I am struggling with {addiction_type}. Here's what I'm going through: {description}"
        xai_response = get_xai_response(user_input)

        entry = Entry(
            addiction_type=addiction_type,
            description=description,
            response=xai_response
        )
        db.session.add(entry)
        db.session.commit()

        return redirect(url_for("index"))

    entries = Entry.query.order_by(Entry.created_at.desc()).all()
    return render_template("index.html", entries=entries)

if __name__ == "__main__":
    app.run(debug=True)

