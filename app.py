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
app.jinja_env.filters['enumerate'] = enumerate

data_df = None
corr_matrix = None
eval_metrics = None  # populated after every upload/process

@app.route('/')
def index():
    history = session.get('history', [])
    return render_template('index.html', history=history, active_page='index')

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
                os.makedirs('data', exist_ok=True)
                data_df.to_csv('data/updated_sample.csv', index=False)
                return redirect(url_for('dashboard'))
            except Exception as e:
                print(f"Error reading CSV: {e}")
                return redirect(url_for('index'))
    return redirect(url_for('index'))


def process_data():
    global data_df, corr_matrix, eval_metrics
    if data_df is None:
        return
    plot_dir = os.path.join(app.static_folder, 'plots')
    os.makedirs(plot_dir, exist_ok=True)

    numeric_cols = ['sleep_hours', 'study_hours', 'stress_level']
    for col in numeric_cols:
        if col in data_df.columns:
            data_df[col] = pd.to_numeric(data_df[col], errors='coerce').fillna(0)
            data_df[col] = data_df[col].apply(lambda x: max(x, 0))

    data_df['burnout_score'] = data_df.apply(
        lambda row: ((row.get('study_hours', 0) / row.get('sleep_hours', 1)
                      if row.get('sleep_hours', 0) > 0 else 0) * row.get('stress_level', 0)) * 10,
        axis=1
    )
    data_df['burnout_score'] = np.clip(data_df['burnout_score'], 0, 100)

    data_df['risk'] = pd.cut(
        data_df['burnout_score'], bins=[-1, 33, 66, 101], labels=['Low', 'Medium', 'High']
    )

    sia = SentimentIntensityAnalyzer()
    if 'feedback' in data_df.columns:
        data_df['sentiment_score'] = data_df['feedback'].apply(
            lambda x: sia.polarity_scores(str(x))['compound']
        )
    else:
        data_df['sentiment_score'] = 0

    available_cols = [c for c in ['sleep_hours', 'study_hours', 'stress_level', 'burnout_score'] if c in data_df.columns]
    corr_matrix = data_df[available_cols].corr()

    dark_bg = '#0f1117'
    text_col = '#c9d1d9'
    grid_col = '#30363d'
    accent = '#4facfe'

    def _dark_fig(w=7, h=4):
        fig, ax = plt.subplots(figsize=(w, h), dpi=150)
        fig.patch.set_facecolor(dark_bg)
        ax.set_facecolor(dark_bg)
        ax.tick_params(colors=text_col)
        for spine in ax.spines.values():
            spine.set_edgecolor(grid_col)
        ax.yaxis.label.set_color(text_col)
        ax.xaxis.label.set_color(text_col)
        ax.title.set_color(text_col)
        ax.grid(True, color=grid_col, linestyle='--', linewidth=0.5)
        return fig, ax

    # 1. Burnout score histogram
    fig, ax = _dark_fig()
    ax.hist(data_df['burnout_score'], bins=20, color=accent, edgecolor='#0b0e14', alpha=0.9)
    ax.set_title('Burnout Score Distribution')
    ax.set_xlabel('Burnout Score')
    ax.set_ylabel('Number of Students')
    plt.tight_layout()
    plt.savefig(os.path.join(plot_dir, 'score_hist.png'))
    plt.close('all')

    # 2. Risk pie chart
    if 'risk' in data_df.columns:
        counts = data_df['risk'].value_counts()
        fig, ax = _dark_fig(6, 5)
        colors = ['#28c76f', '#4facfe', '#ff4b5c']
        wedges, texts, autotexts = ax.pie(
            counts, labels=counts.index, autopct='%1.1f%%',
            colors=colors, startangle=140,
            textprops={'color': text_col}
        )
        for at in autotexts:
            at.set_color(dark_bg)
            at.set_fontweight('bold')
        ax.set_title('Burnout Risk Proportions')
        fig.patch.set_facecolor(dark_bg)
        plt.tight_layout()
        plt.savefig(os.path.join(plot_dir, 'risk_pie.png'))
        plt.close('all')

    # 3. Stress vs Burnout bar
    if 'stress_level' in data_df.columns:
        grouped = data_df.groupby('stress_level')['burnout_score'].mean()
        fig, ax = _dark_fig()
        ax.bar(grouped.index, grouped.values, color=accent, alpha=0.85, edgecolor=dark_bg)
        ax.set_title('Avg Burnout by Stress Level')
        ax.set_xlabel('Stress Level (1-10)')
        ax.set_ylabel('Avg Burnout Score')
        plt.tight_layout()
        plt.savefig(os.path.join(plot_dir, 'stress_vs_burnout.png'))
        plt.close('all')

    # 4. Correlation heatmap
    if len(available_cols) > 1:
        fig, ax = _dark_fig(7, 5)
        sns.heatmap(
            corr_matrix, annot=True, fmt='.2f', cmap='coolwarm',
            ax=ax, linewidths=0.5, linecolor=dark_bg,
            annot_kws={'color': text_col}
        )
        ax.set_title('Feature Correlation Heatmap')
        fig.patch.set_facecolor(dark_bg)
        plt.tight_layout()
        plt.savefig(os.path.join(plot_dir, 'correlation_heatmap.png'))
        plt.close('all')

    # 5. Sleep vs Burnout scatter
    if 'sleep_hours' in data_df.columns:
        fig, ax = _dark_fig()
        scatter_colors = data_df['risk'].map({'Low': '#28c76f', 'Medium': '#4facfe', 'High': '#ff4b5c'})
        ax.scatter(data_df['sleep_hours'], data_df['burnout_score'],
                   c=scatter_colors, alpha=0.7, edgecolors=dark_bg, linewidths=0.5, s=60)
        ax.set_title('Sleep Hours vs Burnout Score')
        ax.set_xlabel('Sleep Hours')
        ax.set_ylabel('Burnout Score')
        plt.tight_layout()
        plt.savefig(os.path.join(plot_dir, 'sleep_vs_burnout.png'))
        plt.close('all')

    # 6. Burnout boxplot by risk
    if 'risk' in data_df.columns:
        fig, ax = _dark_fig()
        risk_groups = [data_df[data_df['risk'] == r]['burnout_score'].dropna() for r in ['Low', 'Medium', 'High']]
        bp = ax.boxplot(risk_groups, labels=['Low', 'Medium', 'High'], patch_artist=True)
        box_colors = ['#28c76f', '#4facfe', '#ff4b5c']
        for patch, color in zip(bp['boxes'], box_colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        for element in ['whiskers', 'caps', 'medians']:
            for item in bp[element]:
                item.set_color(text_col)
        ax.set_title('Burnout Score by Risk Tier')
        ax.set_xlabel('Risk Tier')
        ax.set_ylabel('Burnout Score')
        plt.tight_layout()
        plt.savefig(os.path.join(plot_dir, 'burnout_boxplot.png'))
        plt.close('all')

    # 7. Study vs Burnout scatter
    if 'study_hours' in data_df.columns:
        fig, ax = _dark_fig()
        ax.scatter(data_df['study_hours'], data_df['burnout_score'],
                   color='#7367f0', alpha=0.6, edgecolors=dark_bg, linewidths=0.5, s=60)
        ax.set_title('Study Hours vs Burnout Score')
        ax.set_xlabel('Study Hours')
        ax.set_ylabel('Burnout Score')
        plt.tight_layout()
        plt.savefig(os.path.join(plot_dir, 'study_vs_burnout.png'))
        plt.close('all')

    # 8. Stress vs Sleep scatter
    if 'stress_level' in data_df.columns and 'sleep_hours' in data_df.columns:
        fig, ax = _dark_fig()
        ax.scatter(data_df['stress_level'], data_df['sleep_hours'],
                   color='#ff9f43', alpha=0.6, edgecolors=dark_bg, linewidths=0.5, s=60)
        ax.set_title('Stress Level vs Sleep Hours')
        ax.set_xlabel('Stress Level')
        ax.set_ylabel('Sleep Hours')
        plt.tight_layout()
        plt.savefig(os.path.join(plot_dir, 'stress_vs_sleep.png'))
        plt.close('all')

    # 9. Sentiment distribution
    if 'sentiment_score' in data_df.columns:
        fig, ax = _dark_fig()
        ax.hist(data_df['sentiment_score'], bins=20, color='#28c76f', edgecolor=dark_bg, alpha=0.85)
        ax.set_title('Sentiment Score Distribution')
        ax.set_xlabel('VADER Compound Score (-1 to +1)')
        ax.set_ylabel('Number of Students')
        plt.tight_layout()
        plt.savefig(os.path.join(plot_dir, 'sentiment_dist.png'))
        plt.close('all')

    # 10. Sentiment vs Burnout scatter
    if 'sentiment_score' in data_df.columns:
        fig, ax = _dark_fig()
        ax.scatter(data_df['sentiment_score'], data_df['burnout_score'],
                   color='#ea5455', alpha=0.6, edgecolors=dark_bg, linewidths=0.5, s=60)
        ax.set_title('Sentiment Score vs Burnout Score')
        ax.set_xlabel('Sentiment Score')
        ax.set_ylabel('Burnout Score')
        plt.tight_layout()
        plt.savefig(os.path.join(plot_dir, 'sentiment_vs_burnout.png'))
        plt.close('all')

    # --- Auto-train model and compute eval metrics from current dataset ---
    _auto_train()


def _auto_train():
    """Train a RandomForest on the current data_df and store metrics in eval_metrics."""
    global data_df, eval_metrics
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import LabelEncoder
        from sklearn.metrics import (
            accuracy_score, precision_score, recall_score,
            f1_score, roc_auc_score, confusion_matrix, classification_report
        )

        feature_cols = [c for c in ['sleep_hours', 'study_hours', 'stress_level'] if c in data_df.columns]
        if 'risk' not in data_df.columns or len(feature_cols) < 2:
            eval_metrics = None
            return

        df_clean = data_df[feature_cols + ['risk']].dropna()
        if df_clean.empty or df_clean['risk'].nunique() < 2:
            eval_metrics = None
            return

        le = LabelEncoder()
        y = le.fit_transform(df_clean['risk'])
        X = df_clean[feature_cols].values
        class_names = le.classes_.tolist()

        # Need at least a handful of samples to be meaningful
        if len(y) < 10:
            eval_metrics = None
            return

        test_size = max(0.15, min(0.3, 20 / len(y)))  # adaptive: ~15-30%
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )

        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)

        cm = confusion_matrix(y_test, y_pred).tolist()
        report = classification_report(y_test, y_pred, target_names=class_names, output_dict=True)

        roc_auc = None
        try:
            if len(class_names) > 2:
                roc_auc = round(roc_auc_score(y_test, y_prob, multi_class='ovr'), 4)
        except Exception:
            pass

        eval_metrics = {
            'accuracy':  round(accuracy_score(y_test, y_pred), 4),
            'precision': round(precision_score(y_test, y_pred, average='weighted', zero_division=0), 4),
            'recall':    round(recall_score(y_test, y_pred, average='weighted', zero_division=0), 4),
            'f1':        round(f1_score(y_test, y_pred, average='weighted', zero_division=0), 4),
            'roc_auc':   roc_auc,
            'class_names': class_names,
            'n_test': len(y_test),
            'n_train': len(y_train),
            'n_total': len(y),
            'features': feature_cols,
            'report': report,
            'confusion_matrix': cm,
        }

        # Also save plot of confusion matrix to static/plots
        import seaborn as sns
        plot_dir = os.path.join(app.static_folder, 'plots')
        os.makedirs(plot_dir, exist_ok=True)
        dark_bg = '#0f1117'
        text_col = '#c9d1d9'
        fig, ax = plt.subplots(figsize=(6, 5), dpi=150)
        fig.patch.set_facecolor(dark_bg)
        ax.set_facecolor(dark_bg)
        sns.heatmap(
            confusion_matrix(y_test, y_pred),
            annot=True, fmt='d', cmap='Blues',
            xticklabels=class_names, yticklabels=class_names,
            ax=ax, linewidths=0.5
        )
        ax.set_title('Confusion Matrix', color=text_col)
        ax.tick_params(colors=text_col)
        ax.set_xlabel('Predicted', color=text_col)
        ax.set_ylabel('Actual', color=text_col)
        plt.tight_layout()
        plt.savefig(os.path.join(plot_dir, 'confusion_matrix.png'))
        plt.close('all')

    except Exception as e:
        print(f"[Auto-train error] {e}")
        eval_metrics = None

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
        'high_risk_count': int((data_df['risk'] == 'High').sum()),
        'pct_high_risk': round((data_df['risk'] == 'High').sum() / len(data_df) * 100, 1),
        'avg_sentiment': round(data_df['sentiment_score'].mean(), 2)
    }
    return render_template(
        'dashboard.html',
        data=data_df.to_dict('records'),
        columns=data_df.columns.tolist(),
        active_page='dashboard',
        **stats
    )


