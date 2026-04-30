// Textube Chrome Extension - Popup Script

const elements = {
  videoInfo: document.getElementById('videoInfo'),
  videoTitle: document.getElementById('videoTitle'),
  urlInput: document.getElementById('urlInput'),
  urlHint: document.getElementById('urlHint'),
  includeTimestamp: document.getElementById('includeTimestamp'),
  extractBtn: document.getElementById('extractBtn'),
  loading: document.getElementById('loading'),
  result: document.getElementById('result'),
  resultCount: document.getElementById('resultCount'),
  subtitleText: document.getElementById('subtitleText'),
  copyBtn: document.getElementById('copyBtn'),
  copyWithPromptBtn: document.getElementById('copyWithPromptBtn'),
  downloadBtn: document.getElementById('downloadBtn'),
  error: document.getElementById('error'),
  errorText: document.getElementById('errorText'),
  statusDot: document.getElementById('statusDot'),
  statusText: document.getElementById('statusText'),
  toast: document.getElementById('toast'),
  // プロンプト編集UI
  settingsBtn: document.getElementById('settingsBtn'),
  promptModal: document.getElementById('promptModal'),
  modalCloseBtn: document.getElementById('modalCloseBtn'),
  promptEditor: document.getElementById('promptEditor'),
  promptResetBtn: document.getElementById('promptResetBtn'),
  promptCancelBtn: document.getElementById('promptCancelBtn'),
  promptSaveBtn: document.getElementById('promptSaveBtn')
};

// Default prompt for summarization
const DEFAULT_PROMPT = `以下のテキストを詳細に要約してください：

## 要約作成の指示
以下の構造で、情報の削除を最小限に抑えた包括的な要約を作成してください。

### 概要
（テキスト全体の主題と目的を2-3文で説明）

### 詳細な内容分析

1. **主要トピック1**
   - 核心的な主張や発見
   - 関連する具体例やデータを含む
   - 必要に応じて専門用語の説明を追加

2. **主要トピック2**
   （同様の形式で続ける）

### メタ情報分析（該当する場合）
- 文書の対象読者：
- 主要な専門用語：
- 文脈や背景情報：

## 要約時の注意点
- 元の情報の削除を最小限に抑え、重要なデータや具体例を保持する
- 複雑な概念は簡潔かつ正確に説明する
- 文書のニュアンスや意図を維持する
- 多言語コンテンツがある場合は、翻訳の正確性に注意する
- タイトルが示す問題や主張を最優先で抽出し、それに関連する情報を重点的にまとめる

---
以下が要約対象のテキストです：
`;

// タブ由来の videoId/title（既存経路）
let tabVideoId = null;
let tabVideoTitle = '';
// URL入力欄由来の videoId（新経路）
let urlInputVideoId = null;
// サーバ稼働状態
let serverOnline = false;
// 現在有効なプロンプト（保存値があればそれ、なければDEFAULT_PROMPT）
let activePrompt = DEFAULT_PROMPT;

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
  await loadSettings();
  await loadActivePrompt();
  await checkServerStatus();
  await getVideoInfo();

  elements.extractBtn.addEventListener('click', extractSubtitles);
  elements.copyBtn.addEventListener('click', copyToClipboard);
  elements.copyWithPromptBtn.addEventListener('click', copyWithPrompt);
  elements.downloadBtn.addEventListener('click', downloadSubtitles);
  elements.urlInput.addEventListener('input', onUrlInputChange);

  // プロンプト編集モーダル
  elements.settingsBtn.addEventListener('click', openPromptModal);
  elements.modalCloseBtn.addEventListener('click', closePromptModal);
  elements.promptCancelBtn.addEventListener('click', closePromptModal);
  elements.promptSaveBtn.addEventListener('click', savePrompt);
  elements.promptResetBtn.addEventListener('click', resetPromptToDefault);
  // オーバーレイ外側クリックで閉じる
  elements.promptModal.addEventListener('click', (e) => {
    if (e.target === elements.promptModal) closePromptModal();
  });
});

