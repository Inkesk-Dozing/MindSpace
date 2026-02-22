# 🧠 MindSpace: Student Burnout Analytics

MindSpace is a comprehensive data analytics platform designed to help educators and students understand mental health patterns, burnout risks, and sentiment trends. By analyzing study habits, sleep patterns, and subjective feedback, MindSpace provides actionable insights via an intuitive web dashboard.

## 🚀 Features

- **Data-Driven Insights:** Automatically calculates a "Burnout Score" based on study-to-sleep ratios and stress levels.
- **Sentiment Analysis:** Utilizes Natural Language Processing (VADER Sentiment) to analyze text feedback and gauge student sentiment.
- **Risk Classification:** Categories students into 'Low', 'Medium', and 'High' risk tiers for proactive intervention.
- **Interactive Dashboard:** Visualizes data through distribution histograms and risk category pie charts.
- **Dynamic Dataset Management:** Upload CSV files and edit data directly through the web interface with real-time recalculations.

## 🛠️ Tech Stack

- **Backend:** Python, Flask
- **Data Processing:** Pandas, NumPy
- **NLP:** NLTK (SentimentIntensityAnalyzer)
- **Visualization:** Matplotlib
- **Frontend:** HTML5, CSS3 (Vanilla)

## 📦 Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd MindSpace
    ```

2.  **Install dependencies:**
    It is recommended to use a virtual environment.
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the application:**
    ```bash
    python app.py
    ```

4.  **Access the dashboard:**
    Open your browser and navigate to `http://127.0.0.1:5000`.

## 📊 Data Requirements

The application expects a CSV file with the following columns:

| Column Name | Description | Example Value |
| :--- | :--- | :--- |
| `sleep_hours` | Average nightly sleep hours | `7` |
| `study_hours` | Daily study hours | `5` |
| `stress_level` | Stress rating on a scale of 1-10 | `6` |
| `feedback` | Qualitative text comments | `Feeling a bit overwhelmed.` |

## 📁 Project Structure

```text
MindSpace/
├── app.py              # Flask application & processing logic
├── requirements.txt    # Project dependencies
├── templates/          # HTML templates (index, dashboard, edit)
├── static/             # CSS styles and generated plots
│   └── styles.css      # Core styles
├── data/               # Sample and test datasets
│   ├── sample_data.csv
│   └── test_data.csv
├── README.md           # Project documentation
├── SECURITY.md         # Security policy
└── CODE_OF_CONDUCT.md  # Community standards
```

## 🛡️ License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
