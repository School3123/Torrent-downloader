from flask import Flask, render_template_string, send_from_directory, redirect, url_for
import os
import shutil

app = Flask(__name__)

# downloader.py の SAVE_PATH と同じ設定にする
DOWNLOAD_FOLDER = './downloads'

# デザイン（スマホ対応・見やすいBootstrapデザイン）
TEMPLATE = """
<!doctype html>
<html lang="ja">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>ファイル管理マネージャー</title>
    <!-- Bootstrap CSS (CDN) -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f4f6f9; padding-top: 30px; }
        .card { border: none; box-shadow: 0 4px 10px rgba(0,0,0,0.1); border-radius: 12px; }
        .card-header { background-color: #4a90e2; color: white; border-radius: 12px 12px 0 0 !important; font-weight: bold; }
        .btn-download { background-color: #28a745; color: white; border: none; }
        .btn-download:hover { background-color: #218838; color: white; }
        .btn-delete { color: #dc3545; border: 1px solid #dc3545; background: white; }
        .btn-delete:hover { background-color: #dc3545; color: white; }
        .file-size { font-size: 0.85rem; color: #6c757d; }
        .disk-info { font-size: 0.9rem; color: #555; background: #e9ecef; padding: 10px; border-radius: 8px; margin-bottom: 20px;}
    </style>
</head>
<body>
<div class="container">
    <div class="row justify-content-center">
        <div class="col-md-10">
            
            <!-- ディスク容量表示 -->
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h3 class="text-secondary">📥 ダウンロード・センター</h3>
                <a href="/" class="btn btn-outline-primary btn-sm">🔄 更新</a>
            </div>

            <div class="disk-info d-flex justify-content-between">
                <span>📂 保存先: {{ folder }}</span>
                <span>ディスク残り容量: <strong>{{ free_space }}</strong></span>
            </div>

            <div class="card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <span>ファイル一覧</span>
                    <span class="badge bg-light text-dark">{{ files|length }} 個</span>
                </div>
                <div class="card-body p-0">
                    {% if files %}
                    <div class="list-group list-group-flush">
                        {% for file in files %}
                        <div class="list-group-item d-flex justify-content-between align-items-center py-3">
                            <div class="text-truncate me-3" style="max-width: 60%;">
                                <div class="fw-bold text-dark">{{ file.name }}</div>
                                <div class="file-size">{{ file.size }}</div>
                            </div>
                            <div class="btn-group" role="group">
                                <a href="/download/{{ file.name }}" class="btn btn-download btn-sm">
                                    ⬇ PCへ保存
                                </a>
                                <a href="/delete/{{ file.name }}" class="btn btn-delete btn-sm" onclick="return confirm('本当に「{{ file.name }}」を削除しますか？');">
                                    🗑 削除
                                </a>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                    {% else %}
                    <div class="text-center py-5 text-muted">
                        <p class="mb-0">ファイルが見つかりません</p>
                        <small>downloader.py を実行してファイルをダウンロードしてください</small>
                    </div>
                    {% endif %}
                </div>
            </div>

        </div>
    </div>
</div>
</body>
</html>
"""

def get_readable_size(size_in_bytes):
    """バイト数をKB, MB, GBに変換"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024
    return f"{size_in_bytes:.2f} TB"

@app.route('/')
def index():
    # フォルダがない場合は作成（エラー防止）
    if not os.path.exists(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER)
    
    # ディスク容量の取得
    total, used, free = shutil.disk_usage(DOWNLOAD_FOLDER)
    free_readable = get_readable_size(free)

    files = []
    try:
        # ファイルリストを取得して名前順にソート
        file_list = sorted(os.listdir(DOWNLOAD_FOLDER))
        
        for filename in file_list:
            filepath = os.path.join(DOWNLOAD_FOLDER, filename)
            # 隠しファイル以外を表示
            if os.path.isfile(filepath) and not filename.startswith('.'):
                size = os.path.getsize(filepath)
                files.append({
                    'name': filename,
                    'size': get_readable_size(size)
                })
    except Exception as e:
        return f"エラーが発生しました: {e}"

    return render_template_string(TEMPLATE, files=files, folder=DOWNLOAD_FOLDER, free_space=free_readable)

@app.route('/download/<path:filename>')
def download_file(filename):
    """PCへのダウンロード処理"""
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

@app.route('/delete/<path:filename>')
def delete_file(filename):
    """ファイルの削除処理"""
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        return f"削除中にエラーが発生しました: {e}"
    return redirect(url_for('index'))

if __name__ == '__main__':
    print("🚀 Web UIサーバーを起動しました。")
    print("👉 右下のポップアップ「Open in Browser」をクリックしてください。")
    # Codespacesの外部公開用設定 (host=0.0.0.0)
    app.run(host='0.0.0.0', port=8080)
