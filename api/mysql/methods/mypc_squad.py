# -*- coding: utf8 -*-

from ..session          import Session
from ..models           import *
from ..utils.redis      import *

from .fn_creature       import (fn_creature_get,
                                fn_creature_clean,
                                fn_creatures_clean)
from .fn_user           import fn_user_get

#
# Queries /mypc/<int:pcid>/squad/*
#

# API: /mypc/<int:pcid>/squad/<int:squadid>
def get_squad(username,pcid,squadid):
    (code, success, msg, pc) = fn_creature_get(None,pcid)
    user                     = fn_user_get(username)
    session                  = Session()

    # Pre-flight checks
    if pc is None:
        return (200,
                False,
                f'PC not found (pcid:{pcid})',
                None)
    if pc.account != user.id:
        return (409,
                False,
                f'Token/username mismatch (pcid:{pcid},username:{username})',
                None)
    if pc.squad != squadid:
        return (200,
                False,
                f'Squad request outside of your scope (pcid:{pc.id},squadid:{squadid})',
                None)

    try:
        squad = session.query(Squad).\
                        filter(Squad.id == pc.squad).\
                        filter(PJ.id == pc.id)

        pc_is_member  = squad.filter(PJ.squad_rank != 'Pending').one_or_none()
        pc_is_pending = squad.filter(PJ.squad_rank == 'Pending').one_or_none()

        if pc_is_member:
            squad   = squad.session.query(Squad).filter(Squad.id == pc.squad).one_or_none()
            members = session.query(PJ).filter(PJ.squad == squad.id).filter(PJ.squad_rank != 'Pending').all()
            pending = session.query(PJ).filter(PJ.squad == squad.id).filter(PJ.squad_rank == 'Pending').all()
        elif pc_is_pending:
            squad   = squad.session.query(Squad).filter(Squad.id == pc.squad).one_or_none()

    except Exception as e:
        # Something went wrong during commit
        return (200,
                False,
                f'[SQL] Squad query failed (pcid:{pcid},squadid:{squadid}) [{e}]',
                None)
    else:
        if pc_is_member:
            if squad:
                if isinstance(members, list):
                    if isinstance(pending, list):
                        return (200,
                                True,
                                f'Squad query successed (pcid:{pcid},squadid:{squadid})',
                                {"squad": squad, "members": members, "pending": pending})
        elif pc_is_pending:
            return (200,
                    True,
                    f'PC is pending in a squad (pcid:{pcid},squadid:{squadid})',
                    {"squad": squad})
        else: return (200,
                      False,
                      f'PC is not in a squad (pcid:{pcid},squadid:{squadid})',
                      None)
    finally:
        session.close()

# API: /mypc/<int:pcid>/squad
def add_squad(username,pcid):
    (code, success, msg, pc) = fn_creature_get(None,pcid)
    user                     = fn_user_get(username)
    session                  = Session()

    if pc and pc.account == user.id:
        # Unicity test commented before release:alpha. Meditation needed
        #if session.query(Squad).filter(Squad.name == squadname).one_or_none():
        #    return (409, False, f'Squad already exists (squadname:{squadname})', None)
        if pc.squad is not None:
            return (200,
                    False,
                    'Squad leader already in a squad (pcid:{},squadid:{})'.format(pc.id,pc.squad),
                    None)

        squad = Squad(leader  = pc.id)
        session.add(squad)

        try:
            session.commit()
        except Exception as e:
            # Something went wrong during commit
            return (200, False, '[SQL] Squad creation failed (pcid:{})'.format(pcid), None)

        # Squad created, let's assign the team creator in the squad
        pc            = session.query(PJ).filter(PJ.id == pcid).one_or_none()
        squad         = session.query(Squad).filter(Squad.leader == pc.id).one_or_none()
        pc.squad      = squad.id
        pc.squad_rank = 'Leader'

        try:
            session.commit()
            members       = session.query(PJ).filter(PJ.squad == pc.squad).all()
        except Exception as e:
            # Something went wrong during commit
            return (200,
                    False,
                    '[SQL] Squad leader assignation failed (pcid:{},squadid:{})'.format(pc.id,squad.id),
                    None)
        else:
            # We put the info in queue for ws
            qmsg = {"ciphered": False,
                    "payload": f':information_source: **[{pc.id}] {pc.name}** created this squad',
                    "embed": None,
                    "scope": f'Squad-{pc.squad}'}
            yqueue_put('discord', qmsg)
            # We put the info in queue for ws Front
            qmsg = {"ciphered": False,
                    "payload": fn_creatures_clean(members),
                    "route": 'mypc/{id1}/squad',
                    "scope": 'squad'}
            yqueue_put('broadcast', qmsg)
            return (201,
                    True,
                    'Squad successfully created (pcid:{},squadid:{})'.format(pc.id,squad.id),
                    squad)
        finally:
            session.close()
    else: return (409, False, 'Token/username mismatch', None)

