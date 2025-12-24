from flask import Flask, render_template_string, send_from_directory, redirect, url_for
import os
import shutil

app = Flask(__name__)
DOWNLOAD_FOLDER = './downloads'

# デザイン：Bootstrap CDNを使用して見やすく
TEMPLATE = """
<!doctype html>
<html lang="ja">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Codespaces Downloader</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; padding-top: 20px; }
        .card { box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    </style>
</head>
<body>
<div class="container">
    <div class="card">
        <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
            <h4 class="mb-0">📂 ダウンロード済みファイル</h4>
            <a href="/" class="btn btn-sm btn-light">更新</a>
        </div>
        <div class="card-body">
            <div class="text-end text-muted mb-3">
                ディスク残り容量: <strong>{{ free_space }}</strong>
            </div>

            {% if files %}
            <div class="list-group">
                {% for file in files %}
                <div class="list-group-item d-flex justify-content-between align-items-center">
                    <div class="text-truncate me-3">
                        <span class="fw-bold">{{ file.name }}</span>
                        <br>
                        <small class="text-muted">{{ file.size }}</small>
                    </div>
                    <div class="d-flex gap-2">
                        <a href="/download/{{ file.name }}" class="btn btn-success btn-sm text-nowrap">
                            ⬇ 保存
                        </a>
                        <a href="/delete/{{ file.name }}" class="btn btn-outline-danger btn-sm text-nowrap" onclick="return confirm('削除しますか？');">
                            🗑 削除
                        </a>
                    </div>
                </div>
                {% endfor %}
            </div>
            {% else %}
            <div class="alert alert-secondary text-center">
                ファイルはありません。<br>
                <code>downloader.py</code> を実行してください。
            </div>
            {% endif %}
        </div>
    </div>
</div>
</body>
</html>
"""

def get_readable_size(size_in_bytes):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024
    return f"{size_in_bytes:.2f} TB"

@app.route('/')
def index():
    if not os.path.exists(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER)
    
    # ディスク容量チェック
    total, used, free = shutil.disk_usage(DOWNLOAD_FOLDER)
    
    files = []
    try:
        file_list = os.listdir(DOWNLOAD_FOLDER)
        file_list.sort()
        for filename in file_list:
            filepath = os.path.join(DOWNLOAD_FOLDER, filename)
            if os.path.isfile(filepath):
                size = os.path.getsize(filepath)
                files.append({
                    'name': filename,
                    'size': get_readable_size(size)
                })
    except Exception as e:
        return f"エラー: {e}"

    return render_template_string(TEMPLATE, files=files, free_space=get_readable_size(free))

@app.route('/download/<path:filename>')
def download_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

@app.route('/delete/<path:filename>')
def delete_file(filename):
    """ファイル削除機能"""
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except: pass
    return redirect(url_for('index'))

if __name__ == '__main__':
    print("🚀 Web UI起動: 右下のポップアップからブラウザを開いてください")
    app.run(host='0.0.0.0', port=8080)
