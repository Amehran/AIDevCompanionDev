#!/bin/bash

# Android App Build & Run Script
# This script builds and installs the Android app on a connected device/emulator

set -e  # Exit on error

cd "$(dirname "$0")/.."

# Find Android SDK
ANDROID_SDK="${ANDROID_HOME:-$HOME/Library/Android/sdk}"
ADB="$ANDROID_SDK/platform-tools/adb"

if [ ! -f "$ADB" ]; then
    echo "❌ Error: adb not found at $ADB"
    echo "Please set ANDROID_HOME or install Android SDK"
    exit 1
fi

echo "🔨 Building Android app..."
./gradlew assembleDebug

echo "📱 Installing app on device/emulator..."
./gradlew installDebug

echo "✅ App installed successfully!"
echo ""
echo "🚀 Launching app..."
$ADB shell am start -n com.aidevcompanion.app/.MainActivity

echo ""
echo "✅ App is now running on your device!"

