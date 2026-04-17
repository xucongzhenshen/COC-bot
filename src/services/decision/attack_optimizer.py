from src.cocbot.home import _pick_lightning_targets


class AttackOptimizer:
    def plan_lightning_targets(self, anti_aircraft_list, lightning_number, lightning_damage, deploy_point):
        return _pick_lightning_targets(
            anti_aircraft_list=anti_aircraft_list,
            lightning_number=lightning_number,
            lightning_damage=lightning_damage,
            deploy_point=deploy_point,
        )
