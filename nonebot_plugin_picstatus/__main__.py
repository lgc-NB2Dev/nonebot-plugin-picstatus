from nonebot import logger, on_command
from nonebot.adapters import Message
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.rule import Rule, to_me
from nonebot_plugin_alconna.uniseg import UniMessage

from .config import config
from .render import collect_and_render


def check_empty_arg_rule(arg: Message = CommandArg()):
    return not arg.extract_plain_text()


def trigger_rule():
    rule = Rule(check_empty_arg_rule)
    if config.ps_need_at:
        rule = rule & to_me()
    return rule


_cmd, *_alias = config.ps_command
stat_matcher = on_command(
    _cmd,
    aliases=set(_alias),
    rule=trigger_rule(),
    permission=SUPERUSER if config.ps_only_su else None,
)


@stat_matcher.handle()
async def _():
    try:
        ret = await collect_and_render()
    except Exception:
        logger.exception("获取运行状态图失败")
        await UniMessage("获取运行状态图片失败，请检查后台输出").send(
            reply_to=config.ps_reply_target,
        )
    else:
        await UniMessage.image(raw=ret).send(reply_to=config.ps_reply_target)
