"""
Textube Chrome Extension - Local Server
YouTube字幕取得用ローカルサーバー

Textube2.0のyoutube_v3.pyをベースに作成
youtube-transcript-apiを優先使用（高速・安定）
"""

import os
import sys
import re
from typing import Optional, List, Dict, Any

from flask import Flask, request, jsonify
from flask_cors import CORS

# youtube-transcript-api（新しいAPI v1.0.0+）
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    TRANSCRIPT_API_AVAILABLE = True
    # APIインスタンスを作成
    ytt_api = YouTubeTranscriptApi()
except ImportError:
    TRANSCRIPT_API_AVAILABLE = False
    ytt_api = None
    print("WARNING: youtube-transcript-api not installed")
    print("Run: pip install youtube-transcript-api")

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
    """字幕を取得（新しいAPI v1.0.0+対応）"""
    result = {
        'success': False,
        'subtitles': [],
        'error': None,
        'is_auto_generated': False,
        'language': None
    }

    if not TRANSCRIPT_API_AVAILABLE:
        result['error'] = "youtube-transcript-api is not installed"
        return result

    try:
        print(f"[INFO] Fetching subtitles for {video_id}, lang: {lang_code}")

        # 新しいAPI: ytt_api.list() を使用
        transcript_list = ytt_api.list(video_id)

        subtitle_data = None
        is_auto = False
        found_lang = None

        if lang_code == 'auto':
            # 自動: 利用可能な最初の字幕を取得
            print(f"[INFO] Auto-detecting language...")
            for transcript in transcript_list:
                try:
                    subtitle_data = transcript.fetch()
                    is_auto = transcript.is_generated
                    found_lang = transcript.language
                    print(f"[INFO] Using {found_lang} subtitles ({'auto-generated' if is_auto else 'manual'})")
                    break
                except:
                    continue
        else:
            # 言語指定: 指定言語を探す
            lang_variants = [lang_code]
            if lang_code == 'zh-Hans':
                lang_variants = ['zh-Hans', 'zh-CN', 'zh']
            elif lang_code == 'zh-Hant':
                lang_variants = ['zh-Hant', 'zh-TW', 'zh']
            elif '-' not in lang_code:
                lang_variants.extend([
                    f'{lang_code}-{r}' for r in ['US', 'GB', 'JP', 'CN', 'TW', 'KR']
                ])

            try:
                transcript = transcript_list.find_transcript(lang_variants)
                subtitle_data = transcript.fetch()
                is_auto = transcript.is_generated
                found_lang = transcript.language
                print(f"[INFO] Found {found_lang} subtitles ({'auto-generated' if is_auto else 'manual'})")
            except:
                # フォールバック
                print(f"[INFO] Language not found, trying any available...")
                for transcript in transcript_list:
                    try:
                        subtitle_data = transcript.fetch()
                        is_auto = transcript.is_generated
                        found_lang = transcript.language
                        print(f"[INFO] Using {found_lang} subtitles")
                        break
                    except:
                        continue

        if not subtitle_data:
            result['error'] = "字幕が見つかりません"
            return result

        subtitles = []
        for item in subtitle_data:
            subtitles.append({
                'start': item.start,
                'duration': item.duration,
                'text': item.text.strip()
            })

        result['success'] = True
        result['subtitles'] = subtitles
        result['is_auto_generated'] = is_auto
        result['language'] = found_lang
        print(f"[INFO] Successfully extracted {len(subtitles)} subtitle entries")

    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {str(e)}")
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
