# hive/utils/datetime_util.py
from datetime import datetime
import pytz

def get_current_timestamp(timezone: str = 'Asia/Shanghai') -> str:
    """获取指定时区的当前日期和时间，并格式化为字符串。"""
    tz = pytz.timezone(timezone)
    now = datetime.now(tz)
    # 格式: "2025年07月30日 星期三, 15:30"
    return now.strftime("%Y年%m月%d日 %A, %H:%M") 