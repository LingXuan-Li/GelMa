# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2026 LingXuan-Li

from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal, QUrl

from utils.logger import logging
import logging

logger = logging.getLogger(__name__)

class ColorBridge(QObject):
	color_changed = pyqtSignal(str)
	shortcuts_loaded = pyqtSignal(str)

	def __init__(self, parent=None):
		super().__init__(parent)
		self._parent = parent # control_window または display_window を保持


	@pyqtSlot(str)
	def set_background_color(self, color: str):
		self.color_changed.emit(color)

	@pyqtSlot(result='QVariant')
	def get_shortcuts(self):
		try:
			# 親（control_window）の settings からショートカットを取得
			return self._parent.settings.get_shortcuts()
		except Exception as e:
			logger.error(f"[PyBridge] get_shortcuts error: {e}")
			return []

	@pyqtSlot(str, str, result=bool)
	def add_shortcut(self, name, url):
		try:
			return self._parent.settings.add_shortcut(name, url)
		except Exception as e:
			logger.error(f"[PyBridge] add_shortcut error: {e}")
			return False

	@pyqtSlot(int, result=bool)
	def delete_shortcut(self, id):
		try:
			return self._parent.settings.delete_shortcut(id)
		except Exception as e:
			logger.error(f"[PyBridge] delete_shortcut error: {e}")
			return False

	@pyqtSlot(str, result=bool)
	def open_url(self, url):
		try:
			# 選択されたURLをコントロール側とディスプレイ（TV）側に反映
			if hasattr(self._parent, 'url_bar'):
				self._parent.url_bar.setText(url)
			if hasattr(self._parent, 'preview'):
				self._parent.preview.setUrl(QUrl(url))
			if hasattr(self._parent, 'display') and self._parent.display:
				self._parent.display.load(url)
			return True
		except Exception as e:
			logger.error(f"[PyBridge] open_url error: {e}")
			return False

def inject_color_detection_js():
	return """
	(function() {
		function extractColor() {
			const style = window.getComputedStyle(document.body);
			let bgColor = style.backgroundColor;
			if (bgColor === 'transparent' || bgColor === 'rgba(0, 0, 0, 0)') {
				const htmlStyle = window.getComputedStyle(document.documentElement);
				bgColor = htmlStyle.backgroundColor;
			}
			return (bgColor === 'transparent' || bgColor === 'rgba(0, 0, 0, 0)') ? 'rgb(0, 0, 0)' : bgColor;
		}
		function notifyColor() {
			const color = extractColor();
			if (typeof qt !== 'undefined' && qt.webChannelTransport !== undefined) {
				new QWebChannel(qt.webChannelTransport, function(channel) {
					// 両方の名前に安全に通知を送る
					if (channel.objects.pybridge && channel.objects.pybridge.set_background_color) {
						channel.objects.pybridge.set_background_color(color);
					}
					if (channel.objects.colorBridge && channel.objects.colorBridge.set_background_color) {
						channel.objects.colorBridge.set_background_color(color);
					}
				});
			}
		}
		document.addEventListener('DOMContentLoaded', notifyColor);
		window.addEventListener('load', notifyColor);
		const observer = new MutationObserver(notifyColor);
		observer.observe(document.body, { attributes: true, attributeFilter: ['style'], subtree: false });
	})();
	"""