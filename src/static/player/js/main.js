function show_add_player(id=null) {
    document.querySelector('.add-player-window').style.display = "flex";

    get_player_form();
    if (id) {
        fill_player_form_fields(id);
        document.getElementById('player_save_btn').dataset.id = id;
    }
}

function hide_add_player() {
    document.querySelector('.add-player-window').style.display = "none";
    document.getElementById("country_of_birth_id").innerHTML = '';
    document.getElementById("club_id").innerHTML = '';
}

function get_player_values() {
    let formData = new FormData();
    let surname = document.getElementById('surname').value;
    if (surname !== '') {
        formData.append('surname', surname);
    } else {
        alert('Вы не заполнили имя');
        throw {}
    }
    formData.append('name', document.getElementById('name').value);
    formData.append('middle_name', document.getElementById('middle_name').value);
    formData.append('number', document.getElementById('number').value);
    formData.append('country_of_birth_id', document.getElementById('country_of_birth_id').value);
    formData.append('club_id', document.getElementById('club_id').value);
    let playerPhotoInput = document.getElementById('player_photo');
    if (playerPhotoInput.files.length !== 0) {
        let playerPhotoFile = playerPhotoInput.files[0];
        formData.append('photo', playerPhotoFile);
    }

    return formData;
}

function add_player() {
    let formData= get_player_values();

    request({
        url: '/api/v1/player/',
        form_data: formData,
        method: 'POST',
    }).then(data => {
        hide_add_player();
    });
}

function edit_player(id) {
    let formData = get_player_values();
    formData.append('id', id);

    request({
        url: '/api/v1/player/',
        form_data: formData,
        method: 'PATCH',
    }).then(data => {
        hide_add_player();
    });
}

function get_player_form() {
    request({
        url: '/api/v1/player/form/',
    }).then(data => {
        let selectCountry = document.getElementById("country_of_birth_id");
        data.countries.forEach(country => {
            let option = document.createElement("option");
            option.value = country.id;
            option.text = country.name;
            selectCountry.appendChild(option);
        });

        let selectClub = document.getElementById("club_id");
        data.clubs.forEach(club => {
            let option = document.createElement("option");
            option.value = club.id;
            option.text = club.name;
            selectClub.appendChild(option);
        });

    });
}

function fill_player_form_fields(id) {
    request({
        url: `/api/v1/player/${id}/`,
    }).then(data => {
        document.getElementById('surname').value = data.surname;
        document.getElementById('name').value = data.name;
        document.getElementById('middle_name').value = data.middle_name;
        document.getElementById('number').value = data.number;
        document.getElementById('country_of_birth_id').value = data.country_of_birth.id;
        document.getElementById('club_id').value = data.club.id;
        document.getElementById('player_save_btn').dataset.id = data.id;

        if (data.photo) {
            document.querySelector('.player_photo_block img').src = data.photo;
        }
    });
}

function player_save(elem) {
    let id = elem.dataset.id;
    if (id) {
        edit_player(id);
    } else {
        add_player();
    }
}

function hide_player_card() {
    document.querySelector('.player-card-window').style.display = "none";
}

function show_player_card(id) {
    request({
        url: `/api/v1/player/${id}/`,
    }).then(data => {
        document.querySelector('.player-card-window').style.display = "flex";
        document.querySelector('.player-name').innerText = `${data.surname} ${data.name}`;
        document.querySelector('.player-club').innerText = data.club.name;
        document.querySelector('.player-photo>img').src = data.photo;
        document.querySelector('.player-details').innerHTML = '';
        document.querySelector('.player-details').insertAdjacentHTML(
            'beforeEnd',
            `<li><strong>Страна рождения:</strong> ${data.country_of_birth.name}</li>
            <li style="font-size: 22px"><strong>Рост/Вес:</strong></li>
            <li style="display: flex; width: 100%">
                <span style="margin-right: 7px"><strong>${data.height} </strong>Рост</span>
                <span><strong>${data.weight} </strong>Вес</span>
            </li>
            <li><strong>Игровой номер:</strong> ${data.number}</li>
            <li><strong>Страна рождения:</strong> ${data.country_of_birth.name}</li>
            <li style="font-size: 26px"><strong>Статистика в сезоне 24/25:</strong></li>
            <li><strong>Матчи:</strong> ${data.games}</li>
            <li><strong>Полные матчи:</strong> ${data.full_games}</li>
            <li style="display: flex; width: 100%">
                <span style="margin-right: 12px"><strong>${data.minutes_played} </strong>Сыгранных минут</span>
                <span style="margin-right: 12px"><strong>${data.goals} </strong>Голы</span>
                <span><strong>${data.assists} </strong>Ассисты</span>
            </li>
            <li><strong>Жёлтые карточки:</strong> ${data.yellow_card}</li>
            <li><strong>Красные карточки:</strong> ${data.red_card}</li>
             <li style="font-size: 26px">Рейтинг:<strong> ${data.rating}</strong></li>`
        );
    })
}
