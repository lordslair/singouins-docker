# -*- coding: utf8 -*-

import json
import requests

from variables import (API_URL,
                       AUTH_PAYLOAD)

def test_singouins_pc_delete():
    url      = f'{API_URL}/auth/login' # POST
    response = requests.post(url, json = AUTH_PAYLOAD)
    token    = json.loads(response.text)['access_token']
    headers  = {"Authorization": f"Bearer {token}"}

    url      = f'{API_URL}/mypc' # GET
    response = requests.get(url, headers=headers)
    pclist   = json.loads(response.text)['payload']

    for pc in pclist:
        pcid     = pc['id']
        url      = f'{API_URL}/mypc/{pcid}' # DELETE
        response = requests.delete(url, headers=headers)

        assert json.loads(response.text)['success'] == True
        assert response.status_code == 200

def test_singouins_auth_delete():
    url      = f'{API_URL}/auth/login' # POST
    response = requests.post(url, json = AUTH_PAYLOAD)
    token    = json.loads(response.text)['access_token']
    headers  = {"Authorization": f"Bearer {token}"}

    url      = f'{API_URL}/auth/forgotpassword' # POST
    response = requests.post(url, json = {'mail': 'user@exemple.com'}, headers=headers)

    assert 'Password successfully replaced' in json.loads(response.text)['msg']
    assert response.status_code == 200

    url      = f'{API_URL}/auth/delete' # DELETE
    response = requests.delete(url, json = {'username': 'user@exemple.com'}, headers=headers)

    assert 'User successfully deleted' in json.loads(response.text)['msg']
    assert response.status_code == 200
