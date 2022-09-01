const DEBUG = true;
const PING_INTERVAL = 2000;

const getState = () => {
    return JSON.parse(localStorage.getItem('gameState'));
}

const setState = (state) => {
    localStorage.setItem('gameState', JSON.stringify(state));
}

const api = async (method, params) => {
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
        
        const result = await api('get_status', { 'nickname': game.nickname });
        game.id = result.id;
        setState(game);
      } catch (error) {
        console.error(error);
      }
};

const getStatus = () => {
    //if (DEBUG) console.debug(`PING ${game.id}`);
    if (!game.id) {
        auth().then(getStatus);
        return;
    }

    // TODO: bad id
    api('get_status', { 'id': game.id, 'ready': game.isReady }).then((res) => {
        if (game.players != res.players) {
            game.players = res.players;
            game.playersReadiness = res.isReady; // TODO: 
            showLobby();
        }
    });        
} 

const showLobby = () => {
    const playersList = document.getElementById("playersList");
    playersList.innerHTML = '';

    for (let playerName of game.players) {
        let li = document.createElement("li");
        li.appendChild(document.createTextNode((game.playersReadiness[game.players.indexOf(playerName)] =='True'?'🟢 ':'🟡 ')+playerName)); // TODO: players + ready
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

// -----------------------------------------------------

const defaultState = {
    isReady: false
};

let game = getState() || defaultState;
document.game = game; // DEBUG only

getStatus();
setInterval(getStatus, PING_INTERVAL);

document.getElementById('isReadyBtn').addEventListener('click', getReady);
