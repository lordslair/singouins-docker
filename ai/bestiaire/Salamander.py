# -*- coding: utf8 -*-

# from loguru import logger

from bestiaire._Mob import Mob


class Salamander(Mob):
    def __init__(self, creatureuuid: str):
        super(Mob, self).__init__()
        Mob.__init__(self, creatureuuid)

    def run(self):
        while self.creature.hp.current > 0:
            self.get_pa()
            self.get_creature()
            self.status()

            # MOVE
            self.move()

            """
            # BASIC ATTACK
            if self.pa.red > 8 and randint(0, 1):
                # We check if something is nearby
                (closest, coords) = closest_creature_from_creature(self)
                if (self.x - 1 <= closest['x'] <= self.x + 1 and
                        self.y - 1 <= closest['y'] <= self.y + 1):
                    # The closest creature is in range for basic attack
                    logger.debug(f"{self.logh} | Attack >> "
                                 f"([{closest['id']}] {closest['name']} "
                                 f"@({closest['x']},{closest['y']}))")
                    try:
                        payload = resolver_basic_attack(self, closest)
                    except Exception as e:
                        logger.error(f'{self.logh} | Request KO [{e}]')
                    else:
                        if payload['result']['success']:
                            logger.debug(
                                f"{self.logh} | Attack OK "
                                f"([{closest['id']}] {closest['name']} "
                                f"@({closest['x']},{closest['y']}))"
                                )
                        else:
                            logger.warning(
                                f"{self.logh} | Attack KO "
                                f"([{closest['id']}] {closest['name']} "
                                f"@({closest['x']},{closest['y']}))"
                                )
                else:
                    # There is no NPC next to me
                    logger.debug(
                        f"{self.logh} | Cannot not attack "
                        f"(Target too far"
                        f"@({closest['x'], closest['y']}))"
                        )
        """
            self.sleep()
        return

    def attack(self):
        pass

    def hit(self):
        pass
