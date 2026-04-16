#!/bin/bash
# Build PolyCopilot.app and create DMG
# Run this on your macOS High Sierra iMac

set -e

echo "=== PolyCopilot Build Script ==="

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Python version: $PYTHON_VERSION"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install requests==2.25.1
pip install pyinstaller==4.2

# Build the app
echo "Building PolyCopilot.app..."
pyinstaller \
  --name=PolyCopilot \
  --windowed \
  --onedir \
  --distpath=dist \
  --workpath=build \
  --additional-hooks-dir=. \
  polycopilot/main.py

# Verify build
if [ -d "dist/PolyCopilot.app" ]; then
  echo "✓ App bundle created successfully"
  ls -la dist/PolyCopilot.app
else
  echo "✗ Build failed"
  exit 1
fi

# Create DMG
echo "Creating DMG installer..."
hdiutil create -volname "PolyCopilot" \
  -srcfolder "dist/PolyCopilot.app" \
  -format UDSP \
  -o "PolyCopilot.dmg"

if [ -f "PolyCopilot.dmg" ]; then
  echo "✓ DMG created: PolyCopilot.dmg"
  ls -la PolyCopilot.dmg
else
  echo "✗ DMG creation failed"
  exit 1
fi

echo "=== Build Complete ==="
echo "You can now install PolyCopilot.dmg on your Mac"