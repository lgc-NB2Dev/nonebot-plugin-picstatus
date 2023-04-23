from nonebot import logger, on_command
from nonebot.adapters.onebot.v11 import Bot, Message, MessageEvent, MessageSegment
from nonebot.internal.matcher import Matcher
from nonebot.internal.rule import Rule
from nonebot.params import CommandArg
from nonebot.rule import ToMeRule

from .config import config
from .draw import get_stat_pic


def trigger_rule():
    def check_su(event: MessageEvent):
        if config.ps_only_su:
            return event.get_user_id() in config.superusers
        return True

    def check_empty_arg(arg: Message = CommandArg()):
        return not arg.extract_plain_text()

    checkers = [check_su, check_empty_arg]
    if config.ps_need_at:
        checkers.append(ToMeRule())

    return Rule(*checkers)


stat_matcher = on_command(
    "运行状态",
    aliases={"状态", "zt", "yxzt", "status"},
    rule=trigger_rule(),
)


@stat_matcher.handle()
async def _(
    bot: Bot,
    event: MessageEvent,
    matcher: Matcher,
    arg: Message = CommandArg(),
):
    pic = None

    if img := arg["image"]:
        pic = img[0].data["url"]

    if event.reply and (img := event.reply.message["image"]):
        pic = img[0].data["url"]

    try:
        ret = await get_stat_pic(bot, pic)
    except:
        logger.exception("获取运行状态图失败")
        await matcher.finish("获取运行状态图片失败，请检查后台输出")

    await matcher.finish(MessageSegment.image(ret))
