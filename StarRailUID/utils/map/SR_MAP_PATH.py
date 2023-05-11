from pathlib import Path
from typing import Dict, TypedDict

from msgspec import json as msgjson

from ...version import StarRail_version

MAP = Path(__file__).parent / 'data'

version = StarRail_version

avatarId2Name_fileName = f'avatarId2Name_mapping_{version}.json'
avatarId2EnName_fileName = f'avatarId2EnName_mapping_{version}.json'
EquipmentID2Name_fileName = f'EquipmentID2Name_mapping_{version}.json'
EquipmentID2EnName_fileName = f'EquipmentID2EnName_mapping_{version}.json'
skillId2Name_fileName = f'skillId2Name_mapping_{version}.json'
skillId2Type_fileName = f'skillId2Type_mapping_{version}.json'
Property2Name_fileName = 'Property2Name.json'
RelicId2SetId_fileName = f'RelicId2SetId_mapping_{version}.json'
SetId2Name_fileName = f'SetId2Name_mapping_{version}.json'
rankId2Name_fileName = f'rankId2Name_mapping_{version}.json'


class TS(TypedDict):
    Name: Dict[str, str]
    Icon: Dict[str, str]


with open(MAP / avatarId2Name_fileName, 'r', encoding='UTF-8') as f:
    avatarId2Name = msgjson.decode(f.read(), type=Dict[str, str])

with open(MAP / avatarId2EnName_fileName, 'r', encoding='UTF-8') as f:
    avatarId2EnName = msgjson.decode(f.read(), type=Dict[str, str])

with open(MAP / EquipmentID2Name_fileName, 'r', encoding='UTF-8') as f:
    EquipmentID2Name = msgjson.decode(f.read(), type=Dict[str, str])

with open(MAP / EquipmentID2EnName_fileName, 'r', encoding='UTF-8') as f:
    EquipmentID2EnName = msgjson.decode(f.read(), type=Dict[str, str])

with open(MAP / skillId2Name_fileName, 'r', encoding='UTF-8') as f:
    skillId2Name = msgjson.decode(f.read(), type=Dict[str, str])

with open(MAP / skillId2Type_fileName, 'r', encoding='UTF-8') as f:
    skillId2Type = msgjson.decode(f.read(), type=Dict[str, str])

with open(MAP / Property2Name_fileName, 'r', encoding='UTF-8') as f:
    Property2Name = msgjson.decode(f.read(), type=Dict[str, str])

with open(MAP / RelicId2SetId_fileName, 'r', encoding='UTF-8') as f:
    RelicId2SetId = msgjson.decode(f.read(), type=Dict[str, int])

with open(MAP / SetId2Name_fileName, 'r', encoding='UTF-8') as f:
    SetId2Name = msgjson.decode(f.read(), type=Dict[str, str])

with open(MAP / rankId2Name_fileName, 'r', encoding='UTF-8') as f:
    rankId2Name = msgjson.decode(f.read(), type=Dict[str, str])