# 📖 使い方ガイド (Usage Guide)

GitHub Codespaces 上でのツールの操作手順まとめです。

---

## 1. 開始時のセットアップ (毎回必要)

Codespaces を起動または再起動した際は、まず以下のコマンドをターミナルで実行してライブラリを準備してください。

```bash
sudo apt-get update
sudo apt-get install -y python3-libtorrent python3-requests python3-flask
```

---

## 2. ファイルをダウンロードする (`downloader.py`)

**⚠️ 重要:**
実行時は必ず **`/usr/bin/python3`** を使用してください。単なる `python` ではエラーになります。

### 基本構文
```bash
/usr/bin/python3 downloader.py "ここにリンクまたはファイルパス"
```

### ケース別の実行コマンド

#### 🧲 マグネットリンク (BitTorrent)
リンクは必ずダブルクォーテーション `"` で囲んでください。
```bash
/usr/bin/python3 downloader.py "magnet:?xt=urn:btih:EXAMPLE_HASH..."
```

#### 🌐 Web上のファイル (HTTP/HTTPS)
画像、ZIP、ISOファイルなどを直接ダウンロードします。
```bash
/usr/bin/python3 downloader.py "https://example.com/file.zip"
```

#### 📄 Web上の .torrent ファイル
URLを指定するだけで、自動的にTorrentとして処理されます。
```bash
/usr/bin/python3 downloader.py "https://releases.ubuntu.com/.../ubuntu.iso.torrent"
```

#### 📂 手持ちの .torrent ファイル
1. 左側のエクスプローラーに `.torrent` ファイルをドラッグ＆ドロップ。
2. ファイル名を指定して実行。
```bash
/usr/bin/python3 downloader.py my_file.torrent
```

---

## 3. ファイルをPCへ保存する (`server.py`)

ダウンロードしたファイルを、ブラウザ経由で自分のPCに取り込みます。

### 手順

1.  **Web UIサーバーを起動する**
    ```bash
    /usr/bin/python3 server.py
    ```

2.  **ブラウザで開く**
    *   画面右下に表示される通知 **「Open in Browser」** をクリックします。
    *   または、ターミナルの「PORTS」タブを開き、ポート `8080` の地球儀アイコンをクリックします。

3.  **ダウンロード実行**
    *   ファイル一覧画面が表示されます。
    *   緑色の **「⬇ ダウンロード」** ボタンを押すと、PCへの保存が開始されます。

4.  **終了する**
    *   使い終わったらターミナルで `Ctrl + C` を押してサーバーを停止します。
