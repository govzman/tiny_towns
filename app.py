# -"- coding:utf-8 -"-
import json
import os

import mimetypes
mimetypes.add_type('application/javascript', '.js')

from flask import Flask, request, render_template
import logging
from game import Game
import util


app = Flask('Tiny Towns', static_url_path='',static_folder='static', template_folder='static')
logging.basicConfig(level=logging.DEBUG)

myGame = Game()

API_METHODS = ['get_status', 'restart_game', 'log_out', 'set_monument', 'place_resource',
    'change_readiness', 'choose_resource', 'place_building', 'find_patterns']

@app.route('/', methods=['GET'])
def home():
   return render_template('index.html')

@app.route('/api', methods=['POST'])
def api() -> str:
    logging.info(f'Request: {request.json!r}')

    if not request.json or request.json.get('method') not in API_METHODS:
        return json.dumps(util.error(100, 'bad method'))

    method = getattr(myGame, request.json['method'])
    response = method(request.json.get('params', {}))
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