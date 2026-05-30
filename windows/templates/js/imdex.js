// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this file,
// You can obtain one at https://mozilla.org/MPL/2.0/.

// Copyright (c) 2026 LingXuan-Li

// =========================================================
// GelMa HOME - FULL JS (SQLite + QWebChannel)
// =========================================================

let currentShortcuts = [];
let pybridge = null;

// =========================================================
// 初期化
// =========================================================
document.addEventListener('DOMContentLoaded', () => {
    initWebChannel();
    bindUIEvents();
});

// =========================================================
// WebChannel初期化
// =========================================================
function initWebChannel() {

    if (typeof qt === 'undefined') {
        console.warn('[FrameFit] Qt WebChannelなし → localStorage fallback');

        setupLocalFallback();
        loadLocal();
        return;
    }

    new QWebChannel(qt.webChannelTransport, function (channel) {

        pybridge = channel.objects.pybridge;

        console.log('[FrameFit] WebChannel connected');

        // -----------------------------------------
        // SQLite → データ受信
        // -----------------------------------------
        if (pybridge && typeof pybridge.shortcuts_loaded !== 'undefined') {
            pybridge.shortcuts_loaded.connect(function (jsonData) {

                try {
                    currentShortcuts = JSON.parse(jsonData || "[]");
                    renderShortcuts();
                } catch (e) {
                    console.error('[FrameFit] JSON parse error:', e);
                }
            });

        } else {
		    console.warn('[FrameFit] pybridge未初期化 → 自動フォールバック');
		    setupLocalFallback();
		    loadLocal();
        }
        // -----------------------------------------
        // 保存結果通知
        // -----------------------------------------
        pybridge.save_status_changed.connect(function (success, message) {

            console.log('[SQLite]', success, message);

            if (!success) {
                alert(message);
            }
        });

        // 初回ロード
        pybridge.load_shortcuts();
    });
}

// =========================================================
// UIイベント
// =========================================================
function bindUIEvents() {

    const nameInput = document.getElementById('shortcutName');
    const urlInput = document.getElementById('shortcutUrl');
    const searchInput = document.getElementById('searchInput');

    if (nameInput) {
        nameInput.addEventListener('keydown', e => {
            if (e.key === 'Enter') addShortcut();
        });
    }

    if (urlInput) {
        urlInput.addEventListener('keydown', e => {
            if (e.key === 'Enter') addShortcut();
        });
    }

    if (searchInput) {
        searchInput.addEventListener('keydown', e => {
            if (e.key === 'Enter') filterShortcuts();
        });
    }
}

// =========================================================
// 追加（SQLite保存）
// =========================================================
function addShortcut() {

    const name = document.getElementById('shortcutName').value.trim();
    let url = document.getElementById('shortcutUrl').value.trim();

    if (!name || !url) {
        alert('名前とURLを入力してください');
        return;
    }

    // protocol補完
    if (!/^https?:\/\//i.test(url)) {
        url = 'https://' + url;
    }

    try {
        new URL(url);
    } catch {
        alert('正しいURLを入力してください');
        return;
    }

    if (!pybridge) {
        alert('WebChannel未接続');
        return;
    }

    pybridge.save_shortcut(name, url);

    document.getElementById('shortcutName').value = '';
    document.getElementById('shortcutUrl').value = '';
}

// =========================================================
// 削除（SQLite）
// =========================================================
function deleteShortcut(id) {

    if (!confirm('削除しますか？')) return;

    if (pybridge) {
        pybridge.delete_shortcut(id);
    }
}

// =========================================================
// 検索
// =========================================================
function filterShortcuts() {

    const q = document.getElementById('searchInput').value.toLowerCase();

    if (!q) {
        renderShortcuts();
        return;
    }

    const filtered = currentShortcuts.filter(item => {
        return (
            item.name.toLowerCase().includes(q) ||
            item.url.toLowerCase().includes(q)
        );
    });

    renderShortcuts(filtered);
}

