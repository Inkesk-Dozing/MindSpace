import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import pickle
import os

def train():
    # Load data
    data_path = '../data/sample_data.csv'
    if not os.path.exists(data_path):
        # Fallback for if script is run from project root
        data_path = 'data/sample_data.csv'
        if not os.path.exists(data_path):
            print(f"Error: {data_path} not found.")
            return
    
    df = pd.read_csv(data_path)
    
    # Preprocessing (Match logic in app.py)
    numeric_cols = ['sleep_hours', 'study_hours', 'stress_level']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        df[col] = df[col].apply(lambda x: max(x, 0))
    
    # Calculate burnout_score and risk
    df['burnout_score'] = df.apply(lambda row: ((row['study_hours'] / row['sleep_hours'] if row['sleep_hours'] > 0 else 0) * row['stress_level']) * 10, axis=1)
    df['burnout_score'] = np.clip(df['burnout_score'], 0, 100)
    df['risk'] = pd.cut(df['burnout_score'], bins=[-1, 33, 66, 101], labels=['Low', 'Medium', 'High'])
    
    # Features and Target
    X = df[numeric_cols]
    y = df['risk']
    
    # Encode Target
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    class_names = le.classes_.tolist()
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)
    
    # Train Model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Save Model and Data for evaluation
    model_dir = '../models'
    os.makedirs(model_dir, exist_ok=True)
    
    with open(os.path.join(model_dir, 'model.pkl'), 'wb') as f:
        pickle.dump(model, f)
    
    with open(os.path.join(model_dir, 'eval_data.pkl'), 'wb') as f:
        pickle.dump({
            'X_test': X_test,
            'y_test': y_test,
            'class_names': class_names
        }, f)
        
    print("Model and evaluation data saved successfully.")

if __name__ == "__main__":
    train()
