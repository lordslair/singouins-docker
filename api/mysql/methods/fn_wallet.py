# -*- coding: utf8 -*-

from ..session          import Session
from ..models           import PJ,Wallet,Item,MetaWeapon

def fn_wallet_ammo_get(pc,item,itemmeta):
    session = Session()

    try:
        wallet = session.query(Wallet).filter(Wallet.id == pc.id).one_or_none()
    except Exception as e:
        # Something went wrong during query
        return False
    else:
        if wallet is None:
            return False

        if   itemmeta.caliber == '.22':
            return wallet.cal22
        elif itemmeta.caliber == '.223':
            return wallet.cal223
        elif itemmeta.caliber == '.311':
            return wallet.cal311
        elif itemmeta.caliber == '.50':
            return wallet.cal50
        elif itemmeta.caliber == '.55':
            return wallet.cal55
        elif itemmeta.caliber == 'shell':
            return wallet.shell
        elif itemmeta.caliber == 'bolt':
            return wallet.bolt
        elif itemmeta.caliber == 'arrow':
            return wallet.arrow
        else:
            return 0
    finally:
        session.close()

def fn_wallet_ammo_set(pc,caliber,ammo):
    session = Session()

    try:
        wallet = session.query(Wallet).filter(Wallet.id == pc.id).one_or_none()

        if   caliber == '.22':
            wallet.cal22 += ammo
        elif caliber == '.223':
            wallet.cal223 += ammo
        elif caliber == '.311':
            wallet.cal311 += ammo
        elif caliber == '.50':
            wallet.cal50 += ammo
        elif caliber == '.55':
            wallet.cal55 += ammo
        elif caliber == 'shell':
            wallet.shell += ammo
        elif caliber == 'bolt':
            wallet.bolt += ammo
        elif caliber == 'arrow':
            wallet.arrow += ammo

        session.commit()
    except Exception as e:
        # Something went wrong during query
        session.rollback()
        return False
    else:
        return True
    finally:
        session.close()
