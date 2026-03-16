# Code Explanation for MindSpace Project

This document provides a comprehensive explanation of the technical architecture of MindSpace, a Flask-based analytics platform for student burnout. It covers the data processing pipeline, the machine learning integration, and the multi-dataset comparison logic.

## 1. Project Overview

MindSpace is designed to bridge the gap between categorical student metrics (sleep, study, stress) and qualitative well-being (feedback sentiment). The system processes data through four primary lenses:
1.  **Algorithmic Scoring**: Deterministic burnout score calculation.
2.  **Sentiment Analysis**: NLP-based emotion detection in feedback.
3.  **Predictive Modeling**: Supervised learning to identify risk patterns.
4.  **Comparative Analytics**: Side-by-side cohort delta analysis.

## 2. Core Libraries

### Flask (Web Framework)
Flask manages the application lifecycle, routing, and session state. Key implementations include:
- **Jinja2 Templating**: Utilizes template inheritance (`base.html`) for a unified sidebar and theme-toggle experience.
- **Session Handling**: Re-uses `flask.session` to track upload history and metadata without requiring a permanent database.
- **Dynamic Routing**: Maps complex logic for `/dashboard`, `/evaluate`, `/compare`, and `/results`.

### Scikit-Learn (Machine Learning)
The platform features an automated ML pipeline:
- **Random Forest Classifier**: Chosen for its robustness against small datasets and ability to handle non-linear relationships between stress and sleep.
- **Auto-Training**: The `_auto_train()` function triggers on every data change, ensuring the models in the `models/` directory are always synchronized with the visible data.
- **Performance Metrics**: Calculates Accuracy, F1-Score, Precision, and Recall using `sklearn.metrics`, providing a "Deployment Readiness" verdict based on F1-thresholds.

### NLTK (VADER Sentiment)
- **SentimentIntensityAnalyzer**: Processes raw text feedback to produce a "compound score" (-1 to +1).
- **Integration**: These scores are used to identify "Maskers"—students whose numeric metrics look healthy but whose language suggests high distress.

### Pandas & NumPy
- **Fuzzy Column Mapping**: A robust mapping system handles variations in CSV headers (e.g., "sleep_hours" vs "Sleep Hours"), making the app resilient to different data sources.
- **Data Vectorization**: Used for rapid calculation of the Burnout Score across thousands of rows simultaneously.

## 3. The Analytics Pipeline

### Burnout Calculation
The burnout score is calculated as a weighted ratio:
`Score = (Study Hours / Sleep Hours) * Stress Level * 10`
The result is clamped between 0 and 100 to ensure visualization stability.

### The Dashboard
The dashboard uses **Matplotlib (Agg backend)** and **Seaborn** to generate 10 distinct plots:
- **Histograms**: Score distribution.
- **Boxplots**: Comparison of score variance by risk tier.
- **Heatmaps**: Feature correlation.
- **Scatter Plots**: Sentiment vs. Burnout relationships.

### Comparison Logic
The `/compare` module handles two concurrent DataFrames. It syncs them by calculating shared metrics and generating "Delta" badges (e.g., +15% burnout) to highlight differences between two cohorts or time periods.

## 4. Folder Structure & Organization

- `app.py`: The central logic hub containing routes and data processing.
- `static/css/styles.css`: A comprehensive design system supporting Glassmorphism and Dark/Light modes.
- `templates/`: Modular HTML components that separate data-display logic from layout.
- `models/`: Persistent storage for trained ML weights (`.pkl` files).
- `scripts/`: Independent versions of the ML logic for command-line research.

## 5. UI/UX Philosophy

MindSpace prioritizes "Premium Aesthetics":
- **Glassmorphism**: Uses `backdrop-filter: blur` and translucent backgrounds for a state-of-the-art feel.
- **Micro-interactions**: Hover effects on cards, floating action buttons (FABs), and smooth accordion transitions.
- **Visual Synthesis**: Plain-English "Key Takeaways" accompany every chart to ensure findings are accessible to non-technical users.
