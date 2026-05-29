# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2026 LingXuan-Li

"""SQLite3とQWebChannelを連携させるブリッジモジュール"""

import os
import sqlite3
import logging
import json
from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal

logger = logging.getLogger(__name__)

class SQLWebChannel(QObject):
    """
    QWebChannelを通じてHTML/JS(フロントエンド)から直接呼び出され、
    SQLiteデータベースへの保存や読み込みを安全に行うためのブリッジクラス。
    """
    
    # 処理結果やデータ更新をフロントエンド（JavaScript側）に通知するためのシグナル
    save_status_changed = pyqtSignal(bool, str)  # (成功フラグ, メッセージ)
    shortcuts_loaded = pyqtSignal(str)          # JSON形式のショートカット一覧データ

    def __init__(self):
        super().__init__()
        self.db_path = self._init_db_path()
        self._create_table_if_not_exists()

    def _init_db_path(self) -> str:
        """%APPDATA%/GelMa/gelma.db の絶対パスを取得し、フォルダがない場合は自動生成する"""
        app_data = os.environ.get("APPDATA")
        if not app_data:
            # Windows以外のOSや環境変数が見つからない場合の安全なフォールバック
            app_data = os.path.expanduser("~\\AppData\\Roaming")
            
        db_dir = os.path.join(app_data, "GelMa")
        os.makedirs(db_dir, exist_ok=True)  # ディレクトリがなければ作成
        return os.path.join(db_dir, "gelma.db")

    def _get_connection(self):
        """SQLiteへの接続を取得し、カラム名でデータを扱いやすくする設定を適用"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 辞書形式(key-value)でのデータ取得を可能にする
        return conn

    def _create_table_if_not_exists(self):
        """指定されたカラム構造を持つ shortcuts テーブルを初期化時に自動作成"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS shortcuts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        url TEXT NOT NULL,
                        created_at TEXT DEFAULT (DATETIME('now', 'localtime'))
                    )
                """)
                conn.commit()
            logger.info(f"SQLite初期化完了 パス: {self.db_path}")
        except Exception as e:
            logger.error(f"SQLiteテーブル作成失敗: {e}")

    @pyqtSlot(str, str)
    def save_shortcut(self, name: str, url: str):
        """
        index.htmlのJavaScript側から直接呼び出される保存用メソッド。
        
        Args:
            name (str): ショートカットの名称
            url (str): 保存するURL
        """
        logger.info(f"SQLWebChannel: 保存リクエストを受信 -> name: {name}, url: {url}")
        
        # バリデーション（空文字チェック）
        if not name.strip() or not url.strip():
            self.save_status_changed.emit(False, "名前またはURLが入力されていません。")
            return

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO shortcuts (name, url) 
                    VALUES (?, ?)
                """, (name.strip(), url.strip()))
                conn.commit()
            
            logger.info("SQLWebChannel: SQLiteへのコミットに成功しました。")
            self.save_status_changed.emit(True, "SQLiteへの保存が完了しました。")
            
            # 保存成功後、自動的に最新のリストをフロントエンドへ再配信する
            self.load_shortcuts()
            
        except Exception as e:
            error_msg = f"SQLiteデータベース保存エラー: {str(e)}"
            logger.error(error_msg)
            self.save_status_changed.emit(False, error_msg)

    @pyqtSlot()
    def load_shortcuts(self):
        """
        データベースから登録済みの全ショートカットを取得し、
        JSON文字列に変換してJavaScript側にシグナルで通知するメソッド。
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name, url, created_at FROM shortcuts ORDER BY id DESC")
                rows = cursor.fetchall()
                
                # sqlite3.RowオブジェクトをJavaScriptが解釈しやすい辞書(オブジェクト)配列に変換
                shortcuts_list = [dict(row) for row in rows]
                
            json_data = json.dumps(shortcuts_list, ensure_ascii=False)
            self.shortcuts_loaded.emit(json_data)
            logger.info("SQLWebChannel: ショートカット一覧の配信に成功しました。")
            
        except Exception as e:
            logger.error(f"SQLiteデータ読み込みエラー: {e}")
            self.shortcuts_loaded.emit(json.dumps([])) # エラー時は空配列を返す

    @pyqtSlot(int)
    def delete_shortcut(self, shortcut_id: int):
        """指定されたIDのショートカットをデータベースから削除する"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM shortcuts WHERE id = ?", (shortcut_id,))
                conn.commit()
            logger.info(f"SQLWebChannel: Deleted shortcut ID {shortcut_id}")
            self.save_status_changed.emit(True, "ショートカットを削除しました。")
            self.load_shortcuts() # 最新リストを再送
        except Exception as e:
            logger.error(f"SQLiteデータ削除エラー: {e}")
            self.save_status_changed.emit(False, f"削除失敗: {str(e)}")