from collections.abc import Callable
from datetime import datetime
from typing import Any

from cookit.loguru import log_exception_warning
from nonebot import get_driver, logger
from nonebot.adapters import Bot as BaseBot, Event as BaseEvent
from nonebot.message import event_preprocessor
from nonebot.typing import T_State
from nonebot_plugin_alconna import image_fetch
from nonebot_plugin_alconna.uniseg import Image
from nonebot_plugin_uninfo import User, get_interface

from .config import config

nonebot_run_time: datetime = datetime.now().astimezone()
bot_connect_time: dict[str, datetime] = {}
recv_num: dict[str, int] = {}
send_num: dict[str, int] = {}

bot_info_cache: dict[str, User] = {}
bot_avatar_cache: dict[str, bytes | None] = {}

driver = get_driver()

SEND_APIS: dict[str, list[str] | Callable[[str], bool]] = {
    # "BilibiliLive": [],  # 狗东西发消息不走 call_api
    "Console": ["send_msg"],
    "Ding": ["send"],
    "Discord": ["create_message"],
    "Feishu": ["im/v1/messages"],
    "Kaiheila": ["message_create", "directMessage_create"],
    "Minecraft": ["send_msg"],
    "mirai2": ["send_friend_message", "send_group_message", "send_temp_message"],
    "ntchat": lambda x: x.startswith("send_"),
    "OneBot V11": ["send_private_msg", "send_group_msg", "send_msg"],
    "OneBot V12": ["send_message"],
    "QQ": [
        "post_dms_messages",
        "post_messages",
        "post_c2c_messages",
        "post_c2c_files",
        "post_group_messages",
        "post_group_files",
    ],
    "RedProtocol": ["send_message", "send_fake_forward"],
    "Satori": ["message_create"],
    "Telegram": lambda x: x.startswith("send_"),
    "大别野": ["send_message"],
}


def method_is_send_msg(platform: str, name: str) -> bool:
    return (platform in SEND_APIS) and (
        (name in it) if isinstance((it := SEND_APIS[platform]), list) else it(name)
    )


if config.ps_count_message_sent_event:

    @event_preprocessor
    async def _(bot: BaseBot, event: BaseEvent):
        if (
            config.ps_count_message_sent_event
            and (
                (config.ps_count_message_sent_event is True)
                or bot.adapter.get_name() in config.ps_count_message_sent_event
            )
            and (
                (event.get_type() == "message_sent")
                or (
                    event.get_type() == "message" and event.get_user_id() == bot.self_id
                )
            )
        ):
            # logger.debug(f"Bot {bot.self_id} sent counter +1")
            send_num[bot.self_id] += 1


if config.ps_count_message_sent_event is not True:

    @BaseBot.on_called_api
    async def called_api(
        bot: BaseBot,
        exc: Exception | None,
        api: str,
        _: dict[str, Any],
        __: Any,
    ):
        if (
            (not exc)
            and (config.ps_count_message_sent_event is not True)
            and (
                (config.ps_count_message_sent_event is False)
                or (bot.adapter.get_name() not in config.ps_count_message_sent_event)
            )
            and method_is_send_msg(bot.adapter.get_name(), api)
        ):
            # logger.debug(f"Bot {bot.self_id} sent counter +1")
            send_num[bot.self_id] += 1


async def cache_bot_avatar(avatar: str, bot: BaseBot, event: BaseEvent, state: T_State):
    try:
        img = await image_fetch(event, bot, state, Image(url=avatar))
    except Exception as e:
        log_exception_warning(e, f"Failed to get avatar of bot {bot.self_id}")
        return None
    else:
        if not img:
            logger.warning(
                f"Cannot get avatar of bot {bot.self_id}"
                f" because image_fetch returned None",
            )
    bot_avatar_cache[bot.self_id] = img
    return img


async def cache_bot_info(bot: BaseBot):
    try:
        it = get_interface(bot)
        info = (await it.get_user(bot.self_id)) if it else None
    except Exception as e:
        logger.warning(f"Error when getting bot info: {e.__class__.__name__}: {e}")
    else:
        if info:
            bot_info_cache[bot.self_id] = info
            return info
    return None


@driver.on_bot_connect
async def _(bot: BaseBot):
    bot_connect_time[bot.self_id] = datetime.now().astimezone()
    if bot.self_id not in recv_num:
        recv_num[bot.self_id] = 0
    if (bot.self_id not in send_num) and (bot.adapter.get_name() in SEND_APIS):
        send_num[bot.self_id] = 0
    await cache_bot_info(bot)


@driver.on_bot_disconnect
async def _(bot: BaseBot):
    bot_connect_time.pop(bot.self_id, None)
    if config.ps_disconnect_reset_counter:
        recv_num.pop(bot.self_id, None)
        send_num.pop(bot.self_id, None)


@event_preprocessor
async def _(bot: BaseBot, event: BaseEvent):
    if event.get_type() == "message":
        recv_num[bot.self_id] += 1
