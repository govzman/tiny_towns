export const showMessage = (msg) => {
    // TODO: rewrite
    //alert(msg);
};

export const showDialog = (htmlContent, callback) => {
    const dialog = document.getElementById('dialog');
    dialog.style.display = 'flex';
    dialog.innerHTML = htmlContent;
    dialog.addEventListener('click', (e) => {
        callback(e);
        //dialog.style.display = 'none';
    }, true);
};
