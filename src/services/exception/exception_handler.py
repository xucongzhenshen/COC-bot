
ROI_EXCEPTION = [720-55, 1280-540, 715, 1280+540]  # 以屏幕中心为基准的较大 ROI
ROI_RETRY = [720+80, 1280-500, 720+130, 1280-420]
ROI_RELOAD = [720+80, 1280-510, 720+130, 1280-370]
ROI_RELOAD_GAME = [720+80, 1280-510, 720+130, 1280-320]
ROI_NOMORE_REMIND = [720+80, 1280+250, 720+130, 1280+380]

class ExceptionHandler:
    def __init__(self, config, op, logger, game_initializer):
        self.config = config
        self.op = op
        self.logger = logger
        self.game_initializer = game_initializer

    def run_exception_handler(self, e: Exception, retry_times=None):
        max_retries = int(retry_times if retry_times is not None else self.config.exception_retry_times)
        recovery_wait_seconds = int(self.config.exception_recovery_wait_seconds)
        wait_for_start_timeout = int(self.config.exception_wait_for_start_timeout)

        self.logger.error(f"执行过程中发生异常: {e}")
        for attempt in range(max_retries):
            self.logger.info(f"异常恢复尝试 {attempt + 1}/{max_retries}")
            exception_type = self.reco_exception()
            if exception_type:
                handled = self.handle_specific_exception(exception_type)
                if handled:
                    self.logger.info("成功处理了异常，继续执行")
                else:
                    self.logger.warning("识别到异常类型，但未命中可点击按钮")
            else:
                self.logger.debug("未识别到可处理的异常类型")

            self.game_initializer.cleanup_cycle_images()
            self.logger.info("等待游戏恢复...")
            self.op.sleep(recovery_wait_seconds)
            if self.game_initializer.wait_for_game_start(timeout=wait_for_start_timeout):
                self.logger.info("游戏已恢复，检查异常是否仍然存在...")
                if not self.reco_exception():
                    self.logger.info("异常已消失，继续执行")
                    return True
                else:
                    self.logger.warning("异常仍然存在，继续等待...")
        return False



    def reco_exception(self):
        '''
        异常文本示例：
        [1] debug_battle_search_button_not_found_1775222955.png -> 请在GooglePay给部落冲突（clashofClans评分并反馈意见l
        [2] Screenshot_20260404-140312.png -> 另一个设备正在连接这个村庄o
        [3] Screenshot_20260420-103118.png -> 与服务器失去连接，请检查您的网络连接后再次尝试
        [4] Screenshot_20260420-104327.png -> 客户端和服务器不同步请前往您的应用商店查看并下载最新版本以
        [5] Screenshot_20260420-111750.png -> 因为太久没有进行操作您已断开连接
        '''
        exception_text = self.op.get_text(ROI_EXCEPTION)
        self.logger.debug(f"识别到的异常文本: {exception_text}")
        if "GooglePay" in exception_text or "评分" in exception_text:
            self.logger.info("检测到评分提示，尝试点击确认")
            return "nomore_remind"
        
        if "另一个设备" in exception_text or "正在连接这个村庄" in exception_text:
            self.logger.info("检测到设备连接异常，尝试重新连接")
            return "reload"
        
        if "与服务器失去连接" in exception_text or "检查您的网络连接" in exception_text:
            self.logger.info("检测到网络异常，尝试重新连接")
            return "retry"
        
        if "客户端和服务器不同步" in exception_text or "下载最新版本" in exception_text:
            self.logger.info("检测到版本异常，尝试重新连接")
            return "reload_game"
        if "太久没有进行操作" in exception_text or "已断开连接" in exception_text:
            self.logger.info("检测到操作超时异常，尝试重新连接")
            return "reload_game"
        
        return None
    
    def handle_specific_exception(self, message):
        if message == "nomore_remind" and "不再提醒" in self.op.get_text(ROI_NOMORE_REMIND):
            self._click_center(ROI_NOMORE_REMIND)
            self.logger.info("点击了不再提醒")
            return True
        elif message == "retry" and "重试" in self.op.get_text(ROI_RETRY):
            self._click_center(ROI_RETRY)
            self.logger.info("点击了重试")
            return True
        elif message == "reload" and "重新加载" in self.op.get_text(ROI_RELOAD):
            self._click_center(ROI_RELOAD)
            self.logger.info("点击了重新加载")
            return True
        elif message == "reload_game" and "重新加载游戏" in self.op.get_text(ROI_RELOAD_GAME):
            self._click_center(ROI_RELOAD_GAME)
            self.logger.info("点击了重新加载游戏")
            return True
        return False

    def _click_center(self, roi_pos):
        x_min, y_min, x_max, y_max = roi_pos
        center_x = (x_min + x_max) // 2
        center_y = (y_min + y_max) // 2
        self.op.touch((center_x, center_y))
