"""
Textube Chrome Extension - Local Server
YouTube字幕取得用ローカルサーバー

字幕取得戦略（2026春 YouTube botブロック対応）:
1. youtube-transcript-api を試みる（高速・Cookie不要）
2. 失敗したら yt-dlp + Firefox Cookie にフォールバック（bot検知回避）
"""

import os
import sys
import re
import tempfile
from typing import Optional, List, Dict, Any

from flask import Flask, request, jsonify
from flask_cors import CORS

# youtube-transcript-api（新しいAPI v1.0.0+）
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    TRANSCRIPT_API_AVAILABLE = True
    ytt_api = YouTubeTranscriptApi()
except ImportError:
    TRANSCRIPT_API_AVAILABLE = False
    ytt_api = None
    print("WARNING: youtube-transcript-api not installed")

# yt-dlp（フォールバック。Firefox Cookie + Deno で bot検知を回避）
try:
    import yt_dlp
    YTDLP_AVAILABLE = True
except ImportError:
    YTDLP_AVAILABLE = False
    print("WARNING: yt-dlp not installed")

app = Flask(__name__)
CORS(app)

# 対応言語リスト
SUPPORTED_LANGUAGES = [
    {'code': 'ja', 'name': '日本語'},
    {'code': 'en', 'name': 'English'},
    {'code': 'ko', 'name': '한국어'},
    {'code': 'zh-Hans', 'name': '中文 (简体)'},
    {'code': 'zh-Hant', 'name': '中文 (繁體)'},
    {'code': 'es', 'name': 'Español'},
    {'code': 'fr', 'name': 'Français'},
    {'code': 'de', 'name': 'Deutsch'},
    {'code': 'pt', 'name': 'Português'},
    {'code': 'ru', 'name': 'Русский'},
]


def extract_video_id(video_id_or_url: str) -> Optional[str]:
    """動画IDまたはURLから動画IDを抽出"""
    if re.match(r'^[a-zA-Z0-9_-]{11}$', video_id_or_url):
        return video_id_or_url

    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/shorts\/([a-zA-Z0-9_-]{11})'
    ]

    for pattern in patterns:
        match = re.search(pattern, video_id_or_url)
        if match:
            return match.group(1)

    return None


def extract_subtitles(video_id: str, lang_code: str = 'auto') -> Dict[str, Any]:
    """字幕を取得。youtube-transcript-api → yt-dlp+Firefox の順でフォールバック"""
    result = {
        'success': False,
        'subtitles': [],
        'error': None,
        'is_auto_generated': False,
        'language': None
    }

    # --- 一次試行: youtube-transcript-api ---
    if TRANSCRIPT_API_AVAILABLE:
        try:
            print(f"[INFO] Trying youtube-transcript-api: {video_id}, lang={lang_code}")
            transcript_list = ytt_api.list(video_id)
            subtitle_data = None
            is_auto = False
            found_lang = None

            if lang_code == 'auto':
                for transcript in transcript_list:
                    try:
                        subtitle_data = transcript.fetch()
                        is_auto = transcript.is_generated
                        found_lang = transcript.language
                        break
                    except:
                        continue
            else:
                lang_variants = [lang_code]
                if lang_code == 'zh-Hans':
                    lang_variants = ['zh-Hans', 'zh-CN', 'zh']
                elif lang_code == 'zh-Hant':
                    lang_variants = ['zh-Hant', 'zh-TW', 'zh']
                elif '-' not in lang_code:
                    lang_variants.extend([f'{lang_code}-{r}' for r in ['US', 'GB', 'JP', 'CN', 'TW', 'KR']])
                try:
                    transcript = transcript_list.find_transcript(lang_variants)
                    subtitle_data = transcript.fetch()
                    is_auto = transcript.is_generated
                    found_lang = transcript.language
                except:
                    for transcript in transcript_list:
                        try:
                            subtitle_data = transcript.fetch()
                            is_auto = transcript.is_generated
                            found_lang = transcript.language
                            break
                        except:
                            continue

            if subtitle_data:
                subtitles = [{'start': item.start, 'duration': item.duration, 'text': item.text.strip()} for item in subtitle_data]
                result.update({'success': True, 'subtitles': subtitles, 'is_auto_generated': is_auto, 'language': found_lang})
                print(f"[INFO] transcript-api OK: {len(subtitles)} entries ({found_lang})")
                return result
        except Exception as e:
            print(f"[INFO] transcript-api failed ({type(e).__name__}), trying yt-dlp fallback...")

    # --- フォールバック: yt-dlp + Firefox Cookie (2026春 botブロック対応) ---
    if not YTDLP_AVAILABLE:
        result['error'] = "字幕取得失敗: yt-dlp not installed"
        return result

    try:
        print(f"[INFO] Trying yt-dlp + Firefox Cookie: {video_id}")
        url = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'cookiesfrombrowser': ('firefox',),
        }
        actual_lang = lang_code if lang_code != 'auto' else 'ja'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        manual = info.get('subtitles', {})
        auto_caps = info.get('automatic_captions', {})

        # 言語選択（希望 → 英語 → 最初の利用可能）
        sub_data = None
        is_auto = False
        found_lang = None

        def try_lang(code, data, is_auto_flag):
            if code in data:
                return data[code], is_auto_flag, code
            for k in data:
                if k.startswith(code):
                    return data[k], is_auto_flag, k
            return None, is_auto_flag, None

        if lang_code != 'auto':
            sub_data, is_auto, found_lang = try_lang(actual_lang, manual, False)
            if not sub_data:
                sub_data, is_auto, found_lang = try_lang(actual_lang, auto_caps, True)
        if not sub_data:
            sub_data, is_auto, found_lang = try_lang('ja', manual, False) or try_lang('ja', auto_caps, True)
        if not sub_data and manual:
            found_lang = next(iter(manual)); sub_data = manual[found_lang]; is_auto = False
        if not sub_data and auto_caps:
            found_lang = next(iter(auto_caps)); sub_data = auto_caps[found_lang]; is_auto = True

        if not sub_data:
            result['error'] = "字幕が見つかりません"
            return result

        # vtt/json3 形式のURLから字幕テキストを取得
        import urllib.request
        sub_url = None
        for fmt in sub_data:
            if fmt.get('ext') in ('vtt', 'json3', 'srv3', 'srv2', 'srv1'):
                sub_url = fmt.get('url')
                if sub_url:
                    break
        if not sub_url and sub_data:
            sub_url = sub_data[0].get('url')

        if not sub_url:
            result['error'] = "字幕URLが取得できません"
            return result

        with urllib.request.urlopen(sub_url, timeout=15) as resp:
            raw = resp.read().decode('utf-8')

        # VTT パース（簡易）
        subtitles = []
        for block in re.split(r'\n\n+', raw):
            lines = block.strip().splitlines()
            time_line = next((l for l in lines if '-->' in l), None)
            if not time_line:
                continue
            text_lines = [l for l in lines if '-->' not in l and not l.strip().isdigit() and l.strip() and not l.startswith('WEBVTT')]
            text = ' '.join(text_lines).strip()
            if not text:
                continue
            parts = time_line.split('-->')
            def ts(s):
                s = s.strip().split()[0]
                h, m, sec = (s.split(':') + ['0', '0', '0'])[:3]
                return int(h)*3600 + int(m)*60 + float(sec.replace(',', '.'))
            start = ts(parts[0])
            end = ts(parts[1])
            subtitles.append({'start': start, 'duration': end - start, 'text': re.sub(r'<[^>]+>', '', text).strip()})

        if not subtitles:
            result['error'] = "字幕のパースに失敗"
            return result

        result.update({'success': True, 'subtitles': subtitles, 'is_auto_generated': is_auto, 'language': found_lang})
        print(f"[INFO] yt-dlp OK: {len(subtitles)} entries ({found_lang})")

    except Exception as e:
        print(f"[ERROR] yt-dlp fallback failed: {type(e).__name__}: {e}")
        result['error'] = f"字幕取得エラー: {str(e)}"

    return result


