import {api, qs, setState, getState, isEqual} from './utils.js';
import {getPatterns} from './game.js';
import {showDialog, showMessage} from './ui.js';

const setAnnounce = (announceText) => {
    document.getElementById('announce').textContent = announceText;
};

window.DEBUG = true;
const PING_INTERVAL = 2000;

const defaultState = {
    isReady: false,
    stage: 'lobby',
    turn: {},
    movement: {},
    player: {}
};

const game = getState() || defaultState;
if (window.DEBUG) {
    window.game = game;
}
window.game = game; // TODO

const imp = (params = {}) => {
    // Impersonate params:
    params.player_id = game.playerId;
    return params;
};

const auth = async () => {
    while (!game.nickname) {
        game.nickname = prompt('Enter nickname: ');
    }

    const result = await api('get_status', {nickname: game.nickname});
    if (result.error) {
        document.getElementById('main').innerText = result.error.msg;
        return;
    }

    game.playerId = result.player_id;
    setState(game);

    getStatus(); // ????
    game.timer = setInterval(getStatus, PING_INTERVAL);
};

const logOut = () => {
    clearInterval(game.timer);
    api('log_out', imp()).then(() => {
        localStorage.clear();
        window.location.reload();
    });
    return false;
};

const getMyPlayerNum = () => {
    return game.players.indexOf(game.nickname);
};

const isMaster = (playerNum = getMyPlayerNum()) => {
    return game.turn.master === playerNum;
};

const toggleReadyBtn = (isReady) => {
    game.isReady = isReady;
    qs('#isReadyBtn').textContent = isReady ? 'Waiting...' : 'Ready!';
};

const onStageChanged = (stageName) => {
    console.log('STAGE CHANGED', stageName);
};

const setGameStage = (stageName = game.stage, turnNum = 0) => {
    console.log('SET_STAGE', stageName);
    if (game.stage !== stageName) {
        onStageChanged(stageName);
    }

    if (stageName !== 'lobby') {
        qs('#isReadyBtn').disabled = true;
    }
    toggleReadyBtn();
    game.stage = stageName;
    game.turn.num = turnNum;
    game.turn.currentResource = false;
};

const updateBoard = () => {
    game.isReady = false;
    const td = qs('#myboard').childNodes[3].getElementsByTagName('td');
    for (let x = 0; x < 4; x++) {
        for (let y = 0; y < 4; y++) {
            const figure = game.playersBoards[game.myNum][x][y];
            td[x * 4 + y].className = figure.includes('_house') ? figure : `brick ${figure}`;
        }
    }
};

const onGetStatus = (res) => {
    if (res.error) {
        if (res.error.code === 1) {
            //showMessage('BAD AUTH'); // TODO
            logOut();
            clearInterval(game.timer);
        }
        return;
    }

    if (game.stage === 'main_game' && game.turn.num !== res.turn) {
        //console.log('OOO', game.turn, res )
        setGameStage(game.stage, res.turn);
    }

    if (game.stage !== res.params.stage) { // || !game.currentPage
        showPage(res.params.stage, res.params);
        setGameStage(res.params.stage);

        if (game.stage === 'choose_monument') {
            setAnnounce('Monuments stage...');
        }
    }

    updatePlayersList(res.params);

    if (game.stage === 'main_game') {
        game.player.monument = res.params.player.monument;
        game.turn.master = res.params.MasterBuilder;
        game.turn.currentResource = res.params.currentResource || false;

        document.getElementById('log').innerText = res.params.events.join('\n'); // TODO:

        qs('#resources').className = (isMaster() && !game.turn.currentResource) ? 'selectable' : '';

        setAnnounce(`Turn #${game.turn.num}: ` + (game.turn.currentResource ? `Master ${game.players[res.params.MasterBuilder]} has choosen ${game.turn.currentResource}. Place it!` : (game.players[res.params.MasterBuilder] !== game.nickname ? `Waiting for ${game.players[res.params.MasterBuilder]}` : 'Your turn, Master! Choose resourse...')));

        if (
            game.isReady === undefined ||  // TODO: REWRITE
            JSON.stringify(game.playersBoards[game.myNum]) !== JSON.stringify(res.params.playersBoards[game.myNum])
        ) {
            updateBoard();
        }
    }
};

const getStatus = () => {
    if (!game.playerId) {
        return;
    }

    api(
        'get_status',
        imp({ready: game.isReady, stage: game.stage})
    ).then(onGetStatus);
};

const updatePlayersList = (params) => {
    if (
        !isEqual(params.playersBoards, game.playersBoards) ||
        !isEqual(game.players, params.players) ||
        !isEqual(game.playersReadiness, params.isReady)
    ) {
        game.players = params.players;
        game.playersReadiness = params.isReady;
        game.playersBoards = params.playersBoards;
        game.myNum = params.players.indexOf(game.nickname);

        const playersList = qs('#playersList');
        playersList.innerHTML = '';

        for (const playerName of game.players) {
            const playerNum = game.players.indexOf(playerName);

            playersList.innerHTML += `
                <div class="${isMaster(playerNum) ? 'master' : ''}">
                    <strong class="playername ${game.playersReadiness[playerNum] ? 'ready' : ''}">
                        ${status} ${playerName}
                    </strong>
                    ${getMiniBoard(playerNum)}
                </div>`;
        }
    }
};

