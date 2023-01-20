const DEBUG = true;
const PING_INTERVAL = 2000;

const buildings = {
    'Cottage':[['', 'yellow'],['red', 'blue']],
    'Fountain':[['brown'],['grey']],
    'Millstone':[['brown'],['grey']],
    'Shed':[['brown'],['grey']],
    'Well':[['brown'],['grey']],
    'Feast Hall':[['brown'],['brown'],['blue']],
    'Tavern':[['red'],['red'],['blue']],
    'Inn':[['yellow'],['grey'],['blue']],
    'Almshouse':[['grey'],['grey'],['blue']],
    'Temple':[['grey', 'blue'],['red', ''],['red', '']],
    'Abbey':[['grey', 'blue'],['grey', ''],['red', '']],
    'Chapel':[['grey', 'blue'],['blue', ''],['grey', '']],
    'Cloister':[['grey', 'blue'],['red', ''],['brown', '']],
    'Orchard':[['yellow', 'brown'],['grey', 'yellow']],
    'Farm':[['brown', 'brown'],['yellow', 'yellow']],
    'Granary':[['brown', 'red'],['yellow', 'yellow']],
    'Greenhouse':[['brown', 'brown'],['blue', 'yellow']],
    'Warehouse':[['red', 'yellow'],['', 'brown'],['red', 'yellow']],
    'Factory':[['red', 'brown'],['grey', ''],['grey', ''],['red', '']],
    'Trading Post':[['grey', 'grey'],['brown', 'brown'],['red', '']],
    'Bank':[['brown', 'yellow'],['blue', 'yellow'],['red', '']],
    'Theatre':[['brown', ''],['blue', 'grey'],['brown', '']],
    'Bakery':[['red', ''],['blue', 'yellow'],['red', '']],
    'Tailor':[['grey', ''],['blue', 'yellow'],['grey', '']],
    'Market':[['grey', ''],['blue', 'brown'],['grey', ''] ] 
}

const getPatterns = (buildingName) => {
    const rotate = (matrix, count = 1) => {
        for (let i=0; i<count; i++) {
            matrix = matrix[0].map((val, index) => matrix.map(row => row[index]).reverse())
        }
        return matrix;
    }
         
    const transpose = (matrix) => {        
        let [row] = matrix;
        return row.map((value, column) => matrix.map(row => row[column]))
    }
    
    const mirrorV = (matrix) => rotate(transpose(matrix))
    const mirrorH = (matrix) => mirrorV(rotate(mirrorV(transpose((matrix)))));
    
    let patterns = []
    const m = buildings[buildingName];

    for (let i=0;i<4;i++) {
        patterns.push(rotate(m, i));
        patterns.push(rotate(mirrorH(m),i))
        patterns.push(rotate(mirrorV(m),i))
        patterns.push(rotate(mirrorH(mirrorV(m)),i))    
    }
    return patterns;
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
        game.turn.currentResource = false;
        console.debug('SET STAGE', newStage, turnNum);     
  //  }
};

const getStatus = () => {    
    if (!game.player_id) {
        console.error('NO ID!!!!!')
        //auth().then(getStatus);
        return;
    }

    api('get_status', {'player_id': game.player_id, 'ready': game.isReady,  'stage': game.stage}).then((res) => { // OLD: 'turn_num': game.turn.num, 
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
            //console.log('OOO', game.turn, res )
            setGameStage(game.stage, res.turn);
        }

        if (game.stage != res.params.stage || !game.currentPage) {
            showPage(res.params.stage, res.params);
            setGameStage(res.params.stage);
            //game.log.push('Started...');
            //showLog();
            
            if (game.stage == 'choose_monument') {
                setAnnounce('Monuments stage...');                
            }
        }
        
        updatePlayersList(res.params);

        if (game.stage == 'main_game') {
            game.player.monument = res.params.player.monument;
            game.turn.master = res.params.MasterBuilder;
            game.turn.currentResource = res.params.currentResource || false;            

            document.getElementById('log').innerText = res.params.events.join('\n'); // TODO:

            qs('#resources').className = ( isMaster() && !game.turn.currentResource ) ? 'selectable' : '';                
            
            setAnnounce(`Turn #${game.turn.num}: ` + (game.turn.currentResource ?`Master ${game.players[res.params.MasterBuilder]} has choosen ${game.turn.currentResource}. Place it!` : (game.players[res.params.MasterBuilder] != game.nickname ? `Waiting for ${game.players[res.params.MasterBuilder]}` : 'Your turn, Master! Choose resourse...')) );  // REWRITE

            if (game.isReady == undefined || JSON.stringify(game.playersBoards[game.myNum]) != JSON.stringify(res.params.playersBoards[game.myNum])) { // TODO: REWRITE
                updateBoard();
            }
        }
    });        
}

