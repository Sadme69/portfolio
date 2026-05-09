"""
Portfolio Backend Server
========================
Run:  python server.py
Open: http://localhost:5000

Change DEV_PASSWORD below before sharing the site.
Images are stored in the ./renders/ folder next to this file.
"""

import os
import json
from flask import Flask, request, jsonify, send_from_directory, send_file
from werkzeug.utils import secure_filename

# ── CONFIG ─────────────────────────────────────────────────────────────────
DEV_PASSWORD   = 'runner2026'          # ← CHANGE THIS
RENDERS_DIR    = 'renders'             # folder where images are stored
PORT           = 5000
ALLOWED_EXT    = {'jpg','jpeg','png','webp','gif','bmp','avif'}
MAX_FILE_MB    = 50                    # max upload size per file
# ───────────────────────────────────────────────────────────────────────────

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_MB * 1024 * 1024

os.makedirs(RENDERS_DIR, exist_ok=True)

def allowed(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

def check_password(req):
    """Check password from form data, JSON body, or header."""
    pwd = (
        req.form.get('password') or
        (req.get_json(silent=True) or {}).get('password') or
        req.headers.get('X-Dev-Password', '')
    )
    return pwd == DEV_PASSWORD


# ── ROUTES ──────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_file('portfolio.html')

@app.route('/api/images')
def get_images():
    """Return list of all images in the renders folder."""
    files = []
    for fname in sorted(os.listdir(RENDERS_DIR)):
        if not allowed(fname):
            continue
        fpath = os.path.join(RENDERS_DIR, fname)
        files.append({
            'filename': fname,
            'url':      f'/renders/{fname}',
            'size':     os.path.getsize(fpath),
        })
    return jsonify(files)

@app.route('/api/upload', methods=['POST'])
def upload():
    """Upload one or more images. Requires dev password."""
    if not check_password(request):
        return jsonify({'error': 'Wrong password'}), 401

    if 'files' not in request.files:
        return jsonify({'error': 'No files sent'}), 400

    uploaded = []
    skipped  = []
    for f in request.files.getlist('files'):
        if not f or not f.filename:
            continue
        if not allowed(f.filename):
            skipped.append(f.filename)
            continue
        fname = secure_filename(f.filename)
        f.save(os.path.join(RENDERS_DIR, fname))
        uploaded.append(fname)

    return jsonify({'uploaded': uploaded, 'skipped': skipped})

@app.route('/api/delete', methods=['POST'])
def delete():
    """Delete an image by filename. Requires dev password."""
    data = request.get_json(silent=True) or {}
    pwd  = data.get('password') or request.form.get('password', '')
    if pwd != DEV_PASSWORD:
        return jsonify({'error': 'Wrong password'}), 401

    fname = os.path.basename(data.get('filename', ''))
    if not fname:
        return jsonify({'error': 'No filename'}), 400

    fpath = os.path.join(RENDERS_DIR, fname)
    if not os.path.exists(fpath):
        return jsonify({'error': 'File not found'}), 404

    os.remove(fpath)
    return jsonify({'deleted': fname})

@app.route('/renders/<path:filename>')
def serve_render(filename):
    """Serve image files from the renders folder."""
    return send_from_directory(RENDERS_DIR, filename)


# ── START ────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print('='*52)
    print('  PORTFOLIO SERVER')
    print(f'  Open: http://localhost:{PORT}')
    print(f'  Images folder: {os.path.abspath(RENDERS_DIR)}')
    print('='*52)
    port = int(os.environ.get('PORT', PORT))
    app.run(host='0.0.0.0', port=port, debug=False)