const getMiniBoard = (playerNum, pattern = false) => {
    if (!game.playersBoards) {
        return '';
    }
    const miniboard = [];
    for (let j = 0;j < 4;j++) {
        const cols = [];
        for (let i = 0;i < 4;i++) {
            const highlighted = pattern && pattern.includes(`${i},${j}`);
            cols.push(`<td class="${game.playersBoards[playerNum][j][i]}${highlighted ? ' highlighted' : ''}"></td>`);
        }
        miniboard.push(`<tr>${cols.join('')}</tr>`);
    }
    return `<table class=miniboard>${miniboard.join('')}</table>`;
};

const getBuildigsList = (buildingRow, selectable = true) => {
    let buildingsList = '';
    for (const building of buildingRow) {
        const buildingName = building.split(':')[1];
        const buildingType = building.split(':')[0];
        buildingsList += `
            <div
                class="${selectable ? 'cards' : 'cards notSelectable'}"
                data-type="${buildingType}_house" 
                id="${buildingName}"
                style="background-image: url('/assets/buildings/${buildingName}.png');">
            </div>`;
    }
    return buildingsList;
};

const showPage = (pageName = 'lobby', params = {}) => {
    if (pageName === game.currentPage) {
        return false;
    }

    if (pageName === 'lobby') {
        setAnnounce('Hello!');
    }

    if (pageName === 'choose_monument') {
        //qs('#buildingRow').innerHTML = getBuildigsList(params.bulidingRow, false);
        // TODO:
        const chooseLayout = `
        <div class="buildingRow">
            ${getBuildigsList(params.bulidingRow, false)}
        </div>
        <h2>Choose your monument:</h2>
        <div id="choose_monument">            
            <div 
                class="cards clickable" id=monument1 
                data-name="${params.player.monuments[0]}" 
                style="background-image:url('assets/cards/${params.player.monuments[0]}.webp');"
            ></div>                
            <div
                class="cards clickable" id=monument2
                data-name="${params.player.monuments[1]}"
                style="background-image:url('assets/cards/${params.player.monuments[1]}.webp');"
            ></div>
        </div>`;
        const onChooseMonument = (e) => {
            if (e.target.id === 'choose_monument') {
                return;
            }

            e.target.classList.add('selected');
            qs('#isReadyBtn').disabled = false;

            if (e.target.id === 'monument1') {
                qs('#monument2').classList = ['cards'];
            } else {
                qs('#monument1').classList = ['cards'];
            }
            game.player.monument = e.target.dataset.name;
            api('set_monument', imp({
                stage: 'choose_monument',
                monument: e.target.dataset.name
            }))
                .then((res) => {
                    if (res.status === 'ok') {
                        game.player.monument = e.target.dataset.name;
                        qs('#dialog').style.display = 'none'; // TODO:
                    }
                });
        };
        showDialog(chooseLayout, onChooseMonument);
    }

    if (pageName === 'main_game') {
        qs('#buildingRow').innerHTML = getBuildigsList(params.bulidingRow);
        qs('#yourMonument').style.backgroundImage = `url('/assets/cards/${params.player.monument}.webp')`;
    }
    game.currentPage = pageName;
};

const isReadyBtn = (isReady = false) => {
    qs('#isReadyBtn').className = '';
    if (qs('#myboard')) {
        qs('#myboard').className = '';
    } // no active

    if (game.stage === 'main_game' && game.turn.currentResource) {
        if (!Object.keys(game.movement).length) {
            return;
        }
        api('place_resource', imp({
            movement: game.movement,
            turn_num: game.turn.num
        }))
            .then((res) => {
                if (res.success) {
                    for (let i = 0;i < 1;i++) {
                        const x = Object.keys(res.cords)[i].split(',')[0];
                        const y = Object.keys(res.cords)[i].split(',')[1];

                        qs('#myboard').children[1].rows[y].cells[x].classList.remove('selected');
                    }
                }
            });
    }
    toggleReadyBtn(isReady);
};

// -----------------------------------------------------
setGameStage();
if (game.playerId) {
    getStatus(); // ???
    game.timer = setInterval(getStatus, PING_INTERVAL);
} else {
    auth();
}
qs('#nickname').textContent = game.nickname;

// EVENT LISTENERS
qs('#logOutBtn').addEventListener('click', logOut);
qs('#isReadyBtn').addEventListener('click', () => isReadyBtn(!game.isReady));
qs('#restartBtn').addEventListener('click', () => {
    api('restart_game');
    document.location.reload();
});

