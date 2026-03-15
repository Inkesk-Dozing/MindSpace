import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
#Use a clean style for plots
plt.style.use('ggplot')
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
import seaborn as sns

# Ensure NLTK data is downloaded once
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mindspace_secret_key'

@app.context_processor
def inject_breadcrumbs():
    from flask import request
    breadcrumbs = [{'name': '🏠 Home', 'url': '/'}]
    
    if request.endpoint == 'dashboard':
        breadcrumbs.append({'name': 'Dashboard', 'url': '/dashboard'})
    elif request.endpoint == 'edit':
        breadcrumbs.append({'name': 'Dashboard', 'url': '/dashboard'})
        breadcrumbs.append({'name': 'Edit Dataset', 'url': '/edit'})
    elif request.endpoint == 'compare':
        breadcrumbs.append({'name': 'Dashboard', 'url': '/dashboard'})
        breadcrumbs.append({'name': 'Compare', 'url': '/compare'})
    
    return dict(breadcrumbs=breadcrumbs)

# Global DataFrame to hold data
data_df = None
data_df_b = None  # NEW

@app.route('/')
def index():
    history = session.get('history', [])
    return render_template('index.html', history=history)

@app.route('/reset')
def reset():
    """Clear all session history."""
    global data_df, data_df_b  # NEW
    data_df = None              # NEW
    data_df_b = None            # NEW
    session.pop('history', None)
    return redirect(url_for('index'))

@app.route('/delete-session/<int:idx>')
def delete_session(idx):
    """Remove a specific session entry."""
    history = session.get('history', [])
    if 0 <= idx < len(history):
        history.pop(idx)
        session['history'] = history
        session.modified = True
    return redirect(url_for('index'))

@app.route('/upload', methods=['POST','GET'])
def upload():
    """Handle dataset upload endpoint."""
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
                
                # Update history in session metadata (no disk save per user request)
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
                return redirect(url_for('dashboard'))
            except Exception as e:
                print(f"Error reading CSV: {e}")
                return redirect(url_for('index'))
    return redirect(url_for('index'))

def process_data():
    """Process CSV data and compute burnout scores."""
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
    
    numeric_cols = ['sleep_hours', 'study_hours', 'stress_level']
    for col in numeric_cols:
        if col in data_df.columns:
            data_df[col] = pd.to_numeric(data_df[col], errors='coerce')
            data_df[col]=data_df[col].fillna(0)
    for col in numeric_cols:
        if col in data_df.columns:
            data_df[col]=data_df[col].apply(lambda x : max(x,0))

    data_df['burnout_score'] = data_df.apply(
        lambda row: ((row['study_hours'] / row['sleep_hours'] if row['sleep_hours'] > 0 else 0) * row['stress_level']) * 10,
        axis=1
    )
    data_df['burnout_score'] = np.clip(data_df['burnout_score'], 0, 100)
    
    data_df['risk'] = pd.cut(data_df['burnout_score'], bins=[-1, 33, 66, 101], labels=['Low', 'Medium', 'High'])
    
    sia = SentimentIntensityAnalyzer()
    if 'feedback' in data_df.columns:
        data_df['sentiment_score'] = data_df['feedback'].apply(lambda x: sia.polarity_scores(str(x))['compound'])
    else:
        data_df['sentiment_score'] = 0
    
    numericc_cols = ['sleep_hours', 'study_hours', 'stress_level','burnout_score']
    available_cols=[col for col in numericc_cols if col in data_df.columns]
    corr_matrix=data_df[available_cols].corr()

# NEW - shared processing logic for second dataset
def _process(df):
    numeric_cols = ['sleep_hours', 'study_hours', 'stress_level']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    df['burnout_score'] = df.apply(
        lambda row: ((row['study_hours'] / row['sleep_hours'] if row['sleep_hours'] > 0 else 0) * row['stress_level']) * 10,
        axis=1
    )
    df['burnout_score'] = np.clip(df['burnout_score'], 0, 100)
    df['risk'] = pd.cut(df['burnout_score'], bins=[-1, 33, 66, 101], labels=['Low', 'Medium', 'High'])
    sia = SentimentIntensityAnalyzer()
    if 'feedback' in df.columns:
        df['sentiment_score'] = df['feedback'].apply(lambda x: sia.polarity_scores(str(x))['compound'])
    else:
        df['sentiment_score'] = 0

# NEW - upload second dataset for comparison
@app.route('/upload_b', methods=['POST'])
def upload_b():
    global data_df_b
    if 'file' not in request.files:
        return redirect(url_for('dashboard'))
    file = request.files['file']
    if file and file.filename.endswith('.csv'):
        try:
            data_df_b = pd.read_csv(file)
            _process(data_df_b)
            return redirect(url_for('compare'))
        except Exception as e:
            print(f"Error reading CSV: {e}")
    return redirect(url_for('dashboard'))

