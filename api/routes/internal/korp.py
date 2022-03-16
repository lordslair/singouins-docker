# -*- coding: utf8 -*-

from flask                 import Flask, jsonify, request

from mysql.methods.fn_korp import *
from nosql                 import *

from variables             import API_INTERNAL_TOKEN

#
# Routes /internal
#
# API: GET /internal/korp
def internal_korp_get_one():
    if request.headers.get('Authorization') != f'Bearer {API_INTERNAL_TOKEN}':
        return jsonify({"msg": 'Token not authorized', "success": False, "payload": None}), 403
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request", "success": False, "payload": None}), 400

    korpid  = request.json.get('korpid')

    incr.one('queries:internal:korp')

    try:
        korp = fn_korp_get_one(korpid)
    except Exception as e:
        msg = f'Korp Query KO (korpid:{korpid}) [{e}]'
        logger.error(msg)
        return jsonify({"success": False,
                        "msg": msg,
                        "payload": None}), 200
    else:
        if korp:
            return jsonify({"success": True,
                            "msg": f'Korp Query OK (korpid:{korpid})',
                            "payload": korp}), 200
        elif korp is False:
            return jsonify({"success": False,
                            "msg": f'Korp Query KO - Not Found (korpid:{korpid})',
                            "payload": None}), 200
        else:
            return jsonify({"success": False,
                            "msg": f'Korp Query KO - Failed (korpid:{korpid})',
                            "payload": None}), 200

# API: GET /internal/korps
def internal_korp_get_all():
    if request.headers.get('Authorization') != f'Bearer {API_INTERNAL_TOKEN}':
        return jsonify({"msg": 'Token not authorized', "success": False, "payload": None}), 403

    incr.one('queries:internal:korps')

    try:
        korps = fn_korp_get_all()
    except Exception as e:
        msg = f'Korps Query KO [{e}]'
        logger.error(msg)
        return jsonify({"success": False,
                        "msg": msg,
                        "payload": None}), 200
    else:
        if korps:
            return jsonify({"success": True,
                            "msg": f'Korps Query OK',
                            "payload": korps}), 200
        else:
            return jsonify({"success": False,
                            "msg": f'Korps Query KO',
                            "payload": None}), 200
