# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2026 LingXuan-Li

"""
ロギングシステム
- UTF-8 固定
- Qt ログ統合
- 出力時安全エンコーディング
- 文字化け検知
- 自動バグ検知
"""

import logging
import sys
import traceback
from pathlib import Path
from datetime import datetime
from collections import deque


# =========================================================
# UTF-8 強制（Windows対策）
# =========================================================

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


# =========================================================
# JST Formatter
# =========================================================

class JSTFormatter(logging.Formatter):
    """JST タイムゾーン付きフォーマッタ"""

    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created)

        if datefmt:
            return dt.strftime(datefmt)

        return dt.strftime("%Y-%m-%d %H:%M:%S")


# =========================================================
# 安全エンコーディング Formatter
# =========================================================

class SafeEncodingFormatter(JSTFormatter):
    """
    出力時に文字コード問題を吸収する
    """

    def format(self, record):
        try:
            # メッセージ生成
            msg = super().format(record)

            # UTF-8 安全化
            msg = self._sanitize(msg)

            return msg

        except Exception as e:
            return f"[LOGGER FORMAT ERROR] {e}"

    def _sanitize(self, text: str) -> str:
        if not isinstance(text, str):
            try:
                text = str(text)
            except Exception:
                return "<unprintable>"

        # UTF-8安全化
        try:
            text = text.encode("utf-8", errors="replace").decode(
                "utf-8",
                errors="replace"
            )
        except Exception:
            text = repr(text)

        # NULL文字除去
        text = text.replace("\x00", "")

        return text


# =========================================================
# 文字化け検知
# =========================================================

class MojibakeDetector:
    """
    文字化け監視
    """

    def __init__(self):
        self.window = deque(maxlen=50)

    def check(self, text: str):

        if not isinstance(text, str):
            return None

        replacement_count = text.count("�")

        self.window.append(replacement_count)

        total = sum(self.window)

        # 単発検知
        if replacement_count >= 3:
            return (
                f"[MOJIBAKE] replacement_char={replacement_count}"
            )

        # スパイク検知
        if total >= 20:
            return (
                f"[MOJIBAKE SPIKE] total={total}"
            )

        return None


# =========================================================
# バグ検知
# =========================================================

class BugDetector:
    """
    ログから異常検知
    """

    PATTERNS = {
        "D3D11": "GPU/D3D11 Error",
        "swapchain": "SwapChain Error",
        "Failed to create 2D texture": "Texture Creation Error",
        "Traceback": "Python Exception",
        "Segmentation fault": "Crash",
        "QWindowsWindow::setGeometry": "Geometry Error",
        "maximum texture size": "Texture Size Overflow",
    }

    def analyze(self, text: str):

        alerts = []

        for pattern, label in self.PATTERNS.items():
            if pattern in text:
                alerts.append(label)

        return alerts


# =========================================================
# グローバル検知器
# =========================================================

mojibake_detector = MojibakeDetector()
bug_detector = BugDetector()


# =========================================================
# ログフィルタ
# =========================================================

class SmartLogFilter(logging.Filter):

    def filter(self, record):

        try:
            msg = str(record.getMessage())

            # ---------------------------------------------
            # 文字化け検知
            # ---------------------------------------------

            mojibake = mojibake_detector.check(msg)

            if mojibake:
                record.msg = f"{record.msg} 🚨 {mojibake}"

            # ---------------------------------------------
            # バグ検知
            # ---------------------------------------------

            alerts = bug_detector.analyze(msg)

            if alerts:
                joined = ", ".join(alerts)
                record.msg = f"{record.msg} 🚨 [{joined}]"

        except Exception:
            pass

        return True


# =========================================================
# setup_logger
# =========================================================

def setup_logger():

    # -----------------------------------------------------
    # log ディレクトリ
    # -----------------------------------------------------

    log_dir = Path(__file__).parent.parent / "log"
    log_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now()

    log_filename = f"{now.strftime('%Y%m%d%H%M')}JST.log"

    log_filepath = log_dir / log_filename

    # -----------------------------------------------------
    # root logger
    # -----------------------------------------------------

    root_logger = logging.getLogger()

    root_logger.setLevel(logging.DEBUG)

    # 既存削除
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)

    # -----------------------------------------------------
    # formatter
    # -----------------------------------------------------

    formatter = SafeEncodingFormatter(
        fmt='[%(asctime)s] [%(levelname)-8s] [%(name)-30s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # -----------------------------------------------------
    # file handler
    # -----------------------------------------------------

    file_handler = logging.FileHandler(
        log_filepath,
        encoding="utf-8",
        mode="w"
    )

    file_handler.setLevel(logging.DEBUG)

    file_handler.setFormatter(formatter)

    file_handler.addFilter(SmartLogFilter())

    root_logger.addHandler(file_handler)

    # -----------------------------------------------------
    # console handler
    # -----------------------------------------------------

    console_handler = logging.StreamHandler(sys.stdout)

    console_handler.setLevel(logging.DEBUG)

    console_handler.setFormatter(formatter)

    console_handler.addFilter(SmartLogFilter())

    root_logger.addHandler(console_handler)

    # =====================================================
    # Qt Message Handler
    # =====================================================

    try:

        from PyQt6.QtCore import (
            QtMsgType,
            qInstallMessageHandler
        )

        def qt_message_handler(msg_type, msg_context, msg_string):

            level_map = {
                QtMsgType.QtDebugMsg: logging.DEBUG,
                QtMsgType.QtInfoMsg: logging.INFO,
                QtMsgType.QtWarningMsg: logging.WARNING,
                QtMsgType.QtCriticalMsg: logging.ERROR,
                QtMsgType.QtFatalMsg: logging.CRITICAL,
            }

            level = level_map.get(msg_type, logging.DEBUG)

            # ---------------------------------------------
            # 重要:
            # 入力側は触らない
            # 出力時に formatter で安全化
            # ---------------------------------------------

            try:
                msg = str(msg_string)
            except Exception:
                msg = repr(msg_string)

            # context
            file = None
            line = None

            try:
                if msg_context:
                    file = msg_context.file
                    line = msg_context.line
            except Exception:
                pass

            if file:
                msg = f"{msg} ({file}:{line})"

            qt_logger = logging.getLogger("Qt")

            qt_logger.log(level, msg)

        qInstallMessageHandler(qt_message_handler)

        logging.info("[Logger] Qt message handler installed")

    except Exception as e:

        logging.warning(
            f"[Logger] Qt handler install failed: {e}"
        )

    # =====================================================
    # 起動ログ
    # =====================================================

    logging.info("=" * 80)
    logging.info("GelMa ログシステム起動")
    logging.info(f"📝 ログファイル: {log_filepath}")
    logging.info("=" * 80)

    return logging.getLogger(__name__)


# =========================================================
# exception logger
# =========================================================

def log_exception(exc_info=None):

    logger = logging.getLogger(__name__)

    if exc_info is None:
        exc_info = sys.exc_info()

    logger.error("=" * 80)
    logger.error("❌ 予期しない例外")
    logger.error("=" * 80)

    logger.error(
        "".join(
            traceback.format_exception(*exc_info)
        )
    )

    logger.error("=" * 80)


# =========================================================
# initialize
# =========================================================

logger = setup_logger()