# -- coding: utf-8 --
import json
import os
from astrbot.api import logger

from ..constants import DATA_FILE, LOG_FILE


def _ensure_parent(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def read_data() -> dict:
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"读取数据错误: {e}")
    return {}


def write_data(data: dict) -> None:
    try:
        _ensure_parent(DATA_FILE)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"写入数据错误: {e}")


def append_log(group_id: str, executor_id: str, target_id: str, duration: float, vol: float) -> None:
    try:
        _ensure_parent(LOG_FILE)
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as lf:
                try:
                    logs = json.load(lf)
                    if not isinstance(logs, list):
                        logs = []
                except Exception:
                    logs = []
        else:
            logs = []

        row = {
            "group": group_id,
            "executor": executor_id,
            "target": target_id,
            "time": round(float(duration), 2),
            "vol": round(float(vol), 2),
        }
        logs.append(row)

        with open(LOG_FILE, "w", encoding="utf-8") as lf:
            json.dump(logs, lf, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"append_log 失败: {e}")
