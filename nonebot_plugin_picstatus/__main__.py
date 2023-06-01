from typing import Optional

from nonebot import logger, on_command
from nonebot.internal.adapter import Bot, Event, Message
from nonebot.internal.matcher import Matcher
from nonebot.internal.rule import Rule
from nonebot.params import CommandArg
from nonebot.rule import ToMeRule
from nonebot_plugin_saa import Image, MessageFactory
from nonebot_plugin_saa.utils.platform_send_target import extract_target

from .config import config
from .draw import get_stat_pic
from .util import async_request, download_telegram_file

try:
    from nonebot.adapters.onebot.v11 import MessageEvent as OBV11MessageEvent
except:
    OBV11MessageEvent = None

try:
    from nonebot.adapters.telegram.event import MessageEvent as TGMessageEvent
    from nonebot.adapters.telegram.message import File
except:
    TGMessageEvent = None


async def supported_platform_rule(event: Event):
    if TGMessageEvent and isinstance(event, TGMessageEvent):
        return True

    try:
        extract_target(event)
    except RuntimeError:
        logger.warning("SAA 不支持的平台，取消响应")
        return False

    return True


def trigger_rule():
    def check_su(event: Event):
        if config.ps_only_su:
            return event.get_user_id() in config.superusers
        return True

    def check_empty_arg(arg: Message = CommandArg()):
        return not arg.extract_plain_text()

    checkers = [supported_platform_rule, check_su, check_empty_arg]
    if config.ps_need_at:
        checkers.append(ToMeRule())

    return Rule(*checkers)


async def extract_msg_pic(bot: Bot, event: Event) -> Optional[bytes]:
    if OBV11MessageEvent and isinstance(event, OBV11MessageEvent):
        if (event.reply and (img := event.reply.message["image"])) or (
            img := event.message["image"]
        ):
            url = img[0].data["url"]
            return await async_request(url)

    elif TGMessageEvent and isinstance(event, TGMessageEvent):
        msg = event.message
        if event.reply_to_message and event.reply_to_message.message:
            msg += event.reply_to_message.message

        file_id = None
        if photos := msg["photo"]:
            file_id = photos[0].data["file"]

        elif documents := msg["document"]:
            for doc in documents:
                data = doc.data["document"]
                if data["mime_type"].startswith("image/"):
                    # if not data["file_size"] > (15 * 1024 * 1024):
                    file_id = data["file_id"]
                    break

        if file_id:
            return await download_telegram_file(bot, file_id)

    return None


stat_matcher = on_command(
    "运行状态",
    aliases={"状态", "zt", "yxzt", "status"},
    rule=trigger_rule(),
)


@stat_matcher.handle()
async def _(
    bot: Bot,
    event: Event,
    matcher: Matcher,
):
    pic = None
    try:
        pic = await extract_msg_pic(bot, event)
    except:
        logger.exception("获取消息中附带图片失败，回退到默认行为")

    try:
        ret = await get_stat_pic(bot, pic)
    except:
        logger.exception("获取运行状态图失败")
        await matcher.finish("获取运行状态图片失败，请检查后台输出")

    # 为什么 SAA 还不发版支持 TG
    # 哼哼啊啊啊啊啊啊啊啊啊啊啊啊
    if TGMessageEvent and isinstance(event, TGMessageEvent):
        await matcher.send(File.photo(ret))

    else:
        await MessageFactory(Image(ret)).send()

    await matcher.finish()
