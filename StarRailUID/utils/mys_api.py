import copy
import time
import random
from string import digits, ascii_letters
from typing import Any, Dict, Union, Literal, Optional

import msgspec
from gsuid_core.utils.api.mys_api import _MysApi
from gsuid_core.utils.database.models import GsUser

# from gsuid_core.utils.api.mys.models import MysSign, SignList
from gsuid_core.utils.api.mys.tools import (
    mys_version,
    _random_int_ds,
    generate_os_ds,
    get_web_ds_token,
)

from .api import srdbsqla
from ..sruid_utils.api.mys.api import _API
from ..sruid_utils.api.mys.models import (
    MysSign,
    GachaLog,
    SignInfo,
    SignList,
    AbyssData,
    RogueData,
    RoleIndex,
    AvatarInfo,
    MonthlyAward,
    DailyNoteData,
    RoleBasicInfo,
    WidgetStamina,
    RogueLocustData,
)

RECOGNIZE_SERVER = {
    '1': 'prod_gf_cn',
    '2': 'prod_gf_cn',
    '5': 'prod_qd_cn',
    '6': 'prod_official_usa',
    '7': 'prod_official_euro',
    '8': 'prod_official_asia',
    '9': 'prod_official_cht',
}


def get_ds_token2(
    q: str = '',
    b: Optional[Dict[str, Any]] = None,
):
    salt = 't0qEgfub6cvueAPgR5m9aQWWVciEer7v'
    return _random_int_ds(salt, q, b)


