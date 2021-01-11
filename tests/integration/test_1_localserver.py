import json

import requests


def test_localserver(run_localserver, localhost):
    print('Testing localserver...')

    body = {'foo': 'bar'}

    response = requests.post(
        url=localhost.url,
        data=json.dumps(body),
        headers={
            'Content-type': 'application/json',
        },
    )

    data = response.json()

    assert response.ok is True
    assert data['client']['ip'] == '127.0.0.1'
    assert data['request']['body'] == body
    assert data['request']['http']['method'] == 'POST'
    assert data['request']['headers']['Content-type'] == 'application/json'

    response = requests.post(url=localhost.clear_response_cache_url)

    assert response.ok is True
    assert response.json()['clear_response_cache'] is True

    response = requests.post(url=localhost.last_response_url)

    assert response.ok is True
    assert response.json()['last_response'] is None