# API: /mypc/<int:pcid>/squad/<int:squadid>
def del_squad(username,leaderid,squadid):
    (code, success, msg, leader) = fn_creature_get(None,leaderid)
    user                         = fn_user_get(username)
    session                      = Session()

    if leader:
        if leader.squad != squadid:
            return (200, False, 'Squad request outside of your scope ({} =/= {})'.format(leader.squad,squadid), None)
        if leader.squad_rank != 'Leader':
            return (200, False, 'PC is not the squad Leader', None)
    else:
        return (200, False, 'PC unknown in DB (pcid:{})'.format(leaderid), None)

    if leader and leader.account == user.id:
        try:
            squad = session.query(Squad).filter(Squad.leader == leader.id).one_or_none()
            if not squad: return (200, True, 'No Squad found for this PC (pcid:{})'.format(leader.id), None)

            count = session.query(PJ).filter(PJ.squad == squad.id).count()
            if count > 1: return (200, False, 'Squad not empty (squadid:{})'.format(squad.id), None)

            session.delete(squad)
            pc            = session.query(PJ).filter(PJ.id == leader.id).one_or_none()
            pc.squad      = None
            pc.squad_rank = None
            session.commit()
            members       = session.query(PJ).filter(PJ.squad == leader.squad).all()
        except Exception as e:
            # Something went wrong during commit
            return (200, False, '[SQL] Squad deletion failed (squadid:{})'.format(squad.id), None)
        else:
            # We put the info in queue for ws
            qmsg = {"ciphered": False,
                    "payload": f':information_source: **[{pc.id}] {pc.name}** deleted this squad',
                    "embed": None,
                    "scope": f'Squad-{squad.id}'}
            yqueue_put('discord', qmsg)
            # We put the info in queue for ws Front
            qmsg = {"ciphered": False,
                    "payload": fn_creatures_clean(members),
                    "route": 'mypc/{id1}/squad',
                    "scope": 'squad'}
            yqueue_put('broadcast', qmsg)
            return (200, True, 'Squad successfully deleted (squadid:{})'.format(squad.id), None)
        finally:
            session.close()
    else: return (409, False, 'Token/username mismatch', None)

# API: /mypc/<int:pcid>/squad/<int:squadid>/invite/<int:targetid>
def invite_squad_member(username,leaderid,squadid,targetid):
    (code, success, msg, target) = fn_creature_get(None,targetid)
    (code, success, msg, leader) = fn_creature_get(None,leaderid)
    user                         = fn_user_get(username)
    session                      = Session()

    if leader:
        if leader.squad is None:
            return (200, False, 'PC is not in a squad', None)
        if leader.squad != squadid:
            return (200, False, 'Squad request outside of your scope ({} =/= {})'.format(leader.squad,squadid), None)
        if leader.squad_rank != 'Leader':
            return (200, False, 'PC is not the squad Leader', None)

        members    = session.query(PJ).filter(PJ.squad == leader.squad).all()
        maxmembers = 10
        if len(members) == maxmembers:
            return (200,
                    False,
                    'Squad is already full (slots:{}/{})'.format(len(members),maxmembers),
                    None)
    else:
        return (200, False, 'PC unknown in DB (pcid:{})'.format(leaderid), None)

    if target:
        if target.squad is not None:
            return (200,
                    False,
                    'PC invited is already in a squad (pcid:{},squadid:{})'.format(target.id,target.squad),
                    None)
    else:
        return (200, False, 'PC unknown in DB (pcid:{})'.format(targetid), None)

    if target and leader:
        try:
            pc = session.query(PJ).filter(PJ.id == target.id).one_or_none()
            pc.squad      = leader.squad
            pc.squad_rank = 'Pending'
            session.commit()
            members    = session.query(PJ).filter(PJ.squad == leader.squad).all()
        except Exception as e:
            # Something went wrong during commit
            return (200,
                    False,
                    '[SQL] PC Invite failed (slots:{}/{})'.format(len(members),maxmembers),
                    None)
        else:
            # We put the info in queue for ws
            qmsg = {"ciphered": False,
                    "payload": f':information_source: **[{leader.id}] {leader.name}** invited **[{target.id}] {target.name}** in this squad',
                    "embed": None,
                    "scope": f'Squad-{leader.squad}'}
            yqueue_put('discord', qmsg)
            # We put the info in queue for ws Front
            qmsg = {"ciphered": False,
                    "payload": fn_creatures_clean(members),
                    "route": 'mypc/{id1}/squad',
                    "scope": 'squad'}
            yqueue_put('broadcast', qmsg)
            return (201,
                    True,
                    'PC successfully invited (slots:{}/{})'.format(len(members),maxmembers),
                    fn_creature_clean(pc))
        finally:
            session.close()
    else:
        return (200,
                False,
                'PC/Leader unknown in DB (leaderid:{},targetid:{})'.format(leaderid,targetid),
                None)