class MysApi(_MysApi):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def get_ck(
        self, uid: str, mode: Literal['OWNER', 'RANDOM'] = 'RANDOM'
    ) -> Optional[str]:
        if mode == 'RANDOM':
            return await GsUser.get_random_cookie(uid, game_name='sr')
        return await GsUser.get_user_cookie_by_uid(uid, game_name='sr')

    async def get_stoken(self, uid: str) -> Optional[str]:
        return await GsUser.get_user_stoken_by_uid(uid, 'sr')

    async def get_user_fp(self, uid: str) -> Optional[str]:
        data = await GsUser.get_user_attr_by_uid(uid, 'fp', 'sr')
        if data is None:
            data = await self.generate_fp_by_uid(uid)
            await GsUser.update_data_by_uid_without_bot_id(uid, 'sr', fp=data)
        return data

    async def get_user_device_id(self, uid: str) -> Optional[str]:
        data = await GsUser.get_user_attr_by_uid(uid, 'device_id', 'sr')
        if data is None:
            data = self.get_device_id()
            await GsUser.update_data_by_uid_without_bot_id(
                uid, 'sr', device_id=data
            )
        return data

    def check_os(self, uid: str) -> bool:
        return False if int(str(uid)[0]) < 6 else True

    async def create_qrcode_url(self) -> Union[Dict, int]:
        device_id: str = ''.join(random.choices(ascii_letters + digits, k=64))
        app_id: str = '8'
        data = await self._mys_request(
            _API['CREATE_QRCODE'],
            'POST',
            header={},
            data={'app_id': app_id, 'device': device_id},
        )
        if isinstance(data, Dict):
            url: str = data['data']['url']
            ticket = url.split('ticket=')[1]
            return {
                'app_id': app_id,
                'ticket': ticket,
                'device': device_id,
                'url': url,
            }
        return data

    async def get_daily_data(self, uid: str) -> Union[DailyNoteData, int]:
        is_os = self.check_os(uid)
        if is_os:
            HEADER = copy.deepcopy(self._HEADER_OS)
            ck = await self.get_ck(uid, 'OWNER')
            if ck is None:
                return -51
            HEADER['Cookie'] = ck
            HEADER['DS'] = generate_os_ds()
            header = HEADER
            data = await self.simple_mys_req(
                'STAR_RAIL_NOTE_URL',
                uid,
                params={
                    'role_id': uid,
                    'server': RECOGNIZE_SERVER.get(str(uid)[0], 'prod_gf_cn'),
                },
                header=header,
            )
        else:
            data = await self.simple_mys_req(
                'STAR_RAIL_NOTE_URL', uid, header=self._HEADER
            )
        if isinstance(data, Dict):
            data = msgspec.convert(data['data'], type=DailyNoteData)
            # data = cast(DailyNoteData, data['data'])
        return data

    async def get_widget_stamina_data(
        self, uid: str
    ) -> Union[WidgetStamina, int]:
        header = copy.deepcopy(self._HEADER)
        sk = await self.get_stoken(uid)
        if sk is None:
            return -51
        header['Cookie'] = sk
        header['x-rpc-channel'] = 'beta'
        device_id = await self.get_user_device_id(uid)
        header['x-rpc-device_id'] = (
            '233333' if device_id is None else device_id
        )
        header['x-rpc-app_version'] = '2.53.0'
        header['x-rpc-device_model'] = 'Mi 10'
        fp = await self.get_user_fp(uid)
        header['x-rpc-device_fp'] = 'Asmr489' if fp is None else fp
        header['x-rpc-client_type'] = '2'
        header['DS'] = get_ds_token2()
        header['Referer'] = 'https://app.mihoyo.com'
        del header['Origin']
        header['x-rpc-sys_version'] = '12'
        header['User-Agent'] = 'okhttp/4.8.0'
        data = await self._mys_request(
            _API['STAR_RAIL_WIDGRT_URL'], 'GET', header
        )
        if isinstance(data, Dict):
            data = msgspec.convert(data['data'], type=WidgetStamina)
            # data = cast(WidgetStamina, data['data'])
        return data

    async def get_role_index(self, uid: str) -> Union[RoleIndex, int]:
        is_os = self.check_os(uid)
        if is_os:
            HEADER = copy.deepcopy(self._HEADER_OS)
            ck = await self.get_ck(uid, 'OWNER')
            if ck is None:
                return -51
            HEADER['Cookie'] = ck
            HEADER['DS'] = generate_os_ds()
            header = HEADER
            data = await self.simple_mys_req(
                'STAR_RAIL_INDEX_URL',
                uid,
                params={
                    'role_id': uid,
                    'server': RECOGNIZE_SERVER.get(str(uid)[0], 'prod_gf_cn'),
                },
                header=header,
            )
        else:
            data = await self.simple_mys_req(
                'STAR_RAIL_INDEX_URL', uid, header=self._HEADER
            )
        if isinstance(data, Dict):
            data = msgspec.convert(data['data'], type=RoleIndex)
            # data = cast(RoleIndex, data['data'])
        return data

    async def get_gacha_log_by_link_in_authkey(
        self,
        uid: str,
        authkey: str,
        gacha_type: str = '11',
        page: int = 1,
        end_id: str = '0',
    ) -> Union[int, GachaLog]:
        # server_id = 'cn_qd01' if
        # uid[0] == '5' else 'cn_gf01'
        server_id = RECOGNIZE_SERVER.get(str(uid)[0])
        if self.check_os(uid):
            HEADER = copy.deepcopy(self._HEADER_OS)
            ck = await self.get_ck(uid, 'OWNER')
            if ck is None:
                return -51
            HEADER['Cookie'] = ck
            HEADER['DS'] = generate_os_ds()
            header = HEADER
            url = self.MAPI['STAR_RAIL_GACHA_LOG_URL_OS']
            game_biz = 'hkrpg_global'
        else:
            header = self._HEADER
            url = self.MAPI['STAR_RAIL_GACHA_LOG_URL']
            game_biz = 'hkrpg_cn'
        data = await self._mys_request(
            url=url,
            method='GET',
            header=header,
            params={
                'authkey_ver': '1',
                'sign_type': '2',
                'auth_appid': 'webview_gacha',
                'default_gacha_type': 11,
                'gacha_id': 'dbebc8d9fbb0d4ffa067423482ce505bc5ea',
                'timestamp': str(int(time.time())),
                'lang': 'zh-cn',
                'plat_type': 'pc',
                'region': server_id,
                'authkey': authkey,
                'game_biz': game_biz,
                'gacha_type': gacha_type,
                'page': page,
                'size': '20',
                'end_id': end_id,
            },
        )
        if isinstance(data, Dict):
            data = msgspec.convert(data['data'], type=GachaLog)
            # data = cast(GachaLog, data['data'])
        return data

    async def get_avatar_info(
        self, uid: str, avatar_id: int, need_wiki: bool = False
    ) -> Union[AvatarInfo, int]:
        is_os = self.check_os(uid)
        if is_os:
            HEADER = copy.deepcopy(self._HEADER_OS)
            ck = await self.get_ck(uid, 'OWNER')
            if ck is None:
                return -51
            HEADER['Cookie'] = ck
            HEADER['DS'] = generate_os_ds()
            header = HEADER
            data = await self.simple_mys_req(
                'STAR_RAIL_AVATAR_INFO_URL',
                uid,
                params={
                    'need_wiki': 'true' if need_wiki else 'false',
                    'role_id': uid,
                    'server': RECOGNIZE_SERVER.get(str(uid)[0], 'prod_gf_cn'),
                },
                header=header,
            )
        else:
            data = await self.simple_mys_req(
                'STAR_RAIL_AVATAR_INFO_URL',
                uid,
                params={
                    'id': avatar_id,
                    'need_wiki': 'true' if need_wiki else 'false',
                    'role_id': uid,
                    'server': RECOGNIZE_SERVER.get(str(uid)[0], 'prod_gf_cn'),
                },
                header=self._HEADER,
            )
        if isinstance(data, Dict):
            data = msgspec.convert(data['data'], type=AvatarInfo)
            # data = cast(AvatarInfo, data['data'])
        return data

    async def get_sign_list(self, uid) -> Union[SignList, int]:
        is_os = self.check_os(uid)
        if is_os:
            params = {
                'act_id': 'e202303301540311',
                'lang': 'zh-cn',
            }

        else:
            params = {
                'act_id': 'e202304121516551',
                'lang': 'zh-cn',
            }
        data = await self._mys_req_get(
            'STAR_RAIL_SIGN_LIST_URL', is_os, params
        )
        if isinstance(data, Dict):
            data = msgspec.convert(data['data'], type=SignList)
            # data = cast(SignList, data['data'])
        return data

    async def get_sign_info(self, uid) -> Union[SignInfo, int]:
        # server_id = RECOGNIZE_SERVER.get(str(uid)[0])
        is_os = self.check_os(uid)
        if is_os:
            # TODO
            params = {
                'act_id': 'e202303301540311',
                'lang': 'zh-cn',
            }
            HEADER = copy.deepcopy(self._HEADER_OS)
            ck = await self.get_ck(uid, 'OWNER')
            if ck is None:
                return -51
            HEADER['Cookie'] = ck
            HEADER['DS'] = generate_os_ds()
            header = HEADER
        else:
            params = {
                'act_id': 'e202304121516551',
                'lang': 'zh-cn',
                'region': 'prod_gf_cn',
                'uid': uid,
            }
            header = self._HEADER
        data = await self._mys_req_get(
            'STAR_RAIL_SIGN_INFO_URL', is_os, params, header
        )
        if isinstance(data, Dict):
            data = msgspec.convert(data['data'], type=SignInfo)
            # data = cast(SignInfo, data['data'])
        return data

    async def get_srspiral_abyss_info(
        self,
        uid: str,
        schedule_type='1',
        ck: Optional[str] = None,
    ) -> Union[AbyssData, int]:
        server_id = self.RECOGNIZE_SERVER.get(uid[0])
        is_os = self.check_os(uid)
        if is_os:
            HEADER = copy.deepcopy(self._HEADER_OS)
            ck = await self.get_ck(uid, 'OWNER')
            if ck is None:
                return -51
            HEADER['Cookie'] = ck
            HEADER['DS'] = generate_os_ds()
            header = HEADER
            data = await self.simple_mys_req(
                'CHALLENGE_INFO_URL',
                uid,
                params={
                    'need_all': 'true',
                    'role_id': uid,
                    'schedule_type': schedule_type,
                    'server': server_id,
                },
                header=header,
            )
        else:
            data = await self.simple_mys_req(
                'CHALLENGE_INFO_URL',
                uid,
                params={
                    'isPrev': 'true',
                    'need_all': 'true',
                    'role_id': uid,
                    'schedule_type': schedule_type,
                    'server': server_id,
                },
                cookie=ck,
                header=self._HEADER,
            )
        if isinstance(data, Dict):
            data = msgspec.convert(data['data'], type=AbyssData)
            # data = cast(AbyssData, data['data'])
        return data

    async def get_rogue_info(
        self,
        uid: str,
        schedule_type='3',
        ck: Optional[str] = None,
    ) -> Union[RogueData, int]:
        server_id = self.RECOGNIZE_SERVER.get(uid[0])
        data = await self.simple_mys_req(
            'ROGUE_INFO_URL',
            uid,
            params={
                'need_detail': 'true',
                'role_id': uid,
                'schedule_type': schedule_type,
                'server': server_id,
            },
            cookie=ck,
            header=self._HEADER,
        )
        if isinstance(data, Dict):
            data = msgspec.convert(data['data'], type=RogueData)
            # data = cast(RogueData, data['data'])
        return data

    async def get_rogue_locust_info(
        self,
        uid: str,
        ck: Optional[str] = None,
    ) -> Union[RogueLocustData, int]:
        server_id = self.RECOGNIZE_SERVER.get(uid[0])
        ck = await self.get_ck(uid, 'OWNER')
        data = await self.simple_mys_req(
            'ROGUE_LOCUST_INFO_URL',
            uid,
            params={
                'need_detail': 'true',
                'role_id': uid,
                'server': server_id,
            },
            cookie=ck,
            header=self._HEADER,
        )
        if isinstance(data, Dict):
            data = msgspec.convert(data['data'], type=RogueLocustData)
            # data = cast(RogueLocustData, data['data'])
        return data

    async def mys_sign(
        self, uid, header=None, server_id='cn_gf01'
    ) -> Union[MysSign, int]:
        if header is None:
            header = {}
        ck = await self.get_ck(uid, 'OWNER')
        if ck is None:
            return -51
        if int(str(uid)[0]) < 6:
            HEADER = copy.deepcopy(self._HEADER)
            HEADER['Cookie'] = ck
            HEADER['x-rpc-app_version'] = mys_version
            HEADER['x-rpc-client_type'] = '5'
            HEADER['X_Requested_With'] = 'com.mihoyo.hyperion'
            HEADER['DS'] = get_web_ds_token(True)
            HEADER['Referer'] = 'https://webstatic.mihoyo.com'
            HEADER.update(header)
            data = await self._mys_request(
                url=_API['STAR_RAIL_SIGN_URL'],
                method='POST',
                header=HEADER,
                data={
                    'act_id': 'e202304121516551',
                    'region': 'prod_gf_cn',
                    'uid': uid,
                    'lang': 'zh-cn',
                },
            )
        else:
            HEADER = copy.deepcopy(self._HEADER_OS)
            HEADER['Cookie'] = ck
            HEADER['DS'] = generate_os_ds()
            HEADER.update(header)
            data = await self._mys_request(
                url=_API['STAR_RAIL_SIGN_URL_OS'],
                method='POST',
                header=HEADER,
                data={
                    'act_id': 'e202303301540311',
                    'lang': 'zh-cn',
                },
            )
        if isinstance(data, Dict):
            data = msgspec.convert(data['data'], type=MysSign)
            # data = cast(MysSign, data['data'])
        return data

    async def get_award(self, sr_uid, month) -> Union[MonthlyAward, int]:
        server_id = RECOGNIZE_SERVER.get(str(sr_uid)[0])
        ck = await self.get_ck(sr_uid, 'OWNER')
        if ck is None:
            return -51
        if int(str(sr_uid)[0]) < 6:
            HEADER = copy.deepcopy(self._HEADER)
            HEADER['Cookie'] = ck
            HEADER['DS'] = get_web_ds_token(True)
            data = await self._mys_request(
                url=_API['STAR_RAIL_MONTH_INFO_URL'],
                method='GET',
                header=HEADER,
                params={'uid': sr_uid, 'region': server_id, 'month': month},
            )
        else:
            HEADER = copy.deepcopy(self._HEADER_OS)
            HEADER['Cookie'] = ck
            HEADER['DS'] = generate_os_ds()
            data = await self._mys_request(
                url=_API['STAR_RAIL_MONTH_INFO_URL'],
                method='GET',
                header=HEADER,
                params={'uid': sr_uid, 'region': server_id, 'month': month},
                use_proxy=True,
            )
        if isinstance(data, Dict):
            data = msgspec.convert(data['data'], type=MonthlyAward)
            # data = cast(MonthlyAward, data['data'])
        return data

    async def get_role_basic_info(
        self, sr_uid: str
    ) -> Union[RoleBasicInfo, int]:
        data = await self.simple_mys_req(
            'STAR_RAIL_ROLE_BASIC_INFO_URL', sr_uid, header=self._HEADER
        )
        if isinstance(data, Dict):
            data = msgspec.convert(data['data'], type=RoleBasicInfo)
            # data = cast(RoleBasicInfo, data['data'])
        return data


mys_api = MysApi()
mys_api.dbsqla = srdbsqla
mys_api.MAPI.update(_API)
mys_api.is_sr = True
mys_api.RECOGNIZE_SERVER = RECOGNIZE_SERVER
