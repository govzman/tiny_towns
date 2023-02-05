export const qs = (selector) => {
    return document.querySelector(selector);
};

export const getState = () => {
    return JSON.parse(localStorage.getItem('gameState'));
};

export const setState = (gameState) => {
    localStorage.setItem('gameState', JSON.stringify(gameState));
};

export const isEqual = (a, b) => {
    // TODO: rewrite this dirty hack
    // Doc: https://stackoverflow.com/questions/3115982/how-to-check-if-two-arrays-are-equal-with-javascript
    return JSON.stringify(a) === JSON.stringify(b);
};

export const api = async (method, params = {}) => {
    try {
        const response = await fetch('/api', {
            method: 'POST',
            body: JSON.stringify({
                method: method,
                params: params
            }),
            headers: {
                'Content-Type': 'application/json'
            }
        });
        const jsonResponse = await response.json();
        if (window.DEBUG) {
            /* eslint-disable no-console */
            console.debug('API', method, params, jsonResponse);
            /* eslint-disable no-console */
        }

        return jsonResponse;
    } catch (error) {
        /* eslint-disable no-console */
        console.error('API:TRANSPORT', error);
        /* eslint-disable no-console */
    }
};
