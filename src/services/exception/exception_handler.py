from src.utils import Assets
ROI_EXCEPTION = [720-55, 1280-540, 715, 1280+540]  # 以屏幕中心为基准的较大 ROI
ROI_RETRY = [720+80, 1280-500, 720+130, 1280-420]
ROI_RELOAD = [720+80, 1280-510, 720+130, 1280-370]
ROI_RELOAD_GAME = [720+80, 1280-510, 720+130, 1280-320]
ROI_NOMORE_REMIND = [720+80, 1280+250, 720+130, 1280+380]

class ExceptionHandler:
    """异常处理器，负责处理游戏运行中的各种异常弹窗"""
    
    # 异常类型映射
    EXCEPTION_TYPES = {
        "nomore_remind": {
            "keywords": ["GooglePay", "评分"],
            "roi": ROI_NOMORE_REMIND,
            "target_text": "不再提醒",
            "action": "点击了不再提醒"
        },
        "reload": {
            "keywords": ["另一个设备", "正在连接这个村庄"],
            "roi": ROI_RELOAD,
            "target_text": "重新加载",
            "action": "点击了重新加载"
        },
        "retry": {
            "keywords": ["与服务器失去连接", "检查您的网络连接"],
            "roi": ROI_RETRY,
            "target_text": "重试",
            "action": "点击了重试"
        },
        "reload_game": {
            "keywords": ["客户端和服务器不同步", "下载最新版本", "太久没有进行操作", "已断开连接"],
            "roi": ROI_RELOAD_GAME,
            "target_text": "重新加载游戏",
            "action": "点击了重新加载游戏"
        }
    }
    
    # 弹窗按钮映射
    POPUP_BUTTONS = {
        "back": Assets.BTN_BACK,
        "confirm": Assets.BTN_CONFIRM,
        "close": Assets.CLOSE,
        "close_activity": Assets.CLOSE_ACTIVITY,
    }

    def __init__(self, config, op, logger, game_initializer):
        self.config = config
        self.op = op
        self.logger = logger
        self.game_initializer = game_initializer

    def run_exception_handler(self, e: Exception, retry_times=None):
        """
        执行异常处理主流程
        
        Args:
            e: 异常对象
            retry_times: 重试次数，默认为配置值
        
        Returns:
            bool: 是否成功处理异常
        """
        max_retries = int(retry_times if retry_times is not None 
                         else self.config.exception_retry_times)
        recovery_wait_seconds = int(self.config.exception_recovery_wait_seconds)
        wait_for_start_timeout = int(self.config.exception_wait_for_start_timeout)

        self.logger.error(f"执行过程中发生异常: {e}")
        
        for attempt in range(max_retries):
            self.logger.info(f"异常恢复尝试 {attempt + 1}/{max_retries}")
            
            # 处理弹窗
            popup_handled = self._handle_popup_buttons()
            
            # 识别并处理特定异常
            exception_handled = self._identify_and_handle_exception()
            
            # 检查处理结果
            if self._check_handling_result(popup_handled, exception_handled, attempt, max_retries):
                return True
            
            # 清理资源并等待恢复
            if not self._wait_for_recovery(recovery_wait_seconds, wait_for_start_timeout):
                self.logger.warning("异常仍然存在，继续等待...")
        
        return False

    def _handle_popup_buttons(self, max_attempts=5):
        """
        处理常见的弹窗按钮
        
        Args:
            max_attempts: 每个按钮的最大尝试点击次数
            
        Returns:
            bool: 是否成功处理了弹窗
        """
        for btn_name, asset in self.POPUP_BUTTONS.items():
            if not self._click_button_until_disappear(btn_name, asset, max_attempts):
                return False
        return True

    def _click_button_until_disappear(self, btn_name, asset, max_attempts):
        """
        持续点击按钮直到消失
        
        Args:
            btn_name: 按钮名称
            asset: 按钮资源
            max_attempts: 最大尝试次数
            
        Returns:
            bool: 按钮是否被成功点击并消失
        """
        btn = self.op.exists(asset)
        attempts = 0
        
        while btn and attempts < max_attempts:
            self.logger.info(f"检测到 {btn_name} 按钮，尝试点击 (尝试 {attempts + 1}/{max_attempts})")
            self.op.random_touch(btn)
            self.op.sleep(1)
            btn = self.op.exists(asset)
            attempts += 1
            
        if btn:
            self.logger.warning(f"{btn_name} 按钮点击 {max_attempts} 次后仍然存在")
            return False
            
        return True

    def _identify_and_handle_exception(self):
        """
        识别并处理特定异常
        
        Returns:
            bool: 是否成功处理了异常
        """
        exception_text = self.op.get_text(ROI_EXCEPTION)
        self.logger.debug(f"识别到的异常文本: {exception_text}")
        
        exception_type = self._detect_exception_type(exception_text)
        if not exception_type:
            self.logger.debug("未识别到可处理的异常类型")
            return False
        
        return self._handle_detected_exception(exception_type)

    def _detect_exception_type(self, exception_text):
        """
        根据文本检测异常类型
        
        Args:
            exception_text: 异常文本
            
        Returns:
            str: 异常类型，未检测到时返回None
        """
        for exception_type, config in self.EXCEPTION_TYPES.items():
            for keyword in config["keywords"]:
                if keyword in exception_text:
                    self.logger.info(f"检测到 {exception_type} 异常")
                    return exception_type
        return None

    def _handle_detected_exception(self, exception_type):
        """
        处理检测到的异常
        
        Args:
            exception_type: 异常类型
            
        Returns:
            bool: 是否成功处理异常
        """
        config = self.EXCEPTION_TYPES[exception_type]
        roi_text = self.op.get_text(config["roi"])
        
        if config["target_text"] in roi_text:
            self._click_roi_center(config["roi"])
            self.logger.info(config["action"])
            return True
            
        self.logger.warning(f"识别到 {exception_type} 异常，但未找到对应的可点击按钮")
        return False

    def _check_handling_result(self, popup_handled, exception_handled, attempt, max_attempts):
        """
        检查异常处理结果
        
        Returns:
            bool: 是否应该继续执行
        """
        if popup_handled or exception_handled:
            self.logger.info("异常已处理，继续执行")
            return True
            
        if attempt == max_attempts - 1:
            self.logger.error("已达到最大异常恢复尝试次数，直接重启游戏")
            self.game_initializer.restart_game()
            return True
            
        return False

    def _wait_for_recovery(self, wait_seconds, timeout):
        """
        等待游戏恢复
        
        Args:
            wait_seconds: 等待秒数
            timeout: 超时时间
            
        Returns:
            bool: 游戏是否恢复
        """
        self.game_initializer.cleanup_cycle_images()
        self.logger.info("等待游戏恢复...")
        self.op.sleep(wait_seconds)
        
        if self.game_initializer.wait_for_game_start(timeout=timeout):
            self.logger.info("游戏已恢复，检查异常是否仍然存在...")
            exception_text = self.op.get_text(ROI_EXCEPTION)
            return not any(
                keyword in exception_text 
                for config in self.EXCEPTION_TYPES.values() 
                for keyword in config["keywords"]
            )
            
        return False

    def _click_roi_center(self, roi_pos):
        """
        点击 ROI 区域中心
        
        Args:
            roi_pos: ROI 坐标 [x_min, y_min, x_max, y_max]
        """
        x_min, y_min, x_max, y_max = roi_pos
        center_x = (x_min + x_max) // 2
        center_y = (y_min + y_max) // 2
        self.op.touch((center_x, center_y))