// Textube Chrome Extension - Popup Script

const elements = {
  videoInfo: document.getElementById('videoInfo'),
  videoTitle: document.getElementById('videoTitle'),
  includeTimestamp: document.getElementById('includeTimestamp'),
  extractBtn: document.getElementById('extractBtn'),
  loading: document.getElementById('loading'),
  result: document.getElementById('result'),
  resultCount: document.getElementById('resultCount'),
  subtitleText: document.getElementById('subtitleText'),
  copyBtn: document.getElementById('copyBtn'),
  downloadBtn: document.getElementById('downloadBtn'),
  error: document.getElementById('error'),
  errorText: document.getElementById('errorText'),
  statusDot: document.getElementById('statusDot'),
  statusText: document.getElementById('statusText'),
  toast: document.getElementById('toast')
};

let currentVideoId = null;
let currentVideoTitle = '';

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
  await loadSettings();
  await checkServerStatus();
  await getVideoInfo();

  elements.extractBtn.addEventListener('click', extractSubtitles);
  elements.copyBtn.addEventListener('click', copyToClipboard);
  elements.downloadBtn.addEventListener('click', downloadSubtitles);
});

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

// Check server status
async function checkServerStatus() {
  try {
    const response = await chrome.runtime.sendMessage({ action: 'checkServer' });
    if (response.online) {
      elements.statusDot.className = 'status-dot online';
      elements.statusText.textContent = 'Server online';
      elements.extractBtn.disabled = false;
    } else {
      elements.statusDot.className = 'status-dot offline';
      elements.statusText.textContent = 'Server offline';
      elements.extractBtn.disabled = true;
    }
  } catch (e) {
    elements.statusDot.className = 'status-dot offline';
    elements.statusText.textContent = 'Error';
  }
}

// Get video info from content script
async function getVideoInfo() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    if (!tab.url.includes('youtube.com/watch')) {
      elements.videoTitle.textContent = 'Not a YouTube video page';
      elements.extractBtn.disabled = true;
      return;
    }

    // Try to get info from content script
    try {
      const response = await chrome.tabs.sendMessage(tab.id, { action: 'getVideoInfo' });
      if (response && response.videoId) {
        currentVideoId = response.videoId;
        currentVideoTitle = response.title || 'Unknown';
        elements.videoTitle.textContent = currentVideoTitle;
        return;
      }
    } catch (e) {
      // Content script not loaded, extract from URL
    }

    // Fallback: extract from URL
    const url = new URL(tab.url);
    currentVideoId = url.searchParams.get('v');
    if (currentVideoId) {
      currentVideoTitle = tab.title.replace(' - YouTube', '').trim();
      elements.videoTitle.textContent = currentVideoTitle;
    } else {
      elements.videoTitle.textContent = 'Could not get video ID';
      elements.extractBtn.disabled = true;
    }
  } catch (e) {
    elements.videoTitle.textContent = 'Error getting video info';
    elements.extractBtn.disabled = true;
  }
}

// Extract subtitles
async function extractSubtitles() {
  if (!currentVideoId) {
    showError('No video ID');
    return;
  }

  saveSettings();
  showLoading(true);
  hideError();
  hideResult();

  try {
    const response = await chrome.runtime.sendMessage({
      action: 'extractSubtitle',
      data: {
        video_id: currentVideoId,
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

// Download subtitles
function downloadSubtitles() {
  const text = elements.subtitleText.value;
  if (!text) return;

  const filename = `${currentVideoTitle || 'subtitles'}.txt`;
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
