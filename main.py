# -- coding: utf-8 --
import importlib

from astrbot.api.event import AstrMessageEvent, MessageEventResult, filter
from astrbot.api.star import Context, Star, register
from astrbot.api import AstrBotConfig

from .services.ccb_service import run_ccb
from .services.zha_service import run_zha
from .services.jbcs_service import run_jbcs
from .services.stats_service import (
    build_ccbinfo,
    build_ccbmax,
    build_ccbtop,
    build_ccbvol,
    build_xnn,
)
from .services.user_service import parse_at_target

# 文件名保留为 69_service.py，但普通 import 语法无法直接导入数字开头模块
run_69 = importlib.import_module('.services.69_service', package=__package__).run_69


@register("ccb_pplus", "Jerry0912", "基于 ccb_plus 扩展的插件", "0.5.0")
class CcbPplus(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config

        # ccb 专用：次数限制窗口
        self.window = int(config.get("yw_window", 60))
        self.threshold = int(config.get("yw_threshold", 5))

        # 全玩法共享：养胃时长（配置页填分钟，这里转成秒）
        self.ban_duration_min = int(config.get("yw_ban_duration_min_minutes", 1)) * 60
        self.ban_duration_max = int(config.get("yw_ban_duration_max_minutes", 15)) * 60
        if self.ban_duration_min > self.ban_duration_max:
            self.ban_duration_min, self.ban_duration_max = self.ban_duration_max, self.ban_duration_min
        self.ban_duration = 60  # 回退值

        self.action_times = {}  # 仅 ccb 使用的次数限制窗口
        self.ban_list = {}      # 全玩法共享的养胃状态

        # 概率配置
        self.yw_prob = float(config.get("yw_probability", 0.1))
        self.reject_prob = float(config.get("reject_probability", 0.1))
        self.crit_prob = float(config.get("crit_prob", 0.2))
        self.sixty_nine_blowup_prob = float(config.get("sixty_nine_blowup_probability", 0.1))

        self.white_list = config.get("white_list", [])
        self.selfdo = bool(config.get("self_ccb", False))

        raw_log = config.get("enable_log", config.get("is_log", False))
        if isinstance(raw_log, str):
            self.is_log = raw_log.strip().lower() == "true"
        else:
            self.is_log = bool(raw_log)

    async def _yield_results(self, results):
        if isinstance(results, MessageEventResult):
            yield results
            return
        if isinstance(results, list):
            for result in results:
                yield result
            return
        if results is not None:
            yield results

    @filter.command("ccb")
    async def ccb(self, event: AstrMessageEvent):
        results = await run_ccb(self, event)
        async for result in self._yield_results(results):
            yield result

    @filter.command("榨")
    async def zha(self, event: AstrMessageEvent):
        results = await run_zha(self, event)
        async for result in self._yield_results(results):
            yield result

    @filter.command("zha")
    async def zha_en(self, event: AstrMessageEvent):
        async for result in self.zha(event):
            yield result

    @filter.command("69")
    async def sixty_nine(self, event: AstrMessageEvent):
        results = await run_69(self, event)
        async for result in self._yield_results(results):
            yield result

    @filter.command("1jbcs")
    async def one_jbcs(self, event: AstrMessageEvent):
        results = await run_jbcs(self, event)
        async for result in self._yield_results(results):
            yield result

    @filter.command("ccbtop")
    async def ccbtop(self, event: AstrMessageEvent):
        yield await build_ccbtop(event)

    @filter.command("ccbvol")
    async def ccbvol(self, event: AstrMessageEvent):
        yield await build_ccbvol(event)

    @filter.command("ccbinfo")
    async def ccbinfo(self, event: AstrMessageEvent):
        target_user_id = parse_at_target(event, default_sender=True)
        yield await build_ccbinfo(event, target_user_id)

    @filter.command("ccbmax")
    async def ccbmax(self, event: AstrMessageEvent):
        yield await build_ccbmax(event)

    @filter.command("xnn")
    async def xnn(self, event: AstrMessageEvent):
        yield await build_xnn(event)
