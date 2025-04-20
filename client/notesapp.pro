QT += core gui widgets network
android: QT += androidextras

CONFIG += c++17

SOURCES += main.cpp

# Android specific files
android {
    ANDROID_PACKAGE_SOURCE_DIR = $$PWD/android
    DISTFILES += android/AndroidManifest.xml
}

# Installation settings
target.path = /usr/bin
INSTALLS += target