// YouTube URL/ID から videoId を抽出（11桁の英数+_-）
function parseVideoId(str) {
  if (!str) return null;
  const s = str.trim();
  if (!s) return null;
  // 直接ID
  if (/^[a-zA-Z0-9_-]{11}$/.test(s)) return s;
  // URL各種
  const patterns = [
    /(?:youtube\.com\/watch\?[^#]*\bv=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})/
  ];
  for (const p of patterns) {
    const m = s.match(p);
    if (m) return m[1];
  }
  return null;
}

// URL欄の入力変化時：パース→ヒント表示→ボタン状態更新
function onUrlInputChange() {
  const raw = elements.urlInput.value;
  if (!raw.trim()) {
    urlInputVideoId = null;
    elements.urlHint.textContent = '';
    elements.urlHint.className = 'url-hint';
  } else {
    const id = parseVideoId(raw);
    if (id) {
      urlInputVideoId = id;
      elements.urlHint.textContent = `動画ID: ${id}`;
      elements.urlHint.className = 'url-hint valid';
    } else {
      urlInputVideoId = null;
      elements.urlHint.textContent = 'URLまたは11桁のIDを入力';
      elements.urlHint.className = 'url-hint invalid';
    }
  }
  updateExtractButtonState();
}

// 取得ボタンの有効/無効：サーバオンライン かつ (タブvideoId or URL欄videoId) が必要
function updateExtractButtonState() {
  const hasId = !!(urlInputVideoId || tabVideoId);
  elements.extractBtn.disabled = !(serverOnline && hasId);
}

// Load saved settings
async function loadSettings() {
  return new Promise(resolve => {
    chrome.storage.local.get(['includeTimestamp'], result => {
      if (result.includeTimestamp) elements.includeTimestamp.checked = result.includeTimestamp;
      resolve();
    });
  });
}

// Save settings
function saveSettings() {
  chrome.storage.local.set({
    includeTimestamp: elements.includeTimestamp.checked
  });
}

// 保存済みプロンプトをロード（無ければDEFAULT_PROMPT）
async function loadActivePrompt() {
  return new Promise(resolve => {
    chrome.storage.local.get(['promptTemplate'], result => {
      if (typeof result.promptTemplate === 'string' && result.promptTemplate.length > 0) {
        activePrompt = result.promptTemplate;
      } else {
        activePrompt = DEFAULT_PROMPT;
      }
      resolve();
    });
  });
}

// モーダルを開く（現在のactivePromptをエディタに反映）
function openPromptModal() {
  elements.promptEditor.value = activePrompt;
  elements.promptModal.style.display = 'flex';
  // フォーカスを最後尾に
  setTimeout(() => {
    elements.promptEditor.focus();
    const len = elements.promptEditor.value.length;
    elements.promptEditor.setSelectionRange(len, len);
  }, 0);
}

// モーダルを閉じる（変更は破棄）
function closePromptModal() {
  elements.promptModal.style.display = 'none';
}

// 編集中のテキストエリアをDEFAULT_PROMPTに戻す（保存はまだ）
function resetPromptToDefault() {
  elements.promptEditor.value = DEFAULT_PROMPT;
  elements.promptEditor.focus();
}

// 保存：エディタの内容をchrome.storage.localに永続化、activePromptに反映
function savePrompt() {
  const newPrompt = elements.promptEditor.value;
  chrome.storage.local.set({ promptTemplate: newPrompt }, () => {
    activePrompt = newPrompt;
    closePromptModal();
    showToast('プロンプトを保存しました');
  });
}

// Check server status
async function checkServerStatus() {
  try {
    const response = await chrome.runtime.sendMessage({ action: 'checkServer' });
    if (response.online) {
      elements.statusDot.className = 'status-dot online';
      elements.statusText.textContent = 'Server online';
      serverOnline = true;
    } else {
      elements.statusDot.className = 'status-dot offline';
      elements.statusText.textContent = 'Server offline';
      serverOnline = false;
    }
  } catch (e) {
    elements.statusDot.className = 'status-dot offline';
    elements.statusText.textContent = 'Error';
    serverOnline = false;
  }
  updateExtractButtonState();
}

// Get video info from content script (タブがYouTube再生ページの時のみ自動取得)
async function getVideoInfo() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    if (!tab || !tab.url || !tab.url.includes('youtube.com/watch')) {
      // 非YouTubeページ：URL欄入力で取得可能なのでロックしない
      elements.videoTitle.textContent = 'YouTubeページ外（下のURL欄から取得可）';
      updateExtractButtonState();
      return;
    }

    // Try to get info from content script
    try {
      const response = await chrome.tabs.sendMessage(tab.id, { action: 'getVideoInfo' });
      if (response && response.videoId) {
        tabVideoId = response.videoId;
        tabVideoTitle = response.title || 'Unknown';
        elements.videoTitle.textContent = tabVideoTitle;
        updateExtractButtonState();
        return;
      }
    } catch (e) {
      // Content script not loaded, extract from URL
    }

    // Fallback: extract from URL
    const url = new URL(tab.url);
    tabVideoId = url.searchParams.get('v');
    if (tabVideoId) {
      tabVideoTitle = tab.title.replace(' - YouTube', '').trim();
      elements.videoTitle.textContent = tabVideoTitle;
    } else {
      elements.videoTitle.textContent = 'Could not get video ID';
    }
    updateExtractButtonState();
  } catch (e) {
    elements.videoTitle.textContent = 'Error getting video info';
    updateExtractButtonState();
  }
}

