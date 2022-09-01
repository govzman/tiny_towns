# -"- coding:utf-8 -"-
import json
import os

from flask import Flask, request, render_template
import logging
from game import Game

app = Flask(__name__,static_url_path='',static_folder='static', template_folder='static')
logging.basicConfig(level=logging.DEBUG)

@app.route('/', methods=['GET'])
def home():
   return render_template('index.html')

@app.route('/api', methods=['POST'])
def api():
    global myGame
    logging.info(f'Request: {request.json!r}')
    if request.json['method'] == 'get_status':
        response = myGame.get_status(request.json['params'])
    return json.dumps(response)


if __name__ == '__main__':
    myGame = Game()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

#
