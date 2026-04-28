# -- coding: utf-8 --
import random
import astrbot.api.message_components as Comp

from .message_service import entry, forward_result
from .rule_service import check_shared_ban, check_whitelist_and_self
from .user_service import get_avatar, get_nickname, parse_at_target
from .user_state_service import (
    apply_random_ban,
    commit_action_records,
    format_action_duration,
    format_duration,
    format_min_sec,
    roll_action_values,
)


def _pick_loser(sender_result: dict, target_result: dict, sender_id: str, target_id: str):
    if sender_result["vol"] > target_result["vol"]:
        return target_id
    if sender_result["vol"] < target_result["vol"]:
        return sender_id

    if sender_result["duration"] > target_result["duration"]:
        return target_id
    if sender_result["duration"] < target_result["duration"]:
        return sender_id

    return target_id


async def run_69(plugin, event):
    send_id = str(event.get_sender_id())
    target_user_id = parse_at_target(event, default_sender=False)
    if not target_user_id:
        return [forward_result(event, [entry(Comp.Plain("用法：/69 @某人"), name="69说明")], default_name="69说明")]

    blocked = await check_shared_ban(
        plugin,
        event,
        initiator_id=send_id,
        target_id=target_user_id,
        self_ban_message="你已经进入贤者模式，无法发起69，养胃剩余时间{remain}",
        target_ban_message="{target_name}已经进入贤者模式，无法和你69，养胃剩余时间{remain}",
    )
    if blocked:
        return blocked

    blocked = await check_whitelist_and_self(
        plugin,
        event,
        action_name="69",
        protected_user_id=target_user_id,
        executor_id=send_id,
        target_user_id=target_user_id,
        allow_self=plugin.selfdo,
    )
    if blocked:
        return blocked

    sender_name = await get_nickname(event, send_id)
    target_name = await get_nickname(event, target_user_id)

    # 69玩法特殊：只判定己方是否炸膛，对方不判定
    if random.random() < float(getattr(plugin, "sixty_nine_blowup_prob", 0.1)):
        ban_seconds = apply_random_ban(plugin, send_id)
        return [
            forward_result(
                event,
                [
                    entry(
                        Comp.Plain(
                            f"你发动了一场和{target_name}的对决\n"
                            f"💥还没开始对决你就炸膛了！心态爆炸，陷入了{format_min_sec(ban_seconds)}的贤者时间"
                        ),
                        name="69对决",
                    )
                ],
                default_name="69对决",
            )
        ]

    sender_avatar = get_avatar(send_id)
    target_avatar = get_avatar(target_user_id)

    sender_result = roll_action_values(plugin)
    target_result = roll_action_values(plugin)

    ok = await commit_action_records(
        plugin,
        event,
        [
            {
                "executor_id": send_id,
                "target_user_id": target_user_id,
                "duration": sender_result["duration"],
                "vol": sender_result["vol"],
            },
            {
                "executor_id": target_user_id,
                "target_user_id": send_id,
                "duration": target_result["duration"],
                "vol": target_result["vol"],
            },
        ],
    )
    if not ok:
        return [forward_result(event, [entry(Comp.Plain("这场69对决出了点问题，请稍后再试"), name="69记录")], default_name="69记录")]

    loser_id = _pick_loser(sender_result, target_result, send_id, target_user_id)
    loser_name = sender_name if loser_id == send_id else target_name
    ban_seconds = apply_random_ban(plugin, loser_id)

    entries = [
        entry(Comp.Plain(f"你发动了一场和{target_name}的对决"), name="69对决"),
        entry(
            Comp.Plain(
                f"第一回合，你对{target_name}进行了{format_action_duration(sender_result['duration'])}的ccb，"
                f"注入了{sender_result['vol']:.2f}ml的生命因子"
            ),
            Comp.Image.fromURL(sender_avatar),
            name="69对决",
        ),
        entry(
            Comp.Plain(
                f"第二回合，{target_name}对你进行了{format_action_duration(target_result['duration'])}的ccb，"
                f"注入了{target_result['vol']:.2f}ml的生命因子"
            ),
            Comp.Image.fromURL(target_avatar),
            name="69对决",
        ),
        entry(
            Comp.Plain("你的实力……在我之下！"),
            Comp.Plain(f"{loser_name}落荒而逃，陷入了{format_duration(ban_seconds)}的贤者时间"),
            name="69对决",
        ),
    ]
    return [forward_result(event, entries, default_name="69对决")]