// Extract subtitles
// 優先順: URL欄入力 > タブvideoId（既存）
async function extractSubtitles() {
  const targetVideoId = urlInputVideoId || tabVideoId;
  if (!targetVideoId) {
    showError('No video ID');
    return;
  }

  // ダウンロード時のファイル名用：URL欄経由なら videoId をタイトル代わりに使う
  if (urlInputVideoId) {
    tabVideoTitle = tabVideoTitle || '';
  }

  saveSettings();
  showLoading(true);
  hideError();
  hideResult();

  try {
    const response = await chrome.runtime.sendMessage({
      action: 'extractSubtitle',
      data: {
        video_id: targetVideoId,
        language: 'auto',
        subtitle_type: 'any',
        include_timestamp: elements.includeTimestamp.checked
      }
    });

    showLoading(false);

    if (response.success) {
      showResult(response.data);
    } else {
      showError(response.error || 'Failed to extract subtitles');
    }
  } catch (e) {
    showLoading(false);
    showError(e.message || 'Error');
  }
}

// Show result
function showResult(data) {
  elements.resultCount.textContent = `${data.line_count} lines`;
  elements.subtitleText.value = data.subtitle;
  elements.result.style.display = 'flex';
}

// Hide result
function hideResult() {
  elements.result.style.display = 'none';
}

// Show error
function showError(message) {
  elements.errorText.textContent = message;
  elements.error.style.display = 'block';
}

// Hide error
function hideError() {
  elements.error.style.display = 'none';
}

// Show/hide loading
function showLoading(show) {
  elements.loading.style.display = show ? 'flex' : 'none';
  elements.extractBtn.disabled = show;
}

// Copy to clipboard
async function copyToClipboard() {
  const text = elements.subtitleText.value;
  if (!text) return;

  try {
    await navigator.clipboard.writeText(text);
    showToast('Copied!');
  } catch (e) {
    // Fallback
    elements.subtitleText.select();
    document.execCommand('copy');
    showToast('Copied!');
  }
}

// Copy with prompt
async function copyWithPrompt() {
  const text = elements.subtitleText.value;
  if (!text) return;

  const fullText = activePrompt + '\n' + text;

  try {
    await navigator.clipboard.writeText(fullText);
    showToast('Copied with prompt!');
  } catch (e) {
    // Fallback
    const textarea = document.createElement('textarea');
    textarea.value = fullText;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    showToast('Copied with prompt!');
  }
}

// Download subtitles
function downloadSubtitles() {
  const text = elements.subtitleText.value;
  if (!text) return;

  // ファイル名：タブタイトル → URL欄のvideoId → 既定値
  const filename = `${tabVideoTitle || urlInputVideoId || 'subtitles'}.txt`;
  const blob = new Blob([text], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);

  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();

  URL.revokeObjectURL(url);
}

// Show toast
function showToast(message) {
  elements.toast.textContent = message;
  elements.toast.style.display = 'block';
  setTimeout(() => {
    elements.toast.style.display = 'none';
  }, 2000);
}
