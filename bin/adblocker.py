# MIT License
#
# Copyright (c) 2021-2026 Souvik Nandi
#
# Permission is granted to use, copy, modify, and distribute this software for any purpose with or without fee, provided the copyright notice appears in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.

"""
Backwards-compatible wrapper around PrivacyShieldInterceptor.
Ensures legacy references to AdblockInterceptor continue working smoothly.
"""

from .privacy_shield import PrivacyShieldInterceptor, PrivacyShieldSignals, PrivacyShieldUpdater

class AdblockSignals(PrivacyShieldSignals):
    pass

class AdblockUpdater(PrivacyShieldUpdater):
    pass

class AdblockInterceptor(PrivacyShieldInterceptor):
    """
    Subclasses PrivacyShieldInterceptor to preserve exact API compatibility
    with legacy Neutrino and prospective Qelaro browser modules.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

    def should_block(self, url: str) -> bool:
        """
        Fast O(1) domain lookup method for testing or manual URL verification.
        """
        if not self.rules:
            return False
        try:
            from PyQt6.QtCore import QUrl
            host = QUrl(url).host().lower()
            if not host:
                return False
            parts = host.split('.')
            for i in range(len(parts) - 1):
                candidate = '.'.join(parts[i:])
                if candidate in self.rules:
                    return True
        except Exception:
            return False
        return False
