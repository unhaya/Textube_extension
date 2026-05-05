# Textube - YouTube Subtitle Extractor

A Chrome extension that extracts subtitles from YouTube videos with a local Python server.

**Latest: v2.2.1** — YouTube 2026春 botブロック対応強化版

## What's new in v2.2.1

- **Firefox Cookie を優先使用**: Cookie試行順を Firefox → Brave → Chrome → なし に変更。Brave使用中（DBロック中）でも Firefox Cookie で字幕取得できる
- **Deno PATH 自動設定**: サーバー起動時に `~/.deno/bin` を PATH へ追加。yt-dlp が JS challenge を自動解決できる
- **`player_client: default`**: yt-dlp のデフォルト設定に委ねることで最適なクライアント（tv_downgraded等）が自動選択される
- **Cookie ファイル共有**: デスクトップ版 Textube_app の `cookies/youtube_cookies.txt` を自動参照
- **`restart_server.bat` 追加**: ポート5000のサーバーをワンクリックで再起動できる BAT ファイル

## What's new in v2.2

- **yt-dlp + ブラウザCookie フォールバック**: youtube-transcript-api が IPブロックされた場合に yt-dlp（Firefox → Brave → Chrome → なし の順で Cookie を試行）で突破
- **HTTP 429 修正**: 字幕URLのダウンロードを Cookie なし素 request から yt-dlp の `urlopen`（Cookie付き）に変更。英語など非日本語字幕で発生していた 429 を解消
- **言語フォールバック修正**: 英語など希望言語がない動画でも利用可能な言語に自動フォールバック（従来は「字幕なし」と誤判定していた）
- **デフォルト言語の変更方法**: UIに言語選択はないが、`server/server.py` の先頭付近 `DEFAULT_LANG = 'ja'` を編集すれば取得優先言語を変更できる

## Features

- Extract subtitles from any YouTube video with captions
- **Extract from any page via URL input** — YouTubeページに居なくても、URLか動画IDを貼り付ければ字幕取得 (v2.1)
- **Editable summarization prompt** — popup右下の⚙ボタンから編集・保存・初期化 (v2.1)
- Auto-detect subtitle language (default: Japanese — change `DEFAULT_LANG` in `server/server.py`)
- Copy to clipboard with one click
- Copy with AI summarization prompt
- Download as text file
- Server auto-starts on Windows boot

## Architecture

```
[Chrome Extension] <--HTTP--> [Local Python Server] <--API--> [YouTube]
     (popup)                    (localhost:5000)
```

## Requirements

- Windows 10/11
- Python 3.12+
- Google Chrome

## Installation

### 1. Install Python

Download from [python.org](https://www.python.org/downloads/)

**Important:** Check "Add Python to PATH" during installation

### 2. Install Textube

1. Download ZIP from [Releases](https://github.com/unhaya/Textube_extension/releases)
2. Extract and double-click `install.bat`

This will:
- Install Python dependencies (Flask, youtube-transcript-api)
- Register server for auto-startup
- Start the server in background

### 3. Load Chrome Extension

1. Open Chrome and go to `chrome://extensions`
2. Enable "Developer mode" (top right)
3. Click "Load unpacked"
4. Select the `extension` folder

## Usage

### A. YouTubeページで取得（既存）

1. Open a YouTube video
2. Click the Textube icon in Chrome toolbar
3. Click "Extract Subtitles"
4. Choose an action:
   - **Copy** - Copy subtitles to clipboard
   - **Copy with Prompt** - Copy with AI summarization prompt
   - **Download** - Save as text file

### B. URL入力で取得（v2.1〜）

YouTubeページにいなくても字幕取得できる。

1. 任意のページでTextubeアイコンをクリック
2. 「URLから取得（任意）」欄に YouTube URL または 11桁の動画IDを貼り付け
3. 緑のヒント「動画ID: xxxxxxxxxxx」が出ればOK
4. 「Extract Subtitles」をクリック

URL欄に何か入力されている場合は **URL欄の動画が優先**される（タブの動画ではなく）。

## Customization

### プロンプトの編集（v2.1〜）

「Copy with Prompt」で挿入される要約プロンプトをUIから編集できる。

1. popup右下の **⚙ボタン** をクリック
2. モーダルでプロンプトを編集
3. ボタン操作：
   - **保存** — 編集内容を保存（次回以降も有効）
   - **初期値に戻す** — 編集欄を初期プロンプトに戻す（保存はまだ）
   - **キャンセル** — 変更を破棄して閉じる

保存先は `chrome.storage.local`（拡張内ストレージ）。プロファイル単位で永続化される。

## Uninstall

1. Run `uninstall.bat`
2. Remove extension from `chrome://extensions`
3. Delete the folder

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Server offline | Double-click `restart_server.bat` |
| "Sign in to confirm you're not a bot" | Firefox を起動した状態で `restart_server.bat` を実行（Firefox Cookie を使用） |
| No subtitles found | Video may not have captions |
| Python not found | Install Python with PATH option |

## Tech Stack

- **Extension:** Chrome Manifest V3, Vanilla JS
- **Server:** Python, Flask, youtube-transcript-api
- **Auto-start:** VBScript + Windows Startup folder

## 関連プロジェクト

### 🖥 [Textube_app](https://github.com/unhaya/Textube_app)
履歴管理・サムネ表示・動画ダウンロード(1080p)・翻訳まで含む **デスクトップアプリ版** (PyQt5)。
本格的に字幕を活用したい人向け。

👉 **最新リリース**: [v2.2 をダウンロード](https://github.com/unhaya/Textube_app/releases/tag/v2.2)（Windows用 exe バンドル zip）

## License

MIT
