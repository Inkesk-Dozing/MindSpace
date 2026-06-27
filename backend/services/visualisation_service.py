import os
import matplotlib.pyplot as plt
import numpy as np

def _generate_compare_plots(stats_a, stats_b, label_a, label_b, plot_dir):
    os.makedirs(plot_dir, exist_ok=True)

    dark_bg  = '#0f1117'
    text_col = '#c9d1d9'
    grid_col = '#30363d'
    col_a    = '#4facfe'
    col_b    = '#ff9f43'

    def _ax(fig, ax):
        fig.patch.set_facecolor(dark_bg)
        ax.set_facecolor(dark_bg)
        ax.tick_params(colors=text_col, labelsize=9)
        for sp in ax.spines.values():
            sp.set_edgecolor(grid_col)
        ax.yaxis.label.set_color(text_col)
        ax.xaxis.label.set_color(text_col)
        ax.title.set_color(text_col)
        ax.grid(True, color=grid_col, linestyle='--', linewidth=0.5, alpha=0.6)

    df_a = stats_a['_df']
    df_b = stats_b['_df']

    # 1. Overlaid burnout histograms
    fig, ax = plt.subplots(figsize=(8, 4), dpi=150)
    _ax(fig, ax)
    ax.hist(df_a['burnout_score'], bins=20, color=col_a, alpha=0.6, edgecolor='none', label=label_a)
    ax.hist(df_b['burnout_score'], bins=20, color=col_b, alpha=0.6, edgecolor='none', label=label_b)
    ax.legend(facecolor=dark_bg, labelcolor=text_col, edgecolor=grid_col)
    ax.set_title('Burnout Score Distribution — Overlay')
    ax.set_xlabel('Burnout Score')
    ax.set_ylabel('Students')
    plt.tight_layout()
    plt.savefig(os.path.join(plot_dir, 'cmp_burnout_hist.png'))
    plt.close('all')

    # 2. Risk breakdown side-by-side bar
    fig, ax = plt.subplots(figsize=(7, 4), dpi=150)
    _ax(fig, ax)
    cats = ['Low', 'Medium', 'High']
    va = [stats_a['low_risk'], stats_a['medium_risk'], stats_a['high_risk']]
    vb = [stats_b['low_risk'], stats_b['medium_risk'], stats_b['high_risk']]
    x = np.arange(len(cats))
    w = 0.35
    ax.bar(x - w/2, va, w, color=col_a, alpha=0.85, label=label_a, edgecolor='none')
    ax.bar(x + w/2, vb, w, color=col_b, alpha=0.85, label=label_b, edgecolor='none')
    ax.set_xticks(x)
    ax.set_xticklabels(cats)
    ax.legend(facecolor=dark_bg, labelcolor=text_col, edgecolor=grid_col)
    ax.set_title('Risk Tier Count Comparison')
    ax.set_ylabel('Number of Students')
    plt.tight_layout()
    plt.savefig(os.path.join(plot_dir, 'cmp_risk_bar.png'))
    plt.close('all')

    # 3. Feature averages radar-style bar
    feature_labels = ['Avg Sleep\n(hrs)', 'Avg Study\n(hrs)', 'Avg Stress\n(/10)', 'Avg Burnout\n(/100)']
    scale = [10, 10, 10, 100]   
    def _safe(v, s): return (v or 0) / s
    raw_a = [stats_a['avg_sleep'], stats_a['avg_study'], stats_a['avg_stress'], stats_a['avg_burnout']]
    raw_b = [stats_b['avg_sleep'], stats_b['avg_study'], stats_b['avg_stress'], stats_b['avg_burnout']]
    na = [_safe(v, s) for v, s in zip(raw_a, scale)]
    nb = [_safe(v, s) for v, s in zip(raw_b, scale)]
    fig, ax = plt.subplots(figsize=(8, 4), dpi=150)
    _ax(fig, ax)
    xf = np.arange(len(feature_labels))
    ax.bar(xf - w/2, na, w, color=col_a, alpha=0.85, label=label_a, edgecolor='none')
    ax.bar(xf + w/2, nb, w, color=col_b, alpha=0.85, label=label_b, edgecolor='none')
    for xi, (a, b, ra, rb) in enumerate(zip(na, nb, raw_a, raw_b)):
        ax.text(xi - w/2, a + 0.01, f'{ra or 0:.1f}', ha='center', va='bottom', fontsize=7, color=col_a)
        ax.text(xi + w/2, b + 0.01, f'{rb or 0:.1f}', ha='center', va='bottom', fontsize=7, color=col_b)
    ax.set_xticks(xf)
    ax.set_xticklabels(feature_labels)
    ax.set_ylabel('Normalised Value (0–1)')
    ax.set_ylim(0, 1.2)
    ax.legend(facecolor=dark_bg, labelcolor=text_col, edgecolor=grid_col)
    ax.set_title('Key Feature Averages — Scaled Comparison')
    plt.tight_layout()
    plt.savefig(os.path.join(plot_dir, 'cmp_features.png'))
    plt.close('all')

    # 4. Burnout score boxplots side by side
    fig, ax = plt.subplots(figsize=(6, 4), dpi=150)
    _ax(fig, ax)
    bp = ax.boxplot(
        [df_a['burnout_score'].dropna(), df_b['burnout_score'].dropna()],
        tick_labels=[label_a, label_b], patch_artist=True,
        medianprops={'color': '#fff', 'linewidth': 2}
    )
    for patch, color in zip(bp['boxes'], [col_a, col_b]):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    for element in ['whiskers', 'caps']:
        for item in bp[element]:
            item.set_color(text_col)
    ax.set_title('Burnout Score Spread — Side by Side')
    ax.set_ylabel('Burnout Score')
    plt.tight_layout()
    plt.savefig(os.path.join(plot_dir, 'cmp_boxplot.png'))
    plt.close('all')

    # 5. Sentiment distribution overlay
    if 'sentiment_score' in df_a.columns and 'sentiment_score' in df_b.columns:
        fig, ax = plt.subplots(figsize=(8, 4), dpi=150)
        _ax(fig, ax)
        ax.hist(df_a['sentiment_score'], bins=15, color=col_a, alpha=0.6, edgecolor='none', label=label_a)
        ax.hist(df_b['sentiment_score'], bins=15, color=col_b, alpha=0.6, edgecolor='none', label=label_b)
        ax.axvline(0, color=text_col, linestyle='--', linewidth=0.8, alpha=0.6)
        ax.legend(facecolor=dark_bg, labelcolor=text_col, edgecolor=grid_col)
        ax.set_title('Sentiment Score Distribution — Overlay')
        ax.set_xlabel('VADER Compound Score')
        ax.set_ylabel('Students')
        plt.tight_layout()
        plt.savefig(os.path.join(plot_dir, 'cmp_sentiment.png'))
        plt.close('all')
