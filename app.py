# -"- coding:utf-8 -"-
import json
import os

import mimetypes
mimetypes.add_type('application/javascript', '.js')

from flask import Flask, request, render_template
import logging
from game import Game


app = Flask('Tiny Towns', static_url_path='',static_folder='static', template_folder='static')
logging.basicConfig(level=logging.DEBUG)

myGame = Game()

@app.route('/', methods=['GET'])
def home():
   return render_template('index.html')

@app.route('/api', methods=['POST'])
def api() -> (str or None):
    global myGame
    logging.info(f'Request: {request.json!r}')
    
    if 'method' not in request.json:
        return '{"error":{"code":100, "msg":"bad method"}}'

    # response = {}

    if request.json['method'] in ['get_status', 'restart_game', 'log_out', 'set_monument', 'check_patterns', 'place_resource', 'change_readiness', 'choose_resource', 
    'place_building', 'find_patterns']:
        method = getattr(myGame, request.json['method'])
        response = method(request.json['params'])
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
    app.run(host='0.0.0.0', port=port, debug=False)