from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event

from ..utils.convert import get_uid
from ..utils.sr_prefix import PREFIX
from ..utils.error_reply import UID_HINT
from .get_gachalogs import save_gachalogs
from .draw_gachalogs import draw_gachalogs_img

sv_gacha_log = SV('sr抽卡记录')
sv_get_gachalog_by_link = SV('sr导入抽卡链接', area='DIRECT')


@sv_gacha_log.on_fullmatch(f'{PREFIX}抽卡记录')
async def send_gacha_log_card_info(bot: Bot, ev: Event):
    await bot.logger.info('开始执行[sr抽卡记录]')
    get_uid_ = await get_uid(bot, ev, True, False)
    if get_uid_ is None:
        return await bot.send(UID_HINT)
    uid, user_id = get_uid_
    if uid is None:
        return await bot.send(UID_HINT)
    im = await draw_gachalogs_img(uid, user_id)
    await bot.send(im)
    return None


@sv_get_gachalog_by_link.on_command(f'{PREFIX}导入抽卡链接')
async def get_gachalog_by_link(bot: Bot, ev: Event):
    await bot.logger.info('开始执行[sr导入抽卡链接]')
    uid = await get_uid(bot, ev, only_uid=True)
    if uid is None:
        return await bot.send(UID_HINT)
    gacha_url = ev.text.strip()
    if not gacha_url or not isinstance(gacha_url, str):
        return await bot.send('请给出正确的抽卡记录链接')
    is_force = False
    if ev.command.startswith('强制'):
        await bot.logger.info('[WARNING]本次为强制刷新')
        is_force = True
    await bot.send(f'UID{uid}开始执行[刷新抽卡记录],需要一定时间...请勿重复触发!')
    im = await save_gachalogs(uid, gacha_url, None, is_force)
    return await bot.send(im)
