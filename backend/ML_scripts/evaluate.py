import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, classification_report,
    confusion_matrix
)

def evaluate_model(y_test, y_pred, y_prob=None, class_names=None):
    """
    Evaluate model performance using multiple metrics.
    """
    print("=" * 40)
    print("       MODEL EVALUATION RESULTS")
    print("=" * 40)
    print(f"Accuracy  : {accuracy_score(y_test, y_pred):.4f}")
    print(f"Precision : {precision_score(y_test, y_pred, average='weighted'):.4f}")
    print(f"Recall    : {recall_score(y_test, y_pred, average='weighted'):.4f}")
    print(f"F1 Score  : {f1_score(y_test, y_pred, average='weighted'):.4f}")
    
    if y_prob is not None:
        print(f"ROC-AUC   : {roc_auc_score(y_test, y_prob, multi_class='ovr'):.4f}")
    
    print("\nDetailed Classification Report:")
    print(classification_report(y_test, y_pred, target_names=class_names))
    
    # Plot Confusion Matrix
    plot_confusion_matrix(y_test, y_pred, class_names)


def plot_confusion_matrix(y_test, y_pred, class_names=None):
    """
    Plot and save the confusion matrix.
    """
    cm = confusion_matrix(y_test, y_pred)
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(
        cm, annot=True, fmt='d', cmap='Blues',
        xticklabels=class_names if class_names else "auto",
        yticklabels=class_names if class_names else "auto"
    )
    plt.title('Confusion Matrix', fontsize=14, fontweight='bold')
    plt.ylabel('Actual Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plot_path = '../static/plots/confusion_matrix.png'
    os.makedirs(os.path.dirname(plot_path), exist_ok=True)
    plt.savefig(plot_path, dpi=150)
    plt.show()
    print(f"Confusion matrix saved as {plot_path}")


# --- Run evaluation ---
if __name__ == "__main__":
    import pickle
    import os
    
    model_dir = '../models'
    model_path = os.path.join(model_dir, 'model.pkl')
    data_path = os.path.join(model_dir, 'eval_data.pkl')
    
    # Check if model exists
    if not os.path.exists(model_path) or not os.path.exists(data_path):
        print(f"Error: {model_path} or {data_path} not found. Run train_model.py first.")
    else:
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        
        with open(data_path, 'rb') as f:
            eval_data = pickle.load(f)
            
        X_test = eval_data['X_test']
        y_test = eval_data['y_test']
        class_names = eval_data['class_names']
        
        y_pred = model.predict(X_test)
        
        # Check if model has predict_proba for ROC-AUC
        y_prob = None
        if hasattr(model, 'predict_proba'):
            y_prob = model.predict_proba(X_test)
        
        evaluate_model(y_test, y_pred, y_prob, class_names)