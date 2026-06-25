import os
from flask import Blueprint, request, jsonify, current_app
import pandas as pd
import state
from services.data_processing_service import process_data
from services.ml_service import _auto_train

edit_bp = Blueprint('edit', __name__)

@edit_bp.route('/api/edit', methods=['POST'])
def edit():
    if state.data_df is None:
        return jsonify({'error': 'No dataset loaded'}), 400

    req_data = request.json
    if not req_data:
        return jsonify({'error': 'No data provided'}), 400

    # Expecting: { "updates": [ { "row": 0, "col": "sleep_hours", "value": 8 }, ... ] }
    updates = req_data.get('updates', [])
    for update in updates:
        row = int(update['row'])
        col = update['col']
        value = update['value']

        if row >= len(state.data_df):
            new_rows = row - len(state.data_df) + 1
            new_df = pd.DataFrame(
                index=range(len(state.data_df), len(state.data_df) + new_rows),
                columns=state.data_df.columns
            )
            state.data_df = pd.concat([state.data_df, new_df], ignore_index=False)

        try:
            if col in state.data_df.columns:
                state.data_df.at[row, col] = (
                    pd.to_numeric(value, errors='coerce')
                    if pd.api.types.is_numeric_dtype(state.data_df[col]) else value
                )
        except Exception as e:
            print(f"Error updating row {row} col {col}: {e}")

    plot_dir = os.path.join(current_app.static_folder, 'plots')
    state.data_df, state.corr_matrix = process_data(state.data_df, plot_dir, state.get_sia())

    metrics = _auto_train(state.data_df, plot_dir, 'primary')
    if metrics:
        state.eval_metrics['primary'] = metrics

    os.makedirs('data', exist_ok=True)
    state.data_df.to_csv('data/updated_sample.csv', index=False)

    return jsonify({'success': True, 'message': 'Dataset updated successfully.'})
