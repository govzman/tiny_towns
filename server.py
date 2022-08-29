# -"- coding:utf-8 -"-
import json
import os

from flask import Flask, request, render_template
import logging

app = Flask(__name__,static_url_path='',static_folder='static', template_folder='static')
logging.basicConfig(level=logging.DEBUG)

@app.route('/', methods=['GET'])
def home():
   return render_template('index.html')

@app.route('/api', methods=['POST'])
def api():
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
