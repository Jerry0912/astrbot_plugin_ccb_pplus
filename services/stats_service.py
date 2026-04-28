# -- coding: utf-8 --
from astrbot.api.event import AstrMessageEvent

from ..constants import FIELD_BY, FIELD_ID, FIELD_MAX, FIELD_NUM, FIELD_VOL, XNN_W_ACTION, XNN_W_NUM, XNN_W_VOL
from .storage_service import read_data
from .user_service import get_nickname


def _group_data(group_id: str) -> list:
    return read_data().get(group_id, [])


def _calc_max_value(record: dict) -> float:
    raw_max = record.get(FIELD_MAX, None)
    try:
        if raw_max is not None:
            return float(raw_max)
        total_vol = float(record.get(FIELD_VOL, 0))
        total_num = int(record.get(FIELD_NUM, 0))
        return round(total_vol / total_num, 2) if total_num > 0 else 0.0
    except Exception:
        return 0.0


async def build_ccbtop(event: AstrMessageEvent):
    group_id = str(event.get_group_id())
    group_data = _group_data(group_id)
    if not group_data:
        return event.plain_result("当前群暂无ccb记录。")

    top5 = sorted(group_data, key=lambda x: int(x.get(FIELD_NUM, 0)), reverse=True)[:5]
    msg = "被ccb排行榜 TOP5：\n"
    for i, record in enumerate(top5, 1):
        uid = record[FIELD_ID]
        nick = await get_nickname(event, uid)
        msg += f"{i}. {nick} - 次数：{record[FIELD_NUM]}\n"
    return event.plain_result(msg)


async def build_ccbvol(event: AstrMessageEvent):
    group_id = str(event.get_group_id())
    group_data = _group_data(group_id)
    if not group_data:
        return event.plain_result("当前群暂无ccb记录。")

    top5 = sorted(group_data, key=lambda x: float(x.get(FIELD_VOL, 0)), reverse=True)[:5]
    msg = "被注入量排行榜 TOP5：\n"
    for i, record in enumerate(top5, 1):
        uid = record[FIELD_ID]
        nick = await get_nickname(event, uid)
        msg += f"{i}. {nick} - 累计注入：{float(record[FIELD_VOL]):.2f}ml\n"
    return event.plain_result(msg)


async def build_ccbinfo(event: AstrMessageEvent, target_user_id: str):
    group_id = str(event.get_group_id())
    group_data = _group_data(group_id)

    record = next((r for r in group_data if r.get(FIELD_ID) == target_user_id), None)
    if not record:
        return event.plain_result("该用户暂无ccb记录。")

    total_num = int(record.get(FIELD_NUM, 0))
    total_vol = float(record.get(FIELD_VOL, 0))
    max_val = _calc_max_value(record)

    cb_total = 0
    try:
        for rec in group_data:
            by = rec.get(FIELD_BY, {}) or {}
            info = by.get(target_user_id)
            if info:
                cb_total += int(info.get("count", 0))
    except Exception:
        cb_total = 0

    ccb_by = record.get(FIELD_BY, {}) or {}
    first_actor = None
    for actor_id, info in ccb_by.items():
        if info.get("first"):
            first_actor = actor_id
            break
    if not first_actor and ccb_by:
        first_actor = max(ccb_by.items(), key=lambda x: x[1].get("count", 0))[0]

    first_nick = await get_nickname(event, first_actor) if first_actor else "未知"
    target_nick = await get_nickname(event, target_user_id)

    msg = (
        f"【{target_nick}】\n"
        f"• 破壁人：{first_nick}\n"
        f"• 北朝：{total_num}\n"
        f"• 朝壁：{cb_total}\n"
        f"• 诗经：{total_vol:.2f}ml\n"
        f"• 马克思：{max_val:.2f}ml"
    )
    return event.plain_result(msg)


async def build_ccbmax(event: AstrMessageEvent):
    group_id = str(event.get_group_id())
    group_data = _group_data(group_id)
    if not group_data:
        return event.plain_result("当前群暂无ccb记录。")

    entries = [(record, _calc_max_value(record)) for record in group_data]
    entries.sort(key=lambda x: x[1], reverse=True)
    top5 = entries[:5]

    msg = "单次最大注入排行榜 TOP5：\n"
    for i, (record, max_val) in enumerate(top5, 1):
        uid = record.get(FIELD_ID)
        producer_id = None
        ccb_by = record.get(FIELD_BY, {}) or {}
        for actor_id, info in ccb_by.items():
            if info.get("max"):
                producer_id = actor_id
                break
        if not producer_id and ccb_by:
            try:
                producer_id = max(ccb_by.items(), key=lambda x: x[1].get("count", 0))[0]
            except Exception:
                producer_id = None

        nick = await get_nickname(event, uid)
        producer_nick = await get_nickname(event, producer_id) if producer_id else "未知"
        msg += f"{i}. {nick} - 单次最大：{max_val:.2f}ml（{producer_nick}）\n"
    return event.plain_result(msg)


async def build_xnn(event: AstrMessageEvent):
    group_id = str(event.get_group_id())
    group_data = _group_data(group_id)
    if not group_data:
        return event.plain_result("当前群暂无ccb记录。")

    actor_actions = {}
    for record in group_data:
        ccb_by = record.get(FIELD_BY, {}) or {}
        for actor_id, info in ccb_by.items():
            actor_actions[actor_id] = actor_actions.get(actor_id, 0) + info.get("count", 0)

    ranking = []
    for record in group_data:
        uid = record.get(FIELD_ID)
        num = int(record.get(FIELD_NUM, 0))
        vol = float(record.get(FIELD_VOL, 0))
        actions = actor_actions.get(uid, 0)
        xnn_value = num * XNN_W_NUM + vol * XNN_W_VOL - actions * XNN_W_ACTION
        ranking.append((uid, xnn_value))

    ranking.sort(key=lambda x: x[1], reverse=True)
    msg = "💎 小南梁 TOP5 💎\n"
    for idx, (uid, xnn_val) in enumerate(ranking[:5], 1):
        nick = await get_nickname(event, uid)
        msg += f"{idx}. {nick} - XNN值：{xnn_val:.2f} \n"
    return event.plain_result(msg)
