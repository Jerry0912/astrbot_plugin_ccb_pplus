# -- coding: utf-8 --
import random
import time

from astrbot.api import logger

from ..constants import FIELD_BY, FIELD_ID, FIELD_MAX, FIELD_NUM, FIELD_VOL
from .storage_service import append_log, read_data, write_data


def find_record(group_data: list, target_user_id: str):
    for item in group_data:
        if item.get(FIELD_ID) == target_user_id:
            return item
    return None


def format_duration(seconds: int) -> str:
    seconds = max(0, int(seconds))
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}时{m}分{s}秒"
    if m > 0:
        return f"{m}分{s}秒"
    return f"{s}秒"

def format_action_duration(duration_min: float) -> str:
    total_seconds = max(0, int(round(float(duration_min) * 60)))
    m, s = divmod(total_seconds, 60)
    return f"{m}min{s}s"

def format_min_sec(seconds: int) -> str:
    seconds = max(0, int(seconds))
    m, s = divmod(seconds, 60)
    return f"{m}min{s}s"


def calc_prev_max(item: dict) -> float:
    raw_prev = item.get(FIELD_MAX, None)
    prev_max = 0.0
    if raw_prev is not None:
        try:
            prev_max = float(raw_prev)
        except (TypeError, ValueError):
            prev_max = 0.0

    if prev_max == 0.0:
        try:
            total_vol = float(item.get(FIELD_VOL, 0))
            total_num = int(item.get(FIELD_NUM, 0))
            if total_num > 0:
                prev_max = round(total_vol / total_num, 2)
        except Exception:
            prev_max = 0.0
    return prev_max


def get_random_ban_duration(plugin) -> int:
    low = int(getattr(plugin, "ban_duration_min", getattr(plugin, "ban_duration", 60)))
    high = int(getattr(plugin, "ban_duration_max", getattr(plugin, "ban_duration", 60)))
    if low > high:
        low, high = high, low
    return random.randint(low, high)


def apply_random_ban(plugin, user_id: str) -> int:
    ban_seconds = get_random_ban_duration(plugin)
    plugin.ban_list[str(user_id)] = time.time() + ban_seconds
    return ban_seconds


def apply_fixed_ban(plugin, user_id: str, ban_seconds: int) -> int:
    plugin.ban_list[str(user_id)] = time.time() + int(ban_seconds)
    return int(ban_seconds)


def get_ban_remaining(plugin, user_id: str) -> int:
    now = time.time()
    ban_end = plugin.ban_list.get(str(user_id), 0)
    if now < ban_end:
        return int(ban_end - now)
    return 0


def roll_action_values(plugin, *, force_crit: bool = False) -> dict:
    duration = round(random.uniform(1, 60), 2)
    vol = round(random.uniform(1, 100), 2)
    crit = False
    if force_crit or random.random() < plugin.crit_prob:
        vol = round(vol * 2, 2)
        crit = True
    return {"duration": duration, "vol": vol, "crit": crit}


def _update_single_action_record(group_data: list, executor_id: str, target_user_id: str, vol: float):
    item = find_record(group_data, target_user_id)

    if item is not None:
        item[FIELD_NUM] = int(item.get(FIELD_NUM, 0)) + 1
        item[FIELD_VOL] = round(float(item.get(FIELD_VOL, 0)) + vol, 2)

        ccb_by = item.get(FIELD_BY, {}) or {}
        if executor_id in ccb_by:
            ccb_by[executor_id]["count"] = ccb_by[executor_id].get("count", 0) + 1
            ccb_by[executor_id]["first"] = ccb_by[executor_id].get("first", False)
        else:
            ccb_by[executor_id] = {"count": 1, "first": False, "max": False}

        prev_max = calc_prev_max(item)
        if float(vol) > prev_max:
            item[FIELD_MAX] = round(float(vol), 2)
            for key in ccb_by:
                ccb_by[key]["max"] = False
            ccb_by[executor_id]["max"] = True
        else:
            for key in ccb_by:
                if "max" not in ccb_by[key]:
                    ccb_by[key]["max"] = False

        item[FIELD_BY] = ccb_by
        return item, False

    new_record = {
        FIELD_ID: target_user_id,
        FIELD_NUM: 1,
        FIELD_VOL: round(vol, 2),
        FIELD_BY: {executor_id: {"count": 1, "first": True, "max": True}},
        FIELD_MAX: round(vol, 2),
    }
    group_data.append(new_record)
    return new_record, True


def commit_single_action(plugin, event, *, executor_id: str, target_user_id: str, duration: float, vol: float):
    try:
        all_data = read_data()
        group_id = str(event.get_group_id())
        group_data = all_data.get(group_id, [])

        record, is_first = _update_single_action_record(group_data, executor_id, target_user_id, vol)

        if plugin.is_log:
            append_log(group_id, executor_id, target_user_id, duration, vol)

        all_data[group_id] = group_data
        write_data(all_data)
        return {"ok": True, "record": record, "is_first": is_first}
    except Exception as e:
        logger.error(f"commit_single_action 报错: {e}")
        return {"ok": False}


async def commit_action_records(plugin, event, actions: list[dict]) -> bool:
    try:
        all_data = read_data()
        group_id = str(event.get_group_id())
        group_data = all_data.get(group_id, [])

        for action in actions:
            executor_id = str(action["executor_id"])
            target_user_id = str(action["target_user_id"])
            duration = float(action["duration"])
            vol = float(action["vol"])

            _update_single_action_record(group_data, executor_id, target_user_id, vol)

            if plugin.is_log:
                append_log(group_id, executor_id, target_user_id, duration, vol)

        all_data[group_id] = group_data
        write_data(all_data)
        return True
    except Exception as e:
        logger.error(f"commit_action_records 报错: {e}")
        return False
