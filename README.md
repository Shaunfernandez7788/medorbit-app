🩺 MedOrbit - AI-Powered Health Assistant

**MedOrbit** is a hybrid AI healthcare platform designed to provide accessible medical guidance. It combines **Supervised Machine Learning** for precise disease prediction with **Multimodal Generative AI (Google Gemini)** for interactive medical consultations and image analysis. The platform also features a full appointment booking system, real-time emergency services, and hospital geolocation.

### 🚀 [Click here to visit MedOrbit Live](https://www.google.com/search?q=https://medorbit-app.onrender.com)

> **Note:** The application is hosted on a free Render instance. Please allow **30-50 seconds** for the server to wake up on the first visit.

---

## 🌟 Key Features

### 1. 📸 AI Health Scanner (Computer Vision) [NEW]

* **Multimodal AI:** Users can upload photos of **skin rashes, medical reports, or medicine labels**.
* **Smart Analysis:** Uses **Google Gemini 1.5 Flash/Pro Vision** to analyze the image and explain it in simple terms (e.g., "This looks like Eczema, consider using moisturizer").
* **Privacy First:** Images are processed in memory and never stored permanently on the server.

### 2. 📅 Appointment Booking System [NEW]

* **Full CRUD Functionality:** Users can **Book, View, Edit, and Cancel** appointments with hospitals.
* **Smart Dashboard:** A dedicated "My Appointments" page tracks upcoming visits with status updates.
* **Hospital Integration:** Features a mock booking engine for demonstration and a real Google Maps integration for finding actual facilities.

### 3. 🎙️ Voice-Activated Symptom Search [NEW]

* **Speech-to-Text:** Integrated **Web Speech API** allows users to speak their symptoms (e.g., "I have a headache and fever") instead of typing.
* **Hands-Free:** Critical for elderly users or emergency situations.

### 4. 🤖 AI Medical Chatbot (GenAI)

* **Smart Model Discovery:** Automatically detects and connects to the best available Google Gemini model.
* **Context-Aware:** Provides instant, natural language answers to health-related queries.
* **Persona-Based:** Engineered to act as an empathetic, supportive medical assistant.

### 5. 🔍 Symptom Analyzer (Machine Learning)

* **Algorithm:** Custom-trained **Random Forest Classifier** using Scikit-Learn.
* **Function:** Predicts potential diseases based on user-selected symptoms (e.g., High Fever + Joint Pain + Rash → Chikungunya).
* **Dataset:** Trained on a verified medical dataset covering 40+ common diseases.

### 6. 🆘 Emergency SOS & Location

* **SOS Button:** Instantly dials **112** (Universal Emergency Number).
* **Hospital Locator:** Integrated geolocation feature that finds nearby hospitals and clinics based on the user's current coordinates.

---

## 🛠️ Tech Stack

| Component | Technology Used |
| --- | --- |
| **Backend** | Python, Flask, Gunicorn |
| **Frontend** | HTML5, CSS3, Bootstrap 5, JavaScript (Web Speech API) |
| **Machine Learning** | Scikit-Learn, Pandas, NumPy, Joblib |
| **Generative AI** | Google Gemini API (google-generativeai), Multimodal Vision |
| **Image Processing** | Pillow (PIL) |
| **Database** | SQLite (Development) / SQLAlchemy ORM |
| **Deployment** | Render Cloud Platform |
| **Version Control** | Git, GitHub |

---

## 🏗️ Architecture

MedOrbit uses a hybrid architecture to handle different types of user requests efficiently:

1. **Vision Requests:** Images are converted to bytes in memory and sent securely to Google's Vision API.
2. **Chat Requests:** Routed securely to Google's Gemini API via server-side API calls.
3. **Prediction Requests:** Processed locally by the Flask server using the pre-trained `.pkl` model (Low latency).
4. **Database:** User data and appointments are stored in a secure relational database managed by SQLAlchemy.

---

## 💻 Installation & Setup

Follow these steps to run the project locally on your machine.

### Prerequisites

* Python 3.9 or higher installed.
* A valid **Google AI Studio API Key**.

### Steps

1. **Clone the Repository**
```bash
git clone https://github.com/Shaunfernandez7788/medorbit-app.git
cd medorbit-app

```


2. **Create a Virtual Environment**
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

```


3. **Install Dependencies**
```bash
pip install -r requirements.txt

```


4. **Set Up Environment Variables**
* Create a file named `.env` in the **root** folder.
* Add your API key inside it:
```ini
GEMINI_API_KEY=your_actual_api_key_here

```




*(Note: The `.env` file is hidden and secure. Do not share it publicly.)*
5. **Run the Application**
```bash
python app.py

```


6. **Access the App**
Open your browser and go to: `http://127.0.0.1:5000`

---


## 👨‍💻 Author

**Shaun Anselm Fernandez**

* *Computer Science Engineering Student*
* *Cambridge Institute of Technology, Bangalore*

---

### 📝 License

This project is licensed under the MIT License - see the [LICENSE](https://www.google.com/search?q=LICENSE) file for details.

```
```
* [LinkedIn Profile](https://www.linkedin.com/in/shaun-fernandez7878)
* [GitHub Profile](https://github.com/Shaunfernandez7788)
