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
# (list) Application requirements
requirements = python3, cython==0.29.36, pygame-ce, Pillow, arabic_reshaper, python-bidi, requests, setuptools, certifi, chardet, idna, urllib3
# (list) Supported orientations
orientation = landscape
# (bool) Indicate if the application should be fullscreen or not
fullscreen = 1
# (int) Target Android API (Standard for modern phones)
android.api = 33
# (int) Minimum API support (Android 5.0+)
android.minapi = 21
# (str) Android NDK version
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

[buildozer]
# (int) Log level (2 = debug, very helpful for first-time builds)
log_level = 2
# (int) Display warning if buildozer is run as root
warn_on_root = 1
