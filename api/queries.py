# -*- coding: utf8 -*-

import sqlalchemy as db

from datetime  import datetime
from variables import SQL_DSN

engine     = db.create_engine('mysql+pymysql://' + SQL_DSN, pool_recycle=3600)
connection = engine.connect()
metadata   = db.MetaData()
t_pjsAuth  = db.Table('pjsAuth', metadata, autoload=True, autoload_with=engine)

def query_get_user_exists(username):
    query = db.select([t_pjsAuth.columns.name]).where(t_pjsAuth.columns.name == username)
    ResultProxy = connection.execute(query)
    ResultSet = ResultProxy.fetchone()
    if ResultSet:
        return True

def query_get_mail_exists(usermail):
    query = db.select([t_pjsAuth.columns.name]).where(t_pjsAuth.columns.mail == usermail)
    ResultProxy = connection.execute(query)
    ResultSet = ResultProxy.fetchone()
    if ResultSet:
        return True

def query_get_password(username):
    query = db.select([t_pjsAuth.columns.hash]).where(t_pjsAuth.columns.name == username)
    ResultProxy = connection.execute(query)
    ResultSet = ResultProxy.fetchone()
    if ResultSet:
        return ResultSet[0]

def query_get_pjauth(username):
    query = db.select([t_pjsAuth.columns.id]).where(t_pjsAuth.columns.name == username)
    ResultProxy = connection.execute(query)
    ResultSet = ResultProxy.fetchone()
    if ResultSet:
        return ResultSet

def query_set_pjauth(username,password,usermail):
    if query_get_user_exists(username) or query_get_mail_exists(usermail):
        return (409)
    else:
        from flask_bcrypt import generate_password_hash
        hash  = generate_password_hash(password, rounds = 10) # 10: Way better perf ratio
        query = db.insert(t_pjsAuth).values(name    = username,
                                            hash    = hash,
                                            mail    = usermail,
                                            created = datetime.now(),
                                            active  = False)
        ResultProxy = connection.execute(query)

        if ResultProxy.inserted_primary_key[0] > 0:
            return (201)

def query_set_user_confirmed(usermail):
    query = db.update(t_pjsAuth).where(t_pjsAuth.c.mail==usermail).values(active = True)
    ResultProxy = connection.execute(query)
    if ResultProxy.rowcount == 1:
        return (201)

def query_del_pjauth(username):
    if not query_get_user_exists(username):
        return (404)
    else:
        query = db.delete(t_pjsAuth).where(t_pjsAuth.c.name == username)
        ResultProxy = connection.execute(query)
        if ResultProxy.rowcount == 1:
            return (200)

#
# Queries: /pj
#
t_pjsInfos  = db.Table('pjsInfos', metadata, autoload=True, autoload_with=engine)

def query_get_pj_exists(username):
    query = db.select([t_pjsInfos.columns.name]).where(t_pjsInfos.columns.name == username)
    ResultProxy = connection.execute(query)
    ResultSet = ResultProxy.fetchone()
    if ResultSet:
        return True

def query_new_pj(username,pjname,pjrace):
    if query_get_pj_exists(pjname):
        return (409)
    else:
        pjid  = query_get_pjauth(username)[0]
        query = db.insert(t_pjsInfos).values(name    = pjname,
                                             race    = pjrace,
                                             account = pjid,
                                             level   = 1,
                                             x       = 0,
                                             y       = 0,
                                             xp      = 0)
        ResultProxy = connection.execute(query)

        if ResultProxy.inserted_primary_key[0] > 0:
            return (201)
