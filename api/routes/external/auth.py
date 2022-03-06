# -*- coding: utf8 -*-

from flask                 import Flask, jsonify, request
from flask_bcrypt          import check_password_hash
from flask_jwt_extended    import (jwt_required,
                                   create_access_token,
                                   create_refresh_token,
                                   get_jwt_identity)

from nosql                 import *
from mysql.methods.auth    import *
from mysql.methods.fn_user import *
from utils.mail            import send
from utils.token           import (confirm_token,
                                   generate_confirmation_token)

from variables             import (API_URL,
                                   DISCORD_URL)

#
# Routes /auth
#
# API: POST /auth/login
def auth_login():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    username = request.json.get('username', None)
    password = request.json.get('password', None)

    if not username:
        return jsonify({"msg": "Missing username parameter"}), 400
    if not password:
        return jsonify({"msg": "Missing password parameter"}), 400

    if fn_user_get(username):
        pass_db    = fn_user_get(username).hash
        pass_check = check_password_hash(pass_db, password)
    else:
        pass_check = None

    if not fn_user_get(username) or not pass_check:
        return jsonify({"msg": "Bad username or password"}), 401

    # Identity can be any data that is json serializable
    ret = {
        'access_token': create_access_token(identity=username),
        'refresh_token': create_refresh_token(identity=username)
    }
    return jsonify(ret), 200

# API: POST /auth/refresh
@jwt_required(refresh=True)
def auth_refresh():
    current_user = get_jwt_identity()
    ret = {
        'access_token': create_access_token(identity=current_user)
    }
    return jsonify(ret), 200

# API: POST /auth/register
def auth_register():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    password = request.json.get('password', None)
    mail     = request.json.get('mail', None)
    if not password:
        return jsonify({"msg": "Missing password parameter"}), 400
    if not mail:
        return jsonify({"msg": "Missing mail parameter"}), 400

    code = add_user(mail,password)
    if code == 201:
        subject = '[🐒&🐖] Bienvenue chez le Singouins !'
        token   = generate_confirmation_token(mail)
        url     = API_URL + '/auth/confirm/' + token
        body    = open("/code/data/registered.html", "r").read()
        if send(mail,
                subject,
                body.format(urllogo    = '[INSERT LOGO HERE]',
                            urlconfirm = url,
                            urldiscord = DISCORD_URL)):
            return jsonify({"msg": "User successfully added | mail OK"}), code
        else:
            return jsonify({"msg": "User successfully added | mail KO"}), 206
    elif code == 409:
        return jsonify({"msg": "User or Email already exists"}), code
    else:
        return jsonify({"msg": "Oops!"}), 422

# API: GET /auth/confirm/{token}
def auth_confirm(token):
    if confirm_token(token):
        mail = confirm_token(token)
        code = set_user_confirmed(mail)
        if code == 201:
            return jsonify({"msg": "User successfully confirmed"}), code
        else:
            return jsonify({"msg": "Oops!"}), 422
    else:
        return jsonify({"msg": "Confirmation link invalid or has expired"}), 498

# API: DELETE /auth/delete
@jwt_required()
def auth_delete():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    username     = request.json.get('username', None)
    current_user = get_jwt_identity()

    if not username:
        return jsonify({"msg": "Missing username parameter"}), 400
    if username != current_user:
        return jsonify({"msg": "Token/username mismatch"}), 400

    code = del_user(username)
    if code == 200:
        return jsonify({"msg": "User successfully deleted"}), code
    if code == 404:
        return jsonify({"msg": "Bad username"}), code
    else:
        return jsonify({"msg": "Oops!"}), 422

# API: POST /auth/forgotpassword
def auth_forgotpassword():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    mail            = request.json.get('mail', None)
    (code,password) = forgot_password(mail)

    if code == 200:
        subject = '[🐒&🐖] Mot de passe oublié'
        token   = generate_confirmation_token(mail)
        url     = API_URL + '/auth/confirm/' + token
        body    = open("/code/data/forgot_password.html", "r").read()
        if send(mail,
                subject,
                body.format(urllogo    = '[INSERT LOGO HERE]',
                            password   = password,
                            urldiscord = DISCORD_URL)):
            return jsonify({"msg": "Password successfully replaced | mail OK"}), code
        else:
            return jsonify({"msg": "Password successfully replaced | mail KO"}), 206
    else:
        return jsonify({"msg": "Oops!"}), 422

# API: POST /auth/infos
@jwt_required()
def auth_infos():
    # Access the identity of the current user with get_jwt_identity
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200
