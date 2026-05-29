# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2026 LingXuan-Li

import sys
import os
import logging
from PyQt6.QtCore import Qt, QCoreApplication
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from windows.display_window import DisplayWindow
from windows.control_window import ControlWindow
from utils.screen_manager import ScreenManager
from utils.settings_manager import SettingsManager

# =========================================
# ロギングシステム初期化（最初に実行）
# =========================================

from utils.logger import setup_logger, log_exception
logger = setup_logger()

# =========================================
# Qt / Chromium GPU 無効化（最優先）
# =========================================

os.environ["QT_OPENGL"] = "angle"

os.environ["QTWEBENGINE_DISABLE_GPU"] = "1"

os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    "--disable-gpu "
    "--disable-gpu-compositing "
    "--disable-d3d11 "
    "--disable-gpu-vsync "
    "--disable-features=UseSkiaRenderer,VizDisplayCompositor"
)

os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"

QCoreApplication.setAttribute(
    Qt.ApplicationAttribute.AA_UseSoftwareOpenGL
)

QCoreApplication.setAttribute(
    Qt.ApplicationAttribute.AA_ShareOpenGLContexts
)

logger.info("環境変数設定完了: GPU 無効化")

# =========================================

def main():

    app = QApplication(sys.argv)

    # =========================================
    # アイコン
    # =========================================

    icon_path = os.path.join(
        os.path.dirname(__file__),
        "windows",
        "templates",
        "figure",
        "icon.ico"
    )

    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # =========================================
    # マネージャ
    # =========================================

    settings = SettingsManager()
    screen_manager = ScreenManager(app)

    # =========================================
    # ウィンドウ
    # =========================================

    control = ControlWindow()
    display = DisplayWindow()

    # 初期サイズを与える（D3D11対策）
    display.resize(1280, 720)

    control.set_display_window(display)

    control.show()

    # =========================================
    # 適用
    # =========================================

    def apply():

        is_single = not screen_manager.has_secondary()

        display.set_mode(is_single)

        if is_single:
            display.move_to_screen(
                screen_manager.get_primary()
            )
        else:
            display.move_to_screen(
                screen_manager.get_secondary()
            )

        # URL復元
        saved_url = settings.get("url")

        if saved_url and saved_url != "about:blank":
            display.load(saved_url)

        # スケール復元
        saved_scale_v = settings.get("scale_v", 1.0)
        saved_scale_h = settings.get("scale_h", 1.0)

        display.set_scale_vertical(saved_scale_v)
        display.set_scale_horizontal(saved_scale_h)

    apply()

    # =========================================
    # スクリーン変更
    # =========================================

    app.screenAdded.connect(lambda: apply())
    app.screenRemoved.connect(lambda: apply())

    # =========================================
    # 終了時保存
    # =========================================

    def on_exit():

        settings.set(
            "url",
            control.url_bar.text()
        )

        scale_v = (
            control.scale_v_slider.value() / 40.0
        )

        scale_h = (
            control.scale_h_slider.value() / 40.0
        )

        settings.set("scale_v", scale_v)
        settings.set("scale_h", scale_h)

        settings.set(
            "margin",
            control.margin_slider.value()
        )

    app.aboutToQuit.connect(on_exit)

    sys.exit(app.exec())


if __name__ == "__main__":
    try:
        logger.info("=" * 70)
        logger.info("GelMa 起動開始")
        logger.info("=" * 70)
        main()
    except Exception as e:
        logger.error("=" * 70)
        logger.error("予期しないエラーが発生しました")
        logger.error("=" * 70)
        log_exception()
        sys.exit(1)