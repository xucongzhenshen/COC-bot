# COC-bot 重构建议目录结构

> 目标：配置管理、服务构建、流程编排分层，减少跨模块耦合。
## 1. 思路：
### GonfigManager
- 实现所有参数管理，依赖解析，参数配置包构建。
- 读取整个项目的参数，容易在终端写的可以直接在args写，不好写的或不会频繁变化的可以通过json文件传，args里写读取json的路径即可。
### ServiceFactory
- 使用GonfigManager传来的参数配置包，构建出具体的基础工具包
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
│   ├── app_config/
│   └── strategy/
├── data/ 
│   ├── assets/                             # 存放模板图片、OCR 模型等静态资源
│   ├── game_data/                          # 存放具体的游戏数据(.csv)
│   └── sample_imgs/                        # 存放从游戏采样获得的草地图样
├── logs/                                   # 日志输出目录
├── src/
│   ├── core/                               # 核心基础设施层，用于指导整个项目的组建
│   │   ├── config_manager.py
│   │   ├── service_factory.py
│   │   └── app_builder.py
│   ├── services/                           # 基础服务层（原子功能）
│   │   ├── core/
│   │   │   ├── basic_operator.py
│   │   │   └── logger.py
│   │   ├── positioning/                            # 定位
│   │   │   ├── world_detector.py                   # WorldDetector（辨别当前所在世界）
│   │   │   └── meadow_detector.py                  # MeadowDetector（草地定位）
│   │   ├── movement/                               # 移动
│   │   │   └── calibrated_movement_controller.py   # CalibratedMovementController
│   │   ├── initializer/                            
│   │   │   ├── device_manager.py                   # DeviceManager设备的启动，连接逻辑
│   │   │   └── game_initializer.py                 # GameInitializer游戏启动，重启等
│   │   ├── attack/
│   │   │   ├── strategy_interpreter.py             # 策略解释器，根据策略config执行进攻逻辑
│   │   │   ├── attack_executor.py                  # 完整进攻流程执行器。搜索，进攻，回营
│   │   │   ├── troop_trainer.py                     # 根据策略得到训练参数，训练部队
│   │   │   └── utils/
│   │   │       ├── air_defense_detector.py         # AirDefenseDetector（防空火箭识别）
│   │   │       ├── attack_optimizer.py             # AttackOptimizer（01背包求解）
│   │   │       └── actions.py
│   │   └── exception/
│   │       └── exception_handler.py
│   ├── logic/                                      # 业务逻辑层
│   │   ├── base_bot.py                             # Bot 父类接口
│   │   ├── home_bot.py
│   │   ├── night_bot.py
│   │   └── main_loop.py                    # 调度中心，调度services与Bot完成相关逻辑
│   └── utils/
│   │   └── assets.py
├── main.py                         # 程序唯一入口
└── requirements.txt
```
```
coc_bot/
├── configs/                # 存放各种 JSON 配置文件
│   ├── app_config/
│   └── strategy/
├── data/ 
│   ├── assets/                             # 存放模板图片、OCR 模型等静态资源
│   ├── game_data/                          # 存放具体的游戏数据(.csv)
│   └── sample_imgs/                        # 存放从游戏采样获得的草地图样
├── logs/                                   # 日志输出目录
├── src/
│   ├── core/                               # 核心基础设施层，用于指导整个项目的组建
│   │   ├── config_manager.py
│   │   ├── service_factory.py
│   │   └── app_builder.py
│   ├── services/                           # 基础服务层（原子功能）
│   │   ├── core/
│   │   │   ├── basic_operator.py
│   │   │   └── logger.py
│   │   ├── positioning/                            # 定位
│   │   │   ├── world_detector.py                   # WorldDetector（辨别当前所在世界）
│   │   │   └── meadow_detector.py                  # MeadowDetector（草地定位）
│   │   ├── movement/                               # 移动
│   │   │   └── calibrated_movement_controller.py   # CalibratedMovementController
│   │   ├── initializer/                            
│   │   │   ├── device_manager.py                   # DeviceManager设备的启动，连接逻辑
│   │   │   └── game_initializer.py                 # GameInitializer游戏启动，重启等
│   │   ├── attack/
│   │   │   ├── air_defense_detector.py         # AirDefenseDetector（防空火箭识别）
│   │   │   ├── attack_optimizer.py             # AttackOptimizer（01背包求解）
│   │   │   └── actions.py
│   ├── logic/                                      # 业务逻辑层
|   |   ├── base_state.py                           # 状态模版
|   |   ├── collect_resouorce.py
|   |   ├── correct_pos.py                          
|   |   ├── train.py
|   |   ├── attack.py
|   |   ├── switch.py
|   |   └── strategy/                               # 原strategy_interpreter.py拆分
│   │   │   ├── base_interpreter.py
│   │   │   ├── home_interpreter.py
│   │   │   └── night_interpreter.py
│   ├── app/ 
│   │   ├── base_bot.py                             # Bot 父类接口, 状态机，有logic里定义的5种状态。
│   │   ├── home_bot.py
│   │   └── night_bot.py
│   ├── orchestration/
│   │   └── scheduler.py                    # 调度中心，调度services与Bot完成相关逻辑（原main_loop）
│   └── utils/
│   │   └── assets.py
│   ├── context/                                 # ← 上下文层（纯数据，无业务依赖）
│   │   ├── __init__.py
│   │   ├── enums.py                             # 状态枚举：AttackPhase, ActionStatus 等
│   │   ├── bot_context.py                       # BotContext
│   │   ├── attack_context.py                    # AttackContext
│   │   └── action_context.py                    # ActionContext
│   ├── exception/
|   │   ├── base.py                              # CocBotException 基类
|   │   ├── fatal_exception.py                   # FatalException（设备/游戏启动失败）
|   │   ├── recovery/                            # 恢复策略
|   │   │   ├── __init__.py
│   |   │   ├── base_recovery.py                 # RecoveryStrategy 抽象
│   │   |   ├── bot_recovery.py                  # 利用 BotContext 恢复
│   │   |   ├── attack_recovery.py               # 利用 AttackContext + ActionContext 恢复
|   │   │   └── world_recovery.py                # 选世界失败 → 重启
|   │   └── handler.py                           # ExceptionHandler（调度用哪个 recovery）
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
