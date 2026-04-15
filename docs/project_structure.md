# COC-bot 重构建议目录结构

> 目标：配置管理、服务构建、流程编排分层，减少跨模块耦合。
## 1. 思路：
### GonfigManager
- 实现所有参数管理，依赖解析，参数配置包构建。
- 读取整个项目的参数，容易在终端写的可以直接在args写，不好写的或不会频繁变化的可以通过json文件传，args里写读取json的路径即可。
### ServiceFactory
- 使用GonfigManager传来的参数配置包，构建出具体的基础工具包，包括：
  - Logger（日志路径，创建，管理，写接口）
  - DeviceManager（设备连接，游戏启动关闭）
  - BasicOperator（触控，文字识别，截图）
  - MeadowDetector（同原MeadowDetector）
  - AirDefenseDetector（识别防空火箭）
  - AttackOptimizer（提供最佳劈法）
  - CalibratedMovementController(实现基于追踪回正/校准的分段移动，并使用Meadow实现世界视角回正逻辑)
### AppBuilder，
- Bot类（接口+具体的根据参数包构建run_bot全流程自动化逻辑）
- HomeBot与NightBot，根据Bot类的接口实现其具体逻辑。
- MainLoop，使用两Bot来运行并完成世界的识别，切换时的Bot切换逻辑，终止逻辑与世界切换异常时的异常处理。
### main
- main函数就是args->ConfigManager然后构建或获取各对象，完成初始化逻辑，再进入MainLoop.run一键自动化运行


## 2. 推荐结构
```
coc_bot/
├── configs/                # 存放各种 JSON 配置文件
│   ├── home_settings.json
│   └── night_settings.json
├── data/ 
│   ├── assets/                             # 存放模板图片、OCR 模型等静态资源
│   └── sample_imgs/                        # 存放从游戏采样获得的草地图样
├── logs/                                   # 日志输出目录
├── src/
│   ├── core/                               # 核心基础设施层，用于指导整个项目的组建
│   │   ├── config_manager.py
│   │   ├── service_factory.py
│   │   └── app_builder.py
│   ├── services/                           # 基础服务层（原子功能）
│   │   ├── core/
│   │   │   ├── device_manager.py
│   │   │   ├── basic_operator.py
│   │   │   └── logger.py
│   │   ├── perception/                             # 感知层（识别定位，只读游戏状态）
│   │   │   ├── __init__.py
│   │   │   ├── meadow_detector.py                  # MeadowDetector（草地定位）
│   │   │   └── air_defense_detector.py             # AirDefenseDetector（防空火箭识别）
│   │   ├── decision/                               # 决策层（策略计算，无状态操作）
│   │   │   ├── __init__.py
│   │   │   └── attack_optimizer.py                 # AttackOptimizer（01背包求解）
│   │   ├── execution/                              # 执行层（写操作，改变游戏状态）
│   │   │   ├── __init__.py
│   │   │   └── calibrated_movement_controller.py   # CalibratedMovementController
│   ├── logic/                                      # 业务逻辑层
│   │   ├── base_bot.py                             # Bot 父类接口
│   │   ├── home_bot.py
│   │   ├── night_bot.py
│   │   └── main_loop.py                            # 调度中心
│   └── utils/                              # 纯工具类（不依赖任何服务的静态函数）
│       └── assests.py                  # 定义所有图标
├── main.py                         # 程序唯一入口
└── requirements.txt
```

## 3. 分层架构原理
### 3.1. 核心层 (`src/core/`) —— 系统组装中枢

| 组件               | 职责                                  | 设计原理                                                                 |
| :----------------- | :------------------------------------ | :----------------------------------------------------------------------- |
| **ConfigManager**  | 参数管理、依赖解析、配置包构建        | 统一配置入口，支持命令行参数与JSON文件混合配置，实现"一次读取，全局使用" |
| **ServiceFactory** | 根据配置包构建所有基础服务实例        | 依赖注入容器，解耦服务创建与使用，控制服务生命周期与依赖关系             |
| **AppBuilder**     | 构建业务逻辑对象（Bot实例、MainLoop） | 高层组装器，将服务组合成可执行业务单元                                   |

**核心设计原则**：该层是**唯一允许跨层访问**的层级，负责整个系统的依赖注入与组装。

---

### 3.2. 服务层 (`src/services/`) —— 原子能力层

按**技术职责**分层，严格遵循**依赖方向**：

```
decision/execution → perception → core
        ↑___________________________|
```

#### 3.2.1 基础设施子层 (`services/core/`)

| 服务              | 职责                                 | 特性                             |
| :---------------- | :----------------------------------- | :------------------------------- |
| **Logger**        | 日志路径管理、文件创建、分级写入接口 | 全局唯一，所有层共享同一实例     |
| **DeviceManager** | 设备连接管理、游戏启动/关闭控制      | 硬件抽象，隔离具体设备协议       |
| **BasicOperator** | 触控操作、文字识别（OCR）、截图      | 原子操作接口，上层服务的构建基础 |

**设计约束**：该子层**无任何外部依赖**，可被任意上层服务依赖。

---

#### 3.2.2 感知子层 (`services/perception/`)

| 服务                   | 职责               | 输入输出                            |
| :--------------------- | :----------------- | :---------------------------------- |
| **MeadowDetector**     | 草地特征识别与定位 | 截图 → 草地位置/置信度              |
| **AirDefenseDetector** | 防空火箭目标识别   | 截图 → 目标列表（位置、类型、等级） |