// =========================================================
// 描画
// =========================================================
function renderShortcuts(data = currentShortcuts) {

    const grid = document.getElementById('shortcutsGrid');
    const empty = document.getElementById('emptyMessage');

    if (!grid) return;

    grid.innerHTML = '';

    if (!data || data.length === 0) {
        if (empty) empty.style.display = 'block';
        return;
    }

    if (empty) empty.style.display = 'none';

    data.forEach(item => {

        const card = document.createElement('div');
        card.className = `tile ${getTheme(item.url)}`;

        card.innerHTML = `
            <button class="tile-delete" onclick="deleteShortcut(${item.id})">×</button>

            <div class="tile-header">
                <div class="tile-icon">${getIcon(item.url)}</div>
            </div>

            <div class="tile-body">
                <div class="tile-title">${escapeHtml(item.name)}</div>
                <div class="tile-url">${escapeHtml(item.url)}</div>
            </div>
        `;

        card.addEventListener('click', (e) => {
            if (!e.target.classList.contains('tile-delete')) {
                window.location.href = item.url;
            }
        });

        grid.appendChild(card);
    });
}

// =========================================================
// Google検索
// =========================================================
function googleSearch() {

    const q = document.getElementById('searchInput').value.trim();
    if (!q) return;

    window.location.href =
        `https://www.google.com/search?q=${encodeURIComponent(q)}`;
}

