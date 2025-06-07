window.onload = function() {
   get_clubs();
}

function get_clubs() {
    request({
        url: '/api/club/',
        func: show_lending_page,
    });
}

function show_lending_page(data) {
    console.log(data)
    let clubs = data.clubs;
    let up_line = '';
    let middle_line = '';
    let down_line = '';
    for (let i = 0; i<5; i++) {
        up_line += `<div class="club-info" data-id="${clubs[i].id}" onclick="go_to_page(this, '/club/<id>/')">
                            <img src="${clubs[i].photo_url}" alt="">
                        </div>`;
    }
    for (let i = 5; i<11; i++) {
        middle_line += `<div class="club-info" data-id="${clubs[i].id}" onclick="go_to_page(this, '/club/<id>/')">
                            <img src="${clubs[i].photo_url}" alt="">
                        </div>`;
    }
    for (let i = 11; i<data.clubs.length; i++) {
        down_line += `<div class="club-info" data-id="${clubs[i].id}" onclick="go_to_page(this, '/club/<id>/')">
                            <img src="${clubs[i].photo_url}" alt="">
                        </div>`;
    }
    document.querySelector('.club-up-block').insertAdjacentHTML('beforeEnd', up_line);
    document.querySelector('.club-middle-block').insertAdjacentHTML('beforeEnd', middle_line);
    document.querySelector('.club-down-block').insertAdjacentHTML('beforeEnd', down_line);

    let tournament_table = data.tournament_table;
    let tournament_tbody = document.querySelector('.tournament_tbody');
    let tournament_rows = '';

    for (let i = 0; i < tournament_table.length; i++) {
        tournament_rows += `
        <tr class="data_text">
            <td>${i + 1}</td>
            <td data-id="${tournament_table[i].club.id}" onclick="go_to_page(this, '/club/<id>/')"><img src="${tournament_table[i].club.photo_url}" alt="">${tournament_table[i].club.name}</td>
            <td>${tournament_table[i].game_count}</td>
            <td>${tournament_table[i].wins}</td>
            <td>${tournament_table[i].draw_game_count}</td>
            <td>${tournament_table[i].lose_game_count}</td>
            <td>${tournament_table[i].goals_scored} - ${tournament_table[i].goals_missed}</td>
            <td>${tournament_table[i].goal_difference}</td>
            <td>${tournament_table[i].points}</td>
        </tr>`;
    }

    tournament_tbody.insertAdjacentHTML('beforeend', tournament_rows);

    let club_games = document.querySelector('.club_games');
    let game_html = "";
    let games = data.games;
    let last_date = null;

    for (let i = 0; i< games.length; i++)
    {
        game_date = games[i].game_date.split('T')[0];
        if (game_date !== last_date) {
            game_html += `<p>${game_date}</p>`;
            last_date = game_date;
        }
        game_html += `
        <div class="game_row" data-id="${games[i].id}" onclick="go_to_page(this, '/game/<id>/')">
            <div class="club_img_and_name first_team">
                <div class="tm team_l">
                    <span>${games[i].home_club.name}</span>
                </div>
                <div class="imgs img_r">
                    <img src="${games[i].home_club.photo_url}" alt="">
                </div>
            </div>
            <div class="result">
                <p>${games[i].home_score} - ${games[i].away_score}</p>
            </div>
            <div class="club_img_and_name second_team">
                <div class="imgs img_l">
                    <img src="${games[i].away_club.photo_url}" alt="">
                </div>
                <div class="tm team_r">
                    <span>${games[i].away_club.name}</span>
                </div>
            </div>
        </div>`;
    }
    club_games.insertAdjacentHTML('beforeend', game_html);
}



