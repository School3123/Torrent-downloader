import sys
import os
import time
import requests
import libtorrent as lt
from urllib.parse import urlparse, unquote

# 保存先設定
SAVE_PATH = './downloads'

def get_filename_from_cd(cd):
    """Content-Dispositionヘッダーからファイル名を取得"""
    if not cd: return None
    if 'filename=' in cd:
        try: return cd.split('filename=')[1].strip('"\'')
        except: pass
    return None

def download_http(url):
    """HTTP/HTTPS ダイレクトダウンロード"""
    print(f"🔗 HTTP接続を開始: {url}")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        with requests.get(url, stream=True, headers=headers) as r:
            r.raise_for_status()
            
            filename = get_filename_from_cd(r.headers.get('content-disposition'))
            if not filename:
                filename = os.path.basename(urlparse(url).path)
            if not filename or len(filename) < 2:
                filename = "downloaded_file.dat"
            
            if not os.path.exists(SAVE_PATH): os.makedirs(SAVE_PATH)
            full_path = os.path.join(SAVE_PATH, unquote(filename))
            total = int(r.headers.get('content-length', 0))

            print(f"📥 ダウンロード開始: {filename}")
            
            with open(full_path, 'wb') as f:
                if total == 0:
                    f.write(r.content)
                else:
                    dl = 0
                    for data in r.iter_content(chunk_size=8192):
                        dl += len(data)
                        f.write(data)
                        done = int(50 * dl / total)
                        percent = (dl / total) * 100
                        sys.stdout.write(f"\r[{'=' * done}{' ' * (50-done)}] {percent:.2f}%")
                        sys.stdout.flush()
            print(f"\n✅ 完了: {full_path}")
            
    except Exception as e:
        print(f"\n❌ HTTPエラー: {e}")

def get_torrent_session():
    """Libtorrent 2.x向けセッション設定 (DHT有効化)"""
    settings = {
        'listen_interfaces': '0.0.0.0:6881,0.0.0.0:6891',
        'enable_dht': True,  # DHT有効化 (重要)
        'enable_lsd': True,  # ローカルピア探索
        'dht_bootstrap_nodes': 'router.bittorrent.com:6881,router.utorrent.com:6881',
    }
    ses = lt.session(settings)
    return ses

def download_torrent_session(ses, handle):
    """Torrentダウンロードループ"""
    print(f"⏳ メタデータを取得中... (DHT有効 / 最大60秒)")
    timeout = 0
    while not handle.has_metadata():
        time.sleep(1)
        timeout += 1
        if timeout > 60:
            print("\n⚠️ タイムアウト: マグネットリンクのメタデータ取得に失敗しました。")
            print("   ピアが見つからないか、ネットワーク制限の可能性があります。")
            return

    info = handle.get_torrent_info()
    print(f"📥 Torrent開始: {info.name()}")
    print(f"   サイズ: {info.total_size() / 1024 / 1024:.2f} MB")

    while not handle.is_seed():
        s = handle.status()
        state_str = ['Queued', 'Check', 'DL Meta', 'DL', 'Done', 'Seed', 'Alloc']
        state = state_str[s.state] if s.state < len(state_str) else 'Err'
        
        sys.stdout.write(
            f'\r[{state}] {s.progress*100:.2f}% '
            f'(↓{s.download_rate/1000:.1f} kB/s, '
            f'↑{s.upload_rate/1000:.1f} kB/s, '
            f'Peers: {s.num_peers})'
        )
        sys.stdout.flush()
        time.sleep(1)
    
    print("\n✅ Torrentダウンロード完了！ (シード状態へ移行前に終了します)")

def download_torrent(source_type, data):
    if not os.path.exists(SAVE_PATH): os.makedirs(SAVE_PATH)
    ses = get_torrent_session()
    params = {'save_path': SAVE_PATH, 'storage_mode': lt.storage_mode_t(2)}

    try:
        if source_type == 'magnet':
            print("🧲 マグネットリンクを解析中...")
            handle = ses.add_torrent(lt.parse_magnet_uri(data))
        else:
            # 誤ってHTMLファイルを読み込まないようにチェック
            with open(data, 'rb') as f:
                head = f.read(20)
                if b'<html' in head.lower() or b'<!doctype' in head.lower():
                    print(f"\n❌ エラー: ファイル '{data}' はTorrentファイルではなくHTML(Webページ)です。")
                    print("   URLがリンク切れ(404)になっている可能性があります。")
                    return

            print(f"📄 Torrentファイルを読み込み中: {data}")
            info = lt.torrent_info(data)
            params['ti'] = info
            handle = ses.add_torrent(params)

        handle.save_path = SAVE_PATH
        download_torrent_session(ses, handle)

    except Exception as e:
        print(f"\n❌ Torrentエラー: {e}")

def main():
    if len(sys.argv) < 2:
        print("使用法: /usr/bin/python3 downloader.py \"<リンク または ファイルパス>\"")
        sys.exit(1)

    input_str = sys.argv[1]

    if input_str.startswith("magnet:?"):
        download_torrent('magnet', input_str)
    
    elif input_str.startswith("http://") or input_str.startswith("https://"):
        # URLに .torrent が含まれているか、末尾が .torrent の場合
        if ".torrent" in input_str.lower() and "?" not in input_str:
            print("🌐 Web上の.torrentファイルを検出。一時ダウンロードします...")
            try:
                r = requests.get(input_str, headers={'User-Agent': 'Mozilla/5.0'})
                if r.status_code != 200:
                    print(f"❌ エラー: URLにアクセスできませんでした (Status: {r.status_code})")
                    return
                
                temp_file = "temp_auto.torrent"
                with open(temp_file, 'wb') as f:
                    f.write(r.content)
                
                download_torrent('file', temp_file)
                
                if os.path.exists(temp_file): os.remove(temp_file)
            except Exception as e:
                print(f"❌ .torrent取得エラー: {e}")
        else:
            download_http(input_str)
            
    elif os.path.isfile(input_str):
        download_torrent('file', input_str)
    else:
        print("❌ エラー: 指定されたファイルまたはリンクが見つかりません。")

if __name__ == "__main__":
    main()
