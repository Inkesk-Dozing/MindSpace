from flask import url_for

# Helper to generate full URLs for static files
def get_static_url(filename):
    return url_for(
        'static',
        filename=f'plots/{filename}',
        _external=True
    )
    