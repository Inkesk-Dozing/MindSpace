from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import json
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk

nltk.download('vader_lexicon')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'

# Global DataFrame to hold data
data_df = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    global data_df
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file and file.filename.endswith('.csv'):
        data_df = pd.read_csv(file)
        # Process data
        process_data()
        return redirect(url_for('dashboard'))
    return redirect(request.url)

def process_data():
    global data_df
    if data_df is None:
        return
    # Assume columns: sleep_hours, study_hours, stress_level (1-10), feedback
    # Compute Burnout Score: (study_hours / sleep_hours) * stress_level, normalize to 0-100
    data_df['burnout_score'] = ((data_df['study_hours'] / data_df['sleep_hours']) * data_df['stress_level']) * 10
    data_df['burnout_score'] = np.clip(data_df['burnout_score'], 0, 100)
    # Risk classification
    data_df['risk'] = pd.cut(data_df['burnout_score'], bins=[0, 33, 66, 100], labels=['Low', 'Medium', 'High'])
    # Sentiment analysis
    sia = SentimentIntensityAnalyzer()
    data_df['sentiment_score'] = data_df['feedback'].apply(lambda x: sia.polarity_scores(str(x))['compound'])

@app.route('/dashboard')
def dashboard():
    global data_df
    if data_df is None:
        return redirect(url_for('index'))
    # Generate plots
    os.makedirs('static/plots', exist_ok=True)
    # Histogram of burnout scores
    plt.figure()
    data_df['burnout_score'].hist(bins=20)
    plt.title('Burnout Score Distribution')
    plt.xlabel('Burnout Score')
    plt.ylabel('Frequency')
    plt.savefig('static/plots/score_hist.png')
    plt.close()
    # Pie chart of risk
    risk_counts = data_df['risk'].value_counts()
    plt.figure()
    risk_counts.plot.pie(autopct='%1.1f%%')
    plt.title('Risk Categories')
    plt.ylabel('')
    plt.savefig('static/plots/risk_pie.png')
    plt.close()
    
    # Compute stats
    avg_burnout = round(data_df['burnout_score'].mean(), 1)
    total_records = len(data_df)
    high_risk_count = (data_df['risk'] == 'High').sum()
    
    # Prepare data for charts
    burnout_scores = data_df['burnout_score'].tolist()
    risk_counts_dict = data_df['risk'].value_counts().to_dict()
    risk_data = [risk_counts_dict.get('Low', 0), risk_counts_dict.get('Medium', 0), risk_counts_dict.get('High', 0)]
    
    return render_template('dashboard.html',
                           data=data_df.to_dict('records'),
                           columns=data_df.columns.tolist(),
                           avg_burnout=avg_burnout,
                           total_records=total_records,
                           high_risk_count=high_risk_count,
                           burnout_scores=burnout_scores,
                           risk_data=risk_data)

@app.route('/edit', methods=['GET', 'POST'])
def edit():
    global data_df
    if data_df is None:
        return redirect(url_for('index'))
    if request.method == 'POST':
        # Update data
        for i in range(len(data_df)):
            for col in data_df.columns:
                if col in request.form and f'{col}_{i}' in request.form:
                    data_df.at[i, col] = request.form[f'{col}_{i}']
        process_data()  # Recompute after edit
        return redirect(url_for('dashboard'))
    return render_template('edit.html', data=data_df.to_dict('records'), columns=data_df.columns.tolist())

if __name__ == '__main__':
    app.run(debug=True)
