# -- coding: utf-8 --
import astrbot.api.message_components as Comp

from .message_service import entry, forward_result
from .rule_service import (
    check_ccb_blowup,
    check_reject,
    check_shared_ban,
    check_whitelist_and_self,
    mark_ccb_success_and_check_threshold,
    prepare_ccb_frequency_window,
)
from .user_service import get_avatar, get_nickname, parse_at_target
from .user_state_service import commit_single_action, roll_action_values, format_action_duration

from .message_service import entry, forward_result
from .rule_service import (
    check_ccb_blowup,
    check_reject,
    check_shared_ban,
    check_whitelist_and_self,
    mark_ccb_success_and_check_threshold,
    prepare_ccb_frequency_window,
)
from .user_service import get_avatar, get_nickname, parse_at_target
from .user_state_service import commit_single_action, format_duration, roll_action_values


async def run_ccb(plugin, event):
    send_id = str(event.get_sender_id())
    target_user_id = parse_at_target(event, default_sender=True)

    blocked = await check_shared_ban(
        plugin,
        event,
        initiator_id=send_id,
        target_id=target_user_id,
        self_ban_message="你已经进入养胃状态了，不能再ccb，养胃剩余时间{remain}",
        target_ban_message="{target_name}已经进入养胃状态了，无法被ccb，养胃剩余时间{remain}",
    )
    if blocked:
        return blocked

    blocked = await check_whitelist_and_self(
        plugin,
        event,
        action_name="ccb",
        protected_user_id=target_user_id,
        executor_id=send_id,
        target_user_id=target_user_id,
        allow_self=plugin.selfdo,
    )
    if blocked:
        return blocked

    # 只清理窗口，不计数
    prepare_ccb_frequency_window(plugin, send_id)

    blocked = await check_reject(plugin, event, action_display_name="ccb")
    if blocked:
        return blocked

    blocked = await check_ccb_blowup(plugin, event, user_id=send_id)
    if blocked:
        return blocked

    result = roll_action_values(plugin)
    state = commit_single_action(
        plugin,
        event,
        executor_id=send_id,
        target_user_id=target_user_id,
        duration=result["duration"],
        vol=result["vol"],
    )
    if not state.get("ok"):
        return forward_result(event, [entry(Comp.Plain("这次操作出了点问题，请稍后再试"))])

    # 成功之后才 +1，并判断是否刚好到阈值
    reached_limit_ban_seconds = mark_ccb_success_and_check_threshold(plugin, send_id)

    target_nick = await get_nickname(event, target_user_id)
    avatar = get_avatar(target_user_id)
    record = state["record"]

    text = (
        f"你和{target_nick}发生了{format_action_duration(result['duration'])}长的ccb行为，"
        f"向ta注入了{'💥暴击！' if result['crit'] else ''}{result['vol']:.2f}ml的生命因子"
    )
    tail = "这是ta的初体验。" if state["is_first"] else f"这是ta的第{record['num']}次。"

    components = [
        Comp.Plain(text),
        Comp.Image.fromURL(avatar),
        Comp.Plain(tail),
    ]

    if reached_limit_ban_seconds is not None:
        components.append(
            Comp.Plain(
                f"\n你ccb了太多次，疲软不堪，进入了{format_duration(reached_limit_ban_seconds)}的贤者模式"
            )
        )

    return [
        forward_result(
            event,
            [
                entry(
                    *components,
                    name="ccb记录",
                )
            ],
            default_name="ccb记录",
        )
    ]