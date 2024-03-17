import re
from functools import partial
from typing import List, Optional

from cookit.common.math import format_timedelta

format_time_delta_ps = partial(format_timedelta, day_divider=" ", day_suffix="天")


def match_list_regexp(reg_list: List[str], txt: str) -> Optional[re.Match]:
    return next((match for r in reg_list if (match := re.search(r, txt))), None)


def percent_to_color(percent: float) -> str:
    if percent < 70:
        return "prog-low"
    if percent < 90:
        return "prog-medium"
    return "prog-high"
