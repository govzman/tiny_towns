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
        
        if (!result.player_id) {
            // TODO Exception
            console.error('NO ID', result);
            return;
        }       
        game.player_id = result.player_id;
        setState();
        startTimer();
      } catch (error) {
        console.error(error);
      }
};

const setGameStage = (newStage = game.stage, turnNum = 0) => {
    // if (!newStage){
    //     return setGameStage(game.game_stage);
    // }

//    if (game.game_stage != newStage) {
        if (newStage != 'lobby') {
            qs('#isReadyBtn').disabled = true;
        }
        toggleReadyBtn();
        //game.isReady = false;
        game.stage = newStage;
        game.turn.num = turnNum;
        console.debug('SET STAGE', newStage, turnNum);     
  //  }
};

const getStatus = () => {    
    if (!game.player_id) {
        console.error('NO ID!!!!!')
        //auth().then(getStatus);
        return;
    }

    // if (DEBUG) console.debug(`PING ${game.id}`);

    // TODO: bad id
    api('get_status', {'player_id': game.player_id, 'ready': game.isReady, 'stage': game.stage}).then((res) => {
        console.debug('GET_STATUS', game.isReady, game.stage, res);
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
        
        // TODO: check stage in [lobby choose_monument main_game] -> Unknown stage!
        if (game.stage == 'main_game' && game.turn.num != res.turn) {
            console.log('OOO', game.turn )
            setGameStage(game.stage, res.turn);    
        }

        if (game.stage != res.params.stage || !game.currentPage) {
            showPage(res.params.stage, res.params);
            setGameStage(res.params.stage);
            game.log.push('Started...');
            //showLog();
            
            if (game.stage == 'choose_monument') {
                setAnnounce('Monuments stage...');
                
            }

            if (game.stage == 'main_game') {
                game.player.monument = res.params.player.monument;
                //game.is
                // TODO:
                game.turn.master = 0;
                game.turn.step = 2;
                game.turn.resource = 'yellow';
                //console.info(`!!!! TURN ${res.turn}`)
                /////////setAnnounce(`Turn #${res.turn}: Master ${res.params.MasterBuilder} choosed ${game.turn.resource}`);
            }
        }
        // TODO:

        // setAnnounce()

        updatePlayersList(res.params);

        if (game.stage == 'main_game') {
            setAnnounce(`Turn #${res.turn}: Master ${game.players[res.params.MasterBuilder]} have choosen ${game.turn.resource}`);
            // res.params.isReady[game.id] = false
        }
    });        
}

const isEqual = (a, b) => {
    // TODO: rewrite this dirty hack
    // Doc: https://stackoverflow.com/questions/3115982/how-to-check-if-two-arrays-are-equal-with-javascript
    return JSON.stringify(a) == JSON.stringify(b);
};

const updatePlayersList = (params) => {
    if (!isEqual(game.players,params.players) || !isEqual(game.playersReadiness, params.isReady)) {
        game.players = params.players;
        game.playersReadiness = params.isReady;
        
        const playersList = qs("#playersList");
        playersList.innerHTML = '';

        for (let playerName of game.players) {
            //if (playerName == game.nickname) continue;
            const status = game.playersReadiness[game.players.indexOf(playerName)] ? `<strong>${playerName}</strong>` : `${playerName}`;//'🟢':'🟡';
            playersList.innerHTML += `<div>${status} <span class="scores"> 0 <img src="assets/coin.png" style="width: 20px;margin-bottom:-5px;"></span>${getMiniBoard()}</div>`;            
        }                      
    }
};

const getMiniBoard = () => {
    return `
        <table class=miniboard>
            <tr><td></td><td></td><td></td><td></td></tr>
            <tr><td></td><td></td><td></td><td></td></tr>
            <tr><td></td><td></td><td></td><td></td></tr>
            <tr><td></td><td></td><td></td><td></td></tr>
        </table>`;
};

const setAnnounce = (announceText) => {
    document.getElementById('announce').textContent = announceText;
}

const writeLog = (message) => {
    // TODO: check XSS
    //document.getElementById('log').innerHTML = game.log.join('<br>');
    document.getElementById('log').append(message+'\n') // insertAdjacentHTML('beforebegin', message);
}

const getBuildigsList = (bulidingRow) => {
    if (!bulidingRow) return 'NO BUILDINGS'; // TODO

    let buildingsList = '';
    for (let building of bulidingRow) {
        buildingsList += `<img src="/assets/buildings/${building}.png">`
    }
    
    return buildingsList;
}

