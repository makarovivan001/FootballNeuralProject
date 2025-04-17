window.onload = function() {
   get_clubs();
}

function get_clubs() {
    request({
        url: '/api/v1/club/',
        func: showClubs,
    });
}

function showClubs(data) {
    let clubs = data.clubs;
    let up_line = '';
    let middle_line = '';
    let down_line = '';
    for (let i = 0; i<4; i++) {
        up_line += `<div class="club-info" data-id="${clubs[i].id}" onclick="get_club_info(this)">
                            <img src="${clubs[i].photo}" alt="">
                        </div>`;
    }
    for (let i = 4; i<8; i++) {
        middle_line += `<div class="club-info" data-id="${clubs[i].id}" onclick="get_club_info(this)">
                            <img src="${clubs[i].photo}" alt="">
                        </div>`;
    }
    for (let i = 8; i<data.clubs.length; i++) {
        down_line += `<div class="club-info" data-id="${clubs[i].id}" onclick="get_club_info(this)">
                            <img src="${clubs[i].photo}" alt="">
                        </div>`;
    }
    document.querySelector('.club-up-block').insertAdjacentHTML('beforeEnd', up_line);
    document.querySelector('.club-middle-block').insertAdjacentHTML('beforeEnd', middle_line);
    document.querySelector('.club-down-block').insertAdjacentHTML('beforeEnd', down_line);
}

function get_club_info(elem) {
    let id = elem.dataset.id;
    request({
        url: `/api/v1/club/${id}/`,
    }).then(data => {
        let section_club = document.querySelector('.section-club');
        section_club.style.display = 'flex';
        let player_list_block = document.querySelector('.main-player-list-block');
        let inner_html = '';
        data.player.forEach(player => {
            inner_html += `<div class="player-card">
                                <div class="player-img-block" onclick="show_player_card(${player.id})">
                                    <img src="${player.photo}" alt="" class="player-img">
                                </div>
                                <h3 class="player-title">${player.surname} ${player.name} ${player.middle_name ?? ''}</h3>
                                <div>
                                    <p class="player-number">Номер: ${player.number}</p>
                                    <p class="player-country">Страна: ${player.country_of_birth.name}</p>
                                </div>
                            </div>`;
        });
        player_list_block.insertAdjacentHTML('beforeEnd', inner_html);
        let club_img = document.querySelector('.club-img');
        let club_title = document.querySelector('.club-title');
        let club_desc = document.querySelector('.club-desc');
        let club_coach_title = document.querySelector('.club_coach-title');
        club_img.src = data.photo;
        club_title.innerText = data.name;
        club_desc.innerText = data.description;
        club_coach_title.innerText = `Главный тренер: ${data.coach.surname} ${data.coach.name} ${data.coach.middle_name ?? ''}`;

    });
}

function close_club_info() {
    let section_club = document.querySelector('.section-club');
    section_club.style.display = 'none';
    let player_list_block = document.querySelector('.main-player-list-block');
    player_list_block.innerHTML = ''
}


