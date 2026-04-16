# PolyCopilot - Build & Run Guide

## For macOS High Sierra 10.13 on iMac Mid-2010

### Prerequisites

1. **Install Python 3.7**
   ```bash
   # Using Homebrew (recommended)
   brew install python@3.7
   
   # Or download from python.org
   # https://www.python.org/downloads/release/python-379/
   ```

2. **Verify Python Version**
   ```bash
   python3 --version
   # Should output: Python 3.7.9
   ```

3. **Install Dependencies**
   ```bash
   pip3 install requests==2.25.1
   ```

### Running the Application

```bash
cd /path/to/PolyCopilot
python3 polycopilot/main.py
```

### Building the .dmg Package

#### Option 1: Using Makefile
```bash
make install    # Install dependencies
make test       # Test run
make build      # Build .app bundle
make package    # Create .dmg installer
```

#### Option 2: Manual Build
```bash
# Install PyInstaller
pip3 install pyinstaller

# Build the app
pyinstaller --name=PolyCopilot \
  --windowed \
  --onedir \
  --distpath=dist \
  --additional-hooks-dir=. \
  polycopilot/main.py

# Create .dmg
hdiutil create -volname "PolyCopilot" \
  -srcfolder dist/PolyCopilot.app \
  -format UDSP \
  -o PolyCopilot.dmg
```

### Configuration

The application stores data in:
- **Database**: `~/Library/Application Support/PolyCopilot/polycopilot.db`
- **Logs**: `~/Library/Logs/PolyCopilot/`

### First-Time Setup

1. Launch the app
2. Go to **Settings** tab
3. Configure:
   - Polling interval (default: 30 seconds)
   - Copy mode (fixed/proportional/weighted)
   - Risk controls (max daily loss, max exposure)
   - Bullpen CLI path (if installed)
   - Your wallet address
4. Go to **Traders** tab
5. Click "Refresh Leaderboard" to fetch traders
6. Select traders to follow
7. Start the bot from the sidebar

### Usage Modes

1. **Dry-Run Mode** (default): Logs all trades without executing
2. **Paper Trading**: Simulates execution against paper wallet
3. **Live Trading**: Real execution via Bullpen CLI

### Troubleshooting

**Issue**: App won't launch
- Check Python version: `python3 --version` (must be 3.7.x)
- Install tkinter: `brew install python-tk`

**Issue**: No traders shown
- Check internet connection
- The app uses demo data if API unavailable

**Issue**: Bot won't start
- Verify at least one trader is followed
- Check Settings for valid configuration

### Files Structure

```
PolyCopilot/
├── polycopilot/
│   ├── main.py          # Entry point
│   ├── app.py           # Main UI
│   ├── core/            # Bot logic
│   ├── ui/              # Screens
│   ├── api/             # API clients
│   ├── storage/         # Database
│   └── utils/           # Utilities
├── requirements.txt     # Python deps
├── setup.py            # Package config
├── Makefile            # Build commands
└── README.md           # This file
```

### Safety Features

- Max daily loss limit
- Max exposure limit
- Max concurrent positions
- Duplicate trade prevention
- Stale trade detection
- Dry-run mode
- Paper trading mode
- Full logging

### Support

Check logs at: `~/Library/Logs/PolyCopilot/