# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2026 LingXuan-Li

"""ディスプレイ画面（TV表示用）"""

import logging
import sys

from PyQt6.QtCore import Qt, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
	QApplication,
	QHBoxLayout,
	QLabel,
	QMainWindow,
	QPushButton,
	QSlider,
	QVBoxLayout,
	QWidget,
)
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from pathlib import Path
import logging
from PyQt6.QtWebChannel import QWebChannel

from windows.sql_webchannel import SQLWebChannel
from utils.color_bridge import ColorBridge, inject_color_detection_js
from overlays.debug_overlay import DebugOverlay
from overlays.safe_area_overlay import SafeAreaOverlay
from utils.settings_manager import SettingsManager
# from utils.logger import setup_logger

# setup_logger()
logger = logging.getLogger(__name__)


class DisplayWindow(QMainWindow):
	"""TV表示用ウィンドウ"""

	scale_v_changed = pyqtSignal(float)
	scale_h_changed = pyqtSignal(float)
	margin_changed = pyqtSignal(int)

	# =========================================================
	# 初期化
	# =========================================================

	def __init__(self):
		super().__init__()

		logger.info("DisplayWindow 初期化")

		self.settings = SettingsManager()

		# -----------------------------------------------------
		# 状態
		# -----------------------------------------------------

		self.scale_v = float(self.settings.get("scale_v", 1.0))
		self.scale_h = float(self.settings.get("scale_h", 1.0))
		self.margin = int(self.settings.get("margin", 40))

		self.safe_area_enabled = True
		self.safe_area_visible = True
		self.test_pattern_enabled = bool(
			self.settings.get("test_pattern", 0)
		)

		# GPU限界超え防止
		self.MAX_TEXTURE_SIZE = 16384

		# -----------------------------------------------------
		# Window
		# -----------------------------------------------------

		self.setWindowTitle("GelMa - Display")

		self.setWindowFlags(
			Qt.WindowType.Window
			| Qt.WindowType.FramelessWindowHint
			# | Qt.WindowType.WindowStaysOnTopHint
		)

		self.setStyleSheet("background:black;")

		# -----------------------------------------------------
		# WebEngine
		# -----------------------------------------------------

		self.view = QWebEngineView()

		profile = QWebEngineProfile.defaultProfile()
		settings = profile.settings()

		settings.setAttribute(
			QWebEngineSettings.WebAttribute.ShowScrollBars,
			False,
		)

		# GPU暴走対策
		settings.setAttribute(
			QWebEngineSettings.WebAttribute.WebGLEnabled,
			False,
		)

		settings.setAttribute(
			QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled,
			False,
		)

		settings.setAttribute(
			QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture,
			False,
		)

		# ColorBridge連携用の初期化
		self.color_bridge = ColorBridge()
		self.web_channel = QWebChannel(self.view.page())
		
		# JS側から "colorBridge" という名前で呼び出せるように登録
		self.web_channel.registerObject("colorBridge", self.color_bridge)
		self.view.page().setWebChannel(self.web_channel)
		
		# シグナルとスロットの接続
		self.color_bridge.color_changed.connect(self.on_web_color_changed)
		self.view.loadFinished.connect(self.inject_color_observer)

		# -----------------------------------------------------
		# Layout
		# -----------------------------------------------------

		self.container_widget = QWidget()
		self.container_widget.setStyleSheet("background:black;")

		self.container_layout = QVBoxLayout()
		self.container_layout.setContentsMargins(0, 0, 0, 0)
		self.container_layout.setSpacing(0)

		self.container_layout.addWidget(self.view)

		self.container_widget.setLayout(self.container_layout)

		self.main_widget = QWidget()

		self.main_layout = QHBoxLayout()
		self.main_layout.setContentsMargins(0, 0, 0, 0)
		self.main_layout.setSpacing(0)

		self.main_layout.addStretch()

		self.main_layout.addWidget(
			self.container_widget,
			alignment=Qt.AlignmentFlag.AlignCenter,
		)

		self.main_layout.addStretch()

		self.main_widget.setLayout(self.main_layout)

		self.setCentralWidget(self.main_widget)

		# -----------------------------------------------------
		# Overlay
		# -----------------------------------------------------

		self.overlay = SafeAreaOverlay(self)
		self.overlay.raise_()

		self.debug_overlay = DebugOverlay(self)
		self.debug_overlay.raise_()

		# -----------------------------------------------------
		# Control Panel
		# -----------------------------------------------------

		self.control_panel = self._create_control_panel()
		self.control_panel.hide()

		# -----------------------------------------------------
		# Shortcut
		# -----------------------------------------------------

		QShortcut(QKeySequence("R"), self, activated=self.reload)
		QShortcut(QKeySequence("S"), self, activated=self.toggle_safe_area)
		QShortcut(QKeySequence("D"), self, activated=self.toggle_debug)
		QShortcut(QKeySequence("T"), self, activated=self.toggle_test_pattern)
		QShortcut(QKeySequence("C"), self, activated=self.toggle_control_panel)

		QShortcut(
			QKeySequence(Qt.Key.Key_Up),
			self,
			activated=self.margin_up,
		)

		QShortcut(
			QKeySequence(Qt.Key.Key_Down),
			self,
			activated=self.margin_down,
		)

		# -----------------------------------------------------
		# 表示
		# -----------------------------------------------------

		self.show()
		self.showFullScreen()

		QTimer.singleShot(100, self.apply_frame_scale)

		self.web_channel = QWebChannel()
		self.sql_bridge = SQLWebChannel()
		
		# -----------------------------------------------------
		# SQLWebChannel を WebChannel に登録
		# ------------------------------------------------------

		# JavaScript側で "pybridge" として参照可能になる
		self.web_channel.registerObject("pybridge", self.sql_bridge)
		
		# DisplayWindow の view に WebChannel を割り当て
		self.view.page().setWebChannel(self.web_channel)
		
		logger.info("[DisplayWindow] WebChannel セットアップ完了")

	# =========================================================
	# UI
	# =========================================================

	def _create_control_panel(self):

		panel = QWidget(self)

		panel.setStyleSheet("""
			background: rgba(0,0,0,0.85);
			border-top: 1px solid #666;
		""")

		layout = QHBoxLayout()
		layout.setContentsMargins(10, 5, 10, 5)

		# Vertical
		v_label = QLabel("V")
		v_label.setStyleSheet("color:white;")

		self.v_slider = QSlider(Qt.Orientation.Horizontal)
		self.v_slider.setRange(25, 100)
		self.v_slider.setValue(int(self.scale_v * 50))
		self.v_slider.setMaximumWidth(120)

		self.v_slider.valueChanged.connect(
			self._on_v_slider_changed
		)

		# Horizontal
		h_label = QLabel("H")
		h_label.setStyleSheet("color:white;")

		self.h_slider = QSlider(Qt.Orientation.Horizontal)
		self.h_slider.setRange(25, 100)
		self.h_slider.setValue(int(self.scale_h * 50))
		self.h_slider.setMaximumWidth(120)

		self.h_slider.valueChanged.connect(
			self._on_h_slider_changed
		)

		# Buttons
		btn_reload = QPushButton("Reload")
		btn_reload.clicked.connect(self.reload)

		btn_safe = QPushButton("SafeArea")
		btn_safe.clicked.connect(self.toggle_safe_area)

		btn_test = QPushButton("Test")
		btn_test.clicked.connect(self.toggle_test_pattern)

		layout.addWidget(v_label)
		layout.addWidget(self.v_slider)

		layout.addSpacing(20)

		layout.addWidget(h_label)
		layout.addWidget(self.h_slider)

		layout.addSpacing(20)

		layout.addWidget(btn_reload)
		layout.addWidget(btn_safe)
		layout.addWidget(btn_test)

		layout.addStretch()

		panel.setLayout(layout)

		return panel

	# =========================================================
	# ウィンドウモード切り替え
	# =========================================================

	def set_mode(self, is_single_screen: bool):
		"""
		ウィンドウモード設定
		
		Args:
			is_single_screen: True = 通常ウィンドウ, False = フルスクリーン
		"""
		if is_single_screen:
			logger.info("ウィンドウモード: 通常モード")
			self.setWindowFlags(Qt.WindowType.Window)
			self.showNormal()
		else:
			logger.info("ウィンドウモード: フルスクリーン")
			self.setWindowFlags(
				Qt.WindowType.Window |
				Qt.WindowType.FramelessWindowHint# |
				# Qt.WindowType.WindowStaysOnTopHint
			)
			self.show()
			self.showMaximized()
		self.show()

	def move_to_screen(self, screen):
		"""
		指定スクリーンに移動
		
		Args:
			screen: QScreen オブジェクト
		"""
		if not screen:
			logger.warning("move_to_screen: screen が None です")
			return
		
		self.current_screen = screen
		logger.info(f"スクリーン移動: {screen.name()}")
		
		# 1. 一旦フルスクリーンを解除（ウィンドウ状態にして制限を回避）
		is_fs = self.isFullScreen()
		if is_fs:
			self.showNormal()
		
		# 2. ウィンドウハンドルに対してスクリーンを設定
		handle = self.windowHandle()
		if handle:
			handle.setScreen(screen)
		
		try:
			geometry = screen.geometry()
			# フルスクリーンにする前に対象スクリーンの左上座標（x, y）へ移動させる
			self.move(geometry.topLeft())
			logger.debug(f"スクリーン位置へ移動: {geometry.x()},{geometry.y()}")
		except Exception as e:
			logger.warning(f"移動処理例外（無視）: {e}")

		# 3. 移動後に少しだけ遅延させてフルスクリーンを再適用する（OSの追従待ち）
		if is_fs:
			# 50ミリ秒後に安全にフルスクリーン化
			QTimer.singleShot(50, self.showFullScreen)
		else:
			self.show()

	def show_home(self):
		"""
		Display側ホーム画面表示
		wait.html をロードする（待機画面）
		"""
		try:
			base_dir = Path(__file__).resolve().parent

			wait_path = (
				base_dir /
				"templates" /
				"wait.html"
			).resolve()

			# ファイル存在チェック
			if not wait_path.exists():
				raise FileNotFoundError(
					f"wait.html が見つかりません: {wait_path}"
				)

			wait_url = QUrl.fromLocalFile(str(wait_path))

			# 表示
			self.load(wait_url)

			logger.info(f"Display: wait.html を表示しました: {wait_path}")

		except Exception as e:
			logger.error(f"Displayホーム画面の表示に失敗: {e}")

	# =========================================================
	# SafeArea / Scaling
	# =========================================================

	def apply_frame_scale(self):
		"""
		SafeArea付きスケーリング

		・margin = SafeArea
		・scale = SafeArea内の倍率
		・GPU限界超え防止
		"""

		if not self.isVisible():
			return

		window_w = self.width()
		window_h = self.height()

		safe_margin = self.margin if self.safe_area_enabled else 0

		# SafeArea
		safe_w = max(100, window_w - safe_margin * 2)
		safe_h = max(100, window_h - safe_margin * 2)

		# Scale
		scaled_w = int(safe_w * self.scale_h)
		scaled_h = int(safe_h * self.scale_v)

		# GPU限界防止
		scaled_w = min(scaled_w, self.MAX_TEXTURE_SIZE)
		scaled_h = min(scaled_h, self.MAX_TEXTURE_SIZE)

		# 最小サイズ
		scaled_w = max(320, scaled_w)
		scaled_h = max(180, scaled_h)

		# サイズ適用
		self.container_widget.setFixedSize(
			scaled_w,
			scaled_h,
		)

		# SafeArea Margin
		self.main_layout.setContentsMargins(
			safe_margin,
			safe_margin,
			safe_margin,
			safe_margin,
		)

		# Overlay更新
		self.overlay.set_margin(self.margin)
		self.overlay.set_enabled(
			self.safe_area_visible
		)

		self.overlay.setGeometry(self.rect())
		self.overlay.raise_()

		self.debug_overlay.setGeometry(self.rect())
		self.debug_overlay.raise_()

		self.view.update()

		logger.info(
			f"[Scale] "
			f"{scaled_w}x{scaled_h} "
			f"(safe={safe_margin}px)"
		)

	# =========================================================
	# Resize
	# =========================================================

	def resizeEvent(self, event):

		super().resizeEvent(event)

		self.apply_frame_scale()

		# Control Panel
		panel_h = 50

		self.control_panel.setGeometry(
			0,
			self.height() - panel_h,
			self.width(),
			panel_h,
		)

	# =========================================================
	# Browser
	# =========================================================

	def load(self, url):

		if isinstance(url, str):
			url = QUrl(url)

		self.view.setUrl(url)

	def reload(self):

		self.view.reload()

		logger.info("[Reload]")

	def on_web_color_changed(self, color_str: str):
		"""JavaScriptから通知された背景色をDisplayWindow全体の背景に適用する"""
		logger.info(f"[WebColorSync] Webからの背景色同期: {color_str}")
		# ウィンドウ本体とコンテナの背景色を同期させ、セーフエリア（マージン）の隙間を埋める
		self.setStyleSheet(f"background: {color_str};")
		self.container_widget.setStyleSheet(f"background: {color_str};")

	def inject_color_observer(self, success: bool):
		"""ページ読み込み成功時に背景色監視JavaScriptを注入する"""
		logger.info(f"[ColorObserver] ページ読み込み完了: {success}")
		if success:
			js_code = inject_color_detection_js()
			self.view.page().runJavaScript(js_code)
			logger.debug("[ColorObserver] 背景色監視JavaScriptの注入に成功しました")

	# =========================================================
	# Scale
	# =========================================================

	def set_scale_vertical(self, value: float):

		self.scale_v = max(0.25, min(1.0, value))

		self.apply_frame_scale()

		self.scale_v_changed.emit(self.scale_v)

	def set_scale_horizontal(self, value: float):

		self.scale_h = max(0.25, min(1.0, value))

		self.apply_frame_scale()

		self.scale_h_changed.emit(self.scale_h)

	def _on_v_slider_changed(self, value):

		self.set_scale_vertical(value / 50.0)

	def _on_h_slider_changed(self, value):

		self.set_scale_horizontal(value / 50.0)

	# =========================================================
	# Margin
	# =========================================================

	def set_margin(self, value):

		self.margin = max(0, min(300, value))

		self.apply_frame_scale()

		self.margin_changed.emit(self.margin)

	def margin_up(self):

		self.set_margin(self.margin + 5)

	def margin_down(self):

		self.set_margin(self.margin - 5)

	# =========================================================
	# Toggle
	# =========================================================

	def toggle_safe_area(self):

		self.safe_area_visible = (
			not self.safe_area_visible
		)

		self.apply_frame_scale()

		logger.info(
			f"[SafeArea] "
			f"{self.safe_area_visible}"
		)

	def toggle_test_pattern(self):

		self.test_pattern_enabled = (
			not self.test_pattern_enabled
		)

		self.overlay.set_test_pattern(
			self.test_pattern_enabled
		)

		self.overlay.update()

	def toggle_debug(self):

		self.debug_overlay.set_enabled(
			not self.debug_overlay.enabled
		)

	def toggle_control_panel(self):

		self.control_panel.setVisible(
			not self.control_panel.isVisible()
		)

	# =========================================================
	# Key
	# =========================================================

	def keyPressEvent(self, event):

		if event.key() == Qt.Key.Key_Escape:
			event.ignore()
			return

		super().keyPressEvent(event)

	# =========================================================
	# Close
	# =========================================================

	def closeEvent(self, event):

		self.settings.set("scale_v", self.scale_v)
		self.settings.set("scale_h", self.scale_h)
		self.settings.set("margin", self.margin)

		event.accept()

		logger.info("[Display] Closed")


# =============================================================
# Standalone
# =============================================================

if __name__ == "__main__":

	app = QApplication(sys.argv)

	window = DisplayWindow()

	window.load("https://example.com")

	sys.exit(app.exec())