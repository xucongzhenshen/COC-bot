# COC-bot

## 中文

### 1. 项目简介

COC-bot 是一个基于 Airtest 的《部落冲突》自动化脚本项目，用于学习以下能力：

- 游戏自动化流程设计
- 图像模板匹配与界面状态识别
- OCR 文本识别在自动化中的应用
- Python 工程化组织与日志调试

### 2. 重要声明（请先阅读）

- 本项目仅用于学习与技术研究目的。
- 使用任何自动化脚本都可能违反游戏服务条款（ToS），并可能导致账号处罚（包括但不限于封号）。
- 任何因使用本项目脚本造成的账号、设备、数据或其他损失，项目作者与贡献者概不负责。
- 请你自行评估并承担全部风险。

### 3. 项目架构

#### 3.1 运行流程

1. 解析命令行参数（设备、截图方式、触控方式、日志等级、夜世界流派等）。
2. 连接模拟器/设备并初始化 Airtest 运行环境。
3. 启动 COC（腾讯版或国际服），并关闭弹窗。
4. 进入主循环：
   - 识别当前世界（主世界/夜世界）
   - 执行对应世界逻辑
   - 删除日志目录中的图片缓存，随机等待后进入下一轮
5. 若异常发生：记录日志，重启游戏后继续。

#### 3.2 模块分层

- `main.py`
  - 项目入口
  - 参数解析
  - 主循环与异常恢复

- `cocbot/common.py`
  - 运行时初始化（Airtest 连接、截图检查）
  - 通用操作封装（日志、点击、识别、OCR、随机行为）
  - 启停游戏（ADB）

- `cocbot/advanced.py`
  - 世界识别（HOME/NIGHT）
  - 缩放和世界切换（乘船切换）

- `cocbot/home.py`
  - 主世界流程（视角回正、资源收集、切换夜世界）

- `cocbot/night.py`
  - 夜世界流程（收集资源、练兵、战斗、回主世界）
  - 支持女巫流与弓箭手流

- `cocbot/_assets.py`
  - 模板资源统一定义（按钮、图标、兵种等）

- `assets.air/`
  - Airtest 录制或辅助资源目录

- `test_and_debug/`
  - 调试和测试脚本

#### 3.3 架构示意图

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

### 4. 环境准备

建议使用 Conda（Miniforge/Anaconda）创建环境。

```bash
conda env create -f environment.yml
conda activate COC-bot
```

如果你使用 pip：

```bash
pip install -r requirements.txt
```

### 5. 运行说明

#### 5.1 基本启动

```bash
python main.py
```

#### 5.2 腾讯版示例

```bash
python main.py --log_path="log_tencent"
```

#### 5.3 国际服示例（弓箭手流）

```bash
python main.py --log_path="log_global" --device="emulator-5556" --night_faction="archer" --version="global"
```

### 6. 参数说明

| 参数              | 类型 | 默认值          | 可选值                  | 说明                                     |
| ----------------- | ---- | --------------- | ----------------------- | ---------------------------------------- |
| `--device`        | str  | `emulator-5554` | 任意 ADB 设备 ID        | 目标设备/模拟器序列号                    |
| `--cap_method`    | str  | `MINICAP`       | `MINICAP`, `JAVACAP`    | 截图方式，模拟器一般用 `MINICAP`         |
| `--touch_method`  | str  | `MINITOUCH`     | `MINITOUCH`, `ADBTOUCH` | 触控注入方式                             |
| `--ori_method`    | str  | `ADBORI`        | `ADBORI`, `MINICAPORI`  | 屏幕方向获取方式                         |
| `--loglevel`      | int  | `0`             | `0`, `1`, `2`           | 日志等级：0 流程级，1 步骤级，2 详细调试 |
| `--log_path`      | str  | `log`           | 任意路径名              | 日志输出目录                             |
| `--run_times`     | int  | `50`            | 正整数                  | 主循环执行次数                           |
| `--night_faction` | str  | `witch`         | `witch`, `archer`       | 夜世界练兵/战斗流派                      |
| `--version`       | str  | `tencent`       | `tencent`, `global`     | 游戏版本（腾讯版/国际服）                |

### 7. 日志与调试

- 日志默认写入 `--log_path` 指定目录。
- 当识别失败或流程异常时，会在日志目录生成调试截图。
- 建议先在高日志等级（`--loglevel 2`）下调通流程，再降级到常用日志等级。

### 8. 已知前提

- 需要可用的 ADB 连接。
- 依赖屏幕分辨率与模板匹配，若分辨率变化较大，可能需要更新模板。
- OCR 与图像识别在低画质或遮挡场景下可能出现误判。

---