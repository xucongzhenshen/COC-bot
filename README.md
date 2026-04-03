# COC-bot

## English

### 1. Overview

COC-bot is an Airtest-based automation project for Clash of Clans, built mainly for learning:

- Automation workflow design
- Template matching and UI state detection
- OCR usage in automation
- Python project structure and logging/debugging

### 2. Important Disclaimer (Read First)

- This project is for learning and research purposes only.
- Any automation script may violate the game's Terms of Service and can lead to account penalties (including bans).
- The author and contributors are NOT responsible for any account bans, device issues, data loss, or any other damage caused by using this script.
- You use it at your own risk.

### 3. Architecture

#### 3.1 Runtime Flow

1. Parse CLI arguments (device, capture/touch/orientation methods, log level, night faction, etc.).
2. Connect device/emulator and initialize Airtest runtime.
3. Launch COC (Tencent or Global), then close popups.
4. Enter main loop:
   - Detect current world (HOME/NIGHT)
   - Run corresponding world logic
   - Clean image logs and wait a randomized interval
5. On exception: log error, restart game, continue loop.

#### 3.2 Module Responsibilities

- `main.py`
  - Entry point
  - Argument parsing
  - Main loop and recovery

- `cocbot/common.py`
  - Runtime setup (Airtest connection, screenshot readiness)
  - Shared helpers (logging, touch/wait, OCR, randomization)
  - Game start/stop via ADB

- `cocbot/advanced.py`
  - World detection (HOME/NIGHT)
  - Zooming and world switching

- `cocbot/home.py`
  - Home world flow (camera alignment, resource collection, switch to night)

- `cocbot/night.py`
  - Night world flow (resource collection, training, battles, return home)
  - Supports `witch` and `archer` styles

- `cocbot/_assets.py`
  - Template asset definitions (buttons/icons/troops)

- `assets.air/`
  - Airtest resources/recorded assets

- `test_and_debug/`
  - Debug and test scripts

#### 3.3 Architecture Diagram

```text
CLI Args
   |
   v
main.py
   |
   +--> common.py (runtime/log/ocr/adb)
   +--> advanced.py (detect world / zoom / switch)
   +--> home.py (home tasks)
   +--> night.py (night tasks & battle)
                |
                v
             _assets.py (templates)
```

### 4. Environment Setup

Conda is recommended:

```bash
conda env create -f environment.yml
conda activate COC-bot
```

Or with pip:

```bash
pip install -r requirements.txt
```

### 5. Usage

#### 5.1 Basic Run

```bash
python main.py
```

#### 5.2 Tencent Version Example

```bash
python main.py --log_path="log_tencent"
```

#### 5.3 Global Version Example (Archer)

```bash
python main.py --log_path="log_global" --device="emulator-5556" --night_faction="archer" --version="global"
```

### 6. CLI Parameters

| Argument | Type | Default | Choices | Description |
|---|---|---|---|---|
| `--device` | str | `emulator-5554` | Any ADB device ID | Target emulator/device serial |
| `--cap_method` | str | `MINICAP` | `MINICAP`, `JAVACAP` | Screenshot method |
| `--touch_method` | str | `MINITOUCH` | `MINITOUCH`, `ADBTOUCH` | Touch injection method |
| `--ori_method` | str | `ADBORI` | `ADBORI`, `MINICAPORI` | Orientation detection method |
| `--loglevel` | int | `0` | `0`, `1`, `2` | Logging level: flow/step/debug |
| `--log_path` | str | `log` | Any path name | Log directory |
| `--run_times` | int | `50` | Positive integer | Main loop iterations |
| `--night_faction` | str | `witch` | `witch`, `archer` | Night world style |
| `--version` | str | `tencent` | `tencent`, `global` | Game version |

### 7. Logging and Debugging

- Logs are written to the directory specified by `--log_path`.
- Debug snapshots are generated when recognition/actions fail.
- For troubleshooting, start with `--loglevel 2` first.

### 8. Prerequisites and Notes

- ADB connection must be available.
- Template matching depends on resolution and UI consistency.
- OCR/image recognition can be unstable in low-quality or occluded scenes.
