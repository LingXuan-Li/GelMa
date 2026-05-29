# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2026 LingXuan-Li

"""コントロール画面（多言語対応）"""

from PyQt6.QtWidgets import (
	QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
	QLineEdit, QPushButton, QComboBox, QGroupBox, QScrollArea
)
from PyQt6.QtCore import QUrl, Qt, QTimer
from PyQt6.QtWebEngineWidgets import QWebEngineView
# from PyQt6.QtGui import QColor
from pathlib import Path
from PyQt6.QtWebChannel import QWebChannel
import logging

from windows.sql_webchannel import SQLWebChannel
from utils.settings_manager import SettingsManager
from utils.i18n import t, LANGUAGES, LANGUAGE_CODES
from utils.logger import setup_logger
import json

# setup_logger()
logger = logging.getLogger(__name__)

VALUE = None

class ControlWindow(QMainWindow):
	def __init__(self):
		super().__init__()

		self.setup_ui()
		self.state_update()

	def setup_ui(self):
		self.display = None
		self.settings = SettingsManager()
		
		# 言語設定（保存から復元、デフォルト: ja）
		self.language = self.settings.get("language", "ja")

		self.setWindowTitle("GelMa - Control")
		self.resize(1200, 800)
		
		# ショートカット状態管理
		self.safe_area_enabled = bool(self.settings.get("safe_area", 1))
		self.safe_area_visible = bool(self.settings.get("safe_area_visible", 1))
		self.test_pattern_enabled = bool(self.settings.get("test_pattern", 0))
		self.debug_enabled = bool(self.settings.get("debug", 0))
		self.control_panel_enabled = bool(self.settings.get("control_panel", 0))

		# =========================================================
		# WebView（プレビュー）
		# =========================================================

		self.preview = QWebEngineView()
		# preview URL change -> sync to control and display
		self.preview.urlChanged.connect(self._on_preview_url_changed)

		# =========================================================
		# コントロール用スクロール エリア
		# =========================================================

		scroll = QScrollArea()
		scroll.setWidgetResizable(True)
		scroll.setMaximumWidth(350)

		scroll_widget = QWidget()
		scroll_layout = QVBoxLayout()

		# =========================================================
		# 言語選択
		# =========================================================

		lang_layout = QHBoxLayout()
		self.lang_label = QLabel(t("Language", self.language))
		self.lang_combo = QComboBox()
		self.lang_combo.addItems([LANGUAGES[lang] for lang in LANGUAGE_CODES])
		if self.language in LANGUAGE_CODES:
			self.lang_combo.setCurrentIndex(LANGUAGE_CODES.index(self.language))
		else:
			self.lang_combo.setCurrentIndex(0)
		self.lang_combo.currentIndexChanged.connect(self.on_language_changed)
		lang_layout.addWidget(self.lang_label)
		lang_layout.addWidget(self.lang_combo)
		lang_layout.addStretch()
		scroll_layout.addLayout(lang_layout)
		scroll_layout.addWidget(QLabel(""))  # スペーサー

		# =========================================================
		# URL バー
		# =========================================================

		self.url_label = QLabel(t("URL", self.language))
		self.url_bar = QLineEdit()
		self.url_bar.setPlaceholderText("https://example.com")
		self.url_bar.setText(self.settings.get("url", ""))

		# =========================================================
		# ボタン
		# =========================================================

		self.btn_home = QPushButton(t("HOME", self.language))
		self.btn_home.clicked.connect(self.show_home)
		self.btn_load = QPushButton(t("Load URL", self.language))
		self.btn_load.clicked.connect(self.go)

		# Display に同じサイトを映すボタン
		self.btn_sync = QPushButton("🔄 " + t("Sync to Display", self.language))
		self.btn_sync.clicked.connect(self.sync_to_display)

		self.btn_reload = QPushButton(t("Reload (R)", self.language))
		self.btn_reload.clicked.connect(self.reload_display)

		# SafeArea ボタン + ステータス
		safe_layout = QHBoxLayout()
		self.btn_safe = QPushButton(t("SafeArea (S)", self.language))
		self.btn_safe.clicked.connect(self.toggle_safe_area)
		self.safe_area_label = QLabel(self._get_status_text(self.safe_area_visible))
		safe_layout.addWidget(self.btn_safe)
		safe_layout.addWidget(self.safe_area_label)
		safe_layout.addStretch()

		# Test Pattern ボタン + ステータス
		test_layout = QHBoxLayout()
		self.btn_test = QPushButton(t("Test Pattern (T)", self.language))
		self.btn_test.clicked.connect(self.toggle_test_pattern)
		self.test_pattern_label = QLabel(self._get_status_text(self.test_pattern_enabled))
		test_layout.addWidget(self.btn_test)
		test_layout.addWidget(self.test_pattern_label)
		test_layout.addStretch()

		# Debug ボタン + ステータス
		debug_layout = QHBoxLayout()
		self.btn_debug = QPushButton(t("Debug (D)", self.language))
		self.btn_debug.clicked.connect(self.toggle_debug)
		self.debug_label = QLabel(self._get_status_text(self.debug_enabled))
		debug_layout.addWidget(self.btn_debug)
		debug_layout.addWidget(self.debug_label)
		debug_layout.addStretch()

		# Control Panel ボタン + ステータス
		panel_layout = QHBoxLayout()
		self.btn_panel = QPushButton(t("Control Panel (C)", self.language))
		self.btn_panel.clicked.connect(self.toggle_control_panel)
		self.control_panel_label = QLabel(self._get_status_text(self.control_panel_enabled))
		panel_layout.addWidget(self.btn_panel)
		panel_layout.addWidget(self.control_panel_label)
		panel_layout.addStretch()

		# ショートカット ON/OFF ステータス表示
		self.shortcut_status_label = QLabel()
		self.update_shortcut_status()

		# =========================================================
		# スケール調整（グループボックス）
		# =========================================================

		self.scale_group = QGroupBox(t("Scale Adjustment", self.language))
		scale_layout = QVBoxLayout()

		# 縦スケール: 0.25x - 2.0x
		self.v_label = QLabel(t("Vertical Scale", self.language) + ":")
		self.scale_v_slider = QSlider(Qt.Orientation.Horizontal)
		self.scale_v_slider.setMinimum(10)   # 0.25x
		self.scale_v_slider.setMaximum(80)   # 2.0x
		self.scale_v_slider.setValue(int(self.settings.get("scale_v", 1.0) * 40))
		self.scale_v_slider.setTracking(True)
		self.scale_v_slider.valueChanged.connect(self.on_scale_v_changed)
		
		self.scale_v_label = QLabel(f"{self.settings.get('scale_v', 1.0):.2f}x")

		# 横スケール: 0.25x - 2.0x
		self.h_label = QLabel(t("Horizontal Scale", self.language) + ":")
		self.scale_h_slider = QSlider(Qt.Orientation.Horizontal)
		self.scale_h_slider.setMinimum(10)   # 0.25x
		self.scale_h_slider.setMaximum(80)   # 2.0x
		self.scale_h_slider.setValue(int(self.settings.get("scale_h", 1.0) * 40))
		self.scale_h_slider.setTracking(True)
		self.scale_h_slider.valueChanged.connect(self.on_scale_h_changed)
		
		self.scale_h_label = QLabel(f"{self.settings.get('scale_h', 1.0):.2f}x")

		# リセットボタン
		self.btn_scale_reset = QPushButton(t("Reset Scale", self.language))
		self.btn_scale_reset.clicked.connect(self.reset_scale)

		scale_layout.addWidget(self.v_label)
		scale_layout.addWidget(self.scale_v_slider)
		scale_layout.addWidget(self.scale_v_label)

		scale_layout.addWidget(self.h_label)
		scale_layout.addWidget(self.scale_h_slider)
		scale_layout.addWidget(self.scale_h_label)

		scale_layout.addWidget(self.btn_scale_reset)
		self.scale_group.setLayout(scale_layout)

		# =========================================================
		# マージン調整（グループボックス）
		# =========================================================

		self.margin_group = QGroupBox(t("Margin Adjustment", self.language))
		margin_layout = QVBoxLayout()

		margin_value = self.settings.get('margin', 40)
		self.margin_label = QLabel(f"{t('Margin', self.language)}: {margin_value}px (↑/↓)")
		self.margin_slider = QSlider(Qt.Orientation.Horizontal)
		self.margin_slider.setMinimum(0)
		self.margin_slider.setMaximum(100)
		self.margin_slider.setValue(margin_value)
		self.margin_slider.setTracking(True)
		self.margin_slider.valueChanged.connect(self.on_margin_changed_internal)

		margin_layout.addWidget(self.margin_label)
		margin_layout.addWidget(self.margin_slider)
		self.margin_group.setLayout(margin_layout)

		# =========================================================
		# レイアウト構成
		# =========================================================

		self.nav_header = QLabel("<b>" + t("Navigation", self.language) + "</b>")
		self.shortcuts_header = QLabel("<b>" + t("Keyboard Shortcuts", self.language) + "</b>")
		self.display_header = QLabel("<b>" + t("Display Control", self.language) + "</b>")

		scroll_layout.addWidget(self.nav_header)
		scroll_layout.addWidget(self.url_label)
		scroll_layout.addWidget(self.url_bar)
		scroll_layout.addWidget(self.btn_home)
		scroll_layout.addWidget(self.btn_load)
		scroll_layout.addWidget(self.btn_sync)

		scroll_layout.addWidget(self.shortcuts_header)
		scroll_layout.addWidget(self.shortcut_status_label)
		scroll_layout.addWidget(self.btn_reload)
		scroll_layout.addLayout(safe_layout)
		scroll_layout.addLayout(test_layout)
		scroll_layout.addLayout(debug_layout)
		scroll_layout.addLayout(panel_layout)

		scroll_layout.addWidget(self.display_header)
		scroll_layout.addWidget(self.scale_group)
		scroll_layout.addWidget(self.margin_group)

		self.btn_save = QPushButton(t("Save Settings", self.language))
		self.btn_save.clicked.connect(self.save_settings)
		scroll_layout.addWidget(self.btn_save)
		scroll_layout.addStretch()

		scroll_widget.setLayout(scroll_layout)
		scroll.setWidget(scroll_widget)

		# =========================================================
		# メインレイアウト
		# =========================================================

		main_layout = QHBoxLayout()
		main_layout.addWidget(scroll)
		main_layout.addWidget(self.preview, 1)

		container = QWidget()
		container.setLayout(main_layout)
		self.setCentralWidget(container)

		# 初期表示
		self.show_home()

		# ========================================================
		# index.html → SQLite保存
		# =========================================================

		self.web_channel = QWebChannel()
		self.sql_bridge = SQLWebChannel()

		self.web_channel.registerObject("pybridge", self.sql_bridge)

		self.preview.page().setWebChannel(self.web_channel)
	

	def state_update(self):
		"""ON/OFFや数値など状態更新専用"""

		self.safe_area_label.setText(
			self._get_status_text(self.safe_area_visible)
		)

		self.test_pattern_label.setText(
			self._get_status_text(self.test_pattern_enabled)
		)

		self.debug_label.setText(
			self._get_status_text(self.debug_enabled)
		)

		self.control_panel_label.setText(
			self._get_status_text(self.control_panel_enabled)
		)

		self.shortcut_status_label.setText(
			self.get_shortcut_status_text()
		)

	def set_display_window(self, display):
		self.display = display
		# DisplayWindow のシグナルを接続
		if self.display:
			self.display.scale_v_changed.connect(self.on_display_scale_v_changed)
			self.display.scale_h_changed.connect(self.on_display_scale_h_changed)
			self.display.margin_changed.connect(self.on_display_margin_changed)
	
	def _get_status_text(self, enabled: bool) -> str:
		"""ON/OFF ステータスを取得"""
		if enabled:
			return "🟢 ON"
		else:
			return "⚫ OFF"
	
	def _update_status_label(self, label, enabled: bool):
		"""ステータスラベルを更新"""
		label.setText(self._get_status_text(enabled))
		label.setStyleSheet("font-weight: bold;" + 
			("color: #00AA00;" if enabled else "color: #999999;"))

	def show_home(self):
		"""
		Control側ホーム画面を表示
		Display側には wait.html を表示
		"""
	
		try:
			# =================================
			# パス取得
			# =================================
	
			base_dir = Path(__file__).resolve().parent
	
			home_path = (
				base_dir /
				"templates" /
				"index.html"
			).resolve()
	
			wait_path = (
				base_dir /
				"templates" /
				"wait.html"
			).resolve()
	
			# =================================
			# ファイル存在確認
			# =================================
	
			if not home_path.exists():
				raise FileNotFoundError(
					f"index.html が見つかりません: {home_path}"
				)
	
			if not wait_path.exists():
				raise FileNotFoundError(
					f"wait.html が見つかりません: {wait_path}"
				)
	
			# =================================
			# URL化
			# =================================
	
			home_url = QUrl.fromLocalFile(str(home_path))
	
			wait_url = QUrl.fromLocalFile(str(wait_path))
	
			# =================================
			# signal多重接続防止
			# =================================
	
			try:
				self.preview.loadFinished.disconnect()
			except Exception:
				pass
	
			# =================================
			# Control側ロード完了
			# =================================
	
			def on_load_finished(ok: bool):
	
				try:
					self.preview.loadFinished.disconnect(on_load_finished)
				except Exception:
					pass
	
				if not ok:
					logger.warning("[Control] index.html のロード失敗")
					return
	
				logger.info("[Control] index.html loaded")
	
				# # -----------------------------
				# # Python bridge 注入
				# # -----------------------------
	
				# try:
				# 	self._inject_python_bridge()
				# 	logger.info("[Control] Python bridge injected")
	
				# except Exception as e:
				# 	logger.warning(f"[Control] bridge注入失敗: {e}")
	
			self.preview.loadFinished.connect(on_load_finished)
	
			# =================================
			# Control側ロード
			# =================================
	
			self.preview.load(home_url)
	
			# =================================
			# Display側ロード
			# =================================
	
			if self.display:
				self.display.load(wait_url)
				logger.info("[Display] wait.html loaded")
	
			logger.info(f"[Control] Home loaded: {home_path}")
	
		except Exception as e:
			logger.error(f"[Control] ホーム画面表示失敗: {e}")

	def _inject_python_bridge(self):
		"""QWebChannel ブリッジを作成して pybridge を公開し、背景色も監視する"""
		try:
			from PyQt6.QtWebChannel import QWebChannel
			from utils.color_bridge import ColorBridge, inject_color_detection_js

			# 統合したブリッジを作成 (self を親として渡す)
			self.bridge = ColorBridge(self)
			self.channel = QWebChannel(self.preview.page())
			
			# HTML側が求めている 'pybridge' と、追加した 'colorBridge' の両方で登録
			self.channel.registerObject('pybridge', self.bridge)
			self.channel.registerObject('colorBridge', self.bridge)
			self.preview.page().setWebChannel(self.channel)

			self.bridge.color_changed.connect(lambda color: logger.info(f"Preview color: {color}"))

			# WebChannel初期化 ＆ 背景監視用の JavaScript をまとめて注入
			init_js = f"""
			(function(){{
				var s = document.createElement('script');
				s.src = 'qrc:///qtwebchannel/qwebchannel.js';
				s.onload = function(){{
					new QWebChannel(qt.webChannelTransport, function(channel){{
						window.pybridge = channel.objects.pybridge;
						window.colorBridge = channel.objects.colorBridge;

						if(window.pybridge.shortcuts_loaded) {{
							// ダミーデータまたは初期ロードデータを送る
							// window.pybridge.shortcuts_loaded.emit("[]");
						}}
					}});
				}};
				document.head.appendChild(s);
			}})();
			"""
			
			# ページ読み込み完了時にJSをインジェクション
			self.preview.loadFinished.connect(lambda success: self.preview.page().runJavaScript(init_js) if success else None)
			self.preview.loadFinished.connect(lambda success: self.preview.page().runJavaScript(inject_color_detection_js()) if success else None)

		except Exception as e:
			logger.error(f"[Control] Could not inject Python bridge: {e}")

	def _on_preview_url_changed(self, qurl):
		"""プレビューのURLが変わったとき、URLバーとDisplayに同期"""
		try:
			url = qurl.toString()
			if url and url != 'about:blank':
				self.url_bar.setText(url)
				self.settings.set('url', url)
				if self.display:
					# load on display
					self.display.load(url)
		except Exception as e:
			logger.error(f"[Control] Error on preview url change: {e}")

	def go(self):
		"""URLを読み込む"""
		url = self.url_bar.text().strip()
		if not url:
			self.show_home()
			return
		if not url.startswith(("http://", "https://", "file://", "data:")):
			url = "https://" + url
		self.url_bar.setText(url)
		self.preview.setUrl(QUrl(url))
		if self.display:
			self.display.load(url)

	def reload_display(self):
		"""DisplayWindowをリロード"""
		if self.display:
			self.display.reload()

	def toggle_safe_area(self):
		"""SafeArea トグル"""
		self.safe_area_visible = (not self.safe_area_visible)

		self._update_status_label(
			self.safe_area_label,
			self.safe_area_visible
		)

		if self.display:
			self.display.toggle_safe_area()

	def toggle_test_pattern(self):
		"""テストパターン トグル"""
		self.test_pattern_enabled = not self.test_pattern_enabled
		self._update_status_label(self.test_pattern_label, self.test_pattern_enabled)
		if self.display:
			self.display.toggle_test_pattern()

	def toggle_debug(self):
		"""デバッグ表示 トグル"""
		self.debug_enabled = not self.debug_enabled
		self._update_status_label(self.debug_label, self.debug_enabled)
		if self.display:
			self.display.toggle_debug()

	def toggle_control_panel(self):
		"""コントロールパネル トグル"""
		self.control_panel_enabled = not self.control_panel_enabled
		self._update_status_label(self.control_panel_label, self.control_panel_enabled)
		if self.display:
			self.display.toggle_control_panel()
	
	def sync_to_display(self):
		"""ControlWindow で見ているサイト URL をDisplayWindow に同期"""
		# プレビューウィンドウの現在のURL を取得
		preview_url = self.preview.url().toString()
		
		# URL が空でない場合
		if preview_url and preview_url != "about:blank":
			# URL 入力部分にも同じ URL を設定
			self.url_bar.setText(preview_url)
			# Display に同期
			if self.display:
				self.display.load(preview_url)
			# 設定を保存
			self.settings.set("url", preview_url)
		else:
			# URL バーから手動で入力された URL がある場合
			url = self.url_bar.text().strip()
			if url:
				if not url.startswith(("http://", "https://", "file://", "data:")):
					url = "https://" + url
				# URL 入力部分を更新
				self.url_bar.setText(url)
				# プレビューに表示
				self.preview.setUrl(QUrl(url))
				# Display に同期
				if self.display:
					self.display.load(url)
				# 設定を保存
				self.settings.set("url", url)
			else:
				# URL が無い場合はホーム画面
				self.show_home()
	
	def get_shortcut_status_text(self) -> str:
		"""ショートカットステータスのテキストを返す"""
		return "⚪ Shortcuts: ON (R/S/T/D/C/↑/↓)"

	def update_shortcut_status(self):
		"""ショートカットステータスを更新（LED インジケーター的に表示）"""
		self.shortcut_status_label.setText(self.get_shortcut_status_text())
		self.shortcut_status_label.setStyleSheet(
			"color: #00AA00; font-weight: bold; padding: 5px;"
		)

	def retranslate_ui(self):
		"""言語変更時に全 UI テキストを即時更新"""
		lang = self.language

		# ヘッダーラベル
		self.lang_label.setText(t("Language", lang))
		self.nav_header.setText("<b>" + t("Navigation", lang) + "</b>")
		self.shortcuts_header.setText("<b>" + t("Keyboard Shortcuts", lang) + "</b>")
		self.display_header.setText("<b>" + t("Display Control", lang) + "</b>")

		# URL
		self.url_label.setText(t("URL", lang))

		# ボタン
		self.btn_home.setText(t("HOME", lang))
		self.btn_load.setText(t("Load URL", lang))
		self.btn_sync.setText("🔄 " + t("Sync to Display", lang))
		self.btn_reload.setText(t("Reload (R)", lang))
		self.btn_safe.setText(t("SafeArea (S)", lang))
		self.btn_test.setText(t("Test Pattern (T)", lang))
		self.btn_debug.setText(t("Debug (D)", lang))
		self.btn_panel.setText(t("Control Panel (C)", lang))
		self.btn_save.setText(t("Save Settings", lang))
		self.btn_scale_reset.setText(t("Reset Scale", lang))

		# グループボックスタイトル
		self.scale_group.setTitle(t("Scale Adjustment", lang))
		self.margin_group.setTitle(t("Margin Adjustment", lang))

		# スライダーラベル
		self.v_label.setText(t("Vertical Scale", lang) + ":")
		self.h_label.setText(t("Horizontal Scale", lang) + ":")
		self.margin_label.setText(
			f"{t('Margin', lang)}: {self.margin_slider.value()}px (↑/↓)"
		)

		# ショートカットステータス（言語非依存だが念のため更新）
		self.update_shortcut_status()

		logger.info(f"[Control] UI再翻訳完了: {lang}")


	def on_scale_v_changed(self, value: int):
		"""縦スケール変更"""
		scale = value / 40.0
		self.scale_v_label.setText(f"{scale:.2f}x")
		if self.display:
			self.display.set_scale_vertical(scale)

	def on_scale_h_changed(self, value: int):
		"""横スケール変更"""
		scale = value / 40.0
		self.scale_h_label.setText(f"{scale:.2f}x")
		if self.display:
			self.display.set_scale_horizontal(scale)

	def on_display_scale_v_changed(self, value: float):
		"""DisplayWindow から縦スケール変更通知"""
		self.scale_v_slider.blockSignals(True)
		self.scale_v_slider.setValue(int(value * 40))
		self.scale_v_label.setText(f"{value:.2f}x")
		self.scale_v_slider.blockSignals(False)

	def on_display_scale_h_changed(self, value: float):
		"""DisplayWindow から横スケール変更通知"""
		self.scale_h_slider.blockSignals(True)
		self.scale_h_slider.setValue(int(value * 40))
		self.scale_h_label.setText(f"{value:.2f}x")
		self.scale_h_slider.blockSignals(False)

	def on_margin_changed_internal(self, value: int):
		"""マージン変更（内部用）"""
		self.margin_label.setText(f"{t('Margin', self.language)}: {value}px (↑/↓)")
		global VALUE
		VALUE = value
		if self.display:
			self.display.set_margin(value)

	def on_display_margin_changed(self, value: int):
		"""DisplayWindow からマージン変更通知"""
		self.margin_slider.blockSignals(True)
		self.margin_slider.setValue(value)
		self.margin_slider.blockSignals(False)

	def on_language_changed(self, index: int):
		"""言語変更時のシグナル処理（即時UI更新）"""
		if 0 <= index < len(LANGUAGE_CODES):
			self.language = LANGUAGE_CODES[index]
			self.settings.set("language", self.language)
			
			# UIの文字を即座に書き換える
			self.retranslate_ui()
			
			logger.info(f"[Language] 即時切り替え完了: {self.language} ({LANGUAGES[self.language]})")
			
			# 必要に応じて、連携しているDisplayWindow側の言語も一緒に切り替える指示を出す
			if self.display and hasattr(self.display, 'retranslate_ui'):
				# display_window.py 側にも retranslate_ui を実装しておけば同時に切り替わります
				pass

	def save_settings(self):
		"""設定を保存"""
		self.settings.set("url", self.url_bar.text())
		scale_v = self.scale_v_slider.value() / 40.0
		scale_h = self.scale_h_slider.value() / 40.0
		self.settings.set("scale_v", scale_v)
		self.settings.set("scale_h", scale_h)
		self.settings.set("margin", self.margin_slider.value())
		self.settings.set(
			"safe_area_visible",
			self.safe_area_visible
		)
		logger.info("[Settings] Saved")

	def reset_scale(self):
		"""スケール値をリセット"""
		self.scale_v_slider.setValue(40)
		self.scale_h_slider.setValue(40)

	def closeEvent(self, event):
		"""ウィンドウ終了時"""
		self.settings.set("url", self.url_bar.text())
		scale_v = self.scale_v_slider.value() / 40.0
		scale_h = self.scale_h_slider.value() / 40.0
		self.settings.set("scale_v", scale_v)
		self.settings.set("scale_h", scale_h)
		self.settings.set("margin", self.margin_slider.value())
		self.settings.set("language", self.language)
		self.settings.set("safe_area_visible", self.safe_area_visible)

		if self.display:
			self.display.close()

		event.accept()
		logger.info("[ControlWindow] Closed")