def format_subtitles(subtitles: List[Dict], include_timestamp: bool = False) -> str:
    """字幕をテキスト形式にフォーマット"""
    lines = []

    for sub in subtitles:
        if include_timestamp:
            start = format_time(sub['start'])
            end = format_time(sub['start'] + sub['duration'])
            lines.append(f"[{start} --> {end}]")

        lines.append(sub['text'])

        if include_timestamp:
            lines.append('')

    return '\n'.join(lines)


def format_time(seconds: float) -> str:
    """秒を時間形式にフォーマット"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:05.2f}"
    else:
        return f"{minutes:02d}:{secs:05.2f}"


# === API Endpoints ===

@app.route('/health', methods=['GET'])
def health():
    """ヘルスチェック"""
    return jsonify({
        'status': 'ok',
        'message': 'Textube server is running',
        'transcript_api': TRANSCRIPT_API_AVAILABLE
    })


@app.route('/languages', methods=['GET'])
def languages():
    """対応言語リスト"""
    return jsonify({'languages': SUPPORTED_LANGUAGES})


@app.route('/extract', methods=['POST'])
def extract():
    """字幕を抽出"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Request body required'}), 400

        video_id = data.get('video_id')
        if not video_id:
            return jsonify({'error': 'video_id required'}), 400

        video_id = extract_video_id(video_id)
        if not video_id:
            return jsonify({'error': 'Invalid video ID or URL'}), 400

        lang_code = data.get('language', 'auto')
        include_timestamp = data.get('include_timestamp', False)

        result = extract_subtitles(video_id, lang_code)

        if not result['success']:
            return jsonify({'error': result['error']}), 404

        subtitle_text = format_subtitles(result['subtitles'], include_timestamp)

        return jsonify({
            'success': True,
            'video_id': video_id,
            'language': result['language'],
            'subtitle': subtitle_text,
            'line_count': len(result['subtitles']),
            'is_auto_generated': result['is_auto_generated']
        })

    except Exception as e:
        print(f"[ERROR] /extract: {e}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500


if __name__ == '__main__':
    print("=" * 50)
    print("Textube Local Server")
    print("=" * 50)
    print(f"youtube-transcript-api: {'OK' if TRANSCRIPT_API_AVAILABLE else 'NOT INSTALLED'}")
    print("=" * 50)
    print("Server: http://localhost:5000")
    print("Press Ctrl+C to stop")
    print("=" * 50)

    app.run(host='0.0.0.0', port=5000, debug=False)
