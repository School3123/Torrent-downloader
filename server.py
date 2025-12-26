from flask import Flask, render_template_string, send_from_directory, send_file, redirect, url_for, abort, request
import os
import shutil

app = Flask(__name__)

# ---------------------------------------------------------
# 設定
# ---------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_FOLDER = os.path.join(BASE_DIR, 'downloads')

app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER

# HTMLテンプレート (階層移動対応版)
TEMPLATE = """
<!doctype html>
<html lang="ja">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>File Browser</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">
    <style>
        body { background-color: #f8f9fa; padding-top: 20px; font-family: 'Segoe UI', sans-serif; }
        .container { max-width: 1000px; }
        .card { border: none; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }
        .card-header { background: white; border-bottom: 1px solid #eee; padding: 15px 20px; border-radius: 12px 12px 0 0 !important; }
        .breadcrumb { margin-bottom: 0; font-size: 0.9rem; background: #e9ecef; padding: 8px 15px; border-radius: 6px; }
        .file-row { transition: background 0.15s; cursor: pointer; }
        .file-row:hover { background-color: #f1f3f5; }
        .icon-area { width: 40px; text-align: center; font-size: 1.2rem; color: #555; }
        .folder-link { text-decoration: none; color: #212529; font-weight: 600; display: block; width: 100%; }
        .folder-link:hover { color: #0d6efd; }
        .btn-action { padding: 4px 10px; font-size: 0.85rem; }
    </style>
</head>
<body>
<div class="container">
    <div class="card mb-4">
        <div class="card-header">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h4 class="mb-0 fw-bold"><i class="bi bi-hdd-network"></i> ファイルマネージャー</h4>
                <div class="text-muted small">
                    使用量: {{ used_space }} / 残り: {{ free_space }}
                </div>
            </div>
            
            <!-- パンくずリスト (現在のパス表示) -->
            <nav aria-label="breadcrumb">
                <ol class="breadcrumb">
                    <li class="breadcrumb-item"><a href="/">Home</a></li>
                    {% for part in path_parts %}
                        <li class="breadcrumb-item active">{{ part }}</li>
                    {% endfor %}
                </ol>
            </nav>
        </div>
        
        <div class="card-body p-0">
            <div class="list-group list-group-flush">
                
                <!-- 上の階層へ戻るボタン -->
                {% if current_path != '' %}
                <div class="list-group-item list-group-item-action bg-light">
                    <a href="/browse/{{ parent_path }}" class="text-decoration-none text-secondary d-flex align-items-center">
                        <div class="icon-area"><i class="bi bi-arrow-return-left"></i></div>
                        <div>上の階層へ戻る</div>
                    </a>
                </div>
                {% endif %}

                <!-- ファイル・フォルダ一覧 -->
                {% if files %}
                    {% for file in files %}
                    <div class="list-group-item file-row d-flex justify-content-between align-items-center">
                        <div class="d-flex align-items-center flex-grow-1 overflow-hidden">
                            <div class="icon-area">
                                {% if file.is_dir %}
                                    <i class="bi bi-folder-fill text-warning"></i>
                                {% else %}
                                    <i class="bi bi-file-earmark-text"></i>
                                {% endif %}
                            </div>
                            
                            <div class="text-truncate">
                                {% if file.is_dir %}
                                    <!-- フォルダなら中に入るリンク -->
                                    <a href="/browse/{{ file.rel_path }}" class="folder-link">{{ file.name }}</a>
                                {% else %}
                                    <!-- ファイルならダウンロードリンク -->
                                    <span class="fw-normal">{{ file.name }}</span>
                                {% endif %}
                                <div class="text-muted small" style="font-size: 0.75rem;">{{ file.size }}</div>
                            </div>
                        </div>

                        <div class="d-flex gap-2 ms-3">
                            {% if file.is_dir %}
                                <a href="/download/{{ file.rel_path }}" class="btn btn-outline-warning btn-action">
                                    <i class="bi bi-archive"></i> ZIP
                                </a>
                            {% else %}
                                <a href="/download/{{ file.rel_path }}" class="btn btn-primary btn-action">
                                    <i class="bi bi-download"></i> DL
                                </a>
                            {% endif %}
                            
                            <a href="/delete/{{ file.rel_path }}" class="btn btn-outline-danger btn-action" onclick="return confirm('削除しますか？');">
                                <i class="bi bi-trash"></i>
                            </a>
                        </div>
                    </div>
                    {% endfor %}
                {% else %}
                    <div class="text-center py-5 text-muted">
                        <i class="bi bi-folder2-open display-4"></i>
                        <p class="mt-2">このフォルダは空です</p>
                    </div>
                {% endif %}
            </div>
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

def get_safe_path(req_path):
    """パスの安全性を確認し、絶対パスを返す"""
    # req_pathが空ならルート
    if req_path is None:
        req_path = ''
    
    # 結合して正規化
    abs_path = os.path.abspath(os.path.join(DOWNLOAD_FOLDER, req_path))
    
    # DOWNLOAD_FOLDERの外に出ていないかチェック (Directory Traversal対策)
    if os.path.commonpath([abs_path, DOWNLOAD_FOLDER]) != DOWNLOAD_FOLDER:
        return None
    
    return abs_path

@app.route('/')
def index():
    return redirect(url_for('browse', req_path=''))

@app.route('/browse/', defaults={'req_path': ''})
@app.route('/browse/<path:req_path>')
def browse(req_path):
    """フォルダの中身を表示する"""
    abs_path = get_safe_path(req_path)
    if not abs_path or not os.path.exists(abs_path):
        return abort(404)
    
    if not os.path.isdir(abs_path):
        return "これはフォルダではありません", 400

    # ディスク容量
    try:
        total, used, free = shutil.disk_usage(DOWNLOAD_FOLDER)
        free_readable = get_readable_size(free)
        used_readable = get_readable_size(used)
    except:
        free_readable = "不明"; used_readable = "不明"

    # 親フォルダのパス計算
    parent_path = os.path.dirname(req_path)
    if parent_path == '/': parent_path = ''

    # パンくずリスト用
    path_parts = [p for p in req_path.split('/') if p]

    files = []
    try:
        with os.scandir(abs_path) as entries:
            for entry in entries:
                if not entry.name.startswith('.'):
                    is_dir = entry.is_dir()
                    size_str = "フォルダ"
                    if not is_dir:
                        size_str = get_readable_size(entry.stat().st_size)
                    
                    # 相対パス（リンク用）
                    rel_path = os.path.join(req_path, entry.name)

                    files.append({
                        'name': entry.name,
                        'size': size_str,
                        'is_dir': is_dir,
                        'rel_path': rel_path
                    })
        
        # フォルダを先に、そのあとファイルを名前順でソート
        files.sort(key=lambda x: (not x['is_dir'], x['name']))

    except Exception as e:
        return f"エラー: {e}"

    return render_template_string(
        TEMPLATE, 
        files=files, 
        current_path=req_path, 
        parent_path=parent_path,
        path_parts=path_parts,
        free_space=free_readable,
        used_space=used_readable
    )

@app.route('/download/<path:req_path>')
def download(req_path):
    """ファイルならDL、フォルダならZIPでDL"""
    abs_path = get_safe_path(req_path)
    if not abs_path or not os.path.exists(abs_path):
        return abort(404)

    if os.path.isdir(abs_path):
        # フォルダ -> ZIP
        try:
            zip_name = os.path.basename(abs_path)
            zip_base = os.path.join('/tmp', zip_name)
            shutil.make_archive(zip_base, 'zip', abs_path)
            return send_file(zip_base + '.zip', as_attachment=True)
        except Exception as e:
            return f"ZIP作成エラー: {e}", 500
    else:
        # ファイル -> そのままDL
        directory = os.path.dirname(abs_path)
        filename = os.path.basename(abs_path)
        return send_from_directory(directory, filename, as_attachment=True)

@app.route('/delete/<path:req_path>')
def delete(req_path):
    """削除処理"""
    abs_path = get_safe_path(req_path)
    if not abs_path or not os.path.exists(abs_path):
        return abort(404)

    try:
        if os.path.isfile(abs_path):
            os.remove(abs_path)
        elif os.path.isdir(abs_path):
            shutil.rmtree(abs_path)
    except Exception as e:
        return f"削除エラー: {e}"
    
    # 削除後は元のフォルダに戻る
    parent = os.path.dirname(req_path)
    return redirect(url_for('browse', req_path=parent))

if __name__ == '__main__':
    # フォルダ作成
    if not os.path.exists(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER)
        
    print(f"🚀 ファイルマネージャー起動: {DOWNLOAD_FOLDER}")
    app.run(host='0.0.0.0', port=8080)
