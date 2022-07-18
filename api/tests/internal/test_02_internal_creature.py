# -*- coding: utf8 -*-

import json
import requests

from variables import (API_URL,
                       CREATURE_ID,
                       HEADERS)

def test_singouins_internal_creature_equipment():
    url       = f'{API_URL}/internal/creature/{CREATURE_ID}/equipment'
    response  = requests.get(url, headers=HEADERS)

    assert response.status_code                 == 200
    assert json.loads(response.text)['success'] == True

def test_singouins_internal_creature_pa_get():
    url       = f'{API_URL}/internal/creature/{CREATURE_ID}/pa'
    response  = requests.get(url, headers=HEADERS)

    assert response.status_code                 == 200
    assert json.loads(response.text)['success'] == True

def test_singouins_internal_creature_pa_consume():
    url       = f'{API_URL}/internal/creature/{CREATURE_ID}/pa/consume/1/1'
    response  = requests.put(url, headers=HEADERS)

    assert response.status_code                 == 200
    assert json.loads(response.text)['success'] == True

def test_singouins_internal_creature_pa_reset():
    url       = f'{API_URL}/internal/creature/{CREATURE_ID}/pa/reset'
    response  = requests.put(url, headers=HEADERS)

    assert response.status_code                 == 200
    assert json.loads(response.text)['success'] == True

def test_singouins_internal_creature():
    url       = f'{API_URL}/internal/creature/{CREATURE_ID}'
    response  = requests.get(url, headers=HEADERS)

    assert response.status_code                 == 200
    assert json.loads(response.text)['success'] == True

def test_singouins_internal_creature_stats():
    url       = f'{API_URL}/internal/creature/{CREATURE_ID}/stats'
    response  = requests.get(url, headers=HEADERS)
    stats     = json.loads(response.text)['payload']['stats']

    assert response.status_code                 == 200
    assert json.loads(response.text)['success'] == True
    assert stats['def']['hp']                   <= stats['def']['hpmax']

def test_singouins_internal_creature_stats_hp_consume():
    url       = f'{API_URL}/internal/creature/{CREATURE_ID}/stats'
    response  = requests.get(url, headers=HEADERS)

    assert response.status_code                 == 200
    assert json.loads(response.text)['success'] == True

    hp = json.loads(response.text)['payload']['stats']['def']['hp']

    url       = f'{API_URL}/internal/creature/{CREATURE_ID}/stats/hp/consume/30'
    response  = requests.put(url, headers=HEADERS)
    payload   = json.loads(response.text)['payload']

    assert response.status_code                 == 200
    assert json.loads(response.text)['success'] == True
    assert payload['stats']['def']['hp']        == hp - 30


def test_singouins_internal_creature_stats_hp_add():
    url       = f'{API_URL}/internal/creature/{CREATURE_ID}/stats'
    response  = requests.get(url, headers=HEADERS)

    assert response.status_code                 == 200
    assert json.loads(response.text)['success'] == True

    hp = json.loads(response.text)['payload']['stats']['def']['hp']

    url       = f'{API_URL}/internal/creature/{CREATURE_ID}/stats/hp/add/20'
    response  = requests.put(url, headers=HEADERS)
    payload   = json.loads(response.text)['payload']

    assert response.status_code                 == 200
    assert json.loads(response.text)['success'] == True
    assert payload['stats']['def']['hp']        == hp + 20

def test_singouins_internal_creature_wallet():
    url       = f'{API_URL}/internal/creature/{CREATURE_ID}/wallet'
    response  = requests.get(url, headers=HEADERS)
    payload   = json.loads(response.text)['payload']

    assert response.status_code                 == 200
    assert json.loads(response.text)['success'] == True
    assert payload['wallet']['ammo']['cal50']   >= 0


def test_singouins_internal_creature_wallet_add():
    url       = f'{API_URL}/internal/creature/{CREATURE_ID}/wallet'
    response  = requests.get(url, headers=HEADERS)
    payload   = json.loads(response.text)['payload']
    cal50     = payload['wallet']['ammo']['cal50']

    assert response.status_code                 == 200
    assert json.loads(response.text)['success'] == True
    assert payload['wallet']['ammo']['cal50']   >= 0

    url       = f'{API_URL}/internal/creature/{CREATURE_ID}/wallet/cal50/add/30'
    response  = requests.put(url, headers=HEADERS)
    payload   = json.loads(response.text)['payload']

    assert response.status_code                 == 200
    assert json.loads(response.text)['success'] == True
    assert payload['wallet']['ammo']['cal50']   == cal50 + 30

def test_singouins_internal_creature_wallet_consume():
    url       = f'{API_URL}/internal/creature/{CREATURE_ID}/wallet'
    response  = requests.get(url, headers=HEADERS)
    payload   = json.loads(response.text)['payload']
    cal50     = payload['wallet']['ammo']['cal50']

    assert response.status_code                 == 200
    assert json.loads(response.text)['success'] == True
    assert payload['wallet']['ammo']['cal50']   >= 0

    url       = f'{API_URL}/internal/creature/{CREATURE_ID}/wallet/cal50/consume/25'
    response  = requests.put(url, headers=HEADERS)
    payload   = json.loads(response.text)['payload']

    assert response.status_code                 == 200
    assert json.loads(response.text)['success'] == True
    assert payload['wallet']['ammo']['cal50']   == cal50 - 25

def test_singouins_internal_creature_wallet_weird():
    url       = f'{API_URL}/internal/creature/{CREATURE_ID}/wallet/cal50/plop/30'
    response  = requests.put(url, headers=HEADERS)

    assert response.status_code                 == 200
    assert json.loads(response.text)['success'] == False

    url       = f'{API_URL}/internal/creature/{CREATURE_ID}/wallet/plip/add/30'
    response  = requests.put(url, headers=HEADERS)

    assert response.status_code                 == 200
    assert json.loads(response.text)['success'] == False

    url       = f'{API_URL}/internal/creature/{CREATURE_ID}/wallet/plip/add/plop'
    response  = requests.put(url, headers=HEADERS)

    assert response.status_code                 == 404

def test_singouins_internal_creatures():
    url       = f'{API_URL}/internal/creatures'
    response  = requests.get(url, headers=HEADERS)

    assert response.status_code                 == 200
    assert json.loads(response.text)['success'] == True

def test_singouins_internal_creature_pop():
    url       = f'{API_URL}/internal/creature' # PUT
    payload   = {"raceid": 11,
                 "gender": True,
                 "rarity": "Boss",
                 "instanceid": 0,
                 "x": 3,
                 "y": 3}
    response  = requests.put(url, headers=HEADERS, json = payload)

    creatureid = json.loads(response.text)['payload']['id']

    assert creatureid > 0
    assert response.status_code                 == 201
    assert json.loads(response.text)['success'] == True

    url       = f'{API_URL}/internal/creature/{creatureid}' # DELETE
    response  = requests.delete(url, headers=HEADERS, json = payload)

    assert response.status_code                 == 200
    assert json.loads(response.text)['success'] == True
