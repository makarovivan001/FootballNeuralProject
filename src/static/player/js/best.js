function get_bests() {
    request({
        url: '/api/v1/player/best/',
        func: showbests
    });
}

function showbests(data) {
    document.querySelector('.best-up-block').insertAdjacentHTML('beforeEnd', show_best_block(data.best_minutes_played, 'best_minutes_played'));
    document.querySelector('.best-up-block').insertAdjacentHTML('beforeEnd', show_best_block(data.best_goals, 'best_goals'));
    document.querySelector('.best-middle-block').insertAdjacentHTML('beforeEnd', show_best_block(data.best_assists, 'best_assists'));
    document.querySelector('.best-middle-block').insertAdjacentHTML('beforeEnd', show_best_block(data.best_yellow_card, 'best_yellow_card'));
    document.querySelector('.best-down-block').insertAdjacentHTML('beforeEnd', show_best_block(data.best_red_card, 'best_red_card'));
    document.querySelector('.best-down-block').insertAdjacentHTML('beforeEnd', show_best_block(data.best_rating, 'best_rating'));
}

function show_best_block(player, category) {
    let category_text = '';
    if (category === 'best_minutes_played') {
        category_text = 'Больше всего сыгранных минут';
    }
    else if (category === 'best_goals') {
        category_text = 'Лучший бомбардир';
    }
    else if (category === 'best_assists') {
        category_text = 'Лучший ассистент';
    }
    else if (category === 'best_yellow_card') {
        category_text = 'Больше всего жёлтых каточек';
    }
    else if (category === 'best_red_card') {
        category_text = 'Больше всего красных карточек';
    }
    else if (category === 'best_rating') {
        category_text = 'Лучший рейтинг';
    }

    inner_html = ` <div class="best-card-block" onclick="show_player_card(${player.id})">
                        <div class="best-card-category">
                            <h1>${category_text}</h1>
                        </div>
                        <div class="best-card-content">
                            <div class="best-card-img">
                                <img src="${player.photo}" alt="">
                            </div>
                            <div class="best-card-info">
                                <h4 class="best-full_name">${player.full_name}</h4>
                                <h4 class="best-club_name"> Клуб: ${player.club.name}</h4>
                                <h4 class="best-info">Игровой номер: ${player.number}</h4>
                                <h4 class="best-info">Рейтинг: ${player.rating}</h4>
                            </div>
                        </div>
                    </div>`;


    return inner_html;
}