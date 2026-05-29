# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2026 LingXuan-Li

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush


class SafeAreaOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.margin = 40
        self.enabled = True
        self.test_pattern = False

        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)

        self.setStyleSheet("background: transparent;")

    def set_margin(self, value):
        self.margin = value
        self.update()

    def set_enabled(self, value):
        self.enabled = value
        self.update()

    def set_test_pattern(self, value):
        self.test_pattern = value
        self.update()

    def paintEvent(self, event):
        if not self.enabled:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        m = self.margin

        # テストパターン背景
        if self.test_pattern:
            self._draw_test_pattern(painter, w, h)

        # safe rect
        pen = QPen(QColor(0, 255, 0, 180))
        pen.setWidth(3)
        painter.setPen(pen)
        painter.drawRect(m, m, w - (m * 2), h - (m * 2))

        # center line
        center_pen = QPen(QColor(255, 255, 255, 120))
        center_pen.setWidth(1)
        painter.setPen(center_pen)
        painter.drawLine(w // 2, 0, w // 2, h)
        painter.drawLine(0, h // 2, w, h // 2)

        # corner markers
        marker = 20
        painter.setPen(pen)
        painter.drawLine(m, m, m + marker, m)
        painter.drawLine(m, m, m, m + marker)
        painter.drawLine(w - m, m, w - m - marker, m)
        painter.drawLine(w - m, m, w - m, m + marker)
        painter.drawLine(m, h - m, m + marker, h - m)
        painter.drawLine(m, h - m, m, h - m - marker)
        painter.drawLine(w - m, h - m, w - m - marker, h - m)
        painter.drawLine(w - m, h - m, w - m, h - m - marker)

    def _draw_test_pattern(self, painter, w, h):
        """テストパターンを描画"""
        # グラデーション背景
        step_v = h // 5
        colors = [
            QColor(255, 0, 0, 50),      # Red
            QColor(255, 255, 0, 50),    # Yellow
            QColor(0, 255, 0, 50),      # Green
            QColor(0, 0, 255, 50),      # Blue
            QColor(255, 0, 255, 50),    # Magenta
        ]
        
        for i, color in enumerate(colors):
            painter.fillRect(0, i * step_v, w, step_v, color)

        # 水平グリッド
        grid_pen = QPen(QColor(255, 255, 255, 30))
        grid_pen.setWidth(1)
        painter.setPen(grid_pen)
        
        grid_step = 50
        for x in range(0, w, grid_step):
            painter.drawLine(x, 0, x, h)
        for y in range(0, h, grid_step):
            painter.drawLine(0, y, w, y)