# API: /mypc/<int:pcid>/squad/<int:squadid>/kick/<int:targetid>
def kick_squad_member(username,leaderid,squadid,targetid):
    (code, success, msg, target) = fn_creature_get(None,targetid)
    (code, success, msg, leader) = fn_creature_get(None,leaderid)
    user                         = fn_user_get(username)
    maxmembers                   = 10
    session                      = Session()

    if leader:
        if leader.squad is None:
            return (200, False, 'PC is not in a squad', None)
        if leader.squad != squadid:
            return (200,
                    False,
                    'Squad request outside of your scope ({} =/= {})'.format(leader.squad,squadid),
                    None)
        if leader.squad_rank != 'Leader':
            return (200, False, 'PC is not the squad Leader', None)
        if leader.id == targetid:
            return (200, False, 'PC target cannot be the squad Leader', None)
    else:
        return (200, False, 'PC unknown in DB (pcid:{})'.format(leaderid), None)

    if target:
        if target.squad is None:
            return (200,
                    False,
                    'PC have to be in a squad (pcid:{},squadid:{})'.format(target.id,target.squad),
                    None)
    else:
        return (200, False, 'PC unknown in DB (pcid:{})'.format(targetid), None)

    if target and leader:
        try:
            pc = session.query(PJ).filter(PJ.id == target.id).one_or_none()
            pc.squad      = None
            pc.squad_rank = None
            session.commit()
            members    = session.query(PJ).filter(PJ.squad == leader.squad).all()
        except Exception as e:
            # Something went wrong during commit
            return (200,
                    False,
                    '[SQL] PC Kick failed (pcid:{},squadid:{})'.format(target.id,target.squad),
                    None)
        else:
            # We put the info in queue for ws Discord
            qmsg = {"ciphered": False,
                    "payload": f':information_source: **[{leader.id}] {leader.name}** kicked **[{target.id}] {target.name}** from this squad',
                    "embed": None,
                    "scope": f'Squad-{leader.squad}'}
            yqueue_put('discord', qmsg)
            # We put the info in queue for ws Front
            qmsg = {"ciphered": False,
                    "payload": fn_creatures_clean(members),
                    "route": 'mypc/{id1}/squad',
                    "scope": 'squad'}
            yqueue_put('broadcast', qmsg)
            return (201,
                    True,
                    'PC successfully kicked (slots:{}/{})'.format(len(members),maxmembers),
                    fn_creatures_clean(members))
        finally:
            session.close()
    else:
        return (200,
                False,
                'PC/Leader unknown in DB (leaderid:{},targetid:{})'.format(leaderid,targetid),
                None)

# API: /mypc/<int:pcid>/squad/<int:squadid>/accept
def accept_squad_member(username,pcid,squadid):
    (code, success, msg, pc)     = fn_creature_get(None,pcid)
    user                         = fn_user_get(username)
    session                      = Session()

    if pc:
        # PC is not the Squad member
        if pc.squad != squadid:
            return (200,
                    False,
                    'Squad request outside of your scope (pcid:{},squadid:{})'.format(pc.id,squadid),
                    None)

        if pc.squad_rank != 'Pending':
            return (200, False, 'PC is not pending in a squad', None)

        try:
            pc            = session.query(PJ).filter(PJ.id == pcid).one_or_none()
            pc.squad_rank = 'Member'
            session.commit()
            members       = session.query(PJ).filter(PJ.squad == pc.squad).all()
        except Exception as e:
            # Something went wrong during commit
            return (200,
                    False,
                    '[SQL] PC squad invite accept failed (pcid:{},squadid:{})'.format(pc.id,squadid),
                    None)
        else:
            # We put the info in queue for ws
            qmsg = {"ciphered": False,
                    "payload": f':information_source: **[{pc.id}] {pc.name}** accepted this squad',
                    "embed": None,
                    "scope": f'Squad-{pc.squad}'}
            yqueue_put('discord', qmsg)
            # We put the info in queue for ws Front
            qmsg = {"ciphered": False,
                    "payload": fn_creatures_clean(members),
                    "route": 'mypc/{id1}/squad',
                    "scope": 'squad'}
            yqueue_put('broadcast', qmsg)
            return (201,
                    True,
                    'PC successfully accepted squad invite (pcid:{},squadid:{})'.format(pc.id,squadid),
                    None)
        finally:
            session.close()
    else: return (200, False, 'PC unknown in DB (pcid:{})'.format(pcid), None)