**设计约束**：
- **只读操作**：仅观察游戏状态，绝不改变游戏
- **依赖方向**：仅依赖 `services/core/`
- **输出格式**：返回结构化数据对象，不包含任何执行逻辑

---

#### 3.2.3 决策子层 (`services/decision/`)

| 服务                | 职责             | 算法核心           |
| :------------------ | :--------------- | :----------------- |
| **AttackOptimizer** | 计算最优进攻策略 | 01背包动态规划求解 |

**设计约束**：
- **无状态纯计算**：输入确定则输出确定，无副作用
- **业务无关**：仅实现"给定目标与资源，求最优分配"的数学问题
- **依赖方向**：可依赖 `services/core/`（获取配置）、`services/perception/`（获取目标数据）

---

#### 3.2.4 执行子层 (`services/execution/`)

| 服务                             | 职责                       | 核心机制                                            |
| :------------------------------- | :------------------------- | :-------------------------------------------------- |
| **CalibratedMovementController** | 基于追踪回正的分段移动控制 | 移动→检测偏差→修正→继续，使用Meadow实现世界视角回正 |

**设计约束**：
- **唯一写操作层**：唯一允许改变游戏状态的服务层
- **闭环控制**：感知→决策→执行→感知（校准循环）
- **依赖方向**：依赖 `services/core/`（基础操作）、`services/perception/`（MeadowDetector提供回正参考点）

---

### 3.3. 业务逻辑层 (`src/logic/`) —— 流程编排层

| 组件              | 职责                                                       | 设计模式                                |
| :---------------- | :--------------------------------------------------------- | :-------------------------------------- |
| **BaseBot (ABC)** | 定义Bot接口：`run_bot()`、`can_handle()`、`on_interrupt()` | 模板方法模式，约束子类行为契约          |
| **HomeBot**       | 实现家乡模式自动化逻辑                                     | 继承BaseBot，注入所需服务，实现具体流程 |
| **NightBot**      | 实现夜世界模式自动化逻辑                                   | 继承BaseBot，注入所需服务，实现具体流程 |
| **MainLoop**      | 世界识别、Bot调度、切换逻辑、终止处理、异常恢复            | 状态机模式，管理双世界生命周期          |

**设计约束**：
- Bot类**不直接创建服务**，通过构造函数接收ServiceFactory构建的服务实例
- MainLoop**不感知具体服务**，仅操作Bot接口

---

### 3.4. 工具层 (`src/utils/`) —— 纯工具函数

| 组件            | 职责                           | 约束                                     |
| :-------------- | :----------------------------- | :--------------------------------------- |
| **assests.py** | 图标静态资源路径管理、资源加载工具 | **零依赖**：不导入任何services或core模块 |

---

## 数据流向与调用链

```
┌─────────────────────────────────────────────────────────────┐
│                         main.py                              │
│  args → ConfigManager → ServiceFactory → AppBuilder         │
│         ↓                    ↓              ↓                 │
│    ConfigPackage      ServiceInstances   Bot/MainLoop       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      MainLoop.run()                          │
│  while running:                                              │
│    1. 识别当前世界 → 选择对应Bot                              │
│    2. bot.run_bot()                                          │
│    3. 检测世界切换/异常 → 处理或终止                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    HomeBot / NightBot                        │
│  具体流程编排：                                               │
│    perception.XxxDetector.detect()                           │
│    decision.AttackOptimizer.solve()                          │
│    execution.CalibratedMovementController.move()             │
│    (loop with calibration)                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 关键设计决策

| 决策                       | 原理                                                         |
| :------------------------- | :----------------------------------------------------------- |
| **ConfigManager分离**      | 配置解析与使用分离，支持多源配置（args + JSON）合并          |
| **ServiceFactory集中创建** | 单点控制依赖注入，避免服务实例散落在各处                     |
| **感知/决策/执行三层分离** | 强制解耦"看什么"、"想什么"、"做什么"，便于单元测试与替换实现 |
| **Bot多态设计**            | 家乡/夜世界流程差异通过子类实现，MainLoop无感知切换          |
| **MainLoop统一调度**       | 集中处理跨世界状态管理，Bot专注单世界逻辑                    |

---

## 依赖规则速查

| 层级                   | 允许依赖                                 | 严禁依赖                                              |
| :--------------------- | :--------------------------------------- | :---------------------------------------------------- |
| `utils/`               | 标准库                                   | 任何项目模块                                          |
| `services/core/`       | 标准库、第三方库                         | `services/*`、`logic/`、`core/`                       |
| `services/perception/` | `services/core/`                         | `services/decision/`、`services/execution/`、`logic/` |
| `services/decision/`   | `services/core/`、`services/perception/` | `services/execution/`、`logic/`                       |
| `services/execution/`  | `services/core/`、`services/perception/` | `logic/`                                              |
| `logic/`               | `services/*`                             | `core/`（除入口传参外）                               |
| `core/`                | 任意下层                                 | 无                                                    |

**循环依赖检测**：`execution/` 可依赖 `perception/`，但 `perception/` 严禁依赖 `execution/`。

## 迁移顺序建议

1. 先稳定 ConfigManager（已开始）。
2. 抽 ServiceFactory，先包装旧函数。
3. 抽 Bot 接口并迁 HomeBot/NightBot。
4. 新建 MainLoop 承接世界切换与异常恢复。
5. 清理 legacy 目录并最终收敛。
