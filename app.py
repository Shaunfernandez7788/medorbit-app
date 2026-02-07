import google.generativeai as genai
from flask import jsonify
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import joblib
import pandas as pd
import os

app = Flask(__name__)
# Configure Gemini AI
genai.configure(api_key="AIzaSyD7qowo9WqUBu0-jCpexxuDSBoZbB8pQfU")

# Set up the model with a specific "Persona" for accuracy
generation_config = {
    "temperature": 0.7,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
]

model_ai = genai.GenerativeModel(model_name="gemini-2.5-flash",
                              generation_config=generation_config,
                              safety_settings=safety_settings)
app.config['SECRET_KEY'] = 'secret-key-goes-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

# --- DATABASE SETUP ---
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Create the database file if it doesn't exist
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- LOAD AI MODEL ---
# Loading these once when the app starts
model = joblib.load('model.pkl')
symptom_list = joblib.load('symptoms.pkl')
desc_df = pd.read_csv('symptom_Description.csv')
prec_df = pd.read_csv('symptom_precaution.csv')

# --- ROUTES ---

@app.route('/')
def home():
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if user exists
        if User.query.filter_by(email=email).first():
            flash('Email already exists')
            return redirect(url_for('register'))
            
        new_user = User(email=email, password=generate_password_hash(password, method='scrypt'))
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        return redirect(url_for('dashboard'))
        
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', symptoms=symptom_list, prediction=None)

@app.route('/predict', methods=['POST'])
@login_required
def predict():
    # Get selected symptoms from the form
    selected_symptoms = request.form.getlist('symptoms')
    
    # Create input vector for model
    input_data = [0] * len(symptom_list)
    for symptom in selected_symptoms:
        if symptom in symptom_list:
            index = symptom_list.index(symptom)
            input_data[index] = 1
            
    # AI Prediction
    prediction = model.predict([input_data])[0]
    
    # Get Details
    desc_row = desc_df[desc_df['Disease'] == prediction]
    description = desc_row.iloc[0]['Description'] if not desc_row.empty else "No description."
    
    prec_row = prec_df[prec_df['Disease'] == prediction]
    precautions = prec_row.iloc[0, 1:].dropna().values if not prec_row.empty else []

    return render_template('dashboard.html', 
                           symptoms=symptom_list, 
                           prediction=prediction,
                           description=description,
                           precautions=precautions)
@app.route('/chat_response', methods=['POST'])
def chat_response():
    user_message = request.json.get('message')

    if not user_message:
        return jsonify({'response': "Please say something!"})

    # Strict System Prompt for Accuracy
    prompt = f"""
    You are MedOrbit AI, a highly knowledgeable and responsible medical assistant.
    User Question: {user_message}

    Guidelines:
    1. Provide accurate, science-based health information.
    2. If the user asks about a serious condition, ALWAYS advise them to see a doctor immediately.
    3. Keep answers concise (under 3-4 sentences) unless asked for detail.
    4. Be empathetic but professional.
    """

    try:
        response = model_ai.generate_content(prompt)
        return jsonify({'response': response.text})
    except Exception as e:
        return jsonify({'response': "I'm having trouble connecting to my medical database right now. Please try again."})

if __name__ == '__main__':
    app.run(debug=True)