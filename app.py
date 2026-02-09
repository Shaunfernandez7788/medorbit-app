import google.generativeai as genai
from flask import jsonify, Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import joblib
import pandas as pd
import os
import io                   # NEW: For handling image bytes
from PIL import Image       # NEW: For image processing
from dotenv import load_dotenv # Required for local testing

# --- 1. SECURE API KEY SETUP ---
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

# --- MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Appointment Model
class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    hospital_name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    time = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default="Confirmed")

# Create the database file if it doesn't exist
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- LOAD ML MODELS ---
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
        selected_symptoms = request.form.getlist('symptoms')
        
        input_data = [0] * len(symptom_list)
        for symptom in selected_symptoms:
            if symptom in symptom_list:
                index = symptom_list.index(symptom)
                input_data[index] = 1
                
        prediction = model.predict([input_data])[0]
        
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

# --- APPOINTMENT ROUTES ---
@app.route('/book_appointment', methods=['POST'])
@login_required
def book_appointment():
    try:
        data = request.json
        new_appointment = Appointment(
            user_id=current_user.id,
            hospital_name=data.get('hospital_name'),
            date=data.get('date'),
            time=data.get('time')
        )
        db.session.add(new_appointment)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Appointment booked successfully!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/my_appointments')
@login_required
def my_appointments():
    appointments = Appointment.query.filter_by(user_id=current_user.id).all()
    return render_template('appointments.html', appointments=appointments)

@app.route('/edit_appointment/<int:id>', methods=['POST'])
@login_required
def edit_appointment(id):
    try:
        appt = Appointment.query.get_or_404(id)
        if appt.user_id != current_user.id:
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
        
        data = request.json
        appt.date = data.get('date')
        appt.time = data.get('time')
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Appointment updated!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/delete_appointment/<int:id>', methods=['POST'])
@login_required
def delete_appointment(id):
    try:
        appt = Appointment.query.get_or_404(id)
        if appt.user_id != current_user.id:
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
            
        db.session.delete(appt)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Appointment cancelled!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# --- NEW: AI IMAGE SCANNER ROUTES ---
@app.route('/scan')
@login_required
def scan():
    return render_template('scan.html')

@app.route('/analyze_image', methods=['POST'])
@login_required
def analyze_image():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'})

        # 1. Process the image
        image_data = file.read()
        image = Image.open(io.BytesIO(image_data))
        
        # 2. SMART MODEL DISCOVERY (Fixes 404 Error)
        # We ask Google which models are available and pick the best vision-capable one.
        model_name = "gemini-1.5-flash" # Fallback
        try:
            available_models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available_models.append(m.name)
            
            # Priority list: Try 1.5 Flash -> 1.5 Pro -> Pro Vision
            if any('gemini-1.5-flash' in m for m in available_models):
                model_name = 'gemini-1.5-flash'
            elif any('gemini-1.5-pro' in m for m in available_models):
                model_name = 'gemini-1.5-pro'
            elif any('gemini-pro-vision' in m for m in available_models):
                model_name = 'gemini-pro-vision'
            else:
                # If all else fails, grab the first available gemini model
                model_name = available_models[0]
                
        except Exception as e:
            print(f"⚠️ Model list failed, using default: {e}")

        print(f"✅ ANALYZE IMAGE USING: {model_name}", flush=True)
        model = genai.GenerativeModel(model_name)
        
        # 3. Prompt for Medical Context
        prompt = """
        You are an expert medical AI. Analyze this image. 
        - If it is a skin issue, describe it and suggest potential causes (disclaimer: not a diagnosis).
        - If it is a medicine label, explain what the medicine is for and common side effects.
        - If it is a lab report, summarize the key findings.
        - If it is unrelated to health, strictly say 'I can only analyze medical images.'
        Keep the response clear and structured.
        """
        
        # 4. Generate Response
        response = model.generate_content([prompt, image])
        
        return jsonify({'result': response.text})
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({'error': str(e)})


# --- SMART CHATBOT ROUTE ---
@app.route('/chat_response', methods=['POST'])
def chat_response():
    try:
        user_input = request.json.get('message')
        
        model_name = "gemini-1.5-flash" 
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    if 'flash' in m.name:
                        model_name = m.name
                        break
                    elif 'gemini' in m.name:
                        model_name = m.name
        except Exception as e:
            print(f"⚠️ Could not list models, falling back to default: {e}")

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