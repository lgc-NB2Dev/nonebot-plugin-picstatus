import re
from datetime import timedelta
from typing import List, Optional


def format_timedelta(t: timedelta):
    mm, ss = divmod(t.seconds, 60)
    hh, mm = divmod(mm, 60)
    s = f"{hh}:{mm:02d}:{ss:02d}"
    if t.days:
        s = f"{t.days}天 {s}"
    # if t.microseconds:
    #     s += f" {t.microseconds / 1000:.3f}毫秒"
    return s


def auto_convert_unit(
    value: float,
    round_n: int = 2,
    suffix: str = "",
    multiplier: int = 1024,
    unit_index: int = 0,
) -> str:
    units = ["B", "K", "M", "G", "T", "P"][unit_index:]
    if not units:
        raise ValueError("Wrong `unit_index`")
    unit = None
    for x in units:
        if value < 1000:
            unit = x
            break
        value /= multiplier
    return f"{value:.{round_n}f}{unit or units[-1]}{suffix}"


def match_list_regexp(reg_list: List[str], txt: str) -> Optional[re.Match]:
    return next((match for r in reg_list if (match := re.search(r, txt))), None)


def percent_to_color(percent: float) -> str:
    if percent < 70:
        return "green"
    if percent < 90:
        return "orange"
    return "red"
