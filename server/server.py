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

# Deno PATHを確保（yt-dlp が JS challenge 解決に使用）
_deno_bin = os.path.join(os.path.expanduser("~"), ".deno", "bin")
if os.path.isdir(_deno_bin) and _deno_bin not in os.environ.get("PATH", ""):
    os.environ["PATH"] = _deno_bin + os.pathsep + os.environ.get("PATH", "")

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

# ---- Cookie設定 -------------------------------------------------------------
# Cookieファイルの優先パス（デスクトップ版と共有。なければブラウザCookieを使う）
_SERVER_DIR = os.path.dirname(os.path.abspath(__file__))
_COOKIE_CANDIDATES = [
    os.path.join(_SERVER_DIR, "..", "cookies", "youtube_cookies.txt"),
    r"D:\main\python_cord\Textube\Textube2.0\cookies\youtube_cookies.txt",
]
COOKIE_FILE = next((p for p in _COOKIE_CANDIDATES if os.path.isfile(p)), None)
# -----------------------------------------------------------------------------

# ---- 言語設定 ---------------------------------------------------------------
# ExtensionのUIに言語選択はないため、ここで優先取得言語を指定する。
# 例: 'ja' → 日本語優先、'en' → 英語優先、'ko' → 韓国語優先
# 対象動画にDEFAULT_LANGがなければ 'en' → 最初に見つかった言語 の順でフォールバック。
DEFAULT_LANG = 'ja'
# -----------------------------------------------------------------------------

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

    # --- フォールバック: yt-dlp + ブラウザCookie (2026春 botブロック対応) ---
    if not YTDLP_AVAILABLE:
        result['error'] = "字幕取得失敗: yt-dlp not installed"
        return result

    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        actual_lang = lang_code if lang_code != 'auto' else DEFAULT_LANG

        # ブラウザCookie優先順: brave → chrome → firefox → なし
        # info取得とURL downloadを同一 ydl コンテキスト内で行い cookies を使い回す
        import json as _json

        # Cookie試行順: ファイル → brave → chrome → firefox → なし
        # player_client は 'default' に任せて Deno が PO Token を自動生成
        _cookie_sources = []
        if COOKIE_FILE:
            _cookie_sources.append(('file', COOKIE_FILE))
        _cookie_sources += [('browser', b) for b in ['firefox', 'brave', 'chrome', None]]

        raw = None
        sub_ext = None
        is_auto = False
        found_lang = None
        last_err = None

        def try_lang(code, data, is_auto_flag):
            if code in data:
                return data[code], is_auto_flag, code
            for k in data:
                if k.startswith(code):
                    return data[k], is_auto_flag, k
            return None, is_auto_flag, None

        for src_type, src_val in _cookie_sources:
            try:
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'skip_download': True,
                    'writesubtitles': True,
                    'writeautomaticsub': True,
                    'subtitleslangs': ['all'],
                    'extractor_args': {
                        'youtube': {'player_client': ['default']},
                    },
                }
                if src_type == 'file':
                    ydl_opts['cookiefile'] = src_val
                    print(f"[INFO] yt-dlp trying cookie file: {video_id}")
                elif src_type == 'browser' and src_val:
                    ydl_opts['cookiesfrombrowser'] = (src_val,)
                    print(f"[INFO] yt-dlp trying browser={src_val}: {video_id}")
                else:
                    print(f"[INFO] yt-dlp trying without cookies: {video_id}")

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    print(f"[INFO] yt-dlp extract_info OK ({src_type}={src_val})")

                    manual = info.get('subtitles', {}) or {}
                    auto_caps = info.get('automatic_captions', {}) or {}

                    # 言語選択（希望 → ja → en → 最初の利用可能）
                    sub_data = None
                    if lang_code != 'auto':
                        for d, a in [(manual, False), (auto_caps, True)]:
                            r = try_lang(actual_lang, d, a)
                            if r[0]: sub_data, is_auto, found_lang = r; break
                    if not sub_data:
                        for d, a in [(manual, False), (auto_caps, True)]:
                            r = try_lang(DEFAULT_LANG, d, a)
                            if r[0]: sub_data, is_auto, found_lang = r; break
                    if not sub_data:
                        # DEFAULT_LANG が英語以外の場合は英語も試す
                        fallback2 = 'en' if DEFAULT_LANG != 'en' else 'ja'
                        for d, a in [(manual, False), (auto_caps, True)]:
                            r = try_lang(fallback2, d, a)
                            if r[0]: sub_data, is_auto, found_lang = r; break
                    if not sub_data and manual:
                        found_lang = next(iter(manual)); sub_data = manual[found_lang]; is_auto = False
                    if not sub_data and auto_caps:
                        found_lang = next(iter(auto_caps)); sub_data = auto_caps[found_lang]; is_auto = True

                    if not sub_data:
                        result['error'] = "字幕が見つかりません"
                        return result

                    # json3優先でURL選択（YouTube native形式、最も安定）
                    sub_url = None
                    for ext in ('json3', 'vtt', 'srv3', 'srv2', 'srv1'):
                        for fmt in sub_data:
                            if fmt.get('ext') == ext and fmt.get('url'):
                                sub_url = fmt['url']
                                sub_ext = ext
                                break
                        if sub_url:
                            break
                    if not sub_url and sub_data:
                        sub_url = sub_data[0].get('url')
                        sub_ext = sub_data[0].get('ext', 'vtt')

                    if not sub_url:
                        result['error'] = "字幕URLが取得できません"
                        return result

                    # ydl.urlopen でcookies付きダウンロード（429対策）
                    print(f"[INFO] Fetching subtitle via ydl.urlopen (ext={sub_ext})")
                    raw = ydl.urlopen(sub_url).read().decode('utf-8')
                    break

            except Exception as e:
                last_err = e
                print(f"[INFO] yt-dlp {src_type}={src_val} failed: {type(e).__name__}: {e}")
                raw = None
                continue

        if raw is None:
            result['error'] = f"yt-dlp全ブラウザ失敗: {last_err}"
            return result

        subtitles = []

        if sub_ext == 'json3' or raw.strip().startswith('{'):
            # json3 形式: {"events": [{"tStartMs":0,"dDurationMs":5000,"segs":[{"utf8":"text"}]}]}
            data = _json.loads(raw)
            for ev in data.get('events', []):
                segs = ev.get('segs')
                if not segs:
                    continue
                text = ''.join(s.get('utf8', '') for s in segs).strip()
                text = re.sub(r'<[^>]+>', '', text).strip()
                if not text or text == '\n':
                    continue
                start_ms = ev.get('tStartMs', 0)
                dur_ms = ev.get('dDurationMs', 0)
                subtitles.append({
                    'start': start_ms / 1000,
                    'duration': dur_ms / 1000,
                    'text': text,
                })
        else:
            # VTT / SRV 形式
            def ts(s):
                s = s.strip().split()[0]
                parts2 = s.replace(',', '.').split(':')
                parts2 = (['0'] * (3 - len(parts2))) + parts2
                h, m, sec = parts2
                return int(h) * 3600 + int(m) * 60 + float(sec)

            for block in re.split(r'\n\n+', raw):
                lines = block.strip().splitlines()
                time_line = next((l for l in lines if '-->' in l), None)
                if not time_line:
                    continue
                text_lines = [l for l in lines if '-->' not in l
                              and not l.strip().isdigit()
                              and l.strip()
                              and not l.startswith('WEBVTT')
                              and not l.startswith('NOTE')]
                text = re.sub(r'<[^>]+>', '', ' '.join(text_lines)).strip()
                if not text:
                    continue
                tp = time_line.split('-->')
                start = ts(tp[0])
                end = ts(tp[1])
                subtitles.append({'start': start, 'duration': end - start, 'text': text})

        if not subtitles:
            result['error'] = f"字幕のパースに失敗 (ext={sub_ext}, len={len(raw)})"
            return result

        result.update({'success': True, 'subtitles': subtitles, 'is_auto_generated': is_auto, 'language': found_lang})
        print(f"[INFO] yt-dlp OK: {len(subtitles)} entries ({found_lang})")

    except Exception as e:
        print(f"[ERROR] yt-dlp fallback failed: {type(e).__name__}: {e}")
        import traceback; traceback.print_exc()
        result['error'] = f"yt-dlp エラー [{type(e).__name__}]: {str(e)}"

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
