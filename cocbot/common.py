# -*- encoding=utf8 -*-

import logging
import os
import random
import subprocess
import time
import ddddocr
import cv2
import numpy as np

from airtest.core.api import *

from ._assets import Assets

logging.getLogger("airtest").setLevel(logging.WARNING)

LOG_LEVEL = 0
RUNTIME_LOG_PATH = None

def set_log_level(level):
    global LOG_LEVEL
    LOG_LEVEL = level


def get_log_path(log_path=None):
    if log_path:
        return log_path
    if RUNTIME_LOG_PATH:
        return RUNTIME_LOG_PATH
    curr_path = os.path.dirname(__file__)
    return os.path.join(curr_path, "log")


def capture_debug_snapshot(problem_desc, log_path=None):
    active_log_path = get_log_path(log_path)
    os.makedirs(active_log_path, exist_ok=True)

    safe_desc = "".join(ch if ch.isalnum() else "_" for ch in str(problem_desc)).strip("_")
    if not safe_desc:
        safe_desc = "unknown_issue"
    safe_desc = safe_desc[:60]

    filename = f"debug_{safe_desc}_{int(time.time())}.png"
    filepath = os.path.join(active_log_path, filename)
    try:
        G.DEVICE.snapshot(filepath)
        return filepath
    except Exception:
        return None


def log_msg(message, level=1, log_path=None, log_file="cocbot.log"):
    """print日志消息，并写入日志文件，只有当日志等级满足条件时才输出"""
    if LOG_LEVEL >= level:
        print(message)
        log_path = get_log_path(log_path)
        if log_file:
            with open(os.path.join(log_path, log_file), "a") as f:
                f.write(f"[{level}] {message}\n")

_air_exists = exists
_air_touch = touch


def _describe_target(target):
    """生成可读目标描述，便于排查点击和识别行为。"""
    if isinstance(target, Template):
        return os.path.basename(getattr(target, "filename", str(target)))
    if isinstance(target, (list, tuple)) and len(target) >= 2:
        return f"({target[0]}, {target[1]})"
    if isinstance(target, dict) and "result" in target:
        pos = target.get("result")
        return f"dict-result={pos}"
    return str(target)


def exists(v, *args, **kwargs):
    """包装 exists：在日志等级1输出每次识别动作和结果。"""
    target_desc = _describe_target(v)
    log_msg(f"[exists] start -> {target_desc}", level=2, log_path=get_log_path())
    result = _air_exists(v, *args, **kwargs)
    log_msg(f"[exists] result -> {result}", level=2, log_path=get_log_path())
    return result


def touch(v, *args, **kwargs):
    """包装 touch：在日志等级1输出每次点击动作。"""
    target_desc = _describe_target(v)
    log_msg(f"[touch] exec -> {target_desc}", level=2, log_path=get_log_path())
    return _air_touch(v, *args, **kwargs)


def build_airtest_uri(device_name, cap_method, touch_method, ori_method):
    return (
        f"android://127.0.0.1:5037/{device_name}"
        f"?cap_method={cap_method}&touch_method={touch_method}&ori_method={ori_method}"
    )


def random_touch(pos, offset=5):
    """带随机偏移的点击"""
    if pos:
        x, y = pos
        target_x = x + random.randint(-offset, offset)
        target_y = y + random.randint(-offset, offset)
        touch([target_x, target_y])
        sleep(random.uniform(0.5, 1.0))
    else:
        active_log_path = get_log_path()
        log_msg("random_touch: 无效位置，无法点击", level=0, log_path=active_log_path)
        capture_debug_snapshot("random_touch_invalid_position", log_path=active_log_path)
        raise ValueError("random_touch: 无效位置，无法点击")


def close_popups():
    """处理各种弹窗和练兵完成提示"""
    while exists(Assets.CLOSE):
        random_touch(exists(Assets.CLOSE))
        sleep(1)
    while exists(Assets.CLOSE_ACTIVITY):
        random_touch(exists(Assets.CLOSE_ACTIVITY))
        sleep(1)
    while exists(Assets.BTN_CONFIRM):
        random_touch(exists(Assets.BTN_CONFIRM))
        sleep(1)


