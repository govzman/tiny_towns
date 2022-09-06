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

const qs = (selector) => {
    return document.querySelector(selector);
}

const getState = () => {
    return JSON.parse(localStorage.getItem('gameState'));
}

const setState = (state = game) => {
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
        if (DEBUG) console.debug(method, params, json);
        
        return json;
        
      } catch (error) {
        console.error(error);
      }
};

const auth = async () => {
    try {
        while (!game.nickname) {
            /*document.getElementById('lobby').innerHTML = `<h2>Enter your nickname</h2>
                    <div style="display:flex;">                        
                        <input id="nickname">
                        <button>Ok</button>
                    </div>`;*/
            game.nickname = prompt("Enter nickname: ");
            
            //return;
        }        
        
        const result = await api('get_status', { 'nickname': game.nickname });
        if (result.error){            
            document.getElementById('main').innerText = result.error.msg;
            /////stopTimer();
            return;
        }
        
        if (!result.id) {
            // TODO Exception
            console.error('NO ID', result);
            return;
        }       
        game.id = result.id;
        setState();
        startTimer();
      } catch (error) {
        console.error(error);
      }
};

const getStatus = () => {    
    if (!game.id) {
        console.error('NO ID!!!!!')
        //auth().then(getStatus);
        return;
    }

    if (DEBUG) console.debug(`PING ${game.id}`);

    // TODO: bad id
    api('get_status', { 'id': game.id, 'ready': game.isReady }).then((res) => {
        if (res.error){
            if (res.error.code == 1) {
                console.error("BAD AUTH");
                logOut();               
            } else {
                document.getElementById('lobby').innerText = res.error.msg;
                console.error('UNKNOWN ERR', res, res.error);
            }
            return;
        }
        
        //game.game_stage = res.game_stage;
        switch(res.game_stage) {
            case 'lobby':
                if (game.players != res.params.players) {
                    game.players = res.params.players;
                    game.playersReadiness = res.params.isReady;
                    game.game_stage = 'lobby';
                    showPage('lobby');
                }
                break;
            case 'choose_monument':
                // NB: https://boardgamegeek.com/thread/2227286/monument-tier-list
                game.ready = false; // TODO: check this?

                if (game.game_stage == 'choose_monument') {
                  return; 
                }
                
                game.game_stage = res.params.game_stage;
                showPage('choose_monument', res.params);                
                break;
            default:
                alert('Unknown stage!');                    
        }
    });        
} 

const showPage = (pageName = 'lobby', params = {}) => {
    if (pageName == game.currenPage) return false;
    if (pageName == 'lobby') {
        document.getElementById('main').innerHTML = `
        <div id="lobby">
            <h3>Игроки:</h3>
            <ul id="playersList">
            </ul>
            <button id="isReadyBtn">Start!</button>      
        </div>`;

        const playersList = document.getElementById("playersList");
        playersList.innerHTML = '';

        for (let playerName of game.players) {
            let li = document.createElement("li");
            li.appendChild(document.createTextNode((game.playersReadiness[game.players.indexOf(playerName)]?'🟢 ':'🟡 ')+playerName)); // TODO: players + ready
            playersList.appendChild(li);
        }  
        document.getElementById('isReadyBtn').addEventListener('click', getReady);     
    }

    if (pageName == 'choose_monument') {
        qs('#main').innerHTML = `<div><h2>Choose your monument</h2>
            <div  id="choose_monument" style="display:flex;">                        
                <div>
                    <b>${MONUMENT_NAMES[params.monuments[0]]}:</b>
                    <img class=cards id=monument1 data-id="0" src="assets/cards/${params.monuments[0]}.webp">
                </div>
                <div >
                    <b>${MONUMENT_NAMES[params.monuments[1]]}:</b>
                    <img class=cards id=monument2 src="assets/cards/${params.monuments[1]}.webp">
                </div>
            </div></div>`;
            qs('#choose_monument').addEventListener('click', (e) => {
                e.target.classList.add('selected_card');
                if (e.target.id == 'monument1') {
                    qs('#monument2').classList = ['cards'];                             
                } else {
                    qs('#monument1').classList = ['cards'];                             
                }
            });
            
    }
    game.currenPage = pageName;    
};

const getReady = () => {
    const button = document.getElementById('isReadyBtn');
    game.isReady = !game.isReady;
    if (game.isReady) {
        button.textContent = 'Stop...';        
    } else {
        button.textContent = 'Start!';        
    }
    // Чтоб бысстрее начать: getStatus();
    return false;
};

const restartGame = () => {
    console.debug("RESTART");
    api('restart_game');
    //localStorage.clear();
    document.location.reload();
}

const startTimer = () => {
    getStatus();
    game.timer = setInterval(getStatus, PING_INTERVAL);
}

const stopTimer = () => {
    clearInterval(game.timer);
    console.debug(`Timer ${game.timer} has stopped.`);
}

const logOut = () => {    
    console.debug('LOGOUT');
    stopTimer();
    api('log_out', {'id': game.id}).then(() => {
        localStorage.clear();
        window.location.reload();
    });
    
}

// -----------------------------------------------------

const defaultState = {
    isReady: false
};

let game = getState() || defaultState;

game.ready = false; // TODO !
// document.game = game; // DEBUG only

if (game.id || game.nickname) {
    startTimer();
} else {
    auth();
}
qs('#nickname').textContent = game.nickname;


qs('#restartBtn').addEventListener('click', restartGame);
qs('#logOutBtn').addEventListener('click', logOut);