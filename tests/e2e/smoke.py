"""Exercise the actual Java -> Python -> model HTTP chain through the web proxy."""
import argparse
import json
import uuid
from datetime import date

import httpx


def run(base):
    with httpx.Client(base_url=base, timeout=45) as client:
        def call(method, path, token=None, **kwargs):
            response = client.request(method, '/api/v1' + path, headers={'Authorization': 'Bearer ' + token} if token else {}, **kwargs)
            response.raise_for_status()
            body = response.json()
            assert body['code'] == 0, body
            return body['data']

        suffix = uuid.uuid4().hex[:8]
        owner = call('POST', '/auth/register', json={'username': 'owner' + suffix, 'password': 'test-password'})
        cook = call('POST', '/auth/register', json={'username': 'cook' + suffix, 'password': 'test-password'})
        token = owner['tokens']['access_token']
        cook_token = cook['tokens']['access_token']
        family = call('POST', '/families', token, json={'name': 'Smoke family'})['family']
        call('POST', '/families/join', cook_token, json={'invite_code': family['invite_code']})
        dish = call('POST', '/dishes', token, json={'name': '番茄炒蛋', 'price': 12})
        payload = {'cook_id': cook['user']['id'], 'planned_date': date.today().isoformat(), 'items': [{'dish_id': dish['id'], 'quantity': 1}], 'requestId': uuid.uuid4().hex}
        order = call('POST', '/orders', token, json=payload)
        assert call('POST', '/orders', token, json=payload)['id'] == order['id']
        call('POST', f"/orders/{order['id']}/accept", cook_token)
        call('POST', f"/orders/{order['id']}/review", token, json={'rating': 5, 'content': '好吃'})
        message = call('POST', '/chat/messages', token, json={'content': '准备吃饭'})
        assert call('GET', '/chat/unread-count', cook_token)['unread_count'] == 1
        call('POST', '/chat/read', cook_token, json={'last_read_message_id': message['id']})
        assert call('GET', '/home/summary', token)['monthly_accepted_orders_count'] >= 1
        response = client.post('/api/v1/ai-chat/messages/stream', headers={'Authorization': 'Bearer ' + token}, data={'content': '推荐一道菜'})
        response.raise_for_status()
        assert 'event:ready' in response.text or 'event: ready' in response.text, response.text
        assert 'event:delta' in response.text or 'event: delta' in response.text, response.text
        complete = [block for block in response.text.replace('\r\n', '\n').split('\n\n') if 'event:complete' in block or 'event: complete' in block]
        assert complete, response.text
        turn = json.loads('\n'.join(line.partition(':')[2].lstrip() for line in complete[-1].splitlines() if line.startswith('data:')))
        assert turn['assistant_message']['metadata_json']['recommendations'][0]['rating'] == 5
        assert len(call('GET', '/ai-chat/messages', token, params={'conversation_id': turn['conversation']['id']})['items']) == 2
        cached = call('POST', '/ai-chat/messages', token, data={'content': '推荐一道菜'})
        assert cached['assistant_message']['id'] != turn['assistant_message']['id']
        response = client.get('/api/v1/ai-chat/messages', headers={'Authorization': 'Bearer ' + cook_token}, params={'conversation_id': turn['conversation']['id']})
        assert response.status_code == 404
        assert client.get('/').status_code == 200
        print(json.dumps({'status': 'passed', 'checks': ['auth', 'family', 'dishes', 'idempotency', 'accept', 'review', 'chat', 'home', 'java-python-sse', 'ai-cache', 'conversation-isolation', 'web-proxy']}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('base_url')
    run(parser.parse_args().base_url)
