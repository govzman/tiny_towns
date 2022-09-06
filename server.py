# -"- coding:utf-8 -"-
import json
import os

import mimetypes
mimetypes.add_type('application/javascript', '.js')

from flask import Flask, request, render_template
import logging
from game import Game


app = Flask('Tiny Towns',static_url_path='',static_folder='static', template_folder='static')
logging.basicConfig(level=logging.DEBUG)

myGame = Game()

@app.route('/', methods=['GET'])
def home():
   return render_template('index.html')

@app.route('/api', methods=['POST'])
def api():
    global myGame
    logging.info(f'Request: {request.json!r}')
    
    if 'method' not in request.json:
        return '{"error":{"code":100, "msg":"bad method"}}'

    if request.json['method'] == 'get_status':
        response = myGame.get_status(request.json['params'])
    elif request.json['method'] == 'restart_game':
        response = myGame.restart_game()
    elif request.json['method'] == 'log_out':
        response = myGame.log_out(request.json['params'])
    return json.dumps(response)

# DEV ONLY:
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
    response.headers["Expires"] = '0'
    response.headers["Pragma"] = "no-cache"
    return response

if __name__ == '__main__':    
    print(f"New game ID {myGame.game_id}\n")
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)