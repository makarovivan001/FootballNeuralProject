function authorization_show_window() {
    document.querySelector('.authorization-window').style.display = "flex";
}

function authorization() {
    request({
        url: '/api/v1/login/',
        method: "POST",
        data: {
            login: document.getElementById('login').value,
            password: document.getElementById('password').value,
        }
    }).then(data => {
        location.reload();
    });
}

function logout() {
    request({
        url: '/api/v1/logout/',
        method: "POST",
    }).then(data => {
        location.reload();
    });
}

function authorization_hide_window() {
    document.querySelector('.authorization-window').style.display = "none";
}