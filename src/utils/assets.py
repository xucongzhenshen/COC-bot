from airtest.core.api import Template
import os
from pathlib import Path


def get_project_root(current_file=__file__, marker='.git'):
    """
    通过向上查找标记文件（如 .git、pyproject.toml 等）确定项目根目录
    """
    current_path = Path(current_file).resolve() if current_file else Path.cwd()
    
    for parent in [current_path] + list(current_path.parents):
        if (parent / marker).exists():
            return parent
    return current_path / '../../../'   # 如果没有找到标记文件，默认返回当前文件的上四级目录作为项目根

data_dir = get_project_root() / 'data' / 'assets'

def get_image_path(image_name):
    """构建图片的绝对路径"""
    return str(data_dir / image_name)


# -*- encoding=utf8 -*-
class Assets:
    """游戏界面素材模板。

    组织规则：
    1. 先按世界分类：主世界、夜世界。
    2. 每个世界内再按用途分组：资源/入口、按钮、训练、部署、战斗状态、识别目标。
    3. 变量名保持兼容，不修改对外常量名，避免影响现有调用逻辑。
    """

    # =========================
    # 公共素材（Common Assets）
    # =========================
    # --- BTN（用于关闭弹窗、确认、翻页、搜索与删除） ---
    CLOSE_ACTIVITY = Template(get_image_path("common/close_activity.png"), record_pos=(0.317, -0.156), resolution=(2560, 1440))
    CLOSE = Template(get_image_path("common/close.png"), record_pos=(0.399, -0.202), resolution=(2560, 1440))
    BTN_BACK = Template(get_image_path("common/btn_back.png"), record_pos=(-0.0, 0.194), resolution=(2560, 1440))
    BTN_CONFIRM = Template(get_image_path("common/btn_confirm.png"), record_pos=(0.011, 0.188), resolution=(2560, 1440))
    BTN_TRAIN = Template(get_image_path("common/btn_train.png"), record_pos=(-0.46, 0.126), resolution=(2560, 1440))


    # =========================
    # 主世界（Home Village）
    # =========================

    # --- Resource（用于主界面状态确认、世界切换、资源识别） ---
    OIL = Template(get_image_path("home/resource/oil.png"), record_pos=(-0.37, -0.085), resolution=(2560, 1440))
    WATER = Template(get_image_path("home/resource/water.png"), record_pos=(0.22, -0.191), resolution=(2560, 1440))
    GOLD = Template(get_image_path("home/resource/gold.png"), record_pos=(-0.267, -0.157), resolution=(2560, 1440))

    # Other entrances (用于识别其他功能入口，辅助状态判断与导航) ---
    BEER = Template(get_image_path("home/other_entrances/beer.png"), record_pos=(-0.29, -0.049), resolution=(2560, 1440))
    CLAN_WAR = Template(get_image_path("home/other_entrances/clan_war.png"), record_pos=(-0.461, 0.061), resolution=(2560, 1440))
    SHIP_TO_NIGHT = Template(get_image_path("home/other_entrances/ship_to_night.png"), record_pos=(-0.221, 0.064), resolution=(2560, 1440))

    # --- Train（用于进入并识别训练配置编辑界面） ---
    BTN_HOME_DELETE = Template(get_image_path("home/train/btn_home_delete.png"), record_pos=(0.464, -0.156), resolution=(2560, 1440))
    SAVED_CONFIG = Template(get_image_path("home/train/saved_config.png"), record_pos=(0.002, -0.225), resolution=(2560, 1440))
    CLICK_TO_EDIT = Template(get_image_path("home/train/click_to_edit.png"), record_pos=(0.206, -0.093), resolution=(2560, 1440))

    # --- Army_Train（用于识别兵种/法术训练入口） ---
    DRAGON_TRAIN = Template(get_image_path("home/army_train/dragon_train.png"), record_pos=(-0.02, 0.209), resolution=(2560, 1440))
    LIGHTNING_SPELL_TRAIN = Template(get_image_path("home/army_train/lightning_spell_train.png"), record_pos=(-0.426, 0.102), resolution=(2560, 1440))

    # --- Army_Deploy（用于战斗中识别兵种/英雄/法术可部署按钮） ---
    DRAGON_DEPLOY = Template(get_image_path("home/army_deploy/dragon_deploy.png"), record_pos=(-0.398, 0.238), resolution=(2560, 1440))
    QUEEN_DEPLOY = Template(get_image_path("home/army_deploy/queen_deploy.png"), record_pos=(-0.229, 0.214), resolution=(2560, 1440))
    THE_REVENANT_PRINCE_DEPLOY = Template(get_image_path("home/army_deploy/the_revenant_prince_deploy.png"), record_pos=(-0.154, 0.216), resolution=(2560, 1440))
    LIGHTNING_SPELL_DEPLOY = Template(get_image_path("home/army_deploy/lightning_spell_deploy.png"), record_pos=(-0.145, 0.223), resolution=(2560, 1440))

    # --- Fight（用于识别主世界战斗按钮状态） ---
    FIGHT_HOME = Template(get_image_path("home/fight/fight_home.png"), record_pos=(-0.435, 0.213), resolution=(2560, 1440))
    FIGHT_HOME_WITH_STAR = Template(get_image_path("home/fight/fight_home_with_star.png"), record_pos=(-0.436, 0.212), resolution=(2560, 1440))
    FIGHT_HOME_WITH_3_STAR = Template(get_image_path("home/fight/fight_home_with_3_star.png"), record_pos=(-0.436, 0.212), resolution=(2560, 1440))
    BTN_HOME_SEARCH = Template(get_image_path("home/fight/btn_home_search.png"), record_pos=(-0.329, 0.13), resolution=(2560, 1440))
    BTN_NEXT = Template(get_image_path("home/fight/btn_next.png"), record_pos=(0.409, 0.116), resolution=(2560, 1440))
    BTN_FIGHT_CONFIRM = Template(get_image_path("home/fight/btn_fight_confirm.png"), record_pos=(0.383, 0.22), resolution=(2560, 1440))

    # --- Anti-Aircraft Rocket（用于雷电法术投放定位） ---
    ANTI_AIRCRAFT_ROCKET1 = Template(get_image_path("home/anti_aircraft_rocket/anti_aircraft_rocket1.png"), record_pos=(-0.014, -0.092), resolution=(2560, 1440))
    ANTI_AIRCRAFT_ROCKET2 = Template(get_image_path("home/anti_aircraft_rocket/anti_aircraft_rocket2.png"), record_pos=(0.066, -0.096), resolution=(2560, 1440))
    ANTI_AIRCRAFT_ROCKET3 = Template(get_image_path("home/anti_aircraft_rocket/anti_aircraft_rocket3.png"), record_pos=(0.037, -0.131), resolution=(2560, 1440))
    ANTI_AIRCRAFT_ROCKET4 = Template(get_image_path("home/anti_aircraft_rocket/anti_aircraft_rocket4.png"), record_pos=(0.168, -0.025), resolution=(2560, 1440))
    ANTI_AIRCRAFT_ROCKET5 = Template(get_image_path("home/anti_aircraft_rocket/anti_aircraft_rocket5.png"), record_pos=(-0.037, 0.066), resolution=(2560, 1440))
    ANTI_AIRCRAFT_ROCKET6 = Template(get_image_path("home/anti_aircraft_rocket/anti_aircraft_rocket6.png"), record_pos=(0.125, -0.005), resolution=(2560, 1440))
    ANTI_AIRCRAFT_ROCKET7 = Template(get_image_path("home/anti_aircraft_rocket/anti_aircraft_rocket7.png"), record_pos=(-0.028, -0.071), resolution=(2560, 1440))

    # =========================
    # 夜世界（Builder Base）
    # =========================

    # --- 资源与入口（用于夜世界状态确认、资源识别、回主世界） ---
    NIGHT_GOLD = Template(get_image_path("night/resource/night_gold.png"), record_pos=(-0.082, 0.048), resolution=(2560, 1440))
    NIGHT_WATER = Template(get_image_path("night/resource/night_water.png"), record_pos=(-0.039, 0.002), resolution=(2560, 1440))
    EREMALD = Template(get_image_path("night/resource/eremald.png"), record_pos=(0.239, 0.033), resolution=(2560, 1440))
    BTN_COLLECT = Template(get_image_path("night/resource/btn_collect.png"), record_pos=(0.235, 0.192), resolution=(2560, 1440))

    # --- Other entrances（用于识别其他功能入口，辅助状态判断与导航） ---
    SHIP_BACK_HOME = Template(get_image_path("night/other_entrances/ship_back_home.png"), record_pos=(0.297, -0.125), resolution=(2560, 1440))
    
    # --- Train（用于识别兵种/法术训练入口） ---
    BTN_DELETE = Template(get_image_path("night/train/btn_delete.png"), record_pos=(0.332, 0.02), resolution=(2560, 1440))

    # --- 训练素材（用于识别夜世界兵种训练入口） ---
    MECHA_TRAIN = Template(get_image_path("night/army_train/mecha_train.png"), record_pos=(-0.358, 0.102), resolution=(2560, 1440))
    GIANT_TRAIN = Template(get_image_path("night/army_train/giant_train.png"), record_pos=(-0.201, 0.102), resolution=(2560, 1440))
    ARCHER_TRAIN = Template(get_image_path("night/army_train/archer_train.png"), record_pos=(-0.279, 0.173), resolution=(2560, 1440))
    WITCH_TRAIN = Template(get_image_path("night/army_train/witch_train.png"), record_pos=(-0.042, 0.184), resolution=(2560, 1440))

    # --- 部署素材（用于战斗中识别夜世界兵种可部署按钮） ---
    MECHA_DEPLOY = Template(get_image_path("night/army_deploy/mecha_deploy.png"), record_pos=(-0.4, 0.215), resolution=(2560, 1440))
    GIANT_DEPLOY = Template(get_image_path("night/army_deploy/giant_deploy.png"), record_pos=(-0.311, 0.208), resolution=(2560, 1440))
    ARCHER_DEPLOY = Template(get_image_path("night/army_deploy/archer_deploy.png"), record_pos=(-0.152, 0.214), resolution=(2560, 1440))
    WITCH_DEPLOY = Template(get_image_path("night/army_deploy/witch_deploy.png"), record_pos=(-0.231, 0.212), resolution=(2560, 1440))
    FIGHTER_JET_DEPLOY = Template(get_image_path("night/army_deploy/fighter_jet_deploy.png"), record_pos=(-0.4, 0.216), resolution=(2560, 1440))

    # --- 战斗状态与结算（用于识别战斗入口、投降/结束、领奖） ---
    NIGHT_FIGHT = Template(get_image_path("night/fight/night_fight.png"), record_pos=(-0.436, 0.213), resolution=(2560, 1440))
    NIGHT_FIGHT_WITH_STAR = Template(get_image_path("night/fight/night_fight_with_star.png"), record_pos=(-0.435, 0.229), resolution=(2560, 1440))
    BTN_SEARCH = Template(get_image_path("night/fight/btn_search.png"), record_pos=(0.241, 0.087), resolution=(2560, 1440))
    BTN_GIVE_UP = Template(get_image_path("night/fight/btn_give_up.png"), record_pos=(-0.429, 0.109), resolution=(2560, 1440))
    BTN_END = Template(get_image_path("night/fight/btn_end.png"), record_pos=(-0.43, 0.109), resolution=(2560, 1440))
    


