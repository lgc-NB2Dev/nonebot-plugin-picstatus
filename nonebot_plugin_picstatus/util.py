import re
from functools import partial
from typing import TYPE_CHECKING, List, Optional

from cookit import auto_convert_byte, format_timedelta

if TYPE_CHECKING:
    from .collectors.cpu import CpuFreq

format_time_delta_ps = partial(format_timedelta, day_divider=" ", day_suffix="天")


def match_list_regexp(reg_list: List[str], txt: str) -> Optional[re.Match]:
    return next((match for r in reg_list if (match := re.search(r, txt))), None)


def format_cpu_freq(freq: "CpuFreq") -> str:
    cu = partial(auto_convert_byte, suffix="Hz", unit_index=2, with_space=False)
    if not freq.current:
        return "主频未知"
    if not freq.max:
        return cu(value=freq.current)
    if freq.max == freq.current:
        return cu(value=freq.max)
    return f"{cu(value=freq.current)} / {cu(value=freq.max)}"
