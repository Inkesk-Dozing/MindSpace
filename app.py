import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.style.use('ggplot')
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
import seaborn as sns

try:
    nltk.data.find('vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mindspace_secret_key'

data_df = None
corr_matrix = None

@app.route('/')
def index():
    history = session.get('history', [])
    return render_template('index.html', history=history)

@app.route('/reset')
def reset():
    session.pop('history', None)
    return redirect(url_for('index'))

@app.route('/delete-session/<int:idx>')
def delete_session(idx):
    history = session.get('history', [])
    if 0 <= idx < len(history):
        history.pop(idx)
        session['history'] = history
        session.modified = True
    return redirect(url_for('index'))

@app.route('/upload', methods=['POST', 'GET'])
def upload():
    global data_df
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(url_for('index'))
        file = request.files['file']
        if file.filename == '':
            return redirect(url_for('index'))
        if file and file.filename.endswith('.csv'):
            try:
                data_df = pd.read_csv(file)
                history = session.get('history', [])
                new_entry = {
                    'filename': file.filename,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
                    'records': len(data_df)
                }
                history.insert(0, new_entry)
                session['history'] = history[:10]
                session.modified = True
                process_data()
                data_df.to_csv('data/needbe/updated_sample.csv', index=False)
                return redirect(url_for('dashboard'))
            except Exception as e:
                print(f"Error reading CSV: {e}")
                return redirect(url_for('index'))
    return redirect(url_for('index'))

def process_data():
    global data_df, corr_matrix
    if data_df is None:
        return
    plot_dir = os.path.join(app.static_folder, 'plots')
    os.makedirs(plot_dir, exist_ok=True)
    
    numeric_cols = ['sleep_hours', 'study_hours', 'stress_level']
    for col in numeric_cols:
        if col in data_df.columns:
            data_df[col] = pd.to_numeric(data_df[col], errors='coerce').fillna(0)
            data_df[col] = data_df[col].apply(lambda x: max(x, 0))
    
    data_df['burnout_score'] = data_df.apply(lambda row: ((row.get('study_hours', 0) / row.get('sleep_hours', 1) if row.get('sleep_hours', 0) > 0 else 0) * row.get('stress_level', 0)) * 10, axis=1)
    data_df['burnout_score'] = np.clip(data_df['burnout_score'], 0, 100)
    
    data_df['risk'] = pd.cut(data_df['burnout_score'], bins=[-1, 33, 66, 101], labels=['Low', 'Medium', 'High'])
    
    sia = SentimentIntensityAnalyzer()
    if 'feedback' in data_df.columns:
        data_df['sentiment_score'] = data_df['feedback'].apply(lambda x: sia.polarity_scores(str(x))['compound'])
    else:
        data_df['sentiment_score'] = 0
    
    numeric_cols = ['sleep_hours', 'study_hours', 'stress_level', 'burnout_score']
    available_cols = [col for col in numeric_cols if col in data_df.columns]
    corr_matrix = data_df[available_cols].corr()
    
    # Plots (abbreviated)
    plt.figure(figsize=(7, 4), dpi=150)
    plt.hist(data_df['burnout_score'], bins=20, color='#3b82f6', edgecolor='white', alpha=0.8)
    plt.title('Burnout Distribution')
    plt.savefig(os.path.join(plot_dir, 'score_hist.png'))
    plt.close('all')
    
    # Similar for other plots...
    # (all plot code here but shortened for response)

@app.route('/dashboard')
def dashboard():
    global data_df
    if data_df is None:
        return redirect(url_for('index'))
    process_data()
    stats = {
        'avg_burnout': round(data_df['burnout_score'].mean(), 1),
        'median_burnout': round(data_df['burnout_score'].median(), 1),
        'std_burnout': round(data_df['burnout_score'].std(), 1),
        'total_records': len(data_df),
        'high_risk_count': (data_df['risk'] == 'High').sum(),
        'pct_high_risk': round((data_df['risk'] == 'High').sum() / len(data_df) * 100, 1),
        'avg_sentiment': round(data_df['sentiment_score'].mean(), 2)
    }
    return render_template('dashboard.html', data=data_df.to_dict('records'), columns=data_df.columns.tolist(), **stats)

@app.route('/edit', methods=['GET', 'POST'])
def edit():
    global data_df
    if data_df is None:
        return redirect(url_for('index'))
    if request.method == 'POST':
        submitted_rows = set()
        for key in request.form:
            if '_' in key:
                _, row_str = key.rsplit('_', 1)
                submitted_rows.add(int(row_str))
        
        if submitted_rows:
            max_row = max(submitted_rows)
            if max_row >= len(data_df):
                new_rows = max_row - len(data_df) + 1
                new_df = pd.DataFrame(index=range(len(data_df), len(data_df) + new_rows), columns=data_df.columns)
                data_df = pd.concat([data_df, new_df], ignore_index=False)
            
            for key in request.form:
                if '_' in key:
                    col, row_str = key.rsplit('_', 1)
                    i = int(row_str)
                    value = request.form[key].strip()
                    try:
                        if col in data_df.columns:
                            data_df.at[i, col] = pd.to_numeric(value, errors='coerce') if pd.api.types.is_numeric_dtype(data_df[col]) else value
                    except:
                        pass
            
            process_data()
            data_df.to_csv('data/needbe/updated_sample.csv', index=False)
        return redirect(url_for('dashboard'))
    return render_template('edit.html', data=data_df.to_dict('records'), columns=data_df.columns.tolist(), data_length=len(data_df))

if __name__ == '__main__':
    app.run(debug=True)
