# Textube - YouTube Subtitle Extractor

YouTube動画から字幕を抽出するChrome拡張機能です。

## Features

- YouTube動画から字幕を自動抽出
- 字幕の言語を自動検出
- テキストをクリップボードにコピー
- 要約用プロンプト付きでコピー
- テキストファイルとしてダウンロード

## Requirements

- Windows 10/11
- Python 3.8+
- Google Chrome

## Installation

### 1. Pythonのインストール

[Python公式サイト](https://www.python.org/downloads/)からダウンロード

**重要:** インストール時に「Add Python to PATH」にチェックを入れてください

### 2. Textubeのインストール

1. [Releases](https://github.com/unhaya/Textube_extension/releases)からZIPをダウンロード
2. 解凍して `install.bat` をダブルクリック

### 3. Chrome拡張機能の読み込み

1. Chromeで `chrome://extensions` を開く
2. 右上の「デベロッパーモード」をON
3. 「パッケージ化されていない拡張機能を読み込む」をクリック
4. `extension` フォルダを選択

## Usage

1. YouTubeで動画を開く
2. ブラウザ右上のTextubeアイコンをクリック
3. 「Extract Subtitles」をクリック
4. 字幕が表示されたら：
   - **Copy** - 字幕のみコピー
   - **Copy with Prompt** - 要約用プロンプト付きでコピー
   - **Download** - テキストファイルとして保存

## Uninstall

1. `uninstall.bat` をダブルクリック
2. Chromeで `chrome://extensions` を開き、Textubeを削除
3. フォルダを削除

## How it Works

```
[Chrome Extension] <--HTTP--> [Local Python Server] <--API--> [YouTube]
     (popup)                    (localhost:5000)
```

- Chrome拡張機能がローカルのPythonサーバーと通信
- サーバーがYouTubeから字幕を取得
- PCを再起動してもサーバーは自動起動

## Troubleshooting

| 問題 | 解決策 |
|------|--------|
| Server offline | `install.bat` を再実行 |
| 字幕が取得できない | その動画に字幕がない可能性 |
| Pythonがない | python.orgからインストール |

## License

MIT
