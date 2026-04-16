# -- coding: utf-8 --
import astrbot.api.message_components as Comp

from . import user_state_service as user_state
from .message_service import entry, forward_result
from .rule_service import check_shared_ban, check_sixty_nine_blowup, check_whitelist_and_self
from .user_service import get_avatar, get_nickname, parse_at_target


def _pick_loser(sender_result: dict, target_result: dict, sender_id: str, target_id: str) -> str:
    sender_vol = float(sender_result.get("vol", 0))
    target_vol = float(target_result.get("vol", 0))
    if sender_vol > target_vol:
        return target_id
    if sender_vol < target_vol:
        return sender_id

    sender_duration = float(sender_result.get("duration", 0))
    target_duration = float(target_result.get("duration", 0))
    if sender_duration > target_duration:
        return target_id
    if sender_duration < target_duration:
        return sender_id

    return target_id


async def run_69(plugin, event):
    send_id = str(event.get_sender_id())
    target_user_id = parse_at_target(event, default_sender=False)

    if not target_user_id:
        return [
            forward_result(
                event,
                [entry(Comp.Plain("用法：/69 @某人"), name="69说明")],
                default_name="69说明",
            )
        ]

    sender_name = str(send_id)
    target_name = str(target_user_id)

    try:
        sender_name = await get_nickname(event, send_id) or str(send_id)
    except Exception:
        sender_name = str(send_id)

    try:
        target_name = await get_nickname(event, target_user_id) or str(target_user_id)
    except Exception:
        target_name = str(target_user_id)

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

    blocked = await check_sixty_nine_blowup(plugin, event, user_id=send_id)
    if blocked:
        return blocked

    sender_avatar = get_avatar(send_id)
    target_avatar = get_avatar(target_user_id)

    sender_result = user_state.roll_action_values(plugin)
    target_result = user_state.roll_action_values(plugin)

    ok = await user_state.commit_action_records(
        plugin,
        event,
        [
            {
                "executor_id": send_id,
                "target_user_id": target_user_id,
                "duration": sender_result.get("duration", 0),
                "vol": sender_result.get("vol", 0),
            },
            {
                "executor_id": target_user_id,
                "target_user_id": send_id,
                "duration": target_result.get("duration", 0),
                "vol": target_result.get("vol", 0),
            },
        ],
    )
    if not ok:
        return [
            forward_result(
                event,
                [entry(Comp.Plain("这场69对决出了点问题，请稍后再试"), name="69记录")],
                default_name="69记录",
            )
        ]

    loser_id = _pick_loser(sender_result, target_result, send_id, target_user_id)
    loser_name = sender_name if loser_id == send_id else target_name
    ban_seconds = user_state.apply_random_ban(plugin, loser_id)

    sender_duration_text = user_state.format_action_duration(sender_result.get("duration", 0))
    target_duration_text = user_state.format_action_duration(target_result.get("duration", 0))

    entries = [
        entry(Comp.Plain(f"你发动了一场和{target_name}的对决"), name="69对决"),
        entry(
            Comp.Plain(
                f"第一回合，你对{target_name}进行了{sender_duration_text}的ccb，"
                f"注入了{float(sender_result.get('vol', 0)):.2f}ml的生命因子"
            ),
            Comp.Image.fromURL(sender_avatar),
            name="69对决",
        ),
        entry(
            Comp.Plain(
                f"第二回合，{target_name}对你进行了{target_duration_text}的ccb，"
                f"注入了{float(target_result.get('vol', 0)):.2f}ml的生命因子"
            ),
            Comp.Image.fromURL(target_avatar),
            name="69对决",
        ),
        entry(
            Comp.Plain("你的实力……在我之下！"),
            Comp.Plain(f"{loser_name}落荒而逃，陷入了{user_state.format_duration(ban_seconds)}的贤者时间"),
            name="69对决",
        ),
    ]
    return [forward_result(event, entries, default_name="69对决")]
