import os
from datetime import datetime
from flask import Blueprint, request, jsonify, session, current_app
import pandas as pd
import state
from services.data_processing_service import process_data
from services.ml_service import _auto_train

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/api/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and file.filename.endswith('.csv'):
        try:
            state.data_df = pd.read_csv(file)

            history = session.get('history', [])
            new_entry = {
                'filename': file.filename,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'records': len(state.data_df)
            }
            history.insert(0, new_entry)
            session['history'] = history[:10]
            session.modified = True

            plot_dir = os.path.join(current_app.static_folder, 'plots')
            state.data_df, state.corr_matrix = process_data(state.data_df, plot_dir, state.get_sia())

            metrics = _auto_train(state.data_df, plot_dir, 'primary')
            if metrics:
                state.eval_metrics['primary'] = metrics

            os.makedirs('data', exist_ok=True)
            state.data_df.to_csv('data/updated_sample.csv', index=False)

            return jsonify({
                'success': True,
                'message': f"Successfully uploaded {file.filename}.",
                'records': len(state.data_df)
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'Invalid file format'}), 400