def ensure_screenshot_ready(max_retries=5):
    """确保截图功能正常"""
    for i in range(max_retries):
        try:
            img = snapshot()
            if img is not None:
                log_msg("截图功能正常", level=2, log_path=get_log_path())
                return True
            log_msg(f"截图返回None，尝试 {i + 1}/{max_retries}", level=1, log_path=get_log_path())
        except Exception as exc:
            log_msg(f"截图异常: {exc}，尝试 {i + 1}/{max_retries}", level=1, log_path=get_log_path())

        sleep(2)

    return False


def setup_runtime(script_file, uri, log_path, project_root):
    global RUNTIME_LOG_PATH
    RUNTIME_LOG_PATH = log_path
    connect_device(uri)
    auto_setup(
        script_file,
        logdir=log_path,
        devices=[uri],
        project_root=project_root,
    )
    snapshot()

ROI_LOADING = [1190, 1180, 1240, 1380]
def start_clash_of_clans(device_serial='emulator-5554', version='tencent', adb_path='adb'):
    """
    启动《部落冲突》，兼容国际服和腾讯版。
    """
    # 1. 确定启动路径 (基于你获取到的真实路径)
    if version == 'global':
        package_name = "com.supercell.clashofclans"
        component = f"{package_name}/com.supercell.titan.GameApp"
    else:
        package_name = "com.tencent.tmgp.supercell.clashofclans"
        component = f"{package_name}/com.supercell.titan.tencent.GameAppTencent"
    
    # 2. 启动前先强制关闭，确保从零开始加载
    log_msg(f"正在准备启动 {version} 版...", level=1, log_path=get_log_path())
    subprocess.run([adb_path, "-s", device_serial, "shell", "am", "force-stop", package_name], capture_output=True)
    sleep(1)

    # 3. 构建启动命令 (建议使用传入的 adb_path 避免版本冲突)
    cmd = [adb_path, "-s", device_serial, "shell", "am", "start", "-n", component]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if "Error" in result.stdout or "error" in result.stderr:
            log_msg(f"启动命令执行失败: {result.stderr or result.stdout}", level=0, log_path=get_log_path())
            return False

        # 4. 统一的加载监控逻辑
        log_msg("游戏已指令启动，开始监控加载状态...", level=1, log_path=get_log_path())
        start_time = time.time()
        timeout = 90  # 游戏启动可能较慢，给足 90 秒
        
        while time.time() - start_time < timeout:
            # 识别加载文字
            loading_text = get_text_from_roi(ROI_LOADING)
            
            # 如果识别到了“加载”相关字样，说明正在加载中
            if any(word in loading_text for word in ["加载", "Loading", "正在"]):
                log_msg(f"检测到加载进度: {loading_text}", level=1, log_path=get_log_path())
                sleep(3)
                continue
            
            # 如果加载文字消失了，检查是否进入了游戏世界（主世界或夜世界）
            if exists(Assets.BTN_TRAIN):
                log_msg(f"《部落冲突》{version}版 启动成功", level=0, log_path=get_log_path())
                # 刚进游戏通常有弹窗，顺手清一下
                close_popups()
                return True
            
            # 还没检测到加载文字也没进游戏，可能是刚点开黑屏，继续等
            sleep(2)
            
        log_msg("启动超时，未能进入游戏界面", level=0, log_path=get_log_path())
        return False

    except Exception as e:
        log_msg(f"启动过程发生异常: {e}", level=0, log_path=get_log_path())
        return False


def stop_clash_of_clans(device_serial='emulator-5554', version='tencent', adb_path='adb'):
    """
    使用 ADB 强制关闭《部落冲突》。
    
    Args:
        device_serial (str): 设备序列号。
        version (str): 'tencent' 或 'global'。
        adb_path (str): 外部指定的 ADB 可执行文件路径。
    """
    # 1. 根据版本选择包名 (与启动函数保持一致)
    if version == 'global':
        package_name = "com.supercell.clashofclans"
    else:
        package_name = "com.tencent.tmgp.supercell.clashofclans"
    
    # 2. 构建命令 (显式指定 adb 路径和设备号)
    # am force-stop 是最彻底的关闭方式，不会有任何残留
    cmd = [adb_path, "-s", device_serial, "shell", "am", "force-stop", package_name]
    
    try:
        # 执行关闭指令
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        
        if result.returncode == 0:
            log_msg(f"《部落冲突》{version}版 已执行关闭指令 ({package_name})", level=0, log_path=get_log_path())
            return True
        else:
            log_msg(f"关闭失败 (ADB 返回码 {result.returncode}): {result.stderr}", level=0, log_path=get_log_path())
            return False
            
    except FileNotFoundError:
        log_msg(f"错误: 未找到指定的 ADB 路径 -> {adb_path}", level=0, log_path=get_log_path())
        return False
    except Exception as e:
        log_msg(f"关闭应用时发生异常: {e}", level=0, log_path=get_log_path())
        return False



