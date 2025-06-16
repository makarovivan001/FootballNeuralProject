function show_player_info(data) {
    let stats = data.stats;
    let games = data.games;

    console.log(data);
    let minutes_per_game = Number((stats.minutes_played / stats.matches_uppercase).toFixed(2));
    let goal_conversion = stats.all_ShotsOnTarget > 0
  ? Number(((stats.all_goals / stats.all_ShotsOnTarget) * 100).toFixed(2))
  : 0;
    let minutes_to_goal = stats.all_goals > 0
  ? Number((stats.minutes_played / stats.all_goals).toFixed(2))
  : 0;


    let player_main_info = '';
    let player_info_html = '';
    let game_info_text = '';
    let player_stats_block = document.querySelector(".category_stats_block");
    let player_block = document.querySelector(".player-block");
    let player_info_block = document.querySelector(".general_player_info");
    let player_game_practise_block = document.querySelector(".game_practise");
    let play_in_defense_block = document.querySelector(".play_in_defense");
    let pass_block = document.querySelector(".play_in_pass");
    let driblling_block = document.querySelector(".game_driblling");
    let attack_block = document.querySelector(".play_in_attack");
    let discipline_block = document.querySelector(".game_discipline");
    let rating_block = document.querySelector(".rating");
    let players_game_block = document.querySelector(".players_game_block");
    let positions = data.best_positions;

    let first_position = positions[0];
    let second_position = positions[1];
    let third_position = positions[2];

    if (data.primary_position.name === "Keeper" || data.primary_position.name === "keeper") {
        console.log("вратарь");
        player_game_practise_block.style.display = "none";
        play_in_defense_block.style.display = "none";
        pass_block.style.display = "none";
        driblling_block.style.display = "none";
        attack_block.style.display = "none";
        discipline_block.style.display = "none";
        rating_block.style.display = "none";

        let first_position_name = first_position.position;
        let first_percent_of_best = first_position.percent_of_best;
        let first_outperformed_percent = first_position.players_outperformed_percent;
        let first_final_probability = first_position.final_score;

        player_main_info += `<div class="player-info">
                                 <div class="player_photo_wrapper">
                                    <img src="${data.photo_url}" alt="" class="player-photo">
                                 </div>
                                 <div class="player_card_name_block">
                                    <h2>${data.name} ${data.surname}</h2>
                                 </div>
                             </div>`;
        player_block.insertAdjacentHTML("beforeend", player_main_info);

        player_info_html += `<div class="stat_row"><p>Страна</p><h4>${data.country}</h4></div>
                         <div class="stat_row"><p>Возраст</p><h4>${data.age}</h4></div>
                         <div class="stat_row club" data-id="${data.club.id}" onclick="go_to_page(this, '/club/<id>/')"><p>Текущая команда</p>
                            <div class="best_player_team_info">
                                <img src="${data.club.photo_url}" alt="">
                                <h4 class="team-name">${data.club.name}</h4>
                            </div>
                        </div>
                        <div class="stat_row"><p>Игровой номер</p><h4>${data.number}</h4></div>
                        <div class="stat_row">
                            <p>Нынешняя позиция</p>
                            <div class="main_position">
                                <h4 class="position_name">${data.primary_position?.name ?? "Не задано"}</h4>
                            </div>
                        </div>
                        <div class="stat_row best_positions_row">
                        <div class="position_text_block">
                            <p>Наиболее вероятная позиция</p>
                        </div>
                            <div class="best_positions">
                                <div class="best_position_block">
                                    <div class="pos_name">
                                        <h4>${first_position_name}</h4>
                                    </div>
                                    <div class="pos_value">
                                        <h4>Уровень позиции ${first_final_probability}%</h4>
                                    </div>
                                </div>
                            </div>
                        </div>`

    player_info_block.insertAdjacentHTML("beforeend", player_info_html);

    let fieldToStatKey = {
        "Матчей сыграно": "matches_uppercase",
        "Сыграно минут": "minutes_played",
        "Сэйвы": "saves",
        "Процент сэйвов": "save_percentage",
        "Пропущено голов": "goals_conceded",
        "Сухой матч": "clean_sheet_team_title",
        "Пенальти в ворота": "penalties_faced",
        "Пропущено голов с пенальти": "penalty_goals_conceded",
        "Отбит удар с пенальти": "penalty_saves",
        "Ошибка, приведшая к голу": "error_led_to_goal",
        "Игра на выходе": "keeper_sweeper",
        "Перехвачен верховой пас": "keeper_high_claim",
        "Жёлтые карточки": "all_yellow_cards",
        "Красные карточки": "red_cards",
        "Фолы": "fouls",
        "Голевые передачи": "all_assists",
        "Точность передач (%)": "successful_passes_accuracy",
        "Удачные длинные передачи": "long_balls_accurate",
        "Точность длинных передач (%)": "long_ball_succeeeded_accuracy",
        "Голы": "all_goals",
        "Рейтинг": "rating",
    };

    let html = `
    <div class="general_player_info stats_player_info">

`;

    for (let label in fieldToStatKey) {
        let statKey = fieldToStatKey[label];
        let value = stats[statKey] !== undefined ? stats[statKey] : "-";
        html += `<div class="stat_row"><p>${label}</p><h4>${value}</h4></div>`;
    }

    html += `</div>`;

    player_stats_block.insertAdjacentHTML("beforeend", html);
    }

    else {
        let first_position_name = first_position.position;
        let first_percent_of_best = first_position.percent_of_best;
        let first_outperformed_percent = first_position.players_outperformed_percent;
        let first_final_probability = first_position.final_score;

        let second_position_name = second_position.position;
        let second_percent_of_best = second_position.percent_of_best;
        let second_outperformed_percent = second_position.players_outperformed_percent;
        let second_final_probability = second_position.final_score;

        let third_position_name = third_position.position;
        let third_percent_of_best = third_position.percent_of_best;
        let third_outperformed_percent = third_position.players_outperformed_percent;
        let third_final_probability = third_position.final_score;
        player_main_info += `<div class="player-info">
                                 <div class="player_photo_wrapper">
                                    <img src="${data.photo_url}" alt="" class="player-photo">
                                 </div>
                                 <div class="player_card_name_block">
                                    <h2>${data.name} ${data.surname}</h2>
                                 </div>
                             </div>`;
        player_block.insertAdjacentHTML("beforeend", player_main_info);

        player_info_html += `<div class="stat_row"><p>Страна</p><h4>${data.country}</h4></div>
                         <div class="stat_row"><p>Возраст</p><h4>${data.age}</h4></div>
                         <div class="stat_row club" data-id="${data.club.id}" onclick="go_to_page(this, '/club/<id>/')"><p>Текущая команда</p>
                            <div class="best_player_team_info">
                                <img src="${data.club.photo_url}" alt="">
                                <h4 class="team-name">${data.club.name}</h4>
                            </div>
                        </div>
                        <div class="stat_row"><p>Игровой номер</p><h4>${data.number}</h4></div>
                        <div class="stat_row">
                            <p>Нынешняя позиция</p>
                            <div class="main_position">
                                <h4 class="position_name">${data.primary_position?.name ?? "Не задано"}</h4>
                            </div>
                        </div>
                        <div class="stat_row best_positions_row">
                        <div class="position_text_block">
                            <p>Наиболее подходящие позиции</p>
                        </div>
                            <div class="best_positions">
                                <div class="best_position_block">
                                    <div class="pos_name">
                                        <h4>${first_position_name}</h4>
                                    </div>
                                    <div class="pos_value">
                                        <h4>Уровень позиции ${first_final_probability}%</h4>
                                    </div>
                                </div>
                                <div class="best_position_block">
                                    <div class="pos_name">
                                        <h4>${second_position_name}</h4>
                                    </div>
                                    <div class="pos_value">
                                        <h4>Уровень позиции ${second_final_probability}%</h4>
                                    </div>
                                </div>
                                <div class="best_position_block">
                                    <div class="pos_name">
                                        <h4>${third_position_name}</h4>
                                    </div>
                                    <div class="pos_value">
                                        <h4>Уровень позиции ${third_final_probability}%</h4>
                                    </div>
                                </div>
                            </div>
                        </div>`

        player_info_block.insertAdjacentHTML("beforeend", player_info_html);
        let categories = {
            "Игровая практика": {
                container: player_game_practise_block,
                fields: [
                    "Матчей сыграно",
                    "В стартовом составе",
                    "Минут за матч (в среднем)",
                    "Сыграно минут"
                ]
            },
            "Игра в обороне": {
                container: play_in_defense_block,
                fields: [
                    "Перехваты",
                    "Успешные отборы %",
                    "Успешные единоборства %",
                    "Возврат мяча",
                    "Ободка оппонентом",
                    "Успешные верх. единоборства %",
                    "Заблокировано ударов"
                ]
            },
            "Передачи": {
                container: pass_block,
                fields: [
                    "Голевые передачи",
                    "Голевые передачи за игру",
                    "Создано голевых моментов",
                    "Удачные передачи",
                    "Точность передач (%)",
                    "Удачные длинные передачи",
                    "Точность длинных передач (%)",
                    "Удачные кроссы",
                    "Точность кроссов"
                ]
            },
            "Дриблинг": {
                container: driblling_block,
                fields: [
                    "Удачный дриблинг",
                    "Потеря владения",
                    "Заработано фолов",
                    "Касаний в штр. соперника",
                    "Контроль под давлением (%)"
                ]
            },
            "Атакующие действия": {
                container: attack_block,
                fields: [
                    "Голевая конверсия (%)",
                    "Голы",
                    "Голов за игру",
                    "Минут на гол",
                    "Удары",
                    "Удары в створ",
                    "Единоборства фин.треть"
                ]
            },
            "Игровая дисциплина": {
                container: discipline_block,
                fields: [
                    "Жёлтые карточки",
                    "Красные карточки",
                    "Фолы"
                ]
            },
            "Рейтинг": {
                container: rating_block,
                fields: [
                    "Рейтинг"
                ]
            },
        };

        let fieldToStatKey = {
            "Матчей сыграно": "matches_uppercase",
            "В стартовом составе": "started",
            "Минут за матч (в среднем)": "minutes_per_game",
            "Сыграно минут": "minutes_played",
            "Перехваты": "interceptions",
            "Успешные отборы %": "tackles_succeeded_percent",
            "Успешные единоборства %": "duel_won_percent",
            "Возврат мяча": "recoveries",
            "Ободка оппонентом": "dribbled_past",
            "Успешные верх. единоборства %": "aerials_won_percent",
            "Заблокировано ударов": "shot_blocked",
            "Жёлтые карточки": "all_yellow_cards",
            "Красные карточки": "red_cards",
            "Фолы": "fouls",
            "Голевые передачи": "all_assists",
            "Голевые передачи за игру": "assists",
            "Создано голевых моментов": "chances_created",
            "Удачные передачи": "successful_passes",
            "Точность передач (%)": "successful_passes_accuracy",
            "Удачные длинные передачи": "long_balls_accurate",
            "Точность длинных передач (%)": "long_ball_succeeeded_accuracy",
            "Удачные кроссы": "crosses_succeeeded",
            "Точность кроссов": "crosses_succeeeded_accuracy",
            "Удачный дриблинг": "dribbles_succeeded",
            "Потеря владения": "dispossessed",
            "Заработано фолов": "fouls_won",
            "Касаний в штр. соперника": "touches_opp_box",
            "Контроль под давлением (%)": "won_contest_subtitle",
            "Голы": "all_goals",
            "Голов за игру": "goals",
            "Удары": "shots",
            "Удары в створ": "ShotsOnTarget",
            "Единоборства фин.треть": "poss_won_att_3rd_team_title",
            "Рейтинг": "rating",
        };

        let derivedStats = {
            "Минут за матч (в среднем)": minutes_per_game,
            "Голевая конверсия (%)": goal_conversion,
            "Минут на гол": minutes_to_goal,
        };

        for (let categoryName in categories) {
            let category = categories[categoryName];
            let fields = category.fields;
            let container = category.container;

            let html = ''
            html += `<div class="general_player_info stats_player_info">
                     <div class="category_title"><h3>${categoryName}</h3></div>`;

            for (let i = 0; i < fields.length; i++) {
                let field = fields[i];
                let value = "-";

                if (derivedStats[field] !== undefined) {
                    value = derivedStats[field];
                } else {
                    var key = fieldToStatKey[field];
                    if (key in stats) {
                        value = stats[key];
                    }
                }

                html += `<div class="stat_row"><p>${field}</p><h4>${value}</h4></div>`;
            }

            html += `</div>`;
            container.insertAdjacentHTML("beforeend", html);
        }
    }

    for (let i = 0; i < games.length; i++)  {
        let game_date = games[i].game_date.split('T')[0];
        let game = games[i];
        console.log(games.length);
        game_info_text = `<tr data-id="${game.id}" onclick="go_to_page(this, '/game/<id>/')">
      <td class="date_of_game">${game_date}</td>
      <td>
        <div class="match-info">
          <div class="teams">
            <img class="club-icon" src="${game.home_club.photo_url}" alt="" />
            <span class="team-name">${game.home_club.name}</span>
            <span class="score">${game.home_score} : ${game.away_score}</span>
            <span class="team-name">${game.away_club.name}</span>
            <img class="club-icon" src="${game.away_club.photo_url}" alt="" />
          </div>
          <div class="tournament">RPL</div>
        </div>
      </td>
      <td><h4 class="stat">${game.statistic?.goals || 0}</h4>
      </td>
      <td>
          <h4 class="stat">${game.statistic?.assists || 0}</h4>
      </td>
      <td>
          <h4 class="stat">${game.statistic?.duel_won || 0} / ${game.statistic?.duel_lost || 0}</h4>
      </td>
      <td>
          <h4 class="stat">${game.statistic?.minutes_played || 0}</h4>
      </td>
      <td>
          <h4 class="stat">${game.statistic?.rating_title || 0}</h4>
      </td>
    </tr>`;
        players_game_block.insertAdjacentHTML('beforeend', game_info_text);
    }
}