# NEW - compare two datasets
@app.route('/compare')
def compare():
    global data_df, data_df_b
    if data_df is None or data_df_b is None:
        return redirect(url_for('dashboard'))

    def get_stats(df):
        risk_counts = df['risk'].value_counts().to_dict()
        return {
            'avg_burnout': round(df['burnout_score'].mean(), 1),
            'total_records': len(df),
            'high_risk_count': int((df['risk'] == 'High').sum()),
            'risk_data': [risk_counts.get('Low', 0), risk_counts.get('Medium', 0), risk_counts.get('High', 0)],
            'burnout_scores': df['burnout_score'].tolist()
        }

    return render_template('compare.html',
                           stats_a=get_stats(data_df),
                           stats_b=get_stats(data_df_b))

@app.route('/dashboard')
def dashboard():
    global data_df
    if data_df is None:
        return redirect(url_for('index'))
    
    plot_dir = os.path.join(app.static_folder, 'plots')
    os.makedirs(plot_dir, exist_ok=True)
    
    plt.figure(figsize=(7, 4), dpi=150)
    plt.hist(data_df['burnout_score'], bins=20, color='#3b82f6', edgecolor='white', alpha=0.8)
    plt.title('Burnout Score Distribution', fontsize=14, pad=15)
    plt.xlabel('Burnout Score (0-100)', fontsize=10)
    plt.ylabel('Number of Students', fontsize=10)
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(plot_dir, 'score_hist.png'))
    plt.close('all')
  
    risk_counts = data_df['risk'].value_counts()
    plt.figure(figsize=(5, 5), dpi=150)
    if not risk_counts.empty:
        risk_counts.plot.pie(
            autopct='%1.1f%%',
            colors=["#e28e0f", "#ef4444","#3b82f6"],
            startangle=140,
            textprops={'fontsize':10, 'color':'white', 'weight':'bold'},
            pctdistance=0.75
        )
    plt.title('Burnout Risk Distribution', fontsize=14, pad=5)
    plt.ylabel('')
    plt.tight_layout()
    plt.savefig(os.path.join(plot_dir, 'risk_pie.png'))
    plt.close('all')

    if 'stress_level' in data_df.columns and 'burnout_score' in data_df.columns:
        grouped=data_df.groupby('stress_level')['burnout_score'].mean()
        if not grouped.empty:
            plt.figure(figsize=(7, 4), dpi=150)
            grouped.plot(marker='o', markersize=6, linewidth=2, color='#f59e0b')
            plt.title('Average Burnout vs Stress Level', fontsize=14, pad=15)
            plt.xlabel("Stress Level (1-10)", fontsize=10)
            plt.ylabel("Average Burnout Score", fontsize=10)
            plt.grid(True, linestyle=':', alpha=0.6)
            plt.fill_between(grouped.index, grouped.values, alpha=0.1, color='#f59e0b')
            plt.tight_layout()
            plt.savefig(os.path.join(plot_dir,"stress_vs_burnout.png"))
            plt.close('all')

    if corr_matrix is not None:
        plt.figure(figsize=(8, 6), dpi=150)
        sns.heatmap(
            corr_matrix,
            annot=True,
            cmap='RdBu_r', 
            center=0,
            fmt=".2f",
            linewidths=1,
            annot_kws={"size": 10},
            cbar_kws={"shrink": .8}
        )
        plt.title("Feature Correlation Heatmap", fontsize=14, pad=15)
        plt.tight_layout()
        plt.savefig(os.path.join(plot_dir, "correlation_heatmap.png"))
        plt.close('all')

    if 'sleep_hours' in data_df.columns and 'burnout_score' in data_df.columns:
        plt.figure(figsize=(7, 4), dpi=150)
        colors = {'Low': '#3b82f6', 'Medium': '#f59e0b', 'High': '#ef4444'}
        for risk_level, group in data_df.groupby('risk', observed=True):
            plt.scatter(group['sleep_hours'], group['burnout_score'],
                        label=str(risk_level), alpha=0.6,
                        color=colors.get(str(risk_level), 'gray'), s=50, edgecolors='white')
        plt.title('Sleep Hours vs Burnout Score', fontsize=14, pad=15)
        plt.xlabel('Sleep Hours', fontsize=10)
        plt.ylabel('Burnout Score', fontsize=10)
        plt.legend(title='Risk Level', frameon=True, shadow=False, fontsize='small')
        plt.grid(True, linestyle='--', alpha=0.4)
        plt.tight_layout()
        plt.savefig(os.path.join(plot_dir, 'sleep_vs_burnout.png'))
        plt.close('all')

    if 'risk' in data_df.columns and 'burnout_score' in data_df.columns:
        fig, ax = plt.subplots(figsize=(7, 4), dpi=150)
        risk_order = ['Low', 'Medium', 'High']
        box_data = [data_df[data_df['risk'] == r]['burnout_score'].dropna().tolist()
                    for r in risk_order if r in data_df['risk'].values]
        box_labels = [r for r in risk_order if r in data_df['risk'].values]
        bp = ax.boxplot(box_data, labels=box_labels, patch_artist=True, widths=0.5)
        box_colors = ['#3b82f6', '#f59e0b', '#ef4444']
        for patch, color in zip(bp['boxes'], box_colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.5)
            patch.set_edgecolor('white')
        ax.set_title('Burnout Score by Risk Tier', fontsize=14, pad=15)
        ax.set_xlabel('Risk Category', fontsize=10)
        ax.set_ylabel('Burnout Score', fontsize=10)
        ax.grid(True, axis='y', linestyle='--', alpha=0.4)
        plt.tight_layout()
        plt.savefig(os.path.join(plot_dir, 'burnout_boxplot.png'))
        plt.close('all')

    if 'sentiment_score' in data_df.columns:
        plt.figure(figsize=(7, 4), dpi=150)
        plt.hist(data_df['sentiment_score'], bins=20,
                 color='#6366f1', edgecolor='white', alpha=0.7)
        plt.axvline(0, color='#ef4444', linestyle='--', linewidth=2, label='Neutral')
        plt.title('Sentiment Score Distribution', fontsize=14, pad=15)
        plt.xlabel('Sentiment Score (−1 to +1)', fontsize=10)
        plt.ylabel('Number of Students', fontsize=10)
        plt.legend(frameon=True, fontsize='small')
        plt.grid(axis='y', linestyle='--', alpha=0.4)
        plt.tight_layout()
        plt.savefig(os.path.join(plot_dir, 'sentiment_dist.png'))
        plt.close('all')

    if 'study_hours' in data_df.columns and 'burnout_score' in data_df.columns:
        plt.figure(figsize=(7, 4), dpi=150)
        plt.scatter(data_df['study_hours'], data_df['burnout_score'], 
                    alpha=0.6, color='#8b5cf6', s=50, edgecolors='white')
        plt.title('Study Hours vs Burnout Score', fontsize=14, pad=15)
        plt.xlabel('Daily Study Hours', fontsize=10)
        plt.ylabel('Burnout Score', fontsize=10)
        plt.grid(True, linestyle='--', alpha=0.4)
        plt.tight_layout()
        plt.savefig(os.path.join(plot_dir, 'study_vs_burnout.png'))
        plt.close('all')

    if 'stress_level' in data_df.columns and 'sleep_hours' in data_df.columns:
        plt.figure(figsize=(7, 4), dpi=150)
        grouped_sleep = data_df.groupby('stress_level')['sleep_hours'].mean()
        grouped_sleep.plot(kind='bar', color='#10b981', alpha=0.7, edgecolor='white')
        plt.title('Average Sleep Duration by Stress Level', fontsize=14, pad=15)
        plt.xlabel('Stress Level (1-10)', fontsize=10)
        plt.ylabel('Average Sleep Hours', fontsize=10)
        plt.xticks(rotation=0)
        plt.grid(axis='y', linestyle='--', alpha=0.4)
        plt.tight_layout()
        plt.savefig(os.path.join(plot_dir, 'stress_vs_sleep.png'))
        plt.close('all')

    if 'sentiment_score' in data_df.columns and 'burnout_score' in data_df.columns:
        plt.figure(figsize=(7, 4), dpi=150)
        plt.scatter(data_df['sentiment_score'], data_df['burnout_score'], 
                    alpha=0.6, color='#ec4899', s=50, edgecolors='white')
        plt.title('Sentiment vs Burnout Score', fontsize=14, pad=15)
        plt.xlabel('Sentiment Score', fontsize=10)
        plt.ylabel('Burnout Score', fontsize=10)
        plt.grid(True, linestyle='--', alpha=0.4)
        plt.tight_layout()
        plt.savefig(os.path.join(plot_dir, 'sentiment_vs_burnout.png'))
        plt.close('all')

    avg_burnout = round(data_df['burnout_score'].mean(), 1)
    median_burnout=round(data_df['burnout_score'].median(),1)
    std_burnout=round(data_df['burnout_score'].std(),1)
    total_records = len(data_df)
    high_risk_count = (data_df['risk'] == 'High').sum()
    pct_high_risk = round(high_risk_count / total_records * 100, 1) if total_records else 0
    avg_sentiment = round(data_df['sentiment_score'].mean(), 2) if 'sentiment_score' in data_df.columns else 'N/A'

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
                           pct_high_risk=pct_high_risk,
                           avg_sentiment=avg_sentiment,
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
        process_data()
        return redirect(url_for('dashboard'))
    return render_template('edit.html', data=data_df.to_dict('records'), columns=data_df.columns.tolist())

if __name__ == '__main__':
    app.run(debug=True)