qs('#buildingRow').addEventListener('click', (e) => {
    const buildingName = e.target.id;

    if (!buildingName) {
        return;
    }

    const myboard = game.playersBoards[game.players.indexOf(game.nickname)];

    game.building = {
        name: buildingName,
        type: e.target.dataset.type,
        cells: [],
        patterns: []
    };
    for (const pattern of getPatterns(buildingName)) {
        const patternWidth = pattern[0].length;
        const patternHeight = pattern.length;

        for (let i = 0;i <= 4 - patternWidth;i++) {
            for (let j = 0;j <= 4 - patternHeight;j++) {
                let patternCellsCount = 0;
                const matchedCoords = [];
                for (let x = 0;x < patternWidth;x++) {
                    for (let y = 0;y < patternHeight;y++) {
                        if (!pattern[y][x]) {
                            continue;
                        }
                        if (myboard[y + j][x + i] === pattern[y][x]) {
                            matchedCoords.push(`${i + x},${j + y}`);
                        }
                        patternCellsCount++;
                    }
                }
                if (
                    matchedCoords.length === patternCellsCount &&
                    !game.building.patterns.includes(JSON.stringify(matchedCoords))
                ) {  // REWRITE
                    game.building.cells.push(...matchedCoords);
                    game.building.patterns.push(JSON.stringify(matchedCoords)); // REWRITE
                }
            }
        }
    }

    const td = qs('#myboard').childNodes[3].getElementsByTagName('td');
    for (const c of game.building.cells) {
        td[parseInt(c.split(',')[1], 10) * 4 + parseInt(c.split(',')[0], 10)].classList.add('possible');
    }
});

qs('#myboard').addEventListener('click', (e) => {
    if (!game.turn.currentResource && !game.building) {
        return;
    }

    if (e.target.nodeName === 'TD') {
        const x = e.target.cellIndex;
        const y = e.target.parentElement.rowIndex;

        // To put a building:
        if (game.building && game.building.cells.includes(`${x},${y}`)) {
            const placeBuilding = (pattern, cellX, cellY, type, name) => {
                // TODO: rewrite -> updateBoard
                const td = qs('#myboard').childNodes[3].getElementsByTagName('td');
                for (const c of pattern) {
                    if (c !== `${cellX},${cellY}`) {
                        td[parseInt(c.split(',')[0], 10) + 4 * parseInt(c.split(',')[1], 10)].className = '';
                    }
                }
                td[cellX + cellY * 4].className = type;

                api('place_building', imp({x: cellX, y: cellY, name, cells: pattern}));
                game.building = false;
            };

            const possiblePatterns = [];
            const buildingName = game.building.name;
            const buildingType = game.building.type;

            for (const p of game.building.patterns) {
                if (JSON.parse(p).includes(`${x},${y}`)) {
                    possiblePatterns.push(JSON.parse(p));
                }
            }

            if (possiblePatterns.length === 1) {
                placeBuilding(possiblePatterns[0], x, y, buildingType, buildingName);
                return;
            } else {
                let boards = '';
                for (const p of possiblePatterns) {
                    boards += `
                        <div 
                            data-pattern="${JSON.stringify(p).replaceAll('"', '\'')}"
                            style="width: 100px;display:inline-block;"
                        >
                            ${getMiniBoard(game.myNum, p)}
                        </div>`;
                }

                showDialog(
                    `
                    <h1>Choose the cells:</h1>
                    <div>${boards}</div>
                    <button onClick="document.getElementById('dialog').style.display = 'none'">Cancel</button>
                `, (e) => {
                        const findParent = (el) => {
                            while (el.parentNode) {
                                el = el.parentNode;
                                if (el.tagName === 'DIV') {
                                    return el;
                                }
                            }
                            return null;
                        };
                        // TODO: REWRITE
                        if (!findParent(e.target).dataset.pattern) {
                            return false;
                        }

                        const pattern = JSON.parse(findParent(e.target).dataset.pattern.replaceAll('\'', '"'));
                        placeBuilding(pattern, x, y, buildingType, buildingName);
                        qs('#dialog').style.display = 'none';//remove();
                    });

                return;
            }
        }

        // To put a resource:
        if (game.turn.currentResource) {
            qs('#isReadyBtn').disabled = false;

            for (const selected of document.querySelectorAll('.selected')) {
                selected.className = '';
            }
            e.target.classList.add('selected', 'brick', game.turn.currentResource);
            game.movement = {};
            game.movement[`${x},${y}`] = game.turn.currentResource;
        }
        qs('#isReadyBtn').className = 'blink';
    }
});

qs('#resources').addEventListener('click', (e) => {
    if (isMaster() && e.target.className.includes('brick')) {
        const resource = e.target.className.split(' ')[1]; // TODO: rewrite
        game.turn.currentResource = resource;

        qs('#resources').className = '';
        //qs('#isReadyBtn').className = 'blink';
        qs('#myboard').className = 'active';

        api('choose_resource', imp({resource: resource}));
    }
});
