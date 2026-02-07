import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib

print("🚀 Starting training script...")

# 1. Load the Dataset
try:
    df = pd.read_csv('dataset.csv')
    print(f"✅ Dataset loaded. Shape: {df.shape}")
except FileNotFoundError:
    print("❌ Error: 'dataset.csv' not found. Make sure it's in the same folder.")
    exit()

# 2. DATA PRE-PROCESSING (The Fix)
# Your dataset lists symptoms as text. We need to convert them to 0s and 1s.

print("   Processing data (creating symptom checklist)...")

# Clean the data: Remove any extra spaces in symptom names
for col in df.columns:
    df[col] = df[col].astype(str).str.strip()

# Step A: Find all unique symptoms hidden in the columns
# We skip the first column because that is the Disease name
symptom_columns = df.columns[1:] 
unique_symptoms = pd.unique(df[symptom_columns].values.ravel())

# Remove 'nan' (empty values) from our list of symptoms
unique_symptoms = [s for s in unique_symptoms if s != 'nan']

# Step B: Create a new "Binary" dataset (The Checklist)
# We create a table full of Zeros
X = pd.DataFrame(0, index=df.index, columns=unique_symptoms)

# We fill in the Ones where symptoms exist
# (This loop matches the text symptoms to our new checklist)
for i, row in df.iterrows():
    # Get all symptoms for this person, ignore 'nan'
    symptoms_present = [s for s in row[1:].values if s != 'nan']
    # Mark them as 1 in our new table
    X.loc[i, symptoms_present] = 1

# The Target (The answer we want to predict)
y = df.iloc[:, 0]  # The first column is the Disease

print(f"   Transformed data shape: {X.shape}")
print("   (The AI now sees 0s and 1s instead of text!)")

# 3. Train the Model
print("🧠 Training the model...")
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

# 4. Save the Files
joblib.dump(model, 'model.pkl')
joblib.dump(list(X.columns), 'symptoms.pkl') # Save the column names so the app knows the order

print("✅ Success! Model trained and saved.")
print("   You can now run 'streamlit run app.py'")