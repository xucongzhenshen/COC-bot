import os
import glob
import math

import cv2
import numpy as np

from airtest.core.api import G


class MeadowDetector:
    """基于几何边界搜索的草地平行四边形中心识别器。"""

    def __init__(self, config=None):
        if config is None:
            config = {}
        sample_path = config.get("sample_path")
        if sample_path is None:
            sample_path = os.path.join("cocbot", "sample_imgs", "night")
        self.sample_path = sample_path
        self.hsv_lower = np.array([45, 45, 35], dtype=np.uint8)
        self.hsv_upper = np.array([95, 255, 255], dtype=np.uint8)

        self.angles = [math.radians(36.0), math.radians(143.0)]
        self.search_step = 15
        self.min_line_len = 200
        self._learned = False

    def learn_hsv_range(self, sample_path=None):
        path = sample_path or self.sample_path
        if not path:
            return False

        sample_files = glob.glob(os.path.join(path, "*.png"))
        if not sample_files:
            return False

        h_list, s_list, v_list = [], [], []
        for file_path in sample_files:
            img = cv2.imread(file_path)
            if img is None:
                continue
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            h, s, v = cv2.split(hsv)
            h_list.extend(h.flatten())
            s_list.extend(s.flatten())
            v_list.extend(v.flatten())

        if not h_list:
            return False

        self.hsv_lower = np.array(
            [np.percentile(h_list, 3), np.percentile(s_list, 15), np.percentile(v_list, 15)],
            dtype=np.uint8,
        )
        self.hsv_upper = np.array([np.percentile(h_list, 97), 255, 255], dtype=np.uint8)
        self._learned = True
        return True

    def build_mask(self, screen_bgr):
        hsv = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.hsv_lower, self.hsv_upper)
        mask = cv2.medianBlur(mask, 7)
        mask = cv2.dilate(mask, np.ones((15, 15), np.uint8), iterations=1)
        return mask

    def get_line_points(self, theta, rho, w, h):
        a, b = math.sin(theta), -math.cos(theta)
        points = []

        if abs(b) > 1e-6:
            y = -rho / b
            if 0 <= y <= h:
                points.append((0, y))
            y = (-rho - a * w) / b
            if 0 <= y <= h:
                points.append((w, y))

        if abs(a) > 1e-6:
            x = -rho / a
            if 0 <= x <= w:
                points.append((x, 0))
            x = (-rho - b * h) / a
            if 0 <= x <= w:
                points.append((x, h))

        if len(points) < 2:
            return None

        points = sorted(list(set([(round(p[0]), round(p[1])) for p in points])))
        return points[0], points[-1]

    def score_line(self, mask, p1, p2):
        length = int(math.hypot(p2[0] - p1[0], p2[1] - p1[1]))
        if length < self.min_line_len:
            return 0, length

        x = np.linspace(p1[0], p2[0], length).astype(int)
        y = np.linspace(p1[1], p2[1], length).astype(int)

        h, w = mask.shape
        valid = (x >= 0) & (x < w) & (y >= 0) & (y < h)
        x, y = x[valid], y[valid]
        if len(x) == 0:
            return 0, length

        line_values = mask[y, x]
        white_count = np.sum(line_values > 0)

        if white_count == 0:
            return 0, length

        binary_line = (line_values > 0).astype(np.int8)
        diff = np.diff(np.concatenate(([0], binary_line, [0])))
        starts = np.where(diff == 1)[0]
        ends = np.where(diff == -1)[0]
        if len(starts) <= 1:
            max_gap = 0
        else:
            gaps = starts[1:] - ends[:-1]
            max_gap = np.max(gaps) if len(gaps) > 0 else 0

        return white_count, max_gap

    def find_boundary(self, mask, theta, start_rho):
        h, w = mask.shape
        best_rhos = []

        for direction in (-1, 1):
            current_rho = start_rho
            found_rho = None
            for _ in range(0, 1500, self.search_step):
                current_rho += direction * self.search_step
                pts = self.get_line_points(theta, current_rho, w, h)
                if not pts:
                    continue

                p1, p2 = pts
                line_len = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
                white_count, max_gap = self.score_line(mask, p1, p2)

                if white_count > 0.5 * line_len and max_gap < 0.2 * line_len:
                    found_rho = current_rho
                    break

            if found_rho is not None:
                best_rhos.append(found_rho)

        return best_rhos

    def intersect(self, theta1, rho1, theta2, rho2):
        a1, b1, c1 = math.sin(theta1), -math.cos(theta1), rho1
        a2, b2, c2 = math.sin(theta2), -math.cos(theta2), rho2
        det = a1 * b2 - a2 * b1
        if abs(det) < 1e-6:
            return None

        x = (b1 * c2 - b2 * c1) / det
        y = (a2 * c1 - a1 * c2) / det
        return int(x), int(y)

    def detect_with_debug(self, screen_bgr, min_area_ratio=0.07, debug_output=False, debug_dir=None, debug_prefix="meadow_detect"):
        if screen_bgr is None:
            return None, None, None

        if not self._learned and self.sample_path:
            self.learn_hsv_range(self.sample_path)

        h, w = screen_bgr.shape[:2]
        mask = self.build_mask(screen_bgr)

        moments = cv2.moments(mask)
        if moments["m00"] == 0:
            return None, None, mask

        cx_pre = int(moments["m10"] / moments["m00"])
        cy_pre = int(moments["m01"] / moments["m00"])

        all_rhos = []
        for theta in self.angles:
            start_rho = cy_pre * math.cos(theta) - cx_pre * math.sin(theta)
            rhos = self.find_boundary(mask, theta, start_rho)
            all_rhos.append(rhos)

        vertices = []
        if len(all_rhos) >= 2 and len(all_rhos[0]) >= 2 and len(all_rhos[1]) >= 2:
            for r1 in all_rhos[0]:
                for r2 in all_rhos[1]:
                    v = self.intersect(self.angles[0], r1, self.angles[1], r2)
                    if v is not None:
                        vertices.append(v)

        if len(vertices) >= 4:
            unique_vertices = []
            seen = set()
            for p in vertices:
                key = (int(p[0]), int(p[1]))
                if key in seen:
                    continue
                seen.add(key)
                unique_vertices.append(key)

            pts = np.array(unique_vertices, dtype=np.int32)
            if len(pts) >= 4:
                hull = cv2.convexHull(pts)
                if len(hull) >= 4:
                    box = hull.reshape(-1, 2).astype(int)
                    center = (int(np.mean(box[:, 0])), int(np.mean(box[:, 1])))
                    return center, box, mask

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return (cx_pre, cy_pre), None, mask

        min_area = h * w * float(min_area_ratio)
        best = None
        best_area = 0.0
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > min_area and area > best_area:
                best = cnt
                best_area = area

        if best is not None:
            rect = cv2.minAreaRect(best)
            center = (int(rect[0][0]), int(rect[0][1]))
            box = cv2.boxPoints(rect).astype(int)
            return center, box, mask

        return (cx_pre, cy_pre), None, mask

    def detect_center(self, screen_bgr=None, debug_output=False, debug_dir=None, debug_prefix="meadow_detect"):
        """识别夜世界草地中心，返回 (center, box_points, mask)。"""
        if screen_bgr is None:
            screen_bgr = G.DEVICE.snapshot()
        if screen_bgr is None:
            return None, None, None

        return self.detect_with_debug(
            screen_bgr,
            min_area_ratio=0.07,
            debug_output=debug_output,
            debug_dir=debug_dir,
            debug_prefix=debug_prefix,
        )
