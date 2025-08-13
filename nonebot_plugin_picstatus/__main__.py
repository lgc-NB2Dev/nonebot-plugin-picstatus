import asyncio

from nonebot import logger, on_command
from nonebot.adapters import Message as BaseMessage
from nonebot.matcher import current_bot, current_event, current_matcher
from nonebot.params import CommandArg, Depends
from nonebot.permission import SUPERUSER
from nonebot.rule import Rule, to_me
from nonebot_plugin_alconna.uniseg import Image, Reply, UniMessage, UniMsg, image_fetch

from .bg_provider import BgData, bg_preloader
from .collectors import collect_all
from .config import config
from .templates import render_current_template


def check_empty_arg_rule(arg: BaseMessage = CommandArg()):
    return not arg.extract_plain_text()


def trigger_rule():
    rule = Rule(check_empty_arg_rule)
    if config.ps_need_at:
        rule &= to_me()
    return rule


_cmd, *_alias = config.ps_command
stat_matcher = on_command(
    _cmd,
    aliases=set(_alias),
    rule=trigger_rule(),
    permission=SUPERUSER if config.ps_only_su else None,
)


async def _msg_pic(msg: UniMsg) -> BgData | None:
    msg = (
        r
        if (
            Reply in msg
            and isinstance((r_org := msg[Reply, 0].msg), BaseMessage)
            and Image in (r := await UniMessage.generate(message=r_org))
        )
        else msg
    )
    if Image not in msg:
        return None
    img = msg[Image, 0]
    data = await image_fetch(
        current_event.get(),
        current_bot.get(),
        current_matcher.get().state,
        img,
    )
    if not data:
        return None
    return BgData(data=data, mime=img.mimetype or "image")


def MsgPic():  # noqa: N802
    return Depends(_msg_pic)


@stat_matcher.handle()
async def _(msg_pic: BgData | None = MsgPic()):
    # with suppress(Exception):
    #     await cache_bot_info(bot)

    async def get_bg():
        return msg_pic or (await bg_preloader.get())

    try:
        bg, collected = await asyncio.gather(get_bg(), collect_all())
        ret = await render_current_template(collected=collected, bg=bg)
    except Exception:
        logger.exception("获取运行状态图失败")
        await UniMessage("获取运行状态图片失败，请检查后台输出").send(
            reply_to=config.ps_reply_target,
        )
    else:
        await UniMessage.image(raw=ret).send(reply_to=config.ps_reply_target)
