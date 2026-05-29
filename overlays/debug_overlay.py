# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2026 LingXuan-Li

"""デバッグ表示用Overlay"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QFont


class DebugOverlay(QWidget):
    """デバッグ情報を表示するOverlay"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.enabled = False
        self.debug_info = {}

        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setStyleSheet("background: transparent;")

        # FPS計測用
        self.frame_count = 0
        self.fps = 0
        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self.update_fps)
        self.fps_timer.start(1000)  # 1秒ごと

    def update_fps(self):
        """FPS更新"""
        self.fps = self.frame_count
        self.frame_count = 0
        if self.enabled:
            self.update()

    def set_info(self, key: str, value):
        """デバッグ情報を設定"""
        self.debug_info[key] = value
        if self.enabled:
            self.update()

    def set_enabled(self, enabled: bool):
        """表示/非表示"""
        self.enabled = enabled
        if enabled:
            self.fps_timer.start()
        else:
            self.fps_timer.stop()
        self.update()

    def paintEvent(self, event):
        if not self.enabled:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 背景（半透明）
        bg_color = QColor(0, 0, 0, 180)
        painter.fillRect(self.rect(), bg_color)

        # テキスト
        text_color = QColor(0, 255, 0)
        painter.setPen(text_color)

        font = QFont("Courier")
        font.setPointSize(8)
        painter.setFont(font)

        y = 20
        line_height = 18

        info_list = [
            f"FPS: {self.fps}",
            f"Resolution: {self.width()}x{self.height()}",
        ]

        for key, value in self.debug_info.items():
            info_list.append(f"{key}: {value}")

        for info in info_list:
            painter.drawText(20, y, info)
            y += line_height

        self.frame_count += 1