const isEqual = (a, b) => {
    // TODO: rewrite this dirty hack
    // Doc: https://stackoverflow.com/questions/3115982/how-to-check-if-two-arrays-are-equal-with-javascript
    return JSON.stringify(a) == JSON.stringify(b);
};

const updateBoard = () => {
    console.log("UPDATE") 
    //const myNum = game.players.indexOf(game.nickname); // TODO: REWRITE

    //console.log('MYBOARD',game.playersBoards[myNum], res.params.playersBoards[myNum])
    game.isReady = false;
    const td = qs('#myboard').childNodes[3].getElementsByTagName('td');
    for (let x=0; x<4; x++) {
        for (let y=0; y<4; y++) {
            const figure = game.playersBoards[game.myNum][x][y];
            td[x*4+y].className =  figure.includes('_house') ? figure : `brick ${figure}`;
        }
    }
}

const updatePlayersList = (params) => {    
    if (JSON.stringify(params.playersBoards) != JSON.stringify(game.playersBoards) || !isEqual(game.players,params.players) || !isEqual(game.playersReadiness, params.isReady)) { // WTF! TODO!
        game.players = params.players;
        game.playersReadiness = params.isReady;
        game.playersBoards = params.playersBoards;
        game.myNum = params.players.indexOf(game.nickname)
        
        const playersList = qs("#playersList");
        playersList.innerHTML = '';

        for (let playerName of game.players) {
            //if (playerName == game.nickname) continue;
            const playerNum = game.players.indexOf(playerName);
            
            // <span class="scores"> 0 <img src="assets/coin.png" style="width: 20px;margin-bottom:-5px;"></span>
            playersList.innerHTML += `<div class="${isMaster(playerNum)?'master':''}"><strong class="playername ${game.playersReadiness[playerNum]? 'ready':""}">${status} ${playerName}</strong>${getMiniBoard(playerNum)}</div>`;            
        }                      
    }
};

const getMiniBoard = (playerNum, pattern = false) => {
    if (!game.playersBoards) return ''; //<table class=miniboard><tr><td/><td/><td/><td/></tr><tr><td/><td/><td/><td/></tr><tr><td/><td/><td/><td/></tr><tr><td/><td/><td/><td/></tr></table>'; // REWRITE    
    let miniboard = [];
    for (let i=0;i<4;i++) {        
        let cols = [];
        for (let j=0;j<4;j++) {
            const highlighted = pattern && pattern.includes(`${i},${j}`);            
            cols.push(`<td class="${game.playersBoards[playerNum][i][j]}${highlighted ? ' highlighted':''}"></td>`);
        }
        miniboard.push(`<tr>${cols.join('')}</tr>`)
    }
    return `<table class=miniboard>${miniboard.join('')}</table>`;
};

const setAnnounce = (announceText) => {
    document.getElementById('announce').textContent = announceText;
}

// const writeLog = (message) => {
//     // TODO: check XSS
//     //document.getElementById('log').innerHTML = game.log.join('<br>');
//     document.getElementById('log').append(message+'\n') // insertAdjacentHTML('beforebegin', message);
// }

const getBuildigsList = (bulidingRow, selectable = true) => {
    if (!bulidingRow) return 'NO BUILDINGS'; // TODO

    let buildingsList = '';
    for (let building of bulidingRow) {
        const buildingName = building.split(':')[1];
        const buildingType = building.split(':')[0];
        buildingsList += `<div class="${selectable?'cards':'cards notSelectable'}" data-type="${buildingType}_house" id="${buildingName}" style="background-image: url('/assets/buildings/${buildingName}.png');"></div>`
    }
    
    return buildingsList;
}