# API: /mypc/<int:pcid>/squad/<int:squadid>/decline
def decline_squad_member(username,pcid,squadid):
    (code, success, msg, pc)     = fn_creature_get(None,pcid)
    user                         = fn_user_get(username)
    session                      = Session()

    if pc:
        # PC is not the Squad member
        if pc.squad != squadid:
            return (200,
                    False,
                    'Squad request outside of your scope (pcid:{},squadid:{})'.format(pc.id,squadid),
                    None)

        if pc.squad_rank != 'Pending':
            return (200, False, 'PC is not pending in a squad', None)

        try:
            pc            = session.query(PJ).filter(PJ.id == pcid).one_or_none()
            pc.squad      = None
            pc.squad_rank = None
            session.commit()
            members       = session.query(PJ).filter(PJ.squad == pc.squad).all()
        except Exception as e:
            # Something went wrong during commit
            return (200,
                    False,
                    '[SQL] PC squad invite decline failed (pcid:{},squadid:{})'.format(pc.id,squadid),
                    None)
        else:
            # We put the info in queue for ws
            qmsg = {"ciphered": False,
                    "payload": f':information_source: **[{pc.id}] {pc.name}** declined the invite',
                    "embed": None,
                    "scope": f'Squad-{squadid}'}
            yqueue_put('discord', qmsg)
            # We put the info in queue for ws Front
            qmsg = {"ciphered": False,
                    "payload": fn_creatures_clean(members),
                    "route": 'mypc/{id1}/squad',
                    "scope": 'squad'}
            yqueue_put('broadcast', qmsg)
            return (201, True, 'PC successfully declined squad invite (pcid:{},squadid:{})'.format(pc.id,squadid), None)
        finally:
            session.close()
    else: return (200, False, 'PC unknown in DB (pcid:{})'.format(pcid), None)

# API: /mypc/<int:pcid>/squad/<int:squadid>/leave
def leave_squad_member(username,pcid,squadid):
    (code, success, msg, pc)     = fn_creature_get(None,pcid)
    user                         = fn_user_get(username)
    session                      = Session()

    if pc:
        # PC is not the Squad member
        if pc.squad != squadid:
            return (200,
                    False,
                    'Squad request outside of your scope (pcid:{},squadid:{})'.format(pc.id,squadid),
                    None)

        if pc.squad_rank == 'Leader':
            return (200,
                    False,
                    'PC cannot be the squad Leader (pcid:{},squadid:{})'.format(pc.id,squadid),
                    None)

        try:
            pc            = session.query(PJ).filter(PJ.id == pcid).one_or_none()
            pc.squad      = None
            pc.squad_rank = None
            session.commit()
            members       = session.query(PJ).filter(PJ.squad == pc.squad).all()
        except Exception as e:
            # Something went wrong during commit
            return (200,
                    False,
                    '[SQL] PC squad leave failed (pcid:{},squadid:{})'.format(pc.id,squadid),
                    None)
        else:
            # We put the info in queue for ws
            qmsg = {"ciphered": False,
                    "payload": f':information_source: **[{pc.id}] {pc.name}** left this squad',
                    "embed": None,
                    "scope": f'Squad-{squadid}'}
            yqueue_put('discord', qmsg)
            # We put the info in queue for ws Front
            qmsg = {"ciphered": False,
                    "payload": fn_creatures_clean(members),
                    "route": 'mypc/{id1}/squad',
                    "scope": 'squad'}
            yqueue_put('broadcast', qmsg)
            return (201,
                    True,
                    'PC successfully left (pcid:{},squadid:{})'.format(pc.id,squadid),
                    None)
        finally:
            session.close()
    else: return (200, False, 'PC unknown in DB (pcid:{})'.format(pcid), None)
