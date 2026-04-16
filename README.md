# PolyCopilot - PolyMarket Copy Trading Desktop Application

A local desktop application for macOS High Sierra that enables copy-trading functionality for PolyMarket through Bullpen CLI integration.

## System Requirements

- **OS**: macOS High Sierra 10.13.0 or later
- **Device**: Intel-based Mac (iMac Mid-2010 or newer)
- **RAM**: 4GB minimum
- **Storage**: 100MB available space

## Technology Stack

- **Runtime**: Python 3.7.x
- **UI Framework**: Tkinter (built into Python)
- **Storage**: SQLite3 (built into Python)
- **HTTP Client**: requests
- **Packaging**: PyInstaller for .dmg creation

## Key Features

1. **Trader Discovery**: Pull active traders from PolyMarket leaderboard
2. **Signal Detection**: Real-time monitoring of followed trader activity
3. **Copy Execution**: Mirror trades with configurable sizing rules
4. **Risk Controls**: Daily loss limits, max exposure, position limits
5. **Performance Tracking**: P&L, win rate, trade history
6. **Bot Controls**: Start/stop/pause/resume from UI

## Installation

### Prerequisites

1. Install Python 3.7.x on your Mac:
```bash
brew install python@3.7
```

2. Install dependencies:
```bash
pip3 install -r requirements.txt
```

### Running the Application

```bash
cd polycopilot
python3 main.py
```

## Usage Modes

1. **Dry-run Mode**: Logs all detected trades without executing
2. **Paper Trading**: Simulates execution against paper wallet
3. **Live Trading**: Real execution via Bullpen CLI

## Configuration

Configure settings through the Settings screen:
- Polling interval
- Copy mode (fixed/proportional/weighted)
- Risk limits
- Trader filters
- Bullpen CLI path

## License

MIT License