const showPage = (pageName = 'lobby', params = {}) => {  
    if (pageName == game.currentPage) return false;
        
    if (pageName == 'lobby') {
        setAnnounce('Hello!')        
    }

    if (pageName == 'choose_monument') {
        qs('#main').innerHTML = `
            <div id="bulidingRow">
                ${getBuildigsList(params.bulidingRow, false)}
            </div>
            <h2>Choose your monument:</h2>
            <div id="choose_monument">            
                    <div class=cards id=monument1 data-name="${params.player.monuments[0]}" style="background-image:url('assets/cards/${params.player.monuments[0]}.webp');"></div>                
                    <div class=cards id=monument2 data-name="${params.player.monuments[1]}" style="background-image:url('assets/cards/${params.player.monuments[1]}.webp');"></div>
            </div>`;

            qs('#choose_monument').addEventListener('click', (e) => {                
                if (e.target.id == 'choose_monument') return;

                e.target.classList.add('selected');
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
        <div id="resources" class="selectable">
            <div class="brick red"></div>
            <div class="brick blue"></div>
            <div class="brick brown"></div>
            <div class="brick yellow"></div>
            <div class="brick grey"></div>
        </div>    
        <table>
            <tr><td></td><td></td><td></td><td></td></tr>
            <tr><td></td><td></td><td></td><td></td></tr>
            <tr><td></td><td></td><td></td><td></td></tr>
            <tr><td></td><td></td><td></td><td></td></tr>
        </table>        
        <div id=yourMonument>
            <div class="cards" style="background-image: url('/assets/cards/${params.player.monument}.webp');"></div>
        </div>       
      </div>
      
      `;    
        
        qs('#resources').addEventListener('click', (e) => {
            
            if (!isMaster()) {
                //alert('You are not master!');
                return;
            }
            
            if (e.target.className.includes('brick')) {
                const resource = e.target.className.split(' ')[1]; // TODO: rewrite
                api('choose_resource', {'player_id': game.player_id, 'resource': resource}).then( res => {
                    console.log('CHOOSE_RESOURCE', res);
                });
            }
        });

        qs('#bulidingRow').addEventListener('click', (e) => {
            const buildingName = e.target.id;

            if (!buildingName) return;
            //console.debug('CHECK_BUILDING', buildingName);
            // TODO: document.getElementById(buildingName).classList.add('selected');

            const myboard = game.playersBoards[game.players.indexOf(game.nickname)];
            
            game.building = {
                name: buildingName,
                type: e.target.dataset.type,
                cells: [],
                patterns: []
            };
            for (let pattern of getPatterns(buildingName)) {
                const patternWidth = pattern.length;
                const patternHeight = pattern[0].length;
                

                for (let i=0;i<=4-patternWidth;i++) {
                    for (let j=0;j<=4-patternHeight;j++) { 
                        let patternCellsCount = 0;                  
                        let matchedCoords = [];
                        for (let x=0;x<patternWidth;x++) {
                            for (let y=0;y<patternHeight;y++) {
                                
                                if (!pattern[x][y]) continue;                                
                                if (myboard[i+x][j+y] == pattern[x][y]) {                                    
                                    matchedCoords.push(`${i+x},${j+y}`)
                                }
                                patternCellsCount++;
                            }
                        }
                        if (matchedCoords.length == patternCellsCount && !game.building.patterns.includes(JSON.stringify(matchedCoords))) {  // REWRITE
                            game.building.cells.push(...matchedCoords);
                            game.building.patterns.push(JSON.stringify(matchedCoords)); // REWRITE
                        }
                    }
                }
                //console.log('PATTERN', game.building, myboard, pattern);
            }

            const td = qs('#myboard').childNodes[3].getElementsByTagName('td');
            for (let c of game.building.cells) {
                td[parseInt(c.split(',')[0]) * 4 + parseInt(c.split(',')[1])].classList.add('possible');
            }            
            console.log('BUILDING', game.building)       
        });

        qs('#myboard').addEventListener('click', (e) => {            
            if (!game.turn.currentResource && !game.building) return;
            //console.log('CLICK',e)
            
            // To put a building:
            if (e.target.nodeName == 'TD') {
                const x = e.target.parentElement.rowIndex;
                const y =  e.target.cellIndex;   
                //console.debug('COORDS', x,y);

                if (game.building) {                    
                    if (game.building.cells.includes(`${x},${y}`)) {
                        let possiblePatterns = [];
                        for (let p of game.building.patterns) {
                            if (JSON.parse(p).includes(`${x},${y}`)) {
                                possiblePatterns.push(JSON.parse(p));
                            }
                        }
                        //console.log('PATTERN', possiblePatterns);
                        const placeBuilding = (pattern) => {
                            const td = qs('#myboard').childNodes[3].getElementsByTagName('td'); // TODO: rewrite -> updateBoard
                            for (let c of pattern) { 
                                if (c != `${x},${y}`){
                                    td[parseInt(c.split(',')[0]) * 4 + parseInt(c.split(',')[1])].className = '';
                                }
                            }
                            e.target.className = game.building.type;                            
                            
                            api('place_building', {'player_id': game.player_id, x,y, name: game.building.name, cells: pattern}).then((res) => {   // possiblePatterns[patternNum]
                                console.log('PLACE_BUILDING', res);    // TODO: //updateBoard();
                            });
                            game.building = false;
                        }
                        
                        if (possiblePatterns.length == 1) {
                            placeBuilding(possiblePatterns[0]);
                        } else {
                            let boards = '';                            
                            for (let p of possiblePatterns) {
                                boards += `<div data-pattern="${JSON.stringify(p).replaceAll('"',"'")}" style="width: 100px;display:inline-block;">${getMiniBoard(game.myNum, p)}</div>`;                                
                            }
                            qs('#main').innerHTML += '<div id="dialog"><h1>Выберите клетки:</h1>'+boards+'</div>';
                            qs('#dialog').addEventListener('click', (e) => {
                                console.debug('CHOOSE', e)
                                
                                const findParent = (el) => {
                                    while (el.parentNode) {
                                        el = el.parentNode;
                                        if (el.tagName === 'DIV')
                                            return el;
                                    }
                                    return null;
                                };
                                // TODO: REWRITE
                                const pattern = JSON.parse(findParent(e.target).dataset.pattern.replaceAll("'",'"'));
                                console.log("FIND_PARENT", pattern)
                                placeBuilding(pattern);
                                qs('#dialog').remove();
                            })
                        }
                    }
                }
                // To put a resource:
                if (game.turn.currentResource) {
                    // TODO: Проверку на то стоит ли уже на клетке ресурс в момент, когда игрок ставит новый ресурс                    
                    qs('#isReadyBtn').disabled = false;
                    
                    for (let selected of document.querySelectorAll('.selected')) {
                        selected.className = '';
                    }
                    e.target.classList.add('selected', 'brick', game.turn.currentResource); //e.target.className == '' ? 'selected' : '';
                    game.movement = {};
                    game.movement[`${y},${x}`] = game.turn.currentResource;
                    //writeLog(`Выбран ${game.turn.currentResource} на ${y}, ${x}`)   
                }            

            }        
        });
    }
    game.currentPage = pageName;    
};

const isMaster = (playerNum = game.players.indexOf(game.nickname)) => {
    //const res = game.players[game.turn.master] == game.nickname;
    //console.log('MASTER', game.turn.master, game.players, res);
    //return res;
    return game.turn.master == playerNum;
}


const isReadyBtn = (isReady = false) => {
    
    if (game.stage == 'main_game' && game.turn.currentResource) {
        if (!Object.keys(game.movement).length) {
            alert('Make a move!');
            return;
        }
        api('place_resource', {        
            "movement": game.movement,
            'turn_num': game.turn.num,
            "player_id": game.player_id
            })
        .then((res) => {
            //console.debug('PLACE_RESOURCE', res);
            if (res.success) {
                // TODO: game.turn.step = 1;
                //writeLog('Вы разметили ресурс.');
                for (let i=0;i<1;i++) {
                    const x = Object.keys(res.cords)[i].split(',')[0];
                    const y = Object.keys(res.cords)[i].split(',')[1];
                    //const color = res.cords[`${x},${y}`]
                    qs('#myboard').children[1].rows[y].cells[x].classList.remove('selected') // classList.add('brick',color) // TODO: putResource()
                }
                //isReadyBtn();
                ///game.turn.step = 3;
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
    //log: [],
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