const showPage = (pageName = 'lobby', params = {}) => {  
    //console.log('TEST', pageName, game.currentPage, pageName == game.currentPage)  
    if (pageName == game.currentPage) return false;
    console.debug('SHOW_PAGE', pageName, params);
    
    if (pageName == 'lobby') {
        //document.getElementById('main').innerHTML = `<h1>Willkommen!</h1>`;
        setAnnounce('Hello!')
        //document.getElementById('isReadyBtn').addEventListener('click', isReadyBtn); 
    }

    if (pageName == 'choose_monument') {
        qs('#main').innerHTML = `
            <div id="bulidingRow">
                ${getBuildigsList(params.bulidingRow)}
            </div>
            <h2>Choose your monument:</h2>
            <div id="choose_monument">
            
                    <!--<b>${MONUMENT_NAMES[params.player.monuments[0]]}:</b>-->
                    <img class=cards id=monument1 data-name="${params.player.monuments[0]}" src="assets/cards/${params.player.monuments[0]}.webp">
                
                    <!--<b>${MONUMENT_NAMES[params.player.monuments[1]]}:</b>-->
                    <img class=cards id=monument2 data-name="${params.player.monuments[1]}" src="assets/cards/${params.player.monuments[1]}.webp"> 

            </div>`;

            qs('#choose_monument').addEventListener('click', (e) => {                
                if (e.target.id == 'choose_monument') return;

                e.target.classList.add('selected_card');
                qs('#isReadyBtn').disabled = false;
                
                if (e.target.id == 'monument1') {
                    qs('#monument2').classList = ['cards'];                    
                } else {
                    qs('#monument1').classList = ['cards'];                             
                }
                game.player.monument = e.target.dataset.name;
                api('set_monument', {        
                    "stage": "choose_monument",
                    "monument": e.target.dataset.name,
                    "player_id": game.player_id
                    })
                .then((res) => {
                    if (res['status'] == 'ok')  {
                        game.player.monument = e.target.dataset.name;
                        console.debug('MONUMENT', e.target.dataset.name);
                    } else {
                        alert('Error: bad monument');
                        console.error('SET_MONUMENT', res)
                    }
                });
            });
            //qs('#isReadyBtn').disabled = true;
    }

    if (pageName == 'main_game') {        
        qs('#main').innerHTML = `
      <div id="bulidingRow">
        ${getBuildigsList(params.bulidingRow)}
      </div>
      <div id="myboard">
      <div id="resources">
        <div class="brick red"></div>
        <div class="brick blue"></div>
        <div class="brick brown"></div>
        <div class="brick yellow"></div>
        <div class="brick white"></div>
      </div>
    
        <table>
            <tr><td></td><td></td><td></td><td></td></tr>
            <tr><td></td><td></td><td></td><td></td></tr>
            <tr><td></td><td></td><td></td><td></td></tr>
            <tr><td></td><td></td><td></td><td></td></tr>
        </table>
        
        <div id=yourMonument>
            <img class="cards" src="/assets/cards/${params.player.monument}.webp">
        </div>       
      </div>
      
      `;    
        
        qs('#myboard').addEventListener('click', (e) => {
            if (game.turn.step !== 2) return;
            if (e.target.nodeName == 'TD') {
                const x = e.target.parentElement.rowIndex;
                const y =  e.target.cellIndex;
                const color = 'yellow'; // TODO: get color
                //console.debug('COORDS', x,y);

                qs('#isReadyBtn').disabled = false;
                
                for (let selected of document.querySelectorAll('.selected')) {
                    selected.className = '';
                }
                e.target.classList.add('selected', 'brick', color); //e.target.className == '' ? 'selected' : '';
                game.movement = {};
                game.movement[`${y},${x}`] = game.turn.resource;
                writeLog(`Выбран ${game.turn.resource} на ${y}, ${x}`)               

            }        
        });
    }
    game.currentPage = pageName;    
};

const isReadyBtn = (isReady = false) => {
    
    if (game.stage == 'main_game' && game.turn.step == 2) {
        if (!Object.keys(game.movement).length) {
            alert('Make a move!');
            return;
        }
        api('place_resource', {        
            "movement": game.movement,
            "player_id": game.player_id
            })
        .then((res) => {
            console.debug('PLACE_RESOURCE', res);
            if (res.success) {
                // TODO: game.turn.step = 1;
                writeLog('Вы разметили ресурс.');
                for (let i=0;i<1;i++) {
                    const x = Object.keys(res.cords)[i].split(',')[0];
                    const y = Object.keys(res.cords)[i].split(',')[1];
                    //const color = res.cords[`${x},${y}`]
                    qs('#myboard').children[1].rows[y].cells[x].classList.remove('selected') // classList.add('brick',color) // TODO: putResource()
                }
                //isReadyBtn();
                game.turn.step = 3;
            } else {
                alert("Не могу разместить ресурс")
            }
        });        
    }
    toggleReadyBtn(isReady);      
};

const toggleReadyBtn = (isReady) => {
    game.isReady = isReady;
    
    qs('#isReadyBtn').textContent = isReady ? 'Waiting...' : 'Ready!';
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
    api('log_out', {'player_id': game.player_id}).then(() => {
        localStorage.clear();
        window.location.reload();
    });
    return false;
}

// -----------------------------------------------------

const defaultState = {
    isReady: false,
    stage: "lobby",
    turn: {
        // step: 1,
        //resource: '',
        //master: ''
    },
    log: [],
    movement: {},
    player: {
        // NB: monument
    }
};

let game = getState() || defaultState;
setGameStage();
window.game = game; // DEBUG only

if (game.player_id) {
    startTimer();
} else {
    auth();
}
qs('#nickname').textContent = game.nickname;

//game.log = [];

qs('#restartBtn').addEventListener('click', restartGame);
qs('#logOutBtn').addEventListener('click', logOut);
qs('#isReadyBtn').addEventListener('click', () => isReadyBtn(!game.isReady)); 