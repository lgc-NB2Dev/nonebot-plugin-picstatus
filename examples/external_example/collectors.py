import random
from typing_extensions import override

from nonebot_plugin_picstatus.collectors import (
    BaseTimeBasedCounterCollector,
    NormalTimeBasedCounterCollector,
    PeriodicTimeBasedCounterCollector,
    collector,
    first_time_collector,
    normal_collector,
    periodic_collector,
)

# 添加自定义数据源展示
# 实际应用例请见 https://github.com/lgc-NB2Dev/nonebot-plugin-picstatus/tree/master/nonebot_plugin_picstatus/collectors

# PicStatus 内置了三种可以直接用装饰器注册的 collector

# region 1. normal_collector

counter_count = 0


# 该 collector 在每次生成状态图片时都会被调用
# 使用该装饰器时，默认使用函数名作为数据源名称，你也可以手动指定，例如
# @normal_collector("counter")
@normal_collector()
async def counter():
    global counter_count
    counter_count += 1
    return counter_count


# endregion

# region 2. first_time_collector

first_time_counter_count = 0


# 该 collector 只会在 nonebot 启动时被调用一次并缓存结果
# 下面的例子中，该 collector 的结果将会始终为 1
# 装饰器使用教程同上
@first_time_collector()
async def first_time_counter():
    global first_time_counter_count
    first_time_counter_count += 1
    return first_time_counter_count


# endregion

# region 3. periodic_collector

periodic_counter_count = 0


# 该 collector 每隔一定时间被调用一次，并保存一定数量的结果在 deque 中
# 调用的间隔与保留的结果数量可以在 PicStatus 的配置中找到
# 装饰器使用教程同上
@periodic_collector()
async def periodic_counter():
    global periodic_counter_count
    periodic_counter_count += 1
    return periodic_counter_count


# endregion


# 此外 PicStatus 内置了另外一种较特殊的 collector
# 它不可以直接用装饰器装饰一个函数使用


# region 4. TimeBasedCounterCollector


# 它可以根据该次调用与上次调用的时间间隔来计算返回值
# 这对展示 IO 速度等数据可能会很有帮助


# 使用此 collector 你需要继承两个 abstract method
class BaseTestTimeBasedCounter(BaseTimeBasedCounterCollector[int, str]):
    @override
    async def _calc(self, past: int, now: int, time_passed: float) -> str:
        """
        此方法计算你最终想要返回的结果

        Args:
            past: 上次调用时返回的原始结果
            now: 本次调用时返回的原始结果
            time_passed: 从上次调用到本次调用的时间间隔（秒）

        Returns:
            处理后的结果，和 PeriodicCollector 一样保存在 deque 中
        """
        return f"{(now - past) / time_passed:.2f}/s"

    @override
    async def _get_obj(self) -> int:
        """此方法返回传入 _calc 方法中的原始结果"""
        return random.randint(0, 100)


# 其下有两个分支，Normal 与 Periodic
# Normal 不会在后台持续收集数据，而 Periodic 会
# 你可以用一个 Base 同时派生出 Normal 与 Periodic 两个类
# 使用 @collector 装饰器来注册


@collector("time_counter")
class NormalTestTimeBasedCounter(
    BaseTestTimeBasedCounter,
    NormalTimeBasedCounterCollector[int, str],
): ...


@collector("time_counter_periodic")
class PeriodicTestTimeBasedCounter(
    BaseTestTimeBasedCounter,
    PeriodicTimeBasedCounterCollector[int, str],
): ...


# endregion
