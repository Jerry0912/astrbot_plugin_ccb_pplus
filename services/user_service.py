# -- coding: utf-8 --
from astrbot.api.event import AstrMessageEvent
import astrbot.api.message_components as Comp


def get_avatar(user_id: str) -> str:
    return f"https://q4.qlogo.cn/headimg_dl?dst_uin={user_id}&spec=640"


async def get_nickname(event: AstrMessageEvent, user_id: str) -> str:
    nickname = user_id
    if event.get_platform_name() == "aiocqhttp":
        try:
            from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent

            assert isinstance(event, AiocqhttpMessageEvent)
            stranger_info = await event.bot.api.call_action("get_stranger_info", user_id=user_id)
            nickname = stranger_info.get("nick", nickname)
        except Exception:
            pass
    return nickname


def parse_at_target(event: AstrMessageEvent, default_sender: bool = True):
    self_id = str(event.get_self_id())
    target_user_id = next(
        (
            str(seg.qq)
            for seg in event.get_messages()
            if isinstance(seg, Comp.At) and str(seg.qq) != self_id
        ),
        None,
    )
    if target_user_id is None and default_sender:
        return str(event.get_sender_id())
    return target_user_id
