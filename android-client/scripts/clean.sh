#!/bin/bash

# Clean build script - removes all build artifacts and caches

set -e

cd "$(dirname "$0")/.."

echo "🧹 Cleaning project..."
./gradlew clean

echo "🗑️  Clearing Gradle caches..."
rm -rf .gradle
rm -rf build
rm -rf app/build

echo "✅ Clean complete!"
