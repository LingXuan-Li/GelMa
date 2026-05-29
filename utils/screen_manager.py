# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2026 LingXuan-Li

import logging
from PyQt6.QtCore import QObject

logger = logging.getLogger(__name__)

class ScreenManager(QObject):
    def __init__(self, app):
        super().__init__()
        self.app = app

        self.primary = None
        self.secondary = None

        self.app.screenAdded.connect(self.update)
        self.app.screenRemoved.connect(self.update)

        self.update()

    def update(self):
        screens = self.app.screens()
        self.primary = self.app.primaryScreen()

        self.secondary = None
        for s in screens:
            if s != self.primary:
                self.secondary = s
                break

        logger.info("[ScreenManager] primary: %s", self.primary.name())
        logger.info("[ScreenManager] secondary: %s", self.secondary.name() if self.secondary else None)

    def has_secondary(self):
        return self.secondary is not None

    def get_secondary(self):
        return self.secondary

    def get_primary(self):
        return self.primary