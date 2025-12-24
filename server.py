from flask import Flask, render_template_string, send_from_directory
import os

app = Flask(__name__)
DOWNLOAD_FOLDER = './downloads'

TEMPLATE = """
<!doctype html>
<html lang="ja">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Downloader UI</title>
    <style>
        body { font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f4f4f9; }
        h1 { color: #333; border-bottom: 2px solid #ddd; padding-bottom: 10px; }
        .card { background: white; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .list-group { list-style: none; padding: 0; margin: 0; }
        .list-item { padding: 15px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
        .btn { background-color: #28a745; color: white; padding: 8px 16px; text-decoration: none; border-radius: 5px; }
        .btn:hover { background-color: #218838; }
    </style>
</head>
<body>
    <h1>📂 ダウンロード済みファイル</h1>
    <div class="card">
        <ul class="list-group">
            {% for file in files %}
            <li class="list-item">
                <span style="font-weight:bold;">{{ file.name }}</span>
                <div style="display:flex; gap:15px; align-items:center;">
                    <span style="color:#666; font-size:0.9em;">{{ file.size }}</span>
                    <a href="/download/{{ file.name }}" class="btn">⬇ ダウンロード</a>
                </div>
            </li>
            {% else %}
            <li class="list-item" style="justify-content:center; color:#888;">ファイルはありません</li>
            {% endfor %}
        </ul>
    </div>
</body>
</html>
"""

def get_readable_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024: return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"

@app.route('/')
def index():
    if not os.path.exists(DOWNLOAD_FOLDER): os.makedirs(DOWNLOAD_FOLDER)
    files = []
    try:
        for f in os.listdir(DOWNLOAD_FOLDER):
            fp = os.path.join(DOWNLOAD_FOLDER, f)
            if os.path.isfile(fp):
                files.append({'name': f, 'size': get_readable_size(os.path.getsize(fp))})
    except: pass
    return render_template_string(TEMPLATE, files=files)

@app.route('/download/<path:filename>')
def download_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    print("Web UI起動: 右下のポップアップからブラウザを開いてください")
    app.run(host='0.0.0.0', port=8080)
