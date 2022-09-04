const DEBUG = true;
const PING_INTERVAL = 2000;
const MONUMENT_NAMES = {
    'Arch_Guild': 'Architect`s Guild',
    'Arch_Age': 'Archive of the Second Age',
    'Bar_Cast': 'Barrett Castle',
    'Cath_Cat': 'Cathedral of Caterina',
    'Fort_Iron': 'Fort Ironweed',
    'Grove_Un': 'Grove University',
    'Mand_Pal': 'Mandras Palace',
    'Opal_Wat': 'Opaleyes Watch',
    'Shr_Tree': 'Shrine of the Elder Tree',
    'Sil_For': 'Silva Forum',
    'Star': 'The Starloom',
    'Stat_Bond': 'Statue of the Bondmaker',
    'Rodina': 'Grand Mausoleum of the Rodina',
    'Sky_Bath': 'The Sky Baths',
    'Crescent': 'Obelisk of the Crescent'
};

const getState = () => {
    return JSON.parse(localStorage.getItem('gameState'));
}

const setState = (state) => {
    localStorage.setItem('gameState', JSON.stringify(state));
}

const api = async (method, params={}) => {
    try {
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
                // NB: https://boardgamegeek.com/thread/2227286/monument-tier-list
                game.ready = false; // TODO: check this?

                document.getElementById('lobby').innerHTML = `<h3>Choose your monument</h3>
                    <div style="display:flex;">                        
                        <div>
                            <b>${MONUMENT_NAMES[res.monuments[0]]}</b>
                            <img class=cards src="assets/cards/${res.monuments[0]}.webp">
                        </div>
                        <div>
                            <b>${MONUMENT_NAMES[res.monuments[1]]}</b>
                            <img class=cards src="assets/cards/${res.monuments[1]}.webp">
                        </div>
                    </div>`;
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

game.ready = false; // TODO !
// document.game = game; // DEBUG only

getStatus();
setInterval(getStatus, PING_INTERVAL);

document.getElementById('isReadyBtn').addEventListener('click', getReady);
document.getElementById('restartBtn').addEventListener('click', restartGame);