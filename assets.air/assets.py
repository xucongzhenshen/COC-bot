from airtest.core.api import Template
import os

current_dir = os.path.dirname(os.path.abspath(__file__))

def get_image_path(image_name):
    """构建图片的绝对路径"""
    return os.path.join(current_dir, image_name)


# -*- encoding=utf8 -*-
class Assets:
# 主世界
    CLOSE_ACTIVITY = Template(get_image_path("close_activity.png"), record_pos=(0.317, -0.156), resolution=(2560, 1440))

    OIL = Template(get_image_path("oil.png"), record_pos=(-0.37, -0.085), resolution=(2560, 1440))

    WATER = Template(get_image_path("water.png"), record_pos=(0.22, -0.191), resolution=(2560, 1440))

    GOLD = Template(get_image_path("gold.png"), record_pos=(-0.267, -0.157), resolution=(2560, 1440))

    CLAN_WAR = Template(get_image_path("clan_war.png"), record_pos=(-0.461, 0.061), resolution=(2560, 1440))

    BEER = Template(get_image_path("beer.png"), record_pos=(-0.29, -0.049), resolution=(2560, 1440))

    SHIP_TO_NIGHT = Template(get_image_path("ship_to_night.png"), record_pos=(-0.221, 0.064), resolution=(2560, 1440))

    BTN_TRAIN = Template(get_image_path("btn_train.png"), record_pos=(-0.46, 0.126), resolution=(2560, 1440))

    FIGHT_HOME = Template(get_image_path("fight_home.png"), record_pos=(-0.435, 0.213), resolution=(2560, 1440))

    FIGHT_HOME_WITH_STAR = Template(get_image_path("fight_home_with_star.png"), record_pos=(-0.436, 0.212), resolution=(2560, 1440))
    
    FIGHT_HOME_WITH_3_STAR = Template(get_image_path("fight_home_with_3_star.png"), record_pos=(-0.436, 0.212), resolution=(2560, 1440))


# 夜世界
    NIGHT_GOLD = Template(get_image_path("night_gold.png"), record_pos=(-0.082, 0.048), resolution=(2560, 1440))

    NIGHT_WATER = Template(get_image_path("night_water.png"), record_pos=(-0.039, 0.002), resolution=(2560, 1440))

    EREMALD = Template(get_image_path("eremald.png"), record_pos=(0.239, 0.033), resolution=(2560, 1440))

    SHIP_BACK_HOME = Template(get_image_path("ship_back_home.png"), record_pos=(0.297, -0.125), resolution=(2560, 1440))


    NIGHT_FIGHT_WITH_STAR = Template(get_image_path("night_fight_with_star.png"), record_pos=(-0.435, 0.229), resolution=(2560, 1440))

    MECHA_TRAIN = Template(get_image_path("mecha_train.png"), record_pos=(-0.358, 0.102), resolution=(2560, 1440))

    BTN_DELETE = Template(get_image_path("btn_delete.png"), record_pos=(0.332, 0.02), resolution=(2560, 1440))

    GIANT_TRAIN = Template(get_image_path("giant_train.png"), record_pos=(-0.201, 0.102), resolution=(2560, 1440))

    WITCH_TRAIN = Template(get_image_path("witch_train.png"), record_pos=(-0.042, 0.184), resolution=(2560, 1440))
    
    ARCHER_TRAIN = Template(get_image_path("archer_train.png"), record_pos=(-0.279, 0.173), resolution=(2560, 1440))

    CLOSE = Template(get_image_path("close.png"), record_pos=(0.399, -0.202), resolution=(2560, 1440))

    BTN_SEARCH = Template(get_image_path("btn_search.png"), record_pos=(0.241, 0.087), resolution=(2560, 1440))

    GIANT_DEPLOY = Template(get_image_path("giant_deploy.png"), record_pos=(-0.311, 0.208), resolution=(2560, 1440))

    ARCHER_DEPLOY = Template(get_image_path("archer_deploy.png"), record_pos=(-0.152, 0.214), resolution=(2560, 1440))

    WITCH_DEPLOY = Template(get_image_path("witch_deploy.png"), record_pos=(-0.231, 0.212), resolution=(2560, 1440))

    MECHA_DEPLOY = Template(get_image_path("mecha_deploy.png"), record_pos=(-0.4, 0.215), resolution=(2560, 1440))
    
    FIGHTER_JET_DEPLOY = Template(get_image_path("fighter_jet_deploy.png"), record_pos=(-0.4, 0.216), resolution=(2560, 1440))

    BTN_BACK = Template(get_image_path("btn_back.png"), record_pos=(-0.0, 0.194), resolution=(2560, 1440))

    BTN_CONFIRM = Template(get_image_path("btn_confirm.png"), record_pos=(0.011, 0.188), resolution=(2560, 1440))
    
    NIGHT_FIGHT = Template(get_image_path("night_fight.png"), record_pos=(-0.436, 0.213), resolution=(2560, 1440))

    BTN_GIVE_UP = Template(get_image_path("btn_give_up.png"), record_pos=(-0.429, 0.109), resolution=(2560, 1440))
    
    BTN_END = Template(get_image_path("btn_end.png"), record_pos=(-0.43, 0.109), resolution=(2560, 1440))
    
    BTN_COLLECT = Template(get_image_path("btn_collect.png"), record_pos=(0.235, 0.192), resolution=(2560, 1440))



