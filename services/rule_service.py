# -- coding: utf-8 --
import random
import time
from collections import deque

from .message_service import forward_result, text_entry
from .user_service import get_nickname
from .user_state_service import apply_random_ban, format_duration, get_ban_remaining


async def check_shared_ban(
    plugin,
    event,
    *,
    initiator_id: str,
    target_id: str,
    self_ban_message: str,
    target_ban_message: str,
):
    self_remain = get_ban_remaining(plugin, initiator_id)
    if self_remain > 0:
        return forward_result(
            event,
            [text_entry(self_ban_message.format(remain=format_duration(self_remain)))],
        )

    target_remain = get_ban_remaining(plugin, target_id)
    if target_remain > 0:
        target_name = await get_nickname(event, target_id)
        return forward_result(
            event,
            [text_entry(target_ban_message.format(target_name=target_name, remain=format_duration(target_remain)))],
        )

    return None


async def check_whitelist_and_self(
    plugin,
    event,
    *,
    action_name: str,
    protected_user_id: str,
    executor_id: str,
    target_user_id: str,
    allow_self: bool,
):
    if protected_user_id in plugin.white_list:
        nickname = await get_nickname(event, protected_user_id)
        return forward_result(event, [text_entry(f"{nickname} 的后门被后户之神霸占了，不能{action_name}（悲）")])

    if executor_id == target_user_id and not allow_self:
        return forward_result(event, [text_entry("兄啊金箔怎么还能捅到自己的啊（恼）")])

    return None


async def check_reject(plugin, event, *, action_display_name: str):
    if random.random() < float(getattr(plugin, "reject_prob", 0.1)):
        return forward_result(event, [text_entry(f"对方推开了你，拒绝和你{action_display_name}")])
    return None


def prepare_ccb_frequency_window(plugin, initiator_id: str):
    """
    只清理滑动窗口，不增加计数。
    用于 ccb 的前置阶段，避免“被拒绝也计数”。
    """
    now = time.time()
    times = plugin.action_times.setdefault(str(initiator_id), deque())
    while times and now - times[0] > plugin.window:
        times.popleft()
    return times


def mark_ccb_success_and_check_threshold(plugin, initiator_id: str):
    """
    仅在一次 ccb 成功后调用：
    - 追加本次成功记录
    - 若追加后刚好达到阈值，则进入禁闭
    返回 ban_seconds；若未触发则返回 None
    """
    now = time.time()
    times = plugin.action_times.setdefault(str(initiator_id), deque())
    while times and now - times[0] > plugin.window:
        times.popleft()

    times.append(now)

    if len(times) == plugin.threshold:
        ban_seconds = apply_random_ban(plugin, initiator_id)
        times.clear()
        return ban_seconds

    return None


async def check_ccb_blowup(plugin, event, user_id: str):
    if random.random() < plugin.yw_prob:
        ban_seconds = apply_random_ban(plugin, user_id)
        return forward_result(
            event,
            [text_entry(f"💥还没开始你就炸膛了！满身疮痍，再起不能（悲）\n本次养胃：{format_duration(ban_seconds)}")],
        )
    return None