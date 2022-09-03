const DEBUG = true;
const PING_INTERVAL = 2000;

const getState = () => {
    return JSON.parse(localStorage.getItem('gameState'));
}

const setState = (state) => {
    localStorage.setItem('gameState', JSON.stringify(state));
}

const api = async (method, params={}) => {
    try {
        console.log(params)
        const response = await fetch('/api', {
          method: 'POST',
          body: JSON.stringify({
            'method': method,
            'params': params
          }), 
          headers: {
            'Content-Type': 'application/json'
          }
        });
        const json = await response.json();                
        if (DEBUG) console.debug(json);
        
        return json;
        
      } catch (error) {
        console.error(error);
      }
};

const auth = async () => {
    try {
        while (!game.nickname) {
            game.nickname = prompt("Enter nickname: ");            
        }
        console.debug(`NICK ${game.nickname}`);
        const result = await api('get_status', { 'nickname': game.nickname });
        if (result.error){
            // TODO
            document.getElementById('lobby').innerText = result.error.msg;
            return;
        }
        
        if (!result.id) {
            // TODO Exception
            console.error('NO ID', result);
            return;
        }

        game.id = result.id;
        setState(game);
      } catch (error) {
        console.error(error);
      }
};

const getStatus = () => {    
    if (!game.id) {
        auth().then(getStatus);
        return;
    }

    if (DEBUG) console.debug(`PING ${game.id}`);

    // TODO: bad id
    api('get_status', { 'id': game.id, 'ready': game.isReady }).then((res) => {
        if (res.error){
            if (res.error.code == 1) {
                console.error("BAD AUTH");
                auth().then(getStatus);
            } else {
                document.getElementById('lobby').innerText = res.error.msg;
                console.error('UNKNOWN ERR', res, res.error);
            }
            return;
        }
        
        //game.game_stage = res.game_stage;
        switch(res.game_stage) {
            case 'lobby':
                if (game.players != res.players) {
                    game.players = res.players;
                    game.playersReadiness = res.isReady;
                    
                    showLobby();
                }
                break;
            case 'choose_monument':
                ///game.ready = false; // TODO!
                document.getElementById('lobby').innerText = JSON.stringify(res.monuments);
                break;
            default:
                alert('Unknown stage!');                    
        }
    });        
} 

const showLobby = () => {
    const playersList = document.getElementById("playersList");
    playersList.innerHTML = '';

    for (let playerName of game.players) {
        let li = document.createElement("li");
        li.appendChild(document.createTextNode((game.playersReadiness[game.players.indexOf(playerName)]?'🟢 ':'🟡 ')+playerName)); // TODO: players + ready
        playersList.appendChild(li);
    }  
};

const getReady = () => {
    const button = document.getElementById('isReadyBtn');
    game.isReady = !game.isReady;
    if (game.isReady) {
        button.textContent = 'Stop...';        
    } else {
        button.textContent = 'Start!';        
    }
    getStatus();
    return false;
};

const restartGame = () => {
    api('restart_game');
    console.log("Reset!")
}
// -----------------------------------------------------

const defaultState = {
    isReady: false
};

let game = getState() || defaultState;

//game.ready = false; // TODO !
// document.game = game; // DEBUG only

getStatus();
setInterval(getStatus, PING_INTERVAL);

document.getElementById('isReadyBtn').addEventListener('click', getReady);
document.getElementById('restartBtn').addEventListener('click', restartGame);