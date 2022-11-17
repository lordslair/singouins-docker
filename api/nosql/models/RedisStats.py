# -*- coding: utf8 -*-

import copy
import json

from loguru                     import logger

from nosql.connector            import r

from nosql.metas                import metaRaces
from nosql.models.RedisItem     import RedisItem
from nosql.models.RedisSlots    import RedisSlots


class RedisStats:
    def __init__(self, creature):
        self.creature = creature
        self.hkey     = f'stats:{self.creature.id}'
        self.logh     = f'[Creature.id:{self.creature.id}]'

        if r.exists(self.hkey):
            # The pre-generated stats does already exist in redis
            try:
                hashdict = r.hgetall(self.hkey)
                logger.trace(f'{self.logh} Method >> (HASH Loading)')

                for k, v in hashdict.items():
                    # We create the object attribute with converted INT
                    setattr(self, k, int(v))
                # We need to do that as it is stored as 'hp' due to the Setter
                self._hp   = getattr(self, 'hp')

                logger.trace(f'{self.logh} Method >> (HASH Loaded)')
            except Exception as e:
                logger.error(f'{self.logh} Method KO [{e}]')
            else:
                logger.trace(f'{self.logh} Method OK')

    def destroy(self):
        try:
            logger.trace(f'{self.logh} Method >> (Destroying HASH)')
            r.delete(self.hkey)
        except Exception as e:
            logger.error(f'{self.logh} Method KO [{e}]')
            return None
        else:
            logger.trace(f'{self.logh} Method OK')
            return True

    def new(self, classid):
        logger.trace(f'{self.logh} Method >> (HASH Creating)')

        try:
            metaRace = dict(list(filter(
                lambda x: x["id"] == self.creature.race,
                metaRaces))[0]
                )  # Gruikfix

            # This is base stats
            self.m_race = metaRace['min_m']
            self.r_race = metaRace['min_r']
            self.g_race = metaRace['min_g']
            self.v_race = metaRace['min_v']
            self.p_race = metaRace['min_p']
            self.b_race = metaRace['min_b']

            # This is bonus given by Class
            self.m_class = 0
            self.r_class = 0
            self.g_class = 0
            self.v_class = 0
            self.p_class = 0
            self.b_class = 0

            if classid == '1':
                self.m_class = 10
            if classid == '2':
                self.r_class = 10
            if classid == '3':
                self.g_class = 10
            if classid == '4':
                self.v_class = 10
            if classid == '5':
                self.p_class = 10
            if classid == '6':
                self.b_class = 10

            # We got Creature base stats - Just consolidate
            self.m = self.m_race + self.m_class
            self.r = self.r_race + self.r_class
            self.g = self.g_race + self.g_class
            self.v = self.v_race + self.v_class
            self.p = self.p_race + self.p_class
            self.b = self.b_race + self.b_class

            moymr       = round((self.m + self.r) / 2)
            self.capcom = round((self.g + moymr) / 2)
            moybr       = round((self.b + self.r) / 2)
            self.capsho = round((self.v + moybr) / 2)

            self.hpmax = 100 + self.m + round(self.creature.level / 2)
            self._hp   = self.hpmax
            self.hp    = self.hpmax

            self.dodge = self.r
            newg       = (self.g - 100) / 50
            newm       = (self.m - 100) / 50
            self.parry = round(newg * newm)
        except Exception as e:
            logger.error(f'{self.logh} Method KO '
                         f'(Building from Caracs) [{e}]')
        else:
            logger.trace(f'{self.logh} Method >> (Building from Caracs)')

        # Get the metaWeapons
        if r.exists('system:meta:weapon'):
            metaWeapons = json.loads(r.get('system:meta:weapon'))
            logger.trace(f'{self.logh} Method >> metaWeapons OK')
        else:
            logger.warning(f'{self.logh} Method >> metaWeapons KO')
            return False

        try:
            # Working to find armor from equipped items
            self.arm_b = 0
            self.arm_p = 0
            creature_slots = RedisSlots(self.creature)
            if creature_slots:
                armors = [
                    RedisItem(self.creature).get(creature_slots.feet),
                    RedisItem(self.creature).get(creature_slots.hands),
                    RedisItem(self.creature).get(creature_slots.head),
                    RedisItem(self.creature).get(creature_slots.shoulders),
                    RedisItem(self.creature).get(creature_slots.torso),
                    RedisItem(self.creature).get(creature_slots.legs),
                    ]

                for armor in armors:
                    if armor:
                        result = filter(lambda x: x["id"] == armor.metaid,
                                        metaWeapons)
                        metaWeapon = dict(list(result)[0])  # Gruikfix
                        self.arm_b += metaWeapon['arm_b']
                        self.arm_p += metaWeapon['arm_p']
            else:
                logger.warning(f'{self.logh} Method >> Slots Not Found')
        except Exception as e:
            logger.error(f'{self.logh} Method KO '
                         f'(Building from Equipment) [{e}]')
        else:
            logger.trace(f'{self.logh} Method >> '
                         f'(Building from Equipment)')

        try:
            # We push data in final dict
            logger.trace(f'{self.logh} Method >> (Storing HASH)')
            clone = copy.deepcopy(self)
            if clone.creature:
                del clone.creature
            if clone.hkey:
                del clone.hkey
            if clone.logh:
                del clone.logh
            if clone._hp:
                del clone._hp
            hashdict = clone.__dict__

            r.hset(self.hkey, mapping=hashdict)
        except Exception as e:
            logger.error(f'{self.logh} Method KO (Storing HASH) [{e}]')
        else:
            logger.trace(f'{self.logh} Method OK')
            return self

    def _asdict(self):
        hashdict = {
            "base": {
                "m": self.m,
                "r": self.r,
                "g": self.g,
                "v": self.v,
                "p": self.p,
                "b": self.b
            },
            "off": {
                "capcom": self.capcom,
                "capsho": self.capsho,
            },
            "def": {
                "armor": {
                    "p": self.arm_p,
                    "b": self.arm_b,
                },
                "hpmax": self.hpmax,
                "hp": self._hp,
                "dodge": self.r,
                "parry": self.parry,
            }
        }
        return hashdict

    """
    Getter/Setter block for HP management
    It is done that way to r.hset() every time API code manipulates Creature HP
    And avoid to build a store() method just for that purpose
    As it is the only value that can be directly modified in the RedisStats
    """
    @property
    def hp(self):
        return self._hp

    @hp.setter
    def hp(self, hp):
        self._hp = hp
        try:
            logger.trace(f'{self.logh} Method >> (Setting HASH) HP')
            r.hset(self.hkey, 'hp', self._hp)
        except Exception as e:
            logger.error(f'{self.logh} Method KO [{e}]')
        else:
            logger.trace(f'{self.logh} Method OK')


if __name__ == '__main__':
    from nosql.models.RedisCreature import RedisCreature

    Creature = RedisCreature().get('00000000-cafe-cafe-cafe-000000000000')
    Stats = RedisStats(Creature)
    logger.success(Stats)
    Stats = RedisStats(Creature).new(2)
    logger.success(Stats.hp)
    logger.success(Stats._asdict())
