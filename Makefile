# PolyCopilot Build and Package Makefile
# For macOS High Sierra 10.13+

.PHONY: help install test build clean package dmg

PYTHON_VERSION=3.7
VENV_NAME=venv
APP_NAME=PolyCopilot
BUNDLE_ID=com.polycopilot.app

help:
	@echo "PolyCopilot Build Commands"
	@echo "=========================="
	@echo "make install    - Install Python dependencies"
	@echo "make test       - Run the application in test mode"
	@echo "make build      - Build the .app bundle"
	@echo "make package    - Create .dmg installer"
	@echo "make clean      - Clean build artifacts"
	@echo ""
	@echo "Requirements: Python 3.7+ on macOS"

install:
	@echo "Installing dependencies..."
	@if [ ! -d "$(VENV_NAME)" ]; then \
		python3 -m venv $(VENV_NAME); \
	fi
	@source $(VENV_NAME)/bin/activate && \
		pip install --upgrade pip && \
		pip install -r requirements.txt
	@echo "Dependencies installed"

test:
	@echo "Running PolyCopilot..."
	@source $(VENV_NAME)/bin/activate && \
		python polycopilot/main.py

build:
	@echo "Building app bundle with PyInstaller..."
	@source $(VENV_NAME)/bin/activate && \
		pyinstaller --name=$(APP_NAME) \
			--windowed \
			--onedir \
			--distpath=dist \
			--workpath=build \
			--add-data=polycopilot:polycopilot \
			--hidden-import=tkinter \
			--hidden-import=sqlite3 \
			--collect-all=tkinter \
			polycopilot/main.py
	@echo "Build complete: dist/$(APP_NAME).app"

package:
	@echo "Creating .dmg installer..."
	@if [ -d "dist/$(APP_NAME).app" ]; then \
		hdiutil create -volname "$(APP_NAME)" \
			-srcfolder "dist/$(APP_NAME).app" \
			-format UDSP \
			-o "$(APP_NAME).dmg"; \
		echo "Created: $(APP_NAME).dmg"; \
	else \
		echo "Error: App bundle not found. Run 'make build' first."; \
	fi

dmg: build package

clean:
	@echo "Cleaning build artifacts..."
	@rm -rf build dist *.dmg
	@rm -rf __pycache__ */__pycache__ */*/__pycache__
	@find . -name "*.pyc" -delete
	@echo "Clean complete"