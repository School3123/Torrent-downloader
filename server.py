from flask import Flask, render_template_string, send_from_directory, send_file, redirect, url_for, abort
import os
import shutil

app = Flask(__name__)

# ---------------------------------------------------------
# 設定
# ---------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_FOLDER = os.path.join(BASE_DIR, 'downloads')

app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER

# HTMLテンプレート
TEMPLATE = """
<!doctype html>
<html lang="ja">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Codespaces File Manager</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f0f2f5; padding-top: 20px; font-family: 'Segoe UI', sans-serif; }
        .container { max-width: 900px; }
        .card { border: none; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
        .card-header { background: white; border-bottom: 1px solid #eee; padding: 20px; border-radius: 12px 12px 0 0 !important; }
        .path-info { font-size: 0.8em; color: #888; font-family: monospace; background: #eee; padding: 4px 8px; border-radius: 4px; }
        .file-item { transition: background 0.2s; }
        .file-item:hover { background-color: #f8f9fa; }
        .btn-dl { background-color: #0d6efd; color: white; border: none; font-weight: 500; }
        .btn-dl:hover { background-color: #0b5ed7; color: white; }
        .btn-zip { background-color: #ffc107; color: #000; border: none; font-weight: 500; }
        .btn-zip:hover { background-color: #e0a800; }
        .btn-del { color: #dc3545; background: #fff0f1; border: none; }
        .btn-del:hover { background-color: #ffdde0; color: #c82333; }
    </style>
</head>
<body>
<div class="container">
    <div class="card mb-4">
        <div class="card-header d-flex justify-content-between align-items-center">
            <div>
                <h4 class="mb-1 fw-bold text-dark">📂 ダウンロード管理</h4>
                <div class="path-info">{{ folder_path }}</div>
            </div>
            <a href="/" class="btn btn-outline-secondary btn-sm">🔄 リロード</a>
        </div>
        
        <div class="card-body">
            <!-- ディスク容量 -->
            <div class="progress mb-2" style="height: 10px;">
                <div class="progress-bar bg-success" role="progressbar" style="width: {{ usage_percent }}%"></div>
            </div>
            <div class="d-flex justify-content-between text-muted small mb-4">
                <span>使用量: {{ used_space }}</span>
                <span>残り: <strong>{{ free_space }}</strong></span>
            </div>

            <!-- ファイルリスト -->
            {% if files %}
            <div class="list-group list-group-flush border-top">
                {% for file in files %}
                <div class="list-group-item file-item d-flex justify-content-between align-items-center py-3">
                    <div class="text-truncate me-3">
                        <div class="fw-bold text-dark">
                            {% if file.is_dir %}📁 {% else %}📄 {% endif %}
                            {{ file.name }}
                        </div>
                        <div class="small text-muted">{{ file.size }}</div>
                    </div>
                    <div class="d-flex gap-2">
                        {% if not file.is_dir %}
                        <a href="/download/{{ file.name }}" class="btn btn-dl btn-sm px-3 shadow-sm">
                            ⬇ 保存
                        </a>
                        {% else %}
                        <a href="/download/{{ file.name }}" class="btn btn-zip btn-sm px-3 shadow-sm">
                            📦 ZIPで保存
                        </a>
                        {% endif %}
                        <a href="/delete/{{ file.name }}" class="btn btn-del btn-sm px-3" onclick="return confirm('本当に「{{ file.name }}」を削除しますか？');">
                            🗑
                        </a>
                    </div>
                </div>
                {% endfor %}
            </div>
            {% else %}
            <div class="text-center py-5">
                <p class="text-muted mb-0">ファイルが見つかりません</p>
                <small class="text-muted">downloader.py でファイルをダウンロードしてください</small>
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
        try: os.makedirs(DOWNLOAD_FOLDER)
        except: pass

    try:
        total, used, free = shutil.disk_usage(DOWNLOAD_FOLDER)
        usage_percent = (used / total) * 100
        free_readable = get_readable_size(free)
        used_readable = get_readable_size(used)
    except:
        usage_percent = 0; free_readable = "不明"; used_readable = "不明"

    files = []
    try:
        with os.scandir(DOWNLOAD_FOLDER) as entries:
            for entry in entries:
                if not entry.name.startswith('.'):
                    size_str = "フォルダ"
                    is_dir = True
                    if entry.is_file():
                        size_str = get_readable_size(entry.stat().st_size)
                        is_dir = False
                    
                    files.append({
                        'name': entry.name,
                        'size': size_str,
                        'is_dir': is_dir
                    })
        files = sorted(files, key=lambda x: x['name'])
    except Exception as e:
        print(f"Error: {e}")

    return render_template_string(TEMPLATE, files=files, folder_path=DOWNLOAD_FOLDER, free_space=free_readable, used_space=used_readable, usage_percent=usage_percent)

@app.route('/download/<path:filename>')
def download_file(filename):
    """ファイルならそのまま、フォルダならZIPにしてダウンロード"""
    target_path = os.path.join(DOWNLOAD_FOLDER, filename)
    
    if not os.path.exists(target_path):
        return abort(404)

    # フォルダの場合の処理
    if os.path.isdir(target_path):
        try:
            # /tmp フォルダにZIPを作成 (ファイル名: フォルダ名.zip)
            # shutil.make_archive は拡張子(.zip)を自動でつけるので、base_nameには拡張子を含めない
            zip_base_name = os.path.join('/tmp', filename)
            
            # ZIP作成実行
            shutil.make_archive(zip_base_name, 'zip', target_path)
            
            # 作成されたZIPファイルを送信
            return send_file(zip_base_name + '.zip', as_attachment=True)
        except Exception as e:
            return f"ZIP作成エラー: {e}", 500

    # 通常ファイルの場合の処理
    else:
        return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

@app.route('/delete/<path:filename>')
def delete_file(filename):
    target_path = os.path.join(DOWNLOAD_FOLDER, filename)
    try:
        if os.path.commonpath([target_path, DOWNLOAD_FOLDER]) != DOWNLOAD_FOLDER:
            return "不正なパスです", 403
        if os.path.exists(target_path):
            if os.path.isfile(target_path):
                os.remove(target_path)
            elif os.path.isdir(target_path):
                shutil.rmtree(target_path)
    except Exception as e:
        return f"削除エラー: {e}"
    return redirect(url_for('index'))

if __name__ == '__main__':
    print(f"🚀 サーバー起動: {DOWNLOAD_FOLDER}")
    app.run(host='0.0.0.0', port=8080)
