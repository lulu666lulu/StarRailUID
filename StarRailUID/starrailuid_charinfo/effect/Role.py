import json
from pathlib import Path
from typing import List, Union

from gsuid_core.logger import logger

from .Avatar.Avatar import Avatar
from .Weapon.Weapon import Weapon
from .utils import merge_attribute
from ..mono.Character import Character
from .Base.model import DamageInstance
from .Relic.Relic import RelicSet, SingleRelic

Excel_path = Path(__file__).parent
with Path.open(Excel_path / 'Excel' / 'SkillData.json', encoding='utf-8') as f:
    skill_dict = json.load(f)


class RoleInstance:
    def __init__(self, raw_data: Character):
        self.raw_data = DamageInstance(raw_data)

        self.avatar = Avatar.create(self.raw_data.avatar, self.raw_data.skill)
        self.weapon = Weapon.create(self.raw_data.weapon)
        self.relic_set = RelicSet().create(self.raw_data.relic)

        self.base_attr = self.cal_role_base_attr()
        self.attribute_bonus: dict[str, float] = {}

        self.cal_relic_attr_add()
        self.cal_avatar_attr_add()
        self.cal_avatar_eidolon_add()
        self.cal_weapon_attr_add()

    def cal_role_base_attr(self):
        logger.info('cal_role_base_attr')
        base_attr: dict[str, float] = {}
        avatar_attribute = self.avatar.avatar_attribute
        for attr_name, attr_value in avatar_attribute.items():
            if attr_name in base_attr:
                base_attr[attr_name] += attr_value
            else:
                base_attr[attr_name] = attr_value

        weapon_attribute = self.weapon.weapon_base_attribute
        for attr_name, attr_value in weapon_attribute.items():
            if attr_name in base_attr:
                base_attr[attr_name] += attr_value
            else:
                base_attr[attr_name] = attr_value
        return base_attr

    def cal_relic_attr_add(self):
        # 单件属性
        for relic_type in self.relic_set.__dict__:
            if type(self.relic_set.__dict__[relic_type]) == SingleRelic:
                relic: SingleRelic = self.relic_set.__dict__[relic_type]
                for attribute in relic.relic_attribute_bonus:
                    if attribute in self.attribute_bonus:
                        self.attribute_bonus[
                            attribute
                        ] += relic.relic_attribute_bonus[attribute]
                    else:
                        self.attribute_bonus[
                            attribute
                        ] = relic.relic_attribute_bonus[attribute]

        # 套装面板加成属性
        for set_skill in self.relic_set.SetSkill:
            for attribute in set_skill.relicSetAttribute:
                if attribute in self.attribute_bonus:
                    self.attribute_bonus[
                        attribute
                    ] += set_skill.relicSetAttribute[attribute]
                else:
                    self.attribute_bonus[
                        attribute
                    ] = set_skill.relicSetAttribute[attribute]

    def cal_avatar_attr_add(self):
        attribute_bonus = self.avatar.avatar_attribute_bonus
        if attribute_bonus:
            for bonus in attribute_bonus:
                status_add = bonus.statusAdd
                bonus_property = status_add.property
                value = status_add.value
                if bonus_property in self.attribute_bonus:
                    self.attribute_bonus[bonus_property] += value
                else:
                    self.attribute_bonus[bonus_property] = value

    def cal_avatar_eidolon_add(self):
        for attribute in self.avatar.eidolon_attribute:
            if attribute in self.attribute_bonus:
                self.attribute_bonus[
                    attribute
                ] += self.avatar.eidolon_attribute[attribute]
            else:
                self.attribute_bonus[
                    attribute
                ] = self.avatar.eidolon_attribute[attribute]
        for attribute in self.avatar.extra_ability_attribute:
            if attribute in self.attribute_bonus:
                self.attribute_bonus[
                    attribute
                ] += self.avatar.extra_ability_attribute[attribute]
            else:
                self.attribute_bonus[
                    attribute
                ] = self.avatar.extra_ability_attribute[attribute]

    def cal_weapon_attr_add(self):
        for attribute in self.weapon.weapon_attribute:
            if attribute in self.attribute_bonus:
                self.attribute_bonus[
                    attribute
                ] += self.weapon.weapon_attribute[attribute]
            else:
                self.attribute_bonus[attribute] = self.weapon.weapon_attribute[
                    attribute
                ]

    async def cal_damage(self, skill_type: str):
        logger.info('base_attr')
        logger.info(self.base_attr)
        logger.info('attribute_bonus')
        logger.info(self.attribute_bonus)
        logger.info(skill_type)
        # 技能区
        skill_info = self.avatar.Skill_Info(skill_type)
        skill_multiplier = self.avatar.Skill_num(skill_info[4], skill_type)
        # 检查是否有对某一个技能的倍率加成
        for attr in self.attribute_bonus:
            if attr.__contains__('SkillAdd'):
                skill_name = attr.split('SkillAdd')[0]
                if skill_name in (skill_type, skill_info[3]):
                    logger.info(
                        f'{skill_name}对{skill_type}有{self.attribute_bonus[attr]}倍率加成'
                    )
                    skill_multiplier = (
                        skill_multiplier + self.attribute_bonus[attr]
                    )

        logger.info(f'技能区总: {skill_multiplier}')

        # 检查武器战斗生效的buff
        logger.info('检查武器战斗生效的buff')
        Ultra_Use = self.avatar.Ultra_Use()
        logger.info('Ultra_Use')
        logger.info(Ultra_Use)
        self.attribute_bonus = await self.weapon.weapon_ability(
            Ultra_Use, self.base_attr, self.attribute_bonus
        )
        logger.info(self.attribute_bonus)
        logger.info('检查遗器套装战斗生效的buff')
        for set_skill in self.relic_set.SetSkill:
            self.attribute_bonus = await set_skill.set_skill_ability(
                self.base_attr, self.attribute_bonus
            )
        if self.attribute_bonus is None:
            raise Exception('attribute_bonus is None')
        logger.info(self.attribute_bonus)

        # 检查是否有对某一个技能的属性加成
        logger.info('检查是否有对某一个技能的属性加成')
        for attr in self.attribute_bonus:
            # 攻击加成
            if attr.__contains__('AttackAddedRatio'):
                attr_name = attr.split('AttackAddedRatio')[0]
                if attr_name in (skill_type, skill_info[3]):
                    attack_added_ratio = self.attribute_bonus.get(
                        'AttackAddedRatio', 0
                    )
                    self.attribute_bonus['AttackAddedRatio'] = (
                        attack_added_ratio + self.attribute_bonus[attr]
                    )
            # 效果命中加成
            if attr.__contains__('StatusProbabilityBase'):
                attr_name = attr.split('StatusProbabilityBase')[0]
                if attr_name in (skill_type, skill_info[3]):
                    status_probability = self.attribute_bonus.get(
                        'StatusProbabilityBase', 0
                    )
                    self.attribute_bonus['StatusProbabilityBase'] = (
                        status_probability + self.attribute_bonus[attr]
                    )

        merged_attr = await merge_attribute(
            self.base_attr, self.attribute_bonus
        )
        logger.info(f'{merged_attr}')
        skill_info_list = []
        # 技能类型为攻击
        if skill_info[0] == 'attack':
            if isinstance(skill_info[2], str):
                raise Exception('skill_info[2] is str')
            skill_multiplier = skill_multiplier / skill_info[2]
            logger.info(f'技能区单段: {skill_multiplier}')
            if self.raw_data.avatar.id_ == 1004:
                if self.raw_data.avatar.rank >= 6 and skill_type == 'BPSkill':
                    skill_info[2] = skill_info[2] + 1
                multiplier_add = self.avatar.Talent()
                skill_multiplier = skill_multiplier + multiplier_add

            if (
                self.raw_data.avatar.id_ == 1201
                and self.raw_data.avatar.rank >= 4
                and skill_type == 'Normal'
            ):
                skill_info[2] = skill_info[2] + 1

            attack = merged_attr.get('attack', 0)
            if self.raw_data.avatar.id_ == 1104:
                # 杰帕德天赋加攻
                defence = merged_attr['defence']
                attack = attack + (defence * 0.35)
            logger.info(f'攻击力: {attack}')
            damage_add = 0
            hp_multiplier = 0
            hp_num = 0
            if self.raw_data.avatar.id_ in [1205, 1208]:
                hp_num = merged_attr['hp']
                skill_type_hp = skill_type + '_HP'
                if skill_type_hp in skill_dict[str(self.raw_data.avatar.id_)]:
                    hp_multiplier = self.avatar.Skill_num(
                        skill_info[4], skill_type_hp
                    )
                else:
                    hp_multiplier = 0
                for attr in self.attribute_bonus:
                    if attr.__contains__('HpSkillAdd'):
                        skill_name = attr.split('HpSkillAdd')[0]
                        if skill_name in (skill_type, skill_info[3]):
                            logger.info(
                                f'{skill_name}对{skill_type}有{self.attribute_bonus[attr]}倍率加成'
                            )
                            hp_multiplier = (
                                hp_multiplier + self.attribute_bonus[attr]
                            )

                if skill_type == 'Talent':
                    if (
                        self.raw_data.avatar.rank >= 6
                        and self.raw_data.avatar.id_ == 1205
                    ):
                        damage_add = hp_num * 0.5
                attack = (skill_multiplier * attack) + (hp_multiplier * hp_num)
                skill_multiplier = 1
                logger.info(f'混伤区: {attack}')

            logger.info(f'额外伤害: {damage_add}')
            # 模拟 同属性弱点 同等级 的怪物
            # 韧性条减伤
            enemy_damage_reduction = 0.1
            damage_reduction = 1 - enemy_damage_reduction
            logger.info(f'韧性区: {damage_reduction}')
            # 抗性区
            enemy_status_resistance = 0.0
            for attr in merged_attr:
                if attr.__contains__('ResistancePenetration'):
                    # 检查是否有某一属性的抗性穿透
                    attr_name = attr.split('ResistancePenetration')[0]
                    if attr_name in (self.avatar.avatar_element, 'AllDamage'):
                        logger.info(f'{attr_name}属性有{merged_attr[attr]}穿透加成')
                        enemy_status_resistance += merged_attr[attr]
                    # 检查是否有某一技能属性的抗性穿透
                    if attr_name.__contains__('_'):
                        skill_name = attr_name.split('_')[0]
                        skillattr_name = attr_name.split('_')[1]
                        if skill_name in (
                            skill_type,
                            skill_info[3],
                        ) and skillattr_name in (
                            self.avatar.avatar_element,
                            'AllDamage',
                        ):
                            enemy_status_resistance += merged_attr[attr]
                            logger.info(
                                f'{skill_name}对{skillattr_name}属性有{merged_attr[attr]}穿透加成'
                            )
            resistance_area = 1.0 - (0 - enemy_status_resistance)
            logger.info(f'抗性区: {resistance_area}')

            # 防御区
            # 检查是否有 ignore_defence
            logger.info('检查是否有 ignore_defence')
            ignore_defence = 1.0
            for attr in merged_attr:
                if attr == 'ignore_defence':
                    ignore_defence = 1 - merged_attr[attr]
                    break
            logger.info(f'ignore_defence {ignore_defence}')
            enemy_defence = (
                self.avatar.avatar_level * 10 + 200
            ) * ignore_defence
            defence_multiplier = (self.avatar.avatar_level * 10 + 200) / (
                self.avatar.avatar_level * 10 + 200 + enemy_defence
            )
            logger.info(f'防御区: {defence_multiplier}')

            # 增伤区
            # TODO: 这里计算只考虑了希儿,需要重写 injury_area = self.avatar.Talent_add()
            injury_area = self.avatar.Talent_add()
            # 检查是否有对某一个技能的伤害加成
            logger.info('检查是否有对某一个技能的伤害加成')
            for attr in merged_attr:
                if attr.__contains__('DmgAdd'):
                    attr_name = attr.split('DmgAdd')[0]
                    if attr_name in (skill_type, skill_info[3]):
                        logger.info(
                            f'{attr} 对 {skill_type} 有 {merged_attr[attr]} 伤害加成'
                        )
                        injury_area += merged_attr[attr]
            # 检查有无符合属性的伤害加成
            logger.info('检查球有无符合属性的伤害加成')
            element_area = 0
            for attr in merged_attr:
                if attr.__contains__('AddedRatio'):
                    attr_name = attr.split('AddedRatio')[0]
                    if attr_name in (self.avatar.avatar_element, 'AllDamage'):
                        logger.info(
                            f'{attr} 对 {self.avatar.avatar_element} '
                            f'有 {merged_attr[attr]} 伤害加成'
                        )
                        if attr_name == self.avatar.avatar_element:
                            element_area += merged_attr[attr]
                        injury_area += merged_attr[attr]
            injury_area += 1
            logger.info(f'增伤区: {injury_area}')

            # 易伤区
            logger.info('检查是否有易伤加成')
            damage_ratio = merged_attr.get('DmgRatio', 0)
            # 检查是否有对特定技能的易伤加成
            # Talent_DmgRatio
            for attr in merged_attr:
                if attr.__contains__('_DmgRatio'):
                    skill_name = attr.split('_')[0]
                    if skill_name in (skill_type, skill_info[3]):
                        logger.info(
                            f'{attr} 对 {skill_type} 有 {merged_attr[attr]} 易伤加成'
                        )
                        damage_ratio += merged_attr[attr]
            damage_ratio = damage_ratio + 1
            logger.info(f'易伤: {damage_ratio}')

            # 爆伤区
            if skill_type == 'DOT':
                critical_damage_base = 0.0
            else:
                logger.info('检查是否有爆伤加成')
                logger.info(f'{merged_attr}')
                critical_damage_base = merged_attr.get('CriticalDamageBase', 0)
                # 检查是否有对特定技能的爆伤加成
                # Ultra_CriticalChance
                for attr in merged_attr:
                    if attr.__contains__('_CriticalDamageBase'):
                        skill_name = attr.split('_')[0]
                        if skill_name in (skill_type, skill_info[3]):
                            logger.info(
                                f'{attr} 对 {skill_type} 有 '
                                f'{merged_attr[attr]} 爆伤加成'
                            )
                            critical_damage_base += merged_attr[attr]
            critical_damage = critical_damage_base + 1
            logger.info(f'暴伤: {critical_damage}')

            # 暴击区
            logger.info('检查是否有暴击加成')
            critical_chance_base = merged_attr['CriticalChanceBase']
            # 检查是否有对特定技能的爆伤加成
            # Ultra_CriticalChance
            for attr in merged_attr:
                if attr.__contains__('_CriticalChance'):
                    skill_name = attr.split('_')[0]
                    if skill_name in (skill_type, skill_info[3]):
                        logger.info(
                            f'{attr} 对 {skill_type} 有 '
                            f'{merged_attr[attr]} 暴击加成'
                        )
                        critical_chance_base += merged_attr[attr]
            critical_chance_base = min(1, critical_chance_base)
            logger.info(f'暴击: {critical_chance_base}')

            # 期望伤害
            qiwang_damage = (critical_chance_base * critical_damage_base) + 1
            logger.info(f'暴击期望: {qiwang_damage}')
            damage_cd_z = 0.0
            damage_qw_z = 0.0
            damage_tz_z = 0.0
            attack_tz = 0.0
            injury_add = 0.0
            critical_damage_add = 0
            for i in range(1, skill_info[2] + 1):
                injury_add = 0
                critical_damage_add = 0
                if self.raw_data.avatar.id_ == 1213:
                    injury_add = self.avatar.Talent()
                    critical_damage_add = self.avatar.BPSkill()
                    normal_buff = merged_attr.get('Normal_buff', 0)
                    if i >= 4:
                        normal_buff = min(4, int(normal_buff + (i - 3)))
                    if normal_buff >= 1:
                        critical_damage_add = normal_buff * critical_damage_add
                    atk_buff = merged_attr.get('Atk_buff', 0)
                    atk_buff = min(10, int((i - 1) * (atk_buff + 1)))
                    injury_add = atk_buff * injury_add
                    qiwang_damage = (
                        critical_chance_base
                        * (critical_damage_base + critical_damage_add)
                    ) + 1

                damage_cd = (
                    attack
                    * skill_multiplier
                    * damage_ratio
                    * (injury_area + injury_add)
                    * defence_multiplier
                    * resistance_area
                    * damage_reduction
                    * (critical_damage + critical_damage_add)
                    + damage_add
                )
                damage_cd_z += damage_cd
                damage_qw = (
                    attack
                    * skill_multiplier
                    * damage_ratio
                    * (injury_area + injury_add)
                    * defence_multiplier
                    * resistance_area
                    * damage_reduction
                    * qiwang_damage
                    + damage_add
                )
                damage_qw_z += damage_qw

                attr_value_tz: float = self.base_attr.get('attack', 0)
                attribute_atk = self.attribute_bonus.get('AttackDelta', 0)
                attack_tz = (
                    attr_value_tz
                    + attr_value_tz
                    * (
                        1
                        + self.attribute_bonus.get('AttackAddedRatio', 0)
                        + 2.144
                    )
                    + attribute_atk
                )
                if self.raw_data.avatar.id_ in [1205, 1208]:
                    attack_tz = (skill_multiplier * attack_tz) + (
                        hp_multiplier * hp_num
                    )
                injury_add_tz = 0
                if self.avatar.avatar_element == 'Imaginary':
                    injury_add_tz = 0.12
                damage_tz = (
                    attack_tz
                    * skill_multiplier
                    * damage_ratio
                    * (injury_area + injury_add + injury_add_tz + 2.326)
                    * defence_multiplier
                    * resistance_area
                    * damage_reduction
                    * (critical_damage + critical_damage_add + 1.594)
                    * 10
                    + damage_add
                )

                damage_tz_z += damage_tz

            if (
                self.raw_data.avatar.id_ == 1003
                and self.raw_data.avatar.rank >= 6
            ):
                damage_cd_z = damage_cd_z * 1.8
                damage_qw_z = damage_qw_z * 1.8
                damage_tz_z = damage_tz_z * 1.8

            if self.avatar.avatar_element == 'Thunder':
                element_area = 0
            damage_tz_fj = (
                attack_tz
                * 0.44
                * damage_ratio
                * (injury_area + injury_add + 2.326 + element_area)
                * defence_multiplier
                * resistance_area
                * damage_reduction
                * (critical_damage + critical_damage_add + 1.594)
                * 10
            )
            damage_tz_z += damage_tz_fj
            skill_info_list: List[Union[str, float]] = []
            skill_info_list.append(skill_info[1])
            skill_info_list.append(damage_cd_z)
            skill_info_list.append(damage_qw_z)
            skill_info_list.append(damage_tz_z)
            logger.info(
                f'{skill_info[1]} 暴击伤害: {damage_cd_z} 期望伤害{damage_qw_z}'
            )

        # 技能类型为防御
        if skill_info[0] == 'defence':
            defence = merged_attr['defence']
            logger.info(f'防御力: {defence}')
            defence_multiplier = 0

            # 获取技能提供的固定护盾值
            if skill_type == 'Normal':
                defence_multiplier = self.avatar.Normalnum('Normal_G')
            elif skill_type == 'BPSkill':
                defence_multiplier = self.avatar.BPSkill_num('BPSkill_G')
            elif skill_type == 'Ultra':
                defence_multiplier = self.avatar.Ultra_num('Ultra_G')
            elif skill_type == 'Talent':
                defence_multiplier = self.avatar.Talent_num('Talent_G')

            # 检查是否有护盾加成
            shield_added_ratio = merged_attr.get('shield_added_ratio', 0)
            shield_added = shield_added_ratio + 1
            logger.info(f'护盾加成: {shield_added}')

            defence_num = (
                defence * skill_multiplier + defence_multiplier
            ) * shield_added

            skill_info_list: List[Union[str, float]] = []
            skill_info_list.append(skill_info[1])
            skill_info_list.append(defence_num)
            skill_info_list.append(defence_num)
            skill_info_list.append(defence_num)

        return skill_info_list
