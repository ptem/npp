# SPDX-FileCopyrightText: 2020-2025 Nicotine+ Contributors
# SPDX-License-Identifier: GPL-3.0-or-later

import gettext
import locale
import os
import sys

CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))
BASE_PATH = os.path.normpath(os.path.join(CURRENT_PATH, ".."))
LOCALE_PATH = os.path.join(CURRENT_PATH, "locale")
TRANSLATION_DOMAIN = "nicotine"
LANGUAGES = (
    ("ca", "Català"),
    ("cs", "Čeština"),
    ("de", "Deutsch"),
    ("en", "English"),
    ("es_CL", "Español (Chile)"),
    ("es_ES", "Español (España)"),
    ("et", "Eesti"),
    ("fr", "Français"),
    ("hu", "Magyar"),
    ("it", "Italiano"),
    ("lv", "Latviešu"),
    ("nl", "Nederlands"),
    ("pl", "Polski"),
    ("pt_BR", "Português (Brasil)"),
    ("pt_PT", "Português (Portugal)"),
    ("ru", "Русский"),
    ("ta", "தமிழ்"),
    ("tr", "Türkçe"),
    ("uk", "Українська"),
    ("zh_CN", "汉语")
)

if not hasattr(locale, "normalize"):
    def _normalize(loc: str) -> str:
        # very simple: ensure en_US → en_US.UTF-8
        if not loc:
            return loc
        if "." not in loc:
            return f"{loc}.UTF-8"
        return loc
    locale.normalize = _normalize

def _set_system_language(language=None):
    """Extract the default system locale/language and apply it on systems that
    don't set LC_ALL/LANGUAGE by default (Windows, macOS)."""

    default_locale = None

    if (
        sys.platform == "win32"
        and getattr(locale, "windows_locale", None)  # mapping present?
    ):
        try:
            import ctypes
            windll = ctypes.windll.kernel32  # raises if windll/kernel32 aren't available
            if not default_locale:
                default_locale = locale.windows_locale.get(windll.GetUserDefaultLCID())
            if not language and "LANGUAGE" not in os.environ:
                language = locale.windows_locale.get(windll.GetUserDefaultUILanguage())
        except Exception:
            pass

    elif sys.platform == "darwin":
        import plistlib
        os_preferences_path = os.path.join(
            os.path.expanduser("~"), "Library", "Preferences", ".GlobalPreferences.plist")
        try:
            with open(os_preferences_path, "rb") as fh:
                os_preferences = plistlib.load(fh)
        except Exception as error:
            os_preferences = {}
            print(f"Cannot load global preferences: {error}")
        default_locale = next(iter(os_preferences.get("AppleLocale", "").split("@", maxsplit=1)))
        if default_locale.endswith("_ES"):
            default_locale = "pt_PT"
        if not language and "LANGUAGE" not in os.environ:
            languages = os_preferences.get("AppleLanguages", [""])
            language = next(iter(languages)).replace("-", "_")

    if not default_locale:
        default_locale = (
            os.environ.get("NICOTINE_LANG")
            or os.environ.get("LC_ALL")
            or os.environ.get("LC_MESSAGES")
            or os.environ.get("LANG")
            or "en_US.UTF-8"
        )
    if not language:
        language = (default_locale or "en_US").split(".")[0]

    os.environ["LC_ALL"] = default_locale
    os.environ["LANGUAGE"] = language


def apply_translations(language=None):

    # Use the same language as the rest of the system
    _set_system_language(language)

    # Install translations for Python
    gettext.install(TRANSLATION_DOMAIN, LOCALE_PATH)
