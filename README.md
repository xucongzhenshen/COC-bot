# COC-bot: Clash of Clans Automation Research Project

## English |  [中文](./README-chi.md)

### 1. Overview
**COC-bot** is an advanced automation framework for *Clash of Clans*, built on **Airtest** and **OpenCV**. This project is designed as a deep-learning case study for game automation, focusing on:
- **State-Machine Workflow**: Intelligent switching between Home and Night bases.
- **Advanced Computer Vision**: Multi-template matching, confidence-based world detection, and color-space analysis.
- **OCR-Driven Decision Making**: Using `ddddocr` for real-time battle timers and loading state monitoring.

---

### 2. Core Features

#### 🏠 Home Base (Main Village)
- **Auto-Collection**: One-click harvesting of Gold, Elixir, and Dark Elixir.
- **Smart Navigation**: Automatic camera zoom-out and pathfinding to the Night Base ship.
- **Popup Handling**: Intelligent closing of event news, shop offers, and "Trophy" rewards.

#### 🌙 Night Base (Builder Base)
- **Resource Management**: Efficient collection of Builder Gold and Elixir.
- **Advanced Training System**: Support for clearing barracks and re-training specific army compositions.
- **Double-Stage Battle Logic**: Supports the new BH10+ two-stage battle mechanics, including reinforcement deployment.
- **Selectable Battle Styles**:
  - 🧙 **Witch Swarm (BH9 focus)**: 
    - *Main Stage*: Hero + 1 Giant (Tank) + 5 Witches (Summoners).
    - *Reinforcements*: 1 Giant + 1 Witch.
  - 🏹 **Giant-Archer (BH4 focus)**: 
    - *Main Stage*: 3 Giants + 1 Group of Archers for precise early-game clearing.

---

### 3. Important Disclaimer
- **Educational Purpose Only**: This project is created for research on automation and computer vision.
- **Risk Warning**: Using automation scripts violates Supercell's Terms of Service. There is a **significant risk of account suspension or permanent ban**.
- **No Liability**: The author is NOT responsible for any consequences resulting from the use of this software. Proceed with caution.

---

### 4. Architecture & Modules

#### 4.1 Module Responsibilities
- **`main.py`**: The central brain. Handles CLI parsing, world scheduling, and exception recovery.
- **`cocbot/common.py`**: The hardware abstraction layer. Manages ADB connections, `force_snapshot` (for high-res stability), and OCR functions.
- **`cocbot/advanced.py`**: High-level logic including `detect_world()` (confidence-based weighting) and `pinch-to-zoom` view controls.
- **`cocbot/home.py` & `night.py`**: Domain-specific tasks. `night.py` contains the complex two-stage battle state machine.
- **`cocbot/_assets.py`**: A centralized library for 2K-resolution templates.

#### 4.2 Runtime Workflow
```text
[Start] -> [Connect ADB] -> [Launch App] 
   |
   v
[Detect World] <-------------+
   |                         |
   +--[HOME]--> [Collect] -> [Ship to Night] --+
   |                                           |
   +--[NIGHT]--> [Collect] -> [Train] -> [Battle] -> [Back Home]
   |                                           |
[Handle Exception] <---------------------------+
```

---

### 5. Environment & Setup

**Prerequisites:**
- **Emulator**: [LDPlayer 9](https://www.ldplayer.net/) (Recommended).
- **Resolution**: **Must be set to 2560 x 1440 (DPI 480)**.
- **Python**: 3.9+

**Installation:**
```bash
# Recommended: Conda
conda env create -f environment.yml
conda activate COC-bot

# Critical Dependency Note:
# To avoid conflicts between Airtest and OCR, we use:
# opencv-contrib-python==4.6.0.66
```

---

### 6. Usage & CLI Parameters

#### Basic Launch
```bash
python main.py --version tencent --night_faction witch
```

#### CLI Parameter Table
| Argument          | Default         | Choices             | Description                                    |
| ----------------- | --------------- | ------------------- | ---------------------------------------------- |
| `--device`        | `emulator-5554` | -                   | ADB Serial Number                              |
| `--version`       | `tencent`       | `tencent`, `global` | Game Package Version                           |
| `--night_faction` | `witch`         | `witch`, `archer`   | Battle Strategy (BH9 Witch / BH4 Giant-Archer) |
| `--loglevel`      | `0`             | `0, 1, 2`           | 0: Normal, 1: Flow, 2: Deep Debug              |
| `--cap_method`    | `JAVACAP`       | `JAVACAP, ADBCAP`   | Capture method (ADBCAP is slower but stabler)  |

---

### 7. Technical Notes
- **2K Support**: This bot is specifically tuned for 2560x1440. Most assets will fail on 1080p without re-scaling.
- **ADB Versioning**: The project includes logic to force-sync ADB versions between the environment and the emulator to prevent `Device Connection Timeout`.
- **OCR ROI**: The script uses specific Region of Interest (ROI) scanning for the top-center battle timer to minimize CPU usage.