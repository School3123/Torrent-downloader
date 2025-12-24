import sys
import os
import time
import requests
import libtorrent as lt
from urllib.parse import urlparse, unquote

# 保存先フォルダの設定
SAVE_PATH = './downloads'

def get_filename_from_cd(cd):
    """Content-Dispositionヘッダーからファイル名を取得"""
    if not cd:
        return None
    fname = None
    if 'filename=' in cd:
        try:
            fname = cd.split('filename=')[1].strip('"\'')
        except:
            pass
    return fname

def download_http(url):
    """普通のURL（直リンク）からのダウンロード"""
    print(f"🔗 HTTP接続を開始: {url}")
    
    try:
        # ストリームモードでリクエスト（大容量対応）
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            
            # ファイル名の決定
            filename = get_filename_from_cd(r.headers.get('content-disposition'))
            if not filename:
                filename = os.path.basename(urlparse(url).path)
            if not filename:
                filename = "downloaded_file.dat"
            
            # 保存先の準備
            if not os.path.exists(SAVE_PATH):
                os.makedirs(SAVE_PATH)
            
            full_path = os.path.join(SAVE_PATH, unquote(filename))
            total_length = r.headers.get('content-length')

            print(f"📥 ダウンロード開始: {filename}")

            with open(full_path, 'wb') as f:
                if total_length is None:
                    f.write(r.content)
                else:
                    dl = 0
                    total_length = int(total_length)
                    for data in r.iter_content(chunk_size=8192):
                        dl += len(data)
                        f.write(data)
                        # 進捗バー
                        done = int(50 * dl / total_length)
                        percent = (dl / total_length) * 100
                        sys.stdout.write(f"\r[{'=' * done}{' ' * (50-done)}] {percent:.2f}%")
                        sys.stdout.flush()
            
            print(f"\n✅ 完了: {full_path}")

    except Exception as e:
        print(f"\n❌ エラー: {e}")

def download_torrent_session(handle):
    """Torrentのダウンロードループ処理"""
    print(f"⏳ メタデータを取得中...")
    while not handle.has_metadata():
        time.sleep(1)
    
    info = handle.get_torrent_info()
    print(f"📥 Torrent開始: {info.name()}")

    while not handle.is_seed():
        s = handle.status()
        progress = s.progress * 100
        
        state_str = ['Queued', 'Check', 'DL Meta', 'DL', 'Done', 'Seed', 'Alloc']
        state = state_str[s.state]

        # 進捗表示
        sys.stdout.write(
            f'\r[{state}] {progress:.2f}% '
            f'(↓{s.download_rate / 1000:.1f} kB/s, '
            f'↑{s.upload_rate / 1000:.1f} kB/s, '
            f'Peers: {s.num_peers})'
        )
        sys.stdout.flush()
        time.sleep(1)
    
    print("\n✅ Torrentダウンロード完了！")

def setup_torrent_session():
    ses = lt.session()
    ses.listen_on(6881, 6891)
    return ses

def download_torrent(source_type, source_data):
    """Torrentダウンロードの分岐処理"""
    if not os.path.exists(SAVE_PATH):
        os.makedirs(SAVE_PATH)

    ses = setup_torrent_session()
    params = {
        'save_path': SAVE_PATH,
        'storage_mode': lt.storage_mode_t(2),
    }

    handle = None
    
    if source_type == 'magnet':
        print("🧲 マグネットリンクを解析中...")
        handle = lt.add_magnet_uri(ses, source_data, params)
    
    elif source_type == 'file':
        print(f"📄 Torrentファイルを読み込み中: {source_data}")
        try:
            info = lt.torrent_info(source_data)
            params['ti'] = info
            handle = ses.add_torrent(params)
        except Exception as e:
            print(f"❌ ファイル読み込みエラー: {e}")
            return

    download_torrent_session(handle)

def main():
    if len(sys.argv) < 2:
        print("使用法: python3 downloader.py <リンク または ファイルパス>")
        sys.exit(1)

    input_str = sys.argv[1]

    # 1. マグネットリンクの場合
    if input_str.startswith("magnet:?"):
        download_torrent('magnet', input_str)

    # 2. Web上のURLの場合 (http/https)
    elif input_str.startswith("http://") or input_str.startswith("https://"):
        # もしURLの末尾が .torrent なら一時保存してTorrentとして実行
        if input_str.lower().endswith(".torrent") or ".torrent?" in input_str.lower():
            print("🌐 Web上の.torrentファイルを検出。一時ダウンロードします...")
            try:
                r = requests.get(input_str)
                temp_file = "temp_auto.torrent"
                with open(temp_file, 'wb') as f:
                    f.write(r.content)
                download_torrent('file', temp_file)
                os.remove(temp_file) # お掃除
            except Exception as e:
                print(f"❌ .torrent取得エラー: {e}")
        else:
            # 普通のファイルダウンロード
            download_http(input_str)

    # 3. ローカルにあるファイルの場合
    elif os.path.isfile(input_str):
        download_torrent('file', input_str)
    
    else:
        print("❌ エラー: 指定されたファイルまたはリンクが見つかりません。")

if __name__ == "__main__":
    main()
