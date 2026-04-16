# -- coding: utf-8 --
import astrbot.api.message_components as Comp

from .message_service import entry, forward_result
from .rule_service import check_shared_ban, check_whitelist_and_self
from .user_service import get_avatar, get_nickname, parse_at_target
from .user_state_service import (
    apply_fixed_ban,
    commit_action_records,
    format_min_sec,
    format_action_duration,
    get_random_ban_duration,
    roll_action_values,
)


async def run_jbcs(plugin, event):
    send_id = str(event.get_sender_id())
    target_user_id = parse_at_target(event, default_sender=False)

    if not target_user_id:
        return [
            forward_result(
                event,
                [entry(Comp.Plain("用法：/1jbcs @某人"), name="1jbcs说明")],
                default_name="1jbcs说明",
            )
        ]

    blocked = await check_shared_ban(
        plugin,
        event,
        initiator_id=send_id,
        target_id=target_user_id,
        self_ban_message="你已经再起不能了，无法进行自爆卡车。贤者模式剩余{remain}",
        target_ban_message="对方还在昏迷状态中，对你发起的自爆无动于衷，禁闭时间剩余：{remain}",
    )
    if blocked:
        return blocked

    blocked = await check_whitelist_and_self(
        plugin,
        event,
        action_name="1jbcs",
        protected_user_id=target_user_id,
        executor_id=send_id,
        target_user_id=target_user_id,
        allow_self=plugin.selfdo,
    )
    if blocked:
        return blocked

    target_name = await get_nickname(event, target_user_id)
    target_avatar = get_avatar(target_user_id)

    # 一次必定暴击的 ccb
    result = roll_action_values(plugin, force_crit=True)
    duration = result["duration"]
    vol = result["vol"]

    ok = await commit_action_records(
        plugin,
        event,
        [
            {
                "executor_id": send_id,
                "target_user_id": target_user_id,
                "duration": duration,
                "vol": vol,
            }
        ],
    )
    if not ok:
        return [
            forward_result(
                event,
                [entry(Comp.Plain("这次1jbcs出了点问题，请稍后再试"), name="1jbcs记录")],
                default_name="1jbcs记录",
            )
        ]

    self_ban_seconds = apply_fixed_ban(plugin, send_id, get_random_ban_duration(plugin))

    heavy = __import__('random').random() < 0.2
    target_ban_seconds = get_random_ban_duration(plugin)
    if heavy:
        target_ban_seconds *= 2
    apply_fixed_ban(plugin, target_user_id, target_ban_seconds)

    first_text = (
        "同归于尽吧！\n"
        f"你向{target_name}发起了猛烈的攻击，经过了{format_action_duration(duration)}，"
        f"注入了{vol:.2f}ml的生命因子"
    )

    if heavy:
        second_text = (
            f"你用尽全力进攻，陷入了{format_min_sec(self_ban_seconds)}的贤者模式\n"
            f"{target_name}受到了你的毁灭性冲击，原地晕厥，陷入了沉重的休克中，禁闭时间：{format_min_sec(target_ban_seconds)}。"
        )
    else:
        second_text = (
            f"你用尽全力进攻，陷入了{format_min_sec(self_ban_seconds)}的贤者模式\n"
            f"一阵强烈的冲击后，{target_name}陷入了{format_min_sec(target_ban_seconds)}的禁闭。"
        )

    records = [
        entry(
            Comp.Plain(first_text),
            Comp.Image.fromURL(target_avatar),
            name="1jbcs",
        ),
        entry(
            Comp.Plain(second_text),
            name="1jbcs",
        ),
    ]

    return [forward_result(event, records, default_name="1jbcs")]
