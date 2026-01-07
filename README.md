# Textube - YouTube Subtitle Extractor

A Chrome extension that extracts subtitles from YouTube videos with a local Python server.

## Features

- Extract subtitles from any YouTube video with captions
- Auto-detect subtitle language
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
- Python 3.8+
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

1. Open a YouTube video
2. Click the Textube icon in Chrome toolbar
3. Click "Extract Subtitles"
4. Choose an action:
   - **Copy** - Copy subtitles to clipboard
   - **Copy with Prompt** - Copy with AI summarization prompt
   - **Download** - Save as text file

## Uninstall

1. Run `uninstall.bat`
2. Remove extension from `chrome://extensions`
3. Delete the folder

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Server offline | Run `install.bat` again |
| No subtitles found | Video may not have captions |
| Python not found | Install Python with PATH option |

## Tech Stack

- **Extension:** Chrome Manifest V3, Vanilla JS
- **Server:** Python, Flask, youtube-transcript-api
- **Auto-start:** VBScript + Windows Startup folder

## License

MIT