// =========================================================
// ユーティリティ
// =========================================================
function escapeHtml(str) {

    if (!str) return '';

    return str.replace(/[&<>"']/g, m => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    }[m]));
}

// =========================================================
// アイコン
// =========================================================
function getIcon(rawUrl) {
	try {
		const url = new URL(rawUrl.startsWith('http') ? rawUrl : `https://${rawUrl}`);
		const host = url.hostname.toLowerCase();

		const rules = [
			{ match: ['youtube.com', 'youtu.be'], icon: '▶️' },
			{ match: ['google.com', 'google.'], icon: '🔍' },
			{ match: ['amazon.'], icon: '📦' },
			{ match: ['github.com'], icon: '🐙' },
			{ match: ['twitter.com', 'x.com'], icon: '𝕏' },
			{ match: ['linkedin.com'], icon: '🔗' },
			{ match: ['spotify.com'], icon: '🎵' },
			{ match: ['discord.com', 'discord.gg'], icon: '🗪' },
			{ match: ['firefox.com', 'mozilla.org'], icon: '🦊' },
            { match: ['duckduckgo.com'], icon: '🐦' },
			{ match: ['instagram.com'], icon: '📷' },
			{ match: ['facebook.com', 'fb.com'], icon: '𝕗' },
			{ match: ['netflix.com'], icon: '🎬' },
			{ match: ['chatgpt.com', 'openai.com'], icon: '🤖' },
			{ match: ['gemini.google'], icon: '🤖' },
			{ match: ['claude.ai'], icon: '🤖' },
			{ match: ['tiktok.com'], icon: '🎵' },
			{ match: ['reddit.com'], icon: '👽' },
			{ match: ['wikipedia.org'], icon: '📚' },
			{ match: ['yahoo.com'], icon: '𝕐' },
			{ match: ['bing.com'], icon: '𝕓' },
			{ match: ['drive.google.com'], icon: '🗂️' },
			{ match: ['maps.google'], icon: '🗺️' },
			{ match: ['apple.com'], icon: '🍎' },
			{ match: ['microsoft.com'], icon: '🪟' },
			{ match: ['slack.com'], icon: '💬' },
			{ match: ['notion.so', 'notion.com'], icon: '📝' },
			{ match: ['figma.com'], icon: '🎨' },
			{ match: ['zenn.dev'], icon: 'ℤ' },
			{ match: ['qiita.com'], icon: 'ℚ' },
			{ match: ['gamewith.jp'], icon: '🎮' },
			{ match: ['game8.jp'], icon: '🎮' },
			{ match: ['nicovideo.jp'], icon: '🎥' },
			{ match: ['tenki.jp'], icon: '🌤️' },
			{ match: ['wikidot.com'], icon: '🆆' },

			// ローカル系
			{ match: ['localhost'], icon: '🖥️'  },
			{ match: ['127.0.0.1'], icon: '🖥️' },
		];

		for (const rule of rules) {
			if (rule.match.some(m => host.includes(m))) {
				return rule.icon;
			}
		}

		return '🌐'; // デフォルト
	} catch {
		return '🌐';
	}
}

// =========================================================
// テーマ
// =========================================================
function getTheme(url) {
    url = (url || '').toLowerCase();

    // マッチ条件とテーマ名の定義リスト
    const themeRules = [
        { match: ['youtube.com', 'youtu.be', 'youtube'], theme: 'youtube' },
        { match: ['google.com', 'google.', 'google'], theme: 'google' },
        { match: ['amazon.', 'amazon'], theme: 'amazon' },
        { match: ['github.com', 'github'], theme: 'github' },
        { match: ['twitter.com', 'x.com'], theme: 'twitter' },
        { match: ['linkedin.com'], theme: 'linkedin' },
        { match: ['spotify.com', 'spotify.com'], theme: 'spotify' },
        { match: ['discord.com', 'discord.gg'], theme: 'discord' },
        { match: ['firefox.com', 'mozilla.org'], theme: 'firefox' },
        { match: ['duckduckgo.com'], theme: 'duckduckgo' },
        { match: ['instagram.com'], theme: 'instagram' },
        { match: ['facebook.com', 'fb.com'], theme: 'facebook' },
        { match: ['netflix.com'], theme: 'netflix' },
        { match: ['chatgpt.com', 'openai.com'], theme: 'chatgpt' },
        { match: ['gemini.google'], theme: 'gemini' },
        { match: ['claude.ai'], theme: 'claude' },
        { match: ['tiktok.com'], theme: 'tiktok' },
        { match: ['reddit.com'], theme: 'reddit' },
        { match: ['wikipedia.org'], theme: 'wikipedia' },
        { match: ['yahoo.com'], theme: 'yahoo' },
        { match: ['bing.com'], theme: 'bing' },
        { match: ['drive.google.com'], theme: 'google-drive' },
        { match: ['maps.google'], theme: 'google-maps' },
        { match: ['apple.com'], theme: 'apple' },
        { match: ['microsoft.com'], theme: 'microsoft' },
        { match: ['slack.com'], theme: 'slack' },
        { match: ['notion.so', 'notion.com'], theme: 'notion' },
        { match: ['figma.com'], theme: 'figma' },
        { match: ['zenn.dev'], theme: 'zenn' },
        { match: ['qiita.com'], theme: 'qiita' },
        { match: ['gamewith.jp'], theme: 'gamewith' },
        { match: ['game8.jp'], theme: 'game8' },
        { match: ['nicovideo.jp'], theme: 'nicovideo' },
        { match: ['tenki.jp'], theme: 'tenki' },
        { match: ['wikidot.com'], theme: 'wikidot' },
        
        // ローカル系
        { match: ['localhost', '127.0.0.1'], theme: 'local' }
    ];

    // URLに含まれる文字列があるかループで判定
    for (const rule of themeRules) {
        // match配列のいずれかがURLに含まれているかチェック
        const isMatch = rule.match.some(keyword => url.includes(keyword));
        if (isMatch) {
            return rule.theme;
        }
    }

    return 'default';
}

// =========================================================
// fallback（ローカル用）
// =========================================================
function setupLocalFallback() {

    window.pybridge = {

        save_shortcut(name, url) {

            const data = JSON.parse(localStorage.getItem('shortcuts') || '[]');

            data.unshift({ id: Date.now(), name, url });

            localStorage.setItem('shortcuts', JSON.stringify(data));

            currentShortcuts = data;
            renderShortcuts();
        },

        delete_shortcut(id) {

            let data = JSON.parse(localStorage.getItem('shortcuts') || '[]');

            data = data.filter(x => x.id !== id);

            localStorage.setItem('shortcuts', JSON.stringify(data));

            currentShortcuts = data;
            renderShortcuts();
        },

        load_shortcuts() {

            currentShortcuts =
                JSON.parse(localStorage.getItem('shortcuts') || '[]');

            renderShortcuts();
        }
    };
}

// =========================================================
// fallback load
// =========================================================
function loadLocal() {
    window.pybridge.load_shortcuts();
}