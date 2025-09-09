from collections.abc import AsyncIterator

from httpx import AsyncClient
from nonebot_plugin_picstatus.bg_provider import BgData, bg_provider, resp_to_bg_data
from nonebot_plugin_picstatus.config import config

# 添加自定义背景源演示
# 实际应用例请见 https://github.com/lgc-NB2Dev/nonebot-plugin-picstatus/blob/master/nonebot_plugin_picstatus/bg_provider.py


# 需要用 bg_provider 装饰器注册函数为背景源
# 背景源名称默认为函数名，当然你也可以手动指定名称，比如
# @bg_provider("lgc_icon")
@bg_provider()
async def lgc_icon(num: int) -> AsyncIterator[BgData]:
    async with AsyncClient(
        follow_redirects=True,
        proxy=config.proxy,
        timeout=config.ps_req_timeout,
    ) as cli:
        # 注：不推荐使用这种串行的方式获取图片
        # 如想了解并行写法的示例，请插件插件源码的 bg_provider.py
        for _ in range(num):
            yield resp_to_bg_data(
                (
                    await cli.get("https://blog.lgc2333.top/assets/favicon.png")
                ).raise_for_status(),
            )
