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

const setState = () => {
    //console.log('SET_STATE', JSON.stringify(game), game);
    localStorage.setItem('gameState', JSON.stringify(game));
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
       // if (DEBUG) console.debug(method, params, json);
        
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

const setGameStage = (newStage = false) => {
    if (!newStage){
        return setGameStage(game.game_stage);
    }

    if (game.game_stage != newStage) {
        isReadyBtn();        
        game.game_stage = newStage;
        console.debug('STAGE', newStage);     
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
    api('get_status', { 'id': game.id, 'ready': game.isReady, 'game_stage': game.game_stage}).then((res) => {
        if (res.error){
            if (res.error.code == 1) {
                console.error("BAD AUTH");
                logOut(); // TODO
                stopTimer();
                //auth();
            } else {
                qs('#main').innerText = res.error.msg;
                console.error('UNKNOWN ERR', res, res.error);
            }
            return;
        }
        
        showPage(res.game_stage, res.params);
        setGameStage(res.game_stage);

        switch(res.game_stage) {
            case 'lobby':
                updatePlayersList(res.params);
                break;
            case 'choose_monument':
                // NB: https://boardgamegeek.com/thread/2227286/monument-tier-list            
                updatePlayersList(res.params);                
                //showPage('choose_monument', res.params);                
                break;
            case 'main_game':
                showPage('main_game', res.params);
                break;
            default:
                alert('Unknown stage!');
                debugger;
                console.debug('Unknown stage!', res.game_stage, game);
        }
    });        
}

const updatePlayersList = (params) => {
    if (game.players != params.players || game.playersReadiness != params.isReady) {
        game.players = params.players;
        game.playersReadiness = params.isReady;
        
        const playersList = qs("#playersList");
        playersList.innerHTML = '';

        for (let playerName of game.players) {
            if (playerName == game.nickname) continue; // TODO: BUG
            //let li = document.createElement("li");
            const status = game.playersReadiness[game.players.indexOf(playerName)] ? '🟢':'🟡';
            //li.appendChild(document.createTextNode(
                playersList.innerHTML += `<span class="playername">${status} ${playerName}</span>`;
            //playersList.appendChild(li);
        }                      
    }
};

const showPage = (pageName = 'lobby', params = {}) => {
    if (pageName == game.currentPage) return false;
    if (pageName == 'lobby') {
        document.getElementById('main').innerHTML = `<h1>Willkommen!</h1>`;
        //document.getElementById('isReadyBtn').addEventListener('click', isReadyBtn); 
    }

    if (pageName == 'choose_monument') {
        let buildingsList = '';
        for (let building of params.bulidingRow) {
            buildingsList += `<img src="/assets/buildings/${building}.png">`
        }
        qs('#main').innerHTML = `
            <div id="playersList"></div>
            <div id="bulidingRow">
                ${buildingsList}
            </div>
            <div>
            <h2>Choose your monument:</h2>
            <div id="choose_monument">
                    <!--<b>${MONUMENT_NAMES[params.monuments[0]]}:</b>-->
                    <img class=cards id=monument1 data-id="0" src="assets/cards/${params.monuments[0]}.webp">
                
                    <!--<b>${MONUMENT_NAMES[params.monuments[1]]}:</b>-->
                    <img class=cards id=monument2 src="assets/cards/${params.monuments[1]}.webp"> 

            </div></div>`;

            qs('#choose_monument').addEventListener('click', (e) => {
                //console.debug(e);
                if (e.target.id == 'choose_monument') return;

                e.target.classList.add('selected_card');
                if (e.target.id == 'monument1') {
                    qs('#monument2').classList = ['cards'];                             
                } else {
                    qs('#monument1').classList = ['cards'];                             
                }
            });
            
    }

    if (pageName == 'main_game') {
        qs('#main').innerHTML = `<div id="boards">
        <div class="board green">
          <span class="playername">Player 1</span>
          <span class="scores"> 30 <img src="assets/coin.png" style="width: 20px;margin-bottom:-5px;"></span>
        </div>
        <div class="board blue">
          <span class="playername">Player 2</span>
          <span class="scores"> 15 <img src="assets/coin.png" style="width: 20px;margin-bottom:-5px;"></span>
        </div>
        <div class="board red">
          <span class="playername">Player 3</span>
          <span class="scores"> 28 <img src="assets/coin.png" style="width: 20px;margin-bottom:-5px;"></span>
        </div>
      </div>

      <br><br>
      <table>
      <tr>
        <td>
          <div class="myboard">
            <img src="assets/home.png" style="width: 50px;position:relative;top:90px;left:88px;">
            <img src="assets/red.png" style="width: 30px;position:relative;top:155px;left:118px;">
          </div>
        </td>
      
        <td>
        <div id="foo">
          <div id="cards">
            <div class="card"></div>
            <div class="card"></div>
            <div class="card"></div>
            <div class="card"></div>
          </div>

          <div id="resources">
            <div class="brick red"></div>
            <div class="brick blue"></div>
            <div class="brick brown"></div>
            <div class="brick yellow"></div>
            <div class="brick white"></div>
          </div>
        </div>
        </td>
      </tr>
      </table>`;
    }

    game.currentPage = pageName;    
};

const isReadyBtn = (isReady = false) => {
    const button = qs('#isReadyBtn');
    game.isReady = isReady;
    if (isReady) {
        button.textContent = 'Waiting...';        
    } else {
        button.textContent = 'Ready!';        
    }    
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
    return false;
}

// -----------------------------------------------------

const defaultState = {
    isReady: false,
    game_stage: "lobby"
};

let game = getState() || defaultState;
//console.debug('INIT STATE', JSON.stringify(game));
setGameStage();
//game.ready = false; // TODO !
window.game = game; // DEBUG only

if (game.id || game.nickname) {
    startTimer();
} else {
    auth();
}
qs('#nickname').textContent = game.nickname;


qs('#restartBtn').addEventListener('click', restartGame);
qs('#logOutBtn').addEventListener('click', logOut);
qs('#isReadyBtn').addEventListener('click', () => isReadyBtn(!game.isReady)); 