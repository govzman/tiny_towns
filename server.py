# -"- coding:utf-8 -"-
import json
import os

from flask import Flask, request
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)


@app.route('/', methods=['POST'])
def main():
    logging.info(f'Request: {request.json!r}')
    response = {
				'request': request.json,
        'response': {
            'test': 'ok'
        }
    }
    return json.dumps(response)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
