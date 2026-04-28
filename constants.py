# -- coding: utf-8 --

DATA_FILE = "data/ccb_pplus.json"
LOG_FILE = "data/ccb_pplus_log.json"

FIELD_ID = "id"          # qq号
FIELD_NUM = "num"        # 北朝次数
FIELD_VOL = "vol"        # 被注入量
FIELD_BY = "ccb_by"      # 被谁朝了
FIELD_MAX = "max"        # 单次最大值

XNN_W_NUM = 1.0
XNN_W_VOL = 0.1
XNN_W_ACTION = 0.5
