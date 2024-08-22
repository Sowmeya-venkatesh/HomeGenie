from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import re  # For regex-based parsing
from openai import OpenAI
import os
import fitz  # PyMuPDF

app = Flask(__name__)
CORS(app)

api_key = os.getenv('OPENAI_API_KEY')

# Path to your PDF file
PDF_PATH = './sc_data.pdf'

def get_db_connection():
    conn = sqlite3.connect('site.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    with conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS user (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL,
                            email TEXT NOT NULL,
                            phone_number TEXT NOT NULL
                        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS service_selection (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            service_type TEXT NOT NULL,
                            action TEXT NOT NULL,
                            FOREIGN KEY (user_id) REFERENCES user (id)
                        )''')
    conn.close()

init_db()

def extract_text_from_pdf(pdf_path):
    try:
        pdf_document = fitz.open(pdf_path)
        text = ""
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text += page.get_text()
        pdf_document.close()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

def parse_user_info(message):
    name = re.search(r"Name:\s*(\S+)", message)
    email = re.search(r"Email:\s*([\w\.-]+@[\w\.-]+)", message)
    phone_number = re.search(r"Phone:\s*(\d{10})", message)
    
    return {
        'name': name.group(1) if name else None,
        'email': email.group(1) if email else None,
        'phone_number': phone_number.group(1) if phone_number else None
    }

def save_user_info(user_info):
    conn = get_db_connection()
    with conn:
        conn.execute('''
            INSERT INTO user (name, email, phone_number)
            VALUES (?, ?, ?)
        ''', (user_info['name'], user_info['email'], user_info['phone_number']))
    conn.close()

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message')
    if not user_message:
        return jsonify({'error': 'Message is required'}), 400

    pdf_text = extract_text_from_pdf(PDF_PATH)
    with open('./history.txt', 'w') as file:
            file.write('User: ' + user_message + '\n')
    
    with open('./history.txt', 'r') as file:
        content = file.read()

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",  
            messages=[
                {
            "role": "system",
            "content": (
                "Your name is HomeGenie. You are a helpful assistant here to assist users with issues in their home. "
                "The information you need to provide is based on the PDF content. Make sure to remove unnecessary quotations, "
                "asterisks, and other special characters while providing the answer. Provide solutions in points with a newline character. "
                "Review the conversation history before answering the user."
            ),
        },
        {
            "role": "assistant",
            "content": (
                "Please read the provided information carefully and answer the user's questions based on this content. "
                f"This is the information needed by you to assist the user:\n{pdf_text}"
            ),
        },
        {
            "role": "system",
            "content": (
                "This is the conversation history. Answer the user considering their past questions and your previous responses. "
                f"The user's part is marked as 'user' and your part as 'HomeGenie'. Use the following information to assist the user:\n{content}"
            ),
        },
        {
            "role": "user",
            "content": (
                f"content: {user_message}.\n"
                "The information you need to provide is based on the PDF content. Please ensure you provide only the solution based on the user's request. "
                "If the user greets you, just greet them back without providing any unnecessary information. Remove unnecessary quotations, asterisks, and special characters from your answer."
            ),
        },
            ]
        )
        reply = response.choices[0].message.content
        with open('./history.txt', 'w') as file:
            file.write('HomeGenie: ' + reply + '\n')

        user_info = parse_user_info(user_message)
        if all(user_info.values()):  # Check if all fields are filled
            save_user_info(user_info)
    except Exception as e:
        print(f"Error with OpenAI API call: {e}")
        return jsonify({'error': str(e)}), 500

    return jsonify({'reply': reply})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))  # Use the PORT environment variable or default to 5000
    app.run(host='0.0.0.0', port=port, debug=True)
