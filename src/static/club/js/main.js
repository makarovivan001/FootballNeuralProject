function show_club_info(data) {
    console.log(data);
    let club = data.club;
    let club_title_block = document.querySelector(".club_title");
    let club_title_text = '';
    club_title_text += ` <img src="${club.photo_url}" alt="">
                <div class="club_title_info">
                    <h2>${club.name}</h2>
                    <p>Стадион: ${club.stadium_name} ${club.city_name}</p>
                    <p>Вместимость: ${club.stadium_count_of_sits} чел.</p>
                </div>`;
    club_title_block.insertAdjacentHTML('beforeend', club_title_text);

    let club_games = document.querySelector('.club_games');
let game_html = "";
let games = data.games;
let last_date = null;

if (club.name) {
    let sortedGames = games.sort((a, b) => new Date(b.game_date) - new Date(a.game_date));

    let last30Games = sortedGames.slice(0, 30);

    for (let i = 0; i < last30Games.length; i++) {
        let game = last30Games[i];
        let game_date = game.game_date.split('T')[0];

        if (game_date !== last_date) {
            game_html += `<p>${game_date}</p>`;
            last_date = game_date;
        }

        game_html += `
        <div class="game_row" data-id="${game.id}" onclick="go_to_page(this, '/game/<id>/')">
            <div class="club_img_and_name first_team">
                <div class="tm team_l">
                    <span>${game.home_club.name}</span>
                </div>
                <div class="imgs img_r">
                    <img src="${game.home_club.photo_url}" alt="">
                </div>
            </div>
            <div class="result">
                <p>${game.home_score} - ${game.away_score}</p>
            </div>
            <div class="club_img_and_name second_team">
                <div class="imgs img_l">
                    <img src="${game.away_club.photo_url}" alt="">
                </div>
                <div class="tm team_r">
                    <span>${game.away_club.name}</span>
                </div>
            </div>
        </div>`;
    }

    club_games.insertAdjacentHTML('beforeend', game_html);
}

let club_players = data.players;


let club_players_block = document.querySelector(".club_players_block");

let club_players_text = "";
club_players.sort((a, b) => {
  const ratingA = a.statistic?.rating ?? 0;
  const ratingB = b.statistic?.rating ?? 0;
  return ratingB - ratingA;
});

for (let i = 0; i < club_players.length; i++) {

    let club_player = club_players[i];
    if (club_player.number != 0 && club_player.statistic.minutes_played > 30) {
         let club_players_text = `<td class="player-item" data-id="${club_player.id}" onclick="go_to_page(this, '/player/<id>/')">
                                <img src="${club_player.photo_url}" alt="">
                            </td>
                            <td data-id="${club_player.id}" onclick="go_to_page(this, '/player/<id>/')">${club_player.name} ${club_player.surname}</td>
                            <td>${club_player.age}</td>
                            <td>${club_player.number}</td>
                            <td>${club_player.statistic.minutes_played}</td>
                            <td>${club_player.statistic.all_goals}</td>
                            <td>${club_player.statistic.all_assists}</td>
                            <td>${club_player.statistic.all_yellow_cards}</td>
                            <td>${club_player.statistic.all_red_cards}</td>
                            <td>${club_player.statistic.rating}</td>`;

        club_players_block.insertAdjacentHTML('beforeend', club_players_text);
    }

}

}