# 全局初始化一次，避免重复加载模型消耗性能
# beta=True 开启 OCR 模式（适合识别中文和复杂场景）
_OCR_INSTANCE = ddddocr.DdddOcr(show_ad=False, beta=True)

# 你调试出的最佳 ROI [y_min, x_min, y_max, x_max]
ROI_COUNTDOWN = [10, 1080, 60, 1450] 
def get_text_from_roi(roi=ROI_COUNTDOWN):
    """
    自动截图并提取指定区域的文字内容。
    :param roi: 识别区域 [y_min, x_min, y_max, x_max]
    :return: 识别出的字符串（去除空格和换行）
    """
    try:
        # 1. 获取当前屏幕截图
        screen = G.DEVICE.snapshot()
        if screen is None:
            return ""

        # 2. 图像裁剪逻辑
        h, w = screen.shape[:2]
        y_min, x_min, y_max, x_max = [int(v) for v in roi]
        
        # 防止 ROI 越界导致 OpenCV 报错
        y_min, y_max = max(0, y_min), min(h, y_max)
        x_min, x_max = max(0, x_min), min(w, x_max)
        
        cropped = screen[y_min:y_max, x_min:x_max]
        if cropped.size == 0:
            return ""

        # 3. 格式转换（OpenCV 数组 -> PNG 字节流）
        success, encoded_image = cv2.imencode('.png', cropped)
        if not success:
            return ""
        
        # 4. 执行 OCR 识别
        text = _OCR_INSTANCE.classification(encoded_image.tobytes())
        
        # 清洗结果：去掉常见的识别噪音（空格、回车等）
        clean_text = text.strip() if text else ""
        return clean_text

    except Exception as e:
        # 如果报错，返回空字符串，不中断主程序
        log_msg(f"[OCR Error] {e}", level=0, log_path=get_log_path())
        return ""

def delete_img_in_log(log_dir=None):
    """
    删除指定log目录下的所有图片文件
    
    Args:
        log_dir: log目录路径，如果为None则尝试获取当前log目录
    """
    if log_dir is None:
        # 尝试获取Airtest的当前log目录
        from airtest.core.settings import Settings as ST
        log_dir = ST.LOG_DIR if hasattr(ST, 'LOG_DIR') else 'log'
    
    # 确保log_dir是字符串
    if not log_dir or not isinstance(log_dir, str):
        log_dir = 'log'
    
    # 构建log目录的绝对路径
    if not os.path.isabs(log_dir):
        log_dir = os.path.join(os.getcwd(), log_dir)
    
    if not os.path.exists(log_dir):
        print(f"Log目录不存在: {log_dir}")
        return 0
    
    # 查找所有.png, .jpg, .jpeg文件
    png_files = []
    for root, dirs, files in os.walk(log_dir):
        for file in files:
            if "debug" in file.lower():
                continue  # 跳过包含 "debug" 的文件
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                png_files.append(os.path.join(root, file))
    
    # 删除文件
    deleted_count = 0
    for png_file in png_files:
        try:
            os.remove(png_file)
            deleted_count += 1
            log_msg(f"已删除: {png_file}", level=2, log_path=get_log_path(log_dir), log_file="")  # 只在控制台输出删除日志
        except Exception as e:
            log_msg(f"删除文件失败 {png_file}: {e}", level=0, log_path=get_log_path(log_dir))
    
    log_msg(f"已删除 {deleted_count} 个图片文件", level=2, log_path=get_log_path(log_dir))
    return deleted_count