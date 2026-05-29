# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2026 LingXuan-Li

"""SQLite ベースの設定管理"""

import sqlite3
import os
from pathlib import Path

# from utils.logger import setup_logger
# setup_logger()
import logging

logger = logging.getLogger(__name__)

class SettingsManager:
    def __init__(self):
        # データベースファイルのパス
        appdata = os.getenv("APPDATA")
        if appdata is None:
            appdata = os.path.expanduser("~")
        
        self.db_dir = Path(appdata) / "GelMa"
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.db_file = self.db_dir / "gelma.db"

        # DB初期化
        self._init_db()

    def _init_db(self):
        """データベーステーブルの初期化"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT,
                scale_v REAL,
                scale_h REAL,
                margin INTEGER,
                safe_area INTEGER,
                test_pattern INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shortcuts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # デフォルト値の挿入
        defaults = {
            'url': 'about:blank',
            'margin': '40',
            'scale_v': '1.0',
            'scale_h': '1.0',
            'safe_area': '1',
            'test_pattern': '0',
        }
        
        for key, value in defaults.items():
            cursor.execute(
                'INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)',
                (key, value)
            )
        
        conn.commit()
        conn.close()

    def get(self, key: str, default=None):
        """設定値を取得"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                value = result[0]
                # 型変換
                if key in ['margin']:
                    return int(value)
                elif key in ['scale_v', 'scale_h']:
                    return float(value)
                elif key in ['safe_area', 'test_pattern']:
                    return int(value)
                return value
            return default
        except Exception as e:
            logger.error(f"[SettingsManager] Error getting {key}: {e}")
            return default

    def set(self, key: str, value):
        """設定値を設定"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute(
                'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
                (key, str(value))
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"[SettingsManager] Error setting {key}: {e}")

    def get_all(self) -> dict:
        """すべての設定を取得"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('SELECT key, value FROM settings')
            results = cursor.fetchall()
            conn.close()
            
            config = {}
            for key, value in results:
                if key in ['margin']:
                    config[key] = int(value)
                elif key in ['scale_v', 'scale_h']:
                    config[key] = float(value)
                elif key in ['safe_area', 'test_pattern']:
                    config[key] = int(value)
                else:
                    config[key] = value
            return config
        except Exception as e:
            logger.error(f"[SettingsManager] Error getting all: {e}")
            return {}

    def save_history(self, url: str, scale_v: float, scale_h: float, 
                     margin: int, safe_area: int, test_pattern: int):
        """履歴を保存"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO history 
                (url, scale_v, scale_h, margin, safe_area, test_pattern)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (url, scale_v, scale_h, margin, safe_area, test_pattern))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"[SettingsManager] Error saving history: {e}")

    def reset(self):
        """デフォルト設定にリセット"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM settings')
            conn.commit()
            conn.close()
            self._init_db()
        except Exception as e:
            logger.error(f"[SettingsManager] Error resetting: {e}")

    # ========================================
    # ショートカット管理
    # ========================================

    def get_shortcuts(self) -> list:
        """すべてのショートカットを取得"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, url FROM shortcuts ORDER BY created_at DESC')
            results = cursor.fetchall()
            conn.close()
            
            shortcuts = []
            for id, name, url in results:
                shortcuts.append({
                    'id': id,
                    'name': name,
                    'url': url
                })
            return shortcuts
        except Exception as e:
            logger.error(f"[SettingsManager] Error getting shortcuts: {e}")
            return []

    def add_shortcut(self, name: str, url: str) -> bool:
        """ショートカットを追加"""
        try:
            # URLの正規化
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO shortcuts (name, url) VALUES (?, ?)',
                (name, url)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"[SettingsManager] Error adding shortcut: {e}")
            return False

    def delete_shortcut(self, shortcut_id: int) -> bool:
        """ショートカットを削除"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM shortcuts WHERE id = ?', (shortcut_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"[SettingsManager] Error deleting shortcut: {e}")
            return False

    def update_shortcut(self, shortcut_id: int, name: str = None, url: str = None) -> bool:
        """ショートカットを更新"""
        try:
            if name is None and url is None:
                return False
            
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            if name and url:
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                cursor.execute(
                    'UPDATE shortcuts SET name = ?, url = ? WHERE id = ?',
                    (name, url, shortcut_id)
                )
            elif name:
                cursor.execute(
                    'UPDATE shortcuts SET name = ? WHERE id = ?',
                    (name, shortcut_id)
                )
            elif url:
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                cursor.execute(
                    'UPDATE shortcuts SET url = ? WHERE id = ?',
                    (url, shortcut_id)
                )
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"[SettingsManager] Error updating shortcut: {e}")
            return False
