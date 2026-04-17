import math


class AttackOptimizer:
    @staticmethod
    def _distance(p1, p2):
        return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

    def plan_lightning_targets(self, anti_aircraft_list, lightning_number, lightning_damage, deploy_point):
        candidates = []
        for idx, rocket in enumerate(anti_aircraft_list):
            needed = int(math.ceil(rocket["hitpoints"] / lightning_damage))
            dist = self._distance(rocket["position"], deploy_point)
            candidates.append(
                {
                    "idx": idx,
                    "level": rocket["level"],
                    "position": rocket["position"],
                    "dp_second": rocket["dp_second"],
                    "hitpoints": rocket["hitpoints"],
                    "strikes_needed": needed,
                    "distance": dist,
                }
            )

        killable_candidates = [item for item in candidates if item["strikes_needed"] <= lightning_number]
        best = [(0, 0.0, []) for _ in range(lightning_number + 1)]
        for candidate in killable_candidates:
            cost = candidate["strikes_needed"]
            value = candidate["dp_second"]
            dist = candidate["distance"]
            for cap in range(lightning_number, cost - 1, -1):
                prev_value, prev_dist, prev_pick = best[cap - cost]
                new_state = (prev_value + value, prev_dist + dist, prev_pick + [candidate])
                if new_state[0] > best[cap][0] or (new_state[0] == best[cap][0] and new_state[1] > best[cap][1]):
                    best[cap] = new_state

        best_state = max(best, key=lambda s: (s[0], s[1]))
        kill_plan = list(best_state[2])
        used_strikes = sum(item["strikes_needed"] for item in kill_plan)
        total_removed_dp_second = sum(item["dp_second"] for item in kill_plan)

        remaining_lightning = lightning_number - used_strikes
        picked_idx = {picked["idx"] for picked in kill_plan}
        remaining_targets = [item for item in candidates if item["idx"] not in picked_idx]
        remaining_targets.sort(key=lambda item: (item["dp_second"], item["distance"]), reverse=True)

        if remaining_lightning > 0 and remaining_targets:
            strike_state = {item["idx"]: 0 for item in remaining_targets}
            remaining_hp = {item["idx"]: item["hitpoints"] for item in remaining_targets}
            remaining_dp_map = {item["idx"]: item["dp_second"] for item in remaining_targets}
            filler_targets = list(remaining_targets)
            filler_plan = []

            while remaining_lightning > 0 and filler_targets:
                target = filler_targets[0]
                strike_state[target["idx"]] += 1
                remaining_lightning -= 1
                will_destroy = strike_state[target["idx"]] * lightning_damage >= remaining_hp[target["idx"]]
                filler_plan.append(
                    {
                        "idx": target["idx"],
                        "level": target["level"],
                        "position": target["position"],
                        "dp_second": target["dp_second"],
                        "hitpoints": target["hitpoints"],
                        "strikes_needed": 1,
                        "distance": target["distance"],
                        "mode": "kill" if will_destroy else "filler",
                    }
                )
                if will_destroy:
                    total_removed_dp_second += remaining_dp_map[target["idx"]]
                    filler_targets = [item for item in filler_targets if item["idx"] != target["idx"]]

            plan = [
                {
                    **item,
                    "mode": "kill",
                }
                for item in sorted(kill_plan, key=lambda x: x["distance"], reverse=True)
            ] + filler_plan
        else:
            plan = [
                {
                    **item,
                    "mode": "kill",
                }
                for item in sorted(kill_plan, key=lambda x: x["distance"], reverse=True)
            ]

        total_strikes_used = sum(item["strikes_needed"] for item in plan)
        remaining_dp_second = sum(item["dp_second"] for item in candidates) - total_removed_dp_second
        return {
            "plan": plan,
            "total_removed_dp_second": total_removed_dp_second,
            "remaining_dp_second": remaining_dp_second,
            "total_strikes_used": total_strikes_used,
        }
