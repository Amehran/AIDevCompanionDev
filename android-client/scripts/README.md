# Android Client Scripts

This directory contains helper scripts for building and running the Android app.

## Available Scripts

### `run_app.sh`
Builds and installs the app on a connected device or emulator.

```bash
./scripts/run_app.sh
```

After installation, the app will be available on your device. You can launch it manually or run:
```bash
adb shell am start -n com.aidevcompanion.app/.MainActivity
```

### `clean.sh`
Cleans all build artifacts and Gradle caches.

```bash
./scripts/clean.sh
```

Use this if you encounter build issues or want a fresh start.

## Prerequisites

- Android device or emulator connected and authorized
- Check connected devices: `adb devices`
- If no devices show up, start an emulator from Android Studio

## Quick Start

1. Connect your Android device or start an emulator
2. Run: `./scripts/run_app.sh`
3. Launch the app from your device

## Troubleshooting

If the build fails:
1. Run `./scripts/clean.sh`
2. Run `./scripts/run_app.sh` again

If installation fails:
- Check that a device is connected: `adb devices`
- Make sure USB debugging is enabled on your device
- Try restarting adb: `adb kill-server && adb start-server`
