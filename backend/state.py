"""
state.py — Shared in-memory application state.

All route Blueprints import from here so that a single copy of each variable
is maintained across the entire app.
"""

import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

def get_sia():
    global sia
    if sia is None:
        try:
            nltk.data.find('sentiment/vader_lexicon.zip')
        except LookupError:
            nltk.download('vader_lexicon', quiet=True)
        sia = SentimentIntensityAnalyzer()
    return sia

# Shared sentiment analyser instance
sia = None

# Primary uploaded dataset
data_df = None
corr_matrix = None

# Comparison dataset
compare_df = None
compare_meta = None

# ML evaluation metrics keyed by dataset name
eval_metrics = {'primary': None, 'compare': None}
