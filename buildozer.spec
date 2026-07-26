[app]
# (str) Icon of the application
icon.filename = %(source.dir)s/assets/imgs/icons/icon.png
# (str) Title of your application
title = Roboquix
# (str) Package name
package.name = roboquix
# (str) Package domain (needed for android/ios packaging)
package.domain = org.lilrobostudios
# (str) Source code where the main.py live
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,wav,ogg,json,ttf,txt
source.include_patterns = assets/*, assets/**/*, cleobo/*, cleobo/**/*
source.exclude_dirs = bin, buildozer_env, __pycache__, .buildozer
# (str) Application versioning
version = 1.4.1
# (list) Application requirements - includes Arabic text support
# Note: cython is NOT listed here - it's a build-time tool (pip-installed in CI),
# listing it here tells p4a to build Cython itself as an Android target recipe,
# which uses its own pinned/vendored source incompatible with modern Python headers
requirements = python3, pygame-ce, Pillow, arabic_reshaper, python-bidi, requests, setuptools, certifi, chardet, idna, urllib3
# (list) Supported orientations
orientation = landscape
# (bool) Indicate if the application should be fullscreen or not
fullscreen = 1
# (int) Target Android API (Standard for modern phones)
android.api = 33
# (int) Minimum API support (Android 5.0+)
android.minapi = 21
# (str) Android NDK version (25b is minimum required by p4a)
android.ndk = 25b
# (list) The Android archs to build for
android.archs = arm64-v8a
# (bool) automatically accept SDK license
android.accept_sdk_license = True
# (str) The format used to package the app for debug mode
android.debug_artifact = apk
# (list) Android app permissions
android.permissions = INTERNET, ACCESS_NETWORK_STATE
#
# Python for android (p4a) specific
#
# (str) Bootstrap to use for android builds (Critical for Pygame)
p4a.bootstrap = sdl2
# (str) Local recipes directory - contains a working pygame-ce recipe.
# Mainline p4a has NO built-in pygame-ce recipe (as of writing, it's still
# an open, unmerged PR: kivy/python-for-android#2971), so without this,
# "pygame-ce" isn't recognized as a compiled package and p4a silently
# falls back to a generic pip install, which grabs the prebuilt x86_64
# wheel from PyPI instead of cross-compiling for the target arch - that's
# the actual cause of "base.so is for EM_X86_64 instead of EM_AARCH64".
p4a.local_recipes = ./recipes

[buildozer]
# (int) Log level (2 = debug, very helpful for first-time builds)
log_level = 2
# (int) Display warning if buildozer is run as root
warn_on_root = 1
# Increase android toolchain log level for better diagnostics
android.log_level = 2
