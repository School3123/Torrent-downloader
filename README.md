# 📥 Python Universal Downloader for GitHub Codespaces

**GitHub Codespaces (Linux環境)** 上で動作するように設計された、オールインワン・ファイルダウンローダーです。

BitTorrentプロトコル（マグネットリンク、.torrentファイル）と、標準的なWebダウンロード（HTTP/HTTPS）の両方をサポートしており、入力されたURLやファイルパスに応じて**最適なダウンロード方法を自動的に選択**します。

---

## ✨ 主な機能

1.  **Magnetリンク対応 (BitTorrent)**
    *   `magnet:?` で始まるリンクを解析し、直接P2Pネットワークからダウンロードします。
    *   Libtorrent 2.x系に対応した最新の接続方式を採用。
2.  **Torrentファイル対応**
    *   ローカルにある `.torrent` ファイル、またはWeb上の `.torrent` URLの両方を処理可能。
3.  **HTTP/HTTPS ダイレクトダウンロード**
    *   `requests` ライブラリのストリームモードを使用し、巨大なファイルでもメモリを圧迫せずにダウンロード。
    *   `User-Agent` ヘッダーを偽装し、ブラウザからのアクセスのみを許可するサイトにも対応。
4.  **プログレスバー表示**
    *   ダウンロード速度、アップロード速度、ピア数（Torrentの場合）、進捗率をリアルタイムで表示。
5.  **自動ファイル名解決**
    *   URLの解析やHTTPヘッダー（Content-Disposition）から、適切なファイル名を自動で取得。

---

## 🛠️ 環境構築 (セットアップ)

GitHub Codespacesはコンテナ環境であり、再起動するとシステムパッケージがリセットされる場合があります。使用を開始する際は、必ず以下のコマンドを実行してください。

### 1. 依存ライブラリのインストール
Python標準の `pip` ではなく、Ubuntuのシステムパッケージマネージャー `apt` を使用して、安定したC++バインディングを持つ `libtorrent` をインストールします。

```bash
sudo apt-get update
sudo apt-get install -y python3-libtorrent python3-requests
```

---

## ⚠️ 実行時の重要注意点 (Pathについて)

**ここが最も重要です。**

Codespacesには開発用のPython（pyenv等で管理された最新版）と、システム用のPython（`/usr/bin/python3`）が共存しています。
`apt` コマンドでインストールしたライブラリは**システム用のPython**に入るため、以下のコマンドで実行する必要があります。

*   ❌ **NG:** `python downloader.py ...` (ModuleNotFoundError になります)
*   ✅ **OK:** `/usr/bin/python3 downloader.py ...` (こちらを使ってください)

---

## 📖 使用方法

基本的な構文は以下の通りです。

```bash
/usr/bin/python3 downloader.py "<ターゲット>"
```

### パターン別コマンド例

#### 🧲 1. マグネットリンク (Magnet)
引用符 `"` で囲むことを推奨します（`&` などの文字がシェルで誤解釈されるのを防ぐため）。

```bash
/usr/bin/python3 downloader.py "magnet:?xt=urn:btih:d37b83d819c9d64a..."
```

#### 🌐 2. Web上のファイル (HTTP/HTTPS)
画像、ZIP、ISOファイルなどを直接ダウンロードします。

```bash
# 例: Pythonロゴ画像のダウンロード
/usr/bin/python3 downloader.py "https://www.python.org/static/img/python-logo.png"
```

#### 📄 3. Web上の .torrent ファイル
URLの末尾が `.torrent` の場合、自動的に一時ファイルとして保存し、Torrentダウンロードを開始します。

```bash
# 例: Linux ISOのTorrentファイルURL
/usr/bin/python3 downloader.py "https://releases.ubuntu.com/22.04/ubuntu-22.04.3-live-server-amd64.iso.torrent"
```

#### 📂 4. ローカルの .torrent ファイル
1. Codespacesの左側エクスプローラーにファイルをドラッグ＆ドロップ。
2. ファイルパスを指定して実行。

```bash
/usr/bin/python3 downloader.py my_file.torrent
```

---

## 📂 ディレクトリ構成と成果物

スクリプトを実行すると、自動的に `downloads` フォルダが作成されます。

```text
.
├── downloader.py      # メインスクリプト
├── README.md          # この説明書
└── downloads/         # 【保存先】ダウンロードされたファイルはここに入ります
    ├── ubuntu.iso
    ├── image.png
    └── ...
```

### 💻 PCへの取り出し方
1. 左側のファイルエクスプローラーで `downloads` フォルダを展開。
2. 目的のファイルを**右クリック**。
3. **Download (ダウンロード)** を選択すると、ブラウザ経由でローカルPCに保存されます。

---

## ❓ トラブルシューティング

### Q1. `ModuleNotFoundError: No module named 'libtorrent'` と出る
**A.** 実行コマンドを確認してください。`python` ではなく、必ず **`/usr/bin/python3`** を使ってください。
また、`sudo apt-get install python3-libtorrent` を実行し忘れていないか確認してください。

### Q2. マグネットリンクのダウンロードが進まない ("メタデータを取得中" で止まる)
**A.** そのTorrentの「シーダー（Seeder）」がいない可能性があります。
*   TorrentはP2P技術であり、ファイルを持っている他の人（Seeder）がオンラインでないとダウンロードできません。
*   古いファイルや人気のないファイルでは、いつまでも開始されないことがあります。60秒経過するとタイムアウト警告が出ます。

### Q3. Webダウンロードでファイル名がおかしい
**A.** URL自体にファイル名が含まれておらず、サーバーもファイル名情報を送ってこない場合、`downloaded_file.dat` という名前で保存されます。ダウンロード完了後に手動でリネームしてください。

---

## ⚖️ 免責事項 (Disclaimer)

*   **合法的利用:** 本ツールは、LinuxディストリビューションのISOイメージ、学術データ、パブリックドメインコンテンツなどの合法的なファイル共有・ダウンロードを目的としています。
*   **著作権:** 著作権法で保護されているコンテンツ（映画、音楽、アニメ、商用ソフトウェアなど）を権利者の許諾なくダウンロード・共有することは、多くの国で違法行為となります。
*   **責任:** 本ソフトウェアの使用によって生じたいかなる法的トラブル、損害、データの損失について、開発者は一切の責任を負いません。GitHub Codespacesの利用規約（Acceptable Use Policy）を遵守してご利用ください。
