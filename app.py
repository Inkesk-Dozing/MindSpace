from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import json
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk

# Ensure NLTK data is downloaded once
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'

# Global DataFrame to hold data
data_df = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST','GET'])
def upload():
    global data_df
    if request.method=='POST':
        if 'file' not in request.files:
            return redirect(url_for('index'))
        file = request.files['file']
        if file.filename == '':
            return redirect(url_for('index'))
        if file and file.filename.endswith('.csv'):
            try:
                data_df = pd.read_csv(file)
            # Process data
                process_data()
                return redirect(url_for('dashboard'))
            except Exception as e:
                print(f"Error reading CSV: {e}")
                return redirect(url_for('index'))
    return redirect(url_for('index'))

def process_data():
    plot_dir=os.path.join(app.static_folder,'plots')
    os.makedirs(plot_dir,exist_ok=True)
    global data_df
    global corr_matrix
    global burnout_by_stress
    if 'corr_matrix' not in globals():
        corr_matrix=None
    if 'burnout_by_stress' not in globals():
        burnout_by_stress=None
    if data_df is None:
        return
    
    # Ensure numeric columns are actually numeric
    numeric_cols = ['sleep_hours', 'study_hours', 'stress_level']
    for col in numeric_cols:
        if col in data_df.columns:
            data_df[col] = pd.to_numeric(data_df[col], errors='coerce')
            data_df[col]=data_df[col].fillna(0)
    #ENSURE NO NEGATIVE VALUES
    for col in numeric_cols:
        if col in data_df.columns:
            data_df[col]=data_df[col].apply(lambda x : max(x,0))


    # Assume columns: sleep_hours, study_hours, stress_level (1-10), feedback
    # Compute Burnout Score: (study_hours / sleep_hours) * stress_level, normalize to 0-100
    # Guard against division by zero
    data_df['burnout_score'] = data_df.apply(
        lambda row: ((row['study_hours'] / row['sleep_hours'] if row['sleep_hours'] > 0 else 0) * row['stress_level']) * 10,
        axis=1
    )
    #NORMALIZE BURNOUT 0-100

    data_df['burnout_score'] = np.clip(data_df['burnout_score'], 0, 100)
    
    
    # Risk classification
    data_df['risk'] = pd.cut(data_df['burnout_score'], bins=[-1, 33, 66, 101], labels=['Low', 'Medium', 'High'])
    
    # Sentiment analysis
    sia = SentimentIntensityAnalyzer()
    if 'feedback' in data_df.columns:
        data_df['sentiment_score'] = data_df['feedback'].apply(lambda x: sia.polarity_scores(str(x))['compound'])
    else:
        data_df['sentiment_score'] = 0
    
    #CORRELATION ANALYSIS

    numericc_cols = ['sleep_hours', 'study_hours', 'stress_level','burnout_score']
    available_cols=[col for col in numericc_cols if col in data_df.columns]
    corr_matrix=data_df[available_cols].corr()

    


@app.route('/dashboard')
def dashboard():
    global data_df
    if data_df is None:
        return redirect(url_for('index'))
    
    # Generate plots
    plot_dir = 'static/plots'
    os.makedirs(plot_dir, exist_ok=True)
    
    # Histogram of burnout scores
    plt.figure()
    data_df['burnout_score'].hist(bins=20)
    plt.title('Burnout Score Distribution')
    plt.xlabel('Burnout Score')
    plt.ylabel('Frequency')
    plt.savefig(os.path.join(plot_dir, 'score_hist.png'))
    plt.close()
    
    # Pie chart of risk
    risk_counts = data_df['risk'].value_counts()
    plt.figure()
    if not risk_counts.empty:
        risk_counts.plot.pie(autopct='%1.1f%%')
    plt.title('Risk Categories')
    plt.ylabel('')
    plt.savefig(os.path.join(plot_dir, 'risk_pie.png'))
    plt.close()

    #ADDITIONAL GRAPH STRESS VS BURNOUT
    if 'stress_level' in data_df.columns and 'burnout_score' in data_df.columns:
        grouped=data_df.groupby('stress_level')['burnout_score'].mean()
        if not grouped.empty:
            plt.figure()
            grouped.plot(marker='o')
            plt.title('Average Burnout vs Stress Level')
            plt.xlabel("Stress Level")
            plt.ylabel("Average Burnout")
            plt.savefig(os.path.join(plot_dir,"stress_vs_burnout.png"))
            plt.close()
    #ADDITIONAL GRAPH SLEEP VS BURNOUT
    if 'sleep_hours' in data_df.columns and 'burnout_score' in data_df.columns:
            plt.figure()
            plt.scatter(data_df['sleep_hours'],data_df["burnout_score"])

            plt.title('Sleep Hours vs Burnout Score')
            plt.xlabel("Sleep Hours")
            plt.ylabel("Burnout Score")
            plt.tight_layout()
            plt.savefig(os.path.join(plot_dir,"sleep_vs_burnout.png"))
            plt.close()


    # Compute stats
    avg_burnout = round(data_df['burnout_score'].mean(), 1)
    #ADDING MORE FOR SKEWED DATASET
    median_burnout=round(data_df['burnout_score'].median(),1)
    std_burnout=round(data_df['burnout_score'].std(),1)
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
                           median_burnout=median_burnout,
                           std_burnout=std_burnout,
                           total_records=total_records,
                           high_risk_count=high_risk_count,
                           burnout_scores=burnout_scores,
                           risk_data=risk_data,
                           corr_matrix=corr_matrix,
                           burnout_by_stress=burnout_by_stress
                           )

@app.route('/edit', methods=['GET', 'POST'])
def edit():
    global data_df
    if data_df is None:
        return redirect(url_for('index'))
    if request.method == 'POST':
        # Update data
        for i in range(len(data_df)):
            for col in data_df.columns:
                form_key = f'{col}_{i}'
                if form_key in request.form:
                    value = request.form[form_key]
                    if pd.api.types.is_numeric_dtype(data_df[col]):
                        try:
                            value=float(value)
                        except:
                            value=0
                    data_df.at[i,col]=value
        process_data()  # Recompute after edit
        return redirect(url_for('dashboard'))
    return render_template('edit.html', data=data_df.to_dict('records'), columns=data_df.columns.tolist())

if __name__ == '__main__':
    app.run(debug=True)
