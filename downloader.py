import sys
import os
import time
import requests
import libtorrent as lt
from urllib.parse import urlparse, unquote

# 保存先設定
SAVE_PATH = './downloads'

def get_filename_from_cd(cd):
    if not cd: return None
    if 'filename=' in cd:
        try: return cd.split('filename=')[1].strip('"\'')
        except: pass
    return None

def download_http(url):
    print(f"🔗 HTTP接続を開始: {url}")
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        with requests.get(url, stream=True, headers=headers) as r:
            r.raise_for_status()
            filename = get_filename_from_cd(r.headers.get('content-disposition')) or os.path.basename(urlparse(url).path) or "file.dat"
            
            if not os.path.exists(SAVE_PATH): os.makedirs(SAVE_PATH)
            full_path = os.path.join(SAVE_PATH, unquote(filename))
            total = int(r.headers.get('content-length', 0))

            print(f"📥 ダウンロード開始: {filename}")
            with open(full_path, 'wb') as f:
                dl = 0
                for data in r.iter_content(chunk_size=8192):
                    dl += len(data)
                    f.write(data)
                    if total > 0:
                        done = int(50 * dl / total)
                        sys.stdout.write(f"\r[{'=' * done}{' ' * (50-done)}] {dl/total*100:.2f}%")
                        sys.stdout.flush()
            print(f"\n✅ 完了: {full_path}")
    except Exception as e:
        print(f"\n❌ HTTPエラー: {e}")

def get_torrent_session():
    # DeprecationWarning 対策: settings_packを使用
    settings = {'listen_interfaces': '0.0.0.0:6881,0.0.0.0:6891'}
    ses = lt.session(settings)
    return ses

def download_torrent_session(ses, handle):
    print(f"⏳ メタデータを取得中... (最大60秒)")
    timeout = 0
    while not handle.has_metadata():
        time.sleep(1)
        timeout += 1
        if timeout > 60:
            print("\n⚠️ タイムアウト: メタデータ取得失敗。")
            return

    info = handle.get_torrent_info()
    print(f"📥 Torrent開始: {info.name()}")
    
    while not handle.is_seed():
        s = handle.status()
        state = ['Queued', 'Check', 'DL Meta', 'DL', 'Done', 'Seed', 'Alloc'][s.state] if s.state < 7 else 'Err'
        sys.stdout.write(f'\r[{state}] {s.progress*100:.2f}% (↓{s.download_rate/1000:.1f} kB/s, Peers: {s.num_peers})')
        sys.stdout.flush()
        time.sleep(1)
    print("\n✅ Torrent完了！")

def download_torrent(source_type, data):
    if not os.path.exists(SAVE_PATH): os.makedirs(SAVE_PATH)
    ses = get_torrent_session()
    params = {'save_path': SAVE_PATH, 'storage_mode': lt.storage_mode_t(2)}

    try:
        if source_type == 'magnet':
            handle = ses.add_torrent(lt.parse_magnet_uri(data))
        else:
            # ファイルが正しいTorrent形式かチェック（重要）
            with open(data, 'rb') as f:
                header = f.read(100)
                # Bencodeは 'd' で始まり、HTMLは '<!DOCTYPE' や '<html' で始まる
                if b'<!DOCTYPE' in header or b'<html' in header:
                    print(f"\n❌ エラー: ダウンロードしたファイルはHTML（Webページ）です。")
                    print("   リンク切れURLを指定している可能性があります。")
                    return

            info = lt.torrent_info(data) # ここでパース
            params['ti'] = info
            handle = ses.add_torrent(params)
        
        # 保存先ディレクトリを設定（libtorrent 2.0以降の修正）
        handle.save_path = SAVE_PATH 
        download_torrent_session(ses, handle)

    except Exception as e:
        print(f"\n❌ Torrentエラー: {e}")

def main():
    if len(sys.argv) < 2: return
    input_str = sys.argv[1]

    if input_str.startswith("magnet:?"):
        download_torrent('magnet', input_str)
    elif input_str.startswith("http"):
        if ".torrent" in input_str.lower():
            print("🌐 Web上の.torrentを取得中...")
            try:
                r = requests.get(input_str, headers={'User-Agent': 'Mozilla/5.0'})
                if r.status_code == 404:
                    print("❌ エラー: 指定されたURLが見つかりません (404 Not Found)")
                    return
                with open("temp.torrent", 'wb') as f: f.write(r.content)
                download_torrent('file', "temp.torrent")
                if os.path.exists("temp.torrent"): os.remove("temp.torrent")
            except Exception as e: print(f"❌ エラー: {e}")
        else:
            download_http(input_str)
    elif os.path.isfile(input_str):
        download_torrent('file', input_str)

if __name__ == "__main__":
    main()
