import google.generativeai as genai
from flask import jsonify, Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import joblib
import pandas as pd
import os
from dotenv import load_dotenv # Required for local testing

# --- 1. SECURE API KEY SETUP ---
# This looks for the key in Render's "Environment" tab or a local .env file
load_dotenv() 

api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("❌ WARNING: GEMINI_API_KEY not found. Chatbot will fail until added to Render Environment.")
else:
    genai.configure(api_key=api_key)

app = Flask(__name__)

# Config
app.config['SECRET_KEY'] = 'secret-key-goes-here' # Change this to a random string for production
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

# --- LOAD ML MODELS ---
# We use try/except here so the app doesn't crash if files are missing locally
try:
    model = joblib.load('model.pkl')
    symptom_list = joblib.load('symptoms.pkl')
    desc_df = pd.read_csv('symptom_Description.csv')
    prec_df = pd.read_csv('symptom_precaution.csv')
except Exception as e:
    print(f"⚠️ Warning: ML files not found. Prediction will fail. Error: {e}")

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
    try:
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
    except Exception as e:
        return render_template('dashboard.html', symptoms=symptom_list, prediction="Error", description=str(e))

# --- SMART CHATBOT ROUTE (Auto-Detects Working Model) ---
@app.route('/chat_response', methods=['POST'])
def chat_response():
    try:
        user_input = request.json.get('message')
        
        # 1. List available models to find a working one
        model_name = "gemini-1.5-flash" # Default preference
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    # Prefer flash, but take any valid gemini model
                    if 'flash' in m.name:
                        model_name = m.name
                        break
                    elif 'gemini' in m.name:
                        model_name = m.name
        except Exception as e:
            print(f"⚠️ Could not list models, falling back to default: {e}")

        # 2. Configure the model with the found name
        print(f"✅ USING MODEL: {model_name}", flush=True)
        model_ai = genai.GenerativeModel(model_name)
        
        chat = model_ai.start_chat(history=[])
        
        prompt = f"You are a helpful medical assistant named MedOrbit. Keep answers brief. User asks: {user_input}"
        response = chat.send_message(prompt)
        
        return jsonify({'response': response.text})

    except Exception as e:
        print(f"❌ CHATBOT ERROR: {e}", flush=True) 
        return jsonify({'response': "I am having trouble connecting right now. Please try again."})
if __name__ == '__main__':
    app.run(debug=True)