# -*- coding: utf8 -*-

import json

from flask                      import jsonify
from flask_jwt_extended         import (jwt_required,
                                        get_jwt_identity)
from loguru                     import logger

from nosql.models.RedisCreature import RedisCreature
from nosql.models.RedisSquad    import RedisSquad
from nosql.models.RedisUser     import RedisUser
from nosql.queue                import yqueue_put


#
# Routes /mypc/{pcid}/squad
#
# API: POST /mypc/<uuid:pcid>/squad/<uuid:squadid>/accept
@jwt_required()
def squad_accept(pcid, squadid):
    Creature = RedisCreature().get(pcid)
    User = RedisUser().get(get_jwt_identity())
    # We need to convert instanceid to STR as it is UUID type
    squadid = str(squadid)

    # Pre-flight checks
    if Creature is None:
        msg = '[Creature.id:None] Creature NotFound'
        logger.warning(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 200
    else:
        h = f'[Creature.id:{Creature.id}]'  # Header for logging
    if Creature.account != User.id:
        msg = (f'{h} Token/username mismatch (username:{User.name})')
        logger.warning(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 409

    if Creature.squad != squadid:
        msg = f'{h} Squad request outside of your scope (squadid:{squadid})'
        logger.warning(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 200
    if Creature.squad_rank != 'Pending':
        msg = f'{h} Squad pending is required (squadid:{squadid})'
        logger.warning(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 200

    try:
        Creature.squad = None
        Creature.squad_rank = 'Member'
    except Exception as e:
        msg = f'{h} Squad Query KO (squadid:{squadid}) [{e}]'
        logger.error(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 200
    else:
        try:
            Squad = RedisSquad().get(squadid)
        except Exception as e:
            msg = f'{h} Squad Query KO (squadid:{squadid}) [{e}]'
            logger.error(msg)
            return jsonify(
                {
                    "success": False,
                    "msg": msg,
                    "payload": None,
                }
            ), 200
        else:
            # We put the info in queue for ws
            qmsg = {"ciphered": False,
                    "payload": (f':information_source: '
                                f'**{Creature.name}** '
                                f'joined this Squad'),
                    "embed": None,
                    "scope": f'Squad-{Creature.squad}'}
            yqueue_put('yarqueue:discord', qmsg)
            # We put the info in queue for ws Front
            qmsg = {"ciphered": False,
                    "payload": Squad._asdict(),
                    "route": 'mypc/{id1}/squad',
                    "scope": 'squad'}
            yqueue_put('broadcast', json.loads(jsonify(qmsg).get_data()))

            msg = f'{h} Squad accept OK (squadid:{squadid})'
            logger.debug(msg)
            return jsonify(
                {
                    "success": True,
                    "msg": msg,
                    "payload": Squad._asdict(),
                }
            ), 200


# API: POST /mypc/<uuid:pcid>/squad
@jwt_required()
def squad_create(pcid):
    Creature = RedisCreature().get(pcid)
    User = RedisUser().get(get_jwt_identity())

    # Pre-flight checks
    if Creature is None:
        msg = '[Creature.id:None] Creature NotFound'
        logger.warning(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 200
    else:
        h = f'[Creature.id:{Creature.id}]'  # Header for logging
    if Creature.account != User.id:
        msg = (f'{h} Token/username mismatch (username:{User.name})')
        logger.warning(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 409

    if Creature.squad is not None:
        msg = f'{h} PC already in a Squad (squadid:{Creature.squad})'
        logger.warning(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 200

    try:
        Squad = RedisSquad().new(Creature)
    except Exception as e:
        msg = f'{h} Squad Query KO [{e}]'
        logger.error(msg)
        return jsonify({"success": False,
                        "msg": msg,
                        "payload": None}), 200
    else:
        if Squad is False:
            msg = f'{h} Squad Query KO - Already exists'
            logger.warning(msg)
            return jsonify(
                {
                    "success": False,
                    "msg": msg,
                    "payload": None,
                }
            ), 200

    # Squad created, let's assign the team creator in the squad
    try:
        Creature.squad = Squad.id
        Creature.squad_rank = 'Leader'
    except Exception as e:
        msg = f'{h} Squad Query KO (squadid:{Squad.id}) [{e}]'
        logger.error(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 200
    else:
        # We put the info in queue for ws
        qmsg = {"ciphered": False,
                "payload": (f':information_source: '
                            f'**{Creature.name}** '
                            f'created this Squad'),
                "embed": None,
                "scope": f'Squad-{Creature.squad}'}
        yqueue_put('yarqueue:discord', qmsg)
        # We put the info in queue for ws Front
        qmsg = {"ciphered": False,
                "payload": Squad._asdict(),
                "route": 'mypc/{id1}/squad',
                "scope": 'squad'}
        yqueue_put('broadcast', json.loads(jsonify(qmsg).get_data()))

        msg = f'{h} Squad create OK (squadid:{Creature.squad})'
        logger.debug(msg)
        return jsonify(
            {
                "success": True,
                "msg": msg,
                "payload": Squad._asdict(),
            }
        ), 201


# API: POST /mypc/<uuid:pcid>/squad/<uuid:squadid>/decline
@jwt_required()
def squad_decline(pcid, squadid):
    Creature = RedisCreature().get(pcid)
    User = RedisUser().get(get_jwt_identity())
    # We need to convert instanceid to STR as it is UUID type
    squadid = str(squadid)

    # Pre-flight checks
    if Creature is None:
        msg = '[Creature.id:None] Creature NotFound'
        logger.warning(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 200
    else:
        h = f'[Creature.id:{Creature.id}]'  # Header for logging
    if Creature.account != User.id:
        msg = (f'{h} Token/username mismatch (username:{User.name})')
        logger.warning(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 409

    if Creature.squad != squadid:
        msg = f'{h} Squad request outside of your scope (squadid:{squadid})'
        logger.warning(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 200
    if Creature.squad_rank == 'Leader':
        msg = f'{h} PC cannot be the squad Leader (squadid:{squadid})'
        logger.warning(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 200

    try:
        Creature.squad_rank = None
        Creature.squad = None
    except Exception as e:
        msg = f'{h} Squad Query KO (squadid:{squadid}) [{e}]'
        logger.error(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 200
    else:
        try:
            Squad = RedisSquad().get(squadid)
        except Exception as e:
            msg = f'{h} Squad Query KO (squadid:{squadid}) [{e}]'
            logger.error(msg)
            return jsonify(
                {
                    "success": False,
                    "msg": msg,
                    "payload": None,
                }
            ), 200
        else:
            # We put the info in queue for ws
            qname = 'yarqueue:discord'
            qmsg  = {"ciphered": False,
                     "payload": (f':information_source: '
                                 f'**{Creature.name}** '
                                 f'declined this Squad'),
                     "embed": None,
                     "scope": f'Squad-{squadid}'}
            logger.trace(f'{qname}:{qmsg}')
            yqueue_put('yarqueue:discord', qmsg)
            # We put the info in queue for ws Front
            qname = 'broadcast'
            qmsg = {"ciphered": False,
                    "payload": Squad._asdict(),
                    "route": 'mypc/{id1}/squad',
                    "scope": 'squad'}
            logger.trace(f'{qname}:{qmsg}')
            yqueue_put('broadcast', json.loads(jsonify(qmsg).get_data()))

            msg = f'{h} Squad decline OK (squadid:{squadid})'
            logger.debug(msg)
            return jsonify(
                {
                    "success": True,
                    "msg": msg,
                    "payload": Squad._asdict(),
                }
            ), 200


# API: DELETE /mypc/<uuid:pcid>/squad/<uuid:squadid>
@jwt_required()
def squad_delete(pcid, squadid):
    Creature = RedisCreature().get(pcid)
    User = RedisUser().get(get_jwt_identity())
    # We need to convert instanceid to STR as it is UUID type
    squadid = str(squadid)

    # Pre-flight checks
    if Creature is None:
        msg = '[Creature.id:None] Creature NotFound'
        logger.warning(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 200
    else:
        h = f'[Creature.id:{Creature.id}]'  # Header for logging
    if Creature.account != User.id:
        msg = (f'{h} Token/username mismatch (username:{User.name})')
        logger.warning(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 409

    if Creature.squad != squadid:
        msg = f'{h} Squad request outside of your scope (squadid:{squadid})'
        logger.warning(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 200
    if Creature.squad_rank != 'Leader':
        msg = f'{h} PC is not the squad Leader (squadid:{Creature.squad_rank})'
        logger.warning(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 200

    try:
        squad = Creature.squad.replace('-', ' ')
        Members = RedisCreature().search(f"@squad:{squad}")
    except Exception as e:
        msg = f'Creature Query KO (squadid:{squadid}) [{e}]'
        logger.error(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 200

    count = len(Members)
    if count > 1:
        msg = f'Squad not empty (squadid:{squadid},members:{count})'
        logger.error(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 200

    try:
        RedisSquad().destroy(squadid)
        Creature.squad = None
        Creature.squad_rank = None
    except Exception as e:
        msg = f'Squad Query KO (squadid:{squadid}) [{e}]'
        logger.error(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 200
    else:
        # We put the info in queue for ws
        qmsg = {"ciphered": False,
                "payload": (f':information_source: '
                            f'**{Creature.name}** '
                            f'deleted this Squad'),
                "embed": None,
                "scope": f'Squad-{squadid}'}
        yqueue_put('yarqueue:discord', qmsg)
        # We put the info in queue for ws Front
        qmsg = {"ciphered": False,
                "payload": None,
                "route": 'mypc/{id1}/squad',
                "scope": 'squad'}
        yqueue_put('broadcast', qmsg)

        msg = f'{h} Squad delete OK (squadid:{squadid})'
        logger.debug(msg)
        return jsonify(
            {
                "success": True,
                "msg": msg,
                "payload": None,
            }
        ), 200


# API: GET /mypc/{pcid}/squad/{squadid}
@jwt_required()
def squad_get_one(pcid, squadid):
    Creature = RedisCreature().get(pcid)
    User = RedisUser().get(get_jwt_identity())
    # We need to convert instanceid to STR as it is UUID type
    squadid = str(squadid)

    # Pre-flight checks
    if Creature is None:
        msg = '[Creature.id:None] Creature NotFound'
        logger.warning(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 200
    else:
        h = f'[Creature.id:{Creature.id}]'  # Header for logging
    if Creature.account != User.id:
        msg = (f'{h} Token/username mismatch (username:{User.name})')
        logger.warning(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 409

    if Creature.squad != squadid:
        msg = f'{h} Squad request outside of your scope (squadid:{squadid})'
        logger.warning(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 200

    try:
        Squad = RedisSquad().get(squadid)
        squad = Creature.squad.replace('-', ' ')
        SquadMembers = RedisCreature().search(
            f"(@squad:{squad}) & (@squad_rank:-Pending)"
            )
        SquadPending = RedisCreature().search(
            f"(@squad:{squad}) & (@squad_rank:Pending)"
            )
    except Exception as e:
        msg = f'Squad Query KO (squadid:{squadid}) [{e}]'
        logger.error(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 200
    else:
        if Squad:
            msg = f'{h} Squad Query OK (squadid:{squadid})'
            logger.debug(msg)
            return jsonify(
                {
                    "success": True,
                    "msg": msg,
                    "payload": {
                        "members": SquadMembers,
                        "pending": SquadPending,
                        "squad": Squad._asdict(),
                        }
                }
            ), 200
        elif Squad is False:
            msg = f'{h} Squad Query KO - Not Found (squadid:{squadid})'
            logger.warning(msg)
            return jsonify(
                {
                    "success": False,
                    "msg": msg,
                    "payload": None,
                }
            ), 200
        else:
            msg = f'{h} Squad Query KO - Failed (squadid:{squadid})'
            logger.warning(msg)
            return jsonify(
                {
                    "success": False,
                    "msg": msg,
                    "payload": None,
                }
            ), 200


# API: POST /mypc/<uuid:pcid>/squad/<uuid:squadid>/invite/<int:targetid>
@jwt_required()
def squad_invite(pcid, squadid, targetid):
    Creature = RedisCreature().get(pcid)
    CreatureTarget = RedisCreature().get(targetid)
    User = RedisUser().get(get_jwt_identity())
    # We need to convert instanceid to STR as it is UUID type
    squadid = str(squadid)

    # Pre-flight checks
    if Creature is None:
        msg = '[Creature.id:None] Creature NotFound'
        logger.warning(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 200
    else:
        h = f'[Creature.id:{Creature.id}]'  # Header for logging
    if Creature.account != User.id:
        msg = (f'{h} Token/username mismatch (username:{User.name})')
        logger.warning(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 409

    if Creature.squad != squadid:
        msg = f'{h} Squad request outside of your scope (squadid:{squadid})'
        logger.warning(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 200
    if Creature.squad_rank != 'Leader':
        msg = f'{h} PC should be the squad Leader (squadid:{squadid})'
        logger.warning(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 200
    if CreatureTarget.squad is not None:
        msg = (
            f'{h} Already in Squad '
            f'(pcid:{CreatureTarget.id},squadid:{CreatureTarget.squad})'
            )
        logger.warning(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 200

    # Squad population check
    try:
        squad = Creature.squad.replace('-', ' ')
        Members = RedisCreature().search(f"@squad:{squad}")
    except Exception as e:
        msg = f'{h} Squad Query KO (squadid:{squadid}) [{e}]'
        logger.error(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 200

    count      = len(Members)
    maxmembers = 100
    if count == maxmembers:
        members = f'{count}/{maxmembers}'
        msg = f'{h} Squad Full (squadid:{squadid},members:{members})'
        logger.error(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 200

    try:
        CreatureTarget.squad = squadid
        CreatureTarget.squad_rank = 'Pending'
    except Exception as e:
        msg = f'{h} Squad Query KO (squadid:{squadid}) [{e}]'
        logger.error(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 200
    else:
        try:
            Squad = RedisSquad().get(squadid)
        except Exception as e:
            msg = f'{h} Squad Query KO (squadid:{squadid}) [{e}]'
            logger.error(msg)
            return jsonify(
                {
                    "success": False,
                    "msg": msg,
                    "payload": None,
                }
            ), 200
        else:
            # We put the info in queue for ws
            qmsg = {"ciphered": False,
                    "payload": (f':information_source: '
                                f'**{Creature.name}** '
                                f'invited '
                                f'**{CreatureTarget.name}** '
                                f'in this Squad'),
                    "embed": None,
                    "scope": f'Squad-{Creature.squad}'}
            yqueue_put('yarqueue:discord', qmsg)
            # We put the info in queue for ws Front
            qmsg = {"ciphered": False,
                    "payload": Squad._asdict(),
                    "route": 'mypc/{id1}/squad',
                    "scope": 'squad'}
            yqueue_put('broadcast', json.loads(jsonify(qmsg).get_data()))

            msg = f'{h} Squad invite OK (squadid:{squadid})'
            logger.debug(msg)
            return jsonify(
                {
                    "success": True,
                    "msg": msg,
                    "payload": Squad._asdict(),
                }
            ), 200


# API: POST /mypc/<uuid:pcid>/squad/<uuid:squadid>/kick/<int:targetid>
@jwt_required()
def squad_kick(pcid, squadid, targetid):
    Creature = RedisCreature().get(pcid)
    CreatureTarget = RedisCreature().get(targetid)
    User = RedisUser().get(get_jwt_identity())
    # We need to convert instanceid to STR as it is UUID type
    squadid = str(squadid)

    # Pre-flight checks
    if Creature is None:
        msg = '[Creature.id:None] Creature NotFound'
        logger.warning(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 200
    else:
        h = f'[Creature.id:{Creature.id}]'  # Header for logging
    if Creature.account != User.id:
        msg = (f'{h} Token/username mismatch (username:{User.name})')
        logger.warning(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 409

    if Creature.squad != squadid:
        msg = f'{h} Squad request outside of your scope (squadid:{squadid})'
        logger.warning(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 200
    if Creature.squad_rank != 'Leader':
        msg = f'{h} PC should be the squad Leader (squadid:{squadid})'
        logger.warning(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 200
    if CreatureTarget.squad is None:
        msg = f'{h} Should be in Squad (squadid:{CreatureTarget.squad})'
        logger.warning(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 200
    if CreatureTarget.id == Creature.id:
        msg = f'{h} Cannot kick yourself (squadid:{CreatureTarget.squad})'
        logger.warning(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 200

    try:
        CreatureTarget.squad = None
        CreatureTarget.squad_rank = None
    except Exception as e:
        msg = f'{h} Squad Query KO (squadid:{squadid}) [{e}]'
        logger.error(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 200
    else:
        try:
            Squad = RedisSquad().get(squadid)
        except Exception as e:
            msg = f'{h} Squad Query KO (squadid:{squadid}) [{e}]'
            logger.error(msg)
            return jsonify(
                {
                    "success": False,
                    "msg": msg,
                    "payload": None,
                }
            ), 200
        else:
            # We put the info in queue for ws Discord
            qmsg = {"ciphered": False,
                    "payload": (f':information_source: '
                                f'**{Creature.name}** '
                                f'kicked '
                                f'**{CreatureTarget.name}** '
                                f'from this Squad'),
                    "embed": None,
                    "scope": f'Squad-{Creature.squad}'}
            yqueue_put('yarqueue:discord', qmsg)
            # We put the info in queue for ws Front
            qmsg = {"ciphered": False,
                    "payload": Squad._asdict(),
                    "route": 'mypc/{id1}/squad',
                    "scope": 'squad'}
            yqueue_put('broadcast', json.loads(jsonify(qmsg).get_data()))

            msg = f'{h} Squad kick OK (squadid:{squadid})'
            logger.debug(msg)
            return jsonify(
                {
                    "success": True,
                    "msg": msg,
                    "payload": Squad._asdict(),
                }
            ), 200


# API: /mypc/<uuid:pcid>/squad/<uuid:squadid>/leave
@jwt_required()
def squad_leave(pcid, squadid):
    Creature = RedisCreature().get(pcid)
    User = RedisUser().get(get_jwt_identity())
    # We need to convert instanceid to STR as it is UUID type
    squadid = str(squadid)

    # Pre-flight checks
    if Creature is None:
        msg = '[Creature.id:None] Creature NotFound'
        logger.warning(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 200
    else:
        h = f'[Creature.id:{Creature.id}]'  # Header for logging
    if Creature.account != User.id:
        msg = (f'{h} Token/username mismatch (username:{User.name})')
        logger.warning(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 409

    if Creature.squad != squadid:
        msg = f'{h} Squad request outside of your scope (squadid:{squadid})'
        logger.warning(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 200
    if Creature.squad_rank == 'Leader':
        msg = f'{h} PC cannot be the squad Leader (squadid:{squadid})'
        logger.warning(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 200

    try:
        Creature.squad = None
        Creature.squad_rank = None
    except Exception as e:
        msg = f'{h} Squad Query KO (squadid:{squadid}) [{e}]'
        logger.error(msg)
        return jsonify(
            {
                "success": False,
                "msg": msg,
                "payload": None,
            }
        ), 200
    else:
        try:
            Squad = RedisSquad().get(squadid)
        except Exception as e:
            msg = f'{h} Squad Query KO (squadid:{squadid}) [{e}]'
            logger.error(msg)
            return jsonify(
                {
                    "success": False,
                    "msg": msg,
                    "payload": None,
                }
            ), 200
        else:
            # We put the info in queue for ws
            qmsg = {"ciphered": False,
                    "payload": (f':information_source: '
                                f'**{Creature.name}** '
                                f'left this Squad'),
                    "embed": None,
                    "scope": f'Squad-{squadid}'}
            yqueue_put('yarqueue:discord', qmsg)
            # We put the info in queue for ws Front
            qmsg = {"ciphered": False,
                    "payload": Squad._asdict(),
                    "route": 'mypc/{id1}/squad',
                    "scope": 'squad'}
            yqueue_put('broadcast', json.loads(jsonify(qmsg).get_data()))

            msg = f'{h} Squad leave OK (squadid:{squadid})'
            logger.debug(msg)
            return jsonify(
                {
                    "success": True,
                    "msg": msg,
                    "payload": Squad._asdict(),
                }
            ), 200