@app.route('/evaluate')
def evaluate():
    global eval_metrics
    if eval_metrics is None and data_df is None:
        return render_template(
            'evaluation.html',
            error="No dataset loaded yet. Upload a CSV from the Home page first.",
            active_page='evaluate'
        )
    if eval_metrics is None:
        # dataset is loaded but somehow metrics are missing — re-run
        _auto_train()
    if eval_metrics is None:
        return render_template(
            'evaluation.html',
            error="Could not train the model on this dataset. Check that it has valid numeric columns (sleep_hours, study_hours, stress_level).",
            active_page='evaluate'
        )
    return render_template('evaluation.html', metrics=eval_metrics, active_page='evaluate')


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
                            data_df.at[i, col] = (
                                pd.to_numeric(value, errors='coerce')
                                if pd.api.types.is_numeric_dtype(data_df[col]) else value
                            )
                    except:
                        pass

            process_data()
            os.makedirs('data', exist_ok=True)
            data_df.to_csv('data/updated_sample.csv', index=False)
        return redirect(url_for('dashboard'))
    return render_template(
        'edit.html',
        data=data_df.to_dict('records'),
        columns=data_df.columns.tolist(),
        data_length=len(data_df),
        active_page='dashboard'
    )


if __name__ == '__main__':
    app.run(debug=True)
