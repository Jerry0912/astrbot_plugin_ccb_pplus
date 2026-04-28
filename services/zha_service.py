# -- coding: utf-8 --
import random
import astrbot.api.message_components as Comp

from .message_service import entry, forward_result
from .rule_service import check_reject, check_shared_ban, check_whitelist_and_self
from .user_service import get_avatar, get_nickname, parse_at_target
from .user_state_service import (
    apply_random_ban,
    commit_single_action,
    format_duration,
    roll_action_values,
)


async def run_zha(plugin, event):
    send_id = str(event.get_sender_id())
    at_user_id = parse_at_target(event, default_sender=False)
    if not at_user_id:
        return [forward_result(event, [entry(Comp.Plain("用法：/榨 @某人"), name="榨说明")], default_name="榨说明")]

    blocked = await check_shared_ban(
        plugin,
        event,
        initiator_id=send_id,
        target_id=at_user_id,
        self_ban_message="你已经被彻底玩坏了，不能再榨人，养胃剩余时间{remain}",
        target_ban_message="{target_name}已经进入贤者模式，无法被榨，养胃剩余时间{remain}",
    )
    if blocked:
        return blocked

    blocked = await check_whitelist_and_self(
        plugin,
        event,
        action_name="榨",
        protected_user_id=at_user_id,
        executor_id=at_user_id,
        target_user_id=send_id,
        allow_self=plugin.selfdo,
    )
    if blocked:
        return blocked

    blocked = await check_reject(plugin, event, action_display_name="榨")
    if blocked:
        return blocked

    action = roll_action_values(plugin)
    state = commit_single_action(
        plugin,
        event,
        executor_id=at_user_id,
        target_user_id=send_id,
        duration=action["duration"],
        vol=action["vol"],
    )
    if not state.get("ok"):
        return [forward_result(event, [entry(Comp.Plain("这次操作出了点问题，请稍后再试"))])]

    actor_name = await get_nickname(event, at_user_id)
    avatar = get_avatar(send_id)
    record = state["record"]
    action_text = (
        f"你诱导了{actor_name}，{actor_name}被迫反手操作了你，"
        f"向你注入了{'💥暴击！' if action['crit'] else ''}{action['vol']:.2f}ml的生命因子"
    )
    action_tail = "这是你的初体验。" if state["is_first"] else f"这是你的第{record['num']}次。"

    entries = [
        entry(
            Comp.Plain(action_text),
            Comp.Image.fromURL(avatar),
            Comp.Plain(action_tail),
            name="榨记录",
        )
    ]

    roll = random.random()
    if roll < 0.8:
        entries.append(entry(Comp.Plain("这次风平浪静，事后并无波澜。"), name="榨结局"))
    elif roll < 0.9:
        ban_seconds = apply_random_ban(plugin, send_id)
        entries.append(
            entry(
                Comp.Plain(
                    f"对方的攻势过于猛烈，你被彻底玩坏了，掉落了战败CG……\n"
                    f"你进入了养胃状态：{format_duration(ban_seconds)}"
                ),
                name="榨结局",
            )
        )
    else:
        ban_seconds = apply_random_ban(plugin, at_user_id)
        entries.append(
            entry(
                Comp.Plain(
                    f"{actor_name}太杂鱼了，被你狠狠嘲讽后心态爆炸，当场破防。\n"
                    f"对方进入了养胃状态：{format_duration(ban_seconds)}"
                ),
                name="榨结局",
            )
        )

    return [forward_result(event, entries, default_name="榨记录")]
