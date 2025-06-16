// ------------------------ Переменные ------------------------
const field = document.getElementById('field');
const modal = document.getElementById('modal');
const closeModalBtn = document.getElementById('close-modal');
const changeFormationBtn = document.getElementById('change-formation-btn');
const applyFormationBtn = document.getElementById('apply-formation');

// Инпуты для левой команды
const leftLinesCountInput = document.getElementById('left-lines-count');
const leftLinesInputsContainer = document.getElementById('left-lines-inputs');

// Инпуты для правой команды
const rightLinesCountInput = document.getElementById('right-lines-count');
const rightLinesInputsContainer = document.getElementById('right-lines-inputs');

// Массивы DOM-элементов игроков
let leftTeamPlayers = [];
let rightTeamPlayers = [];

// ------------------------ Инициализация игроков ------------------------

// Создаём 11 DOM-элементов для каждой команды (0-й — вратарь, остальные 10 — полевые)
function createPlayers() {
  // Левая команда
  for (let i = 0; i < 11; i++) {
//    Кружочки
    const player = document.createElement('div');
    const player_info = document.createElement('div');
    const player_name = document.createElement('div');
    player.classList.add('player', 'team-left');
    player_info.classList.add('pitch-player-info');
    player_name.classList.add('player-name');

    field.appendChild(player);
    player.appendChild(player_info);
    player_info.appendChild(player_name)
    leftTeamPlayers.push(player);
  }

  // Правая команда
  for (let i = 0; i < 11; i++) {
    const player = document.createElement('div');
    const player_info = document.createElement('div');
    const player_name = document.createElement('div');
    player.classList.add('player', 'team-right');
    player_info.classList.add('pitch-player-info');
    player_name.classList.add('player-name');
    field.appendChild(player);
    player.appendChild(player_info);
    player_info.appendChild(player_name)
    rightTeamPlayers.push(player);
  }
}

// ------------------------ Расстановка игроков на поле ------------------------
/**
 * Расставляем левую команду строго на левой половине поля (0% - 50%).
 * @param {Array<number>} formation - массив вида [3,4,3], суммарно 10
 */
function placeLeftTeam(formation, home_placement) {
  const fieldWidth = field.clientWidth;
  const fieldHeight = field.clientHeight;

  const playerWidth = field.querySelector('.player').offsetWidth;

  // Функция отрисовки гола и замены
  const addIconsAndRating = (container, actions = []) => {
    const topLeft = document.createElement('div');
    topLeft.className = 'player-icon-top-left';
    const topRight = document.createElement('div');
    topRight.className = 'player-icon-top-right';
    const bottomCenter = document.createElement('div');

    const goals = actions.filter(a => a.action?.name === 'Goal').length;
    if (goals > 0) {
      for (let i = 0; i < goals; i++) {
        const icon = document.createElement('span');
        icon.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" fill="#000000" version="1.1" id="Capa_1" height="80%" viewBox="0 0 72.371 72.372" xml:space="preserve">
                             <g>
	                          <path d="M22.57,2.648c-4.489,1.82-8.517,4.496-11.971,7.949C7.144,14.051,4.471,18.08,2.65,22.568C0.892,26.904,0,31.486,0,36.186   c0,4.699,0.892,9.281,2.65,13.615c1.821,4.489,4.495,8.518,7.949,11.971c3.454,3.455,7.481,6.129,11.971,7.949   c4.336,1.76,8.917,2.649,13.617,2.649c4.7,0,9.28-0.892,13.616-2.649c4.488-1.82,8.518-4.494,11.971-7.949   c3.455-3.453,6.129-7.48,7.949-11.971c1.758-4.334,2.648-8.916,2.648-13.615c0-4.7-0.891-9.282-2.648-13.618   c-1.82-4.488-4.496-8.518-7.949-11.971s-7.479-6.129-11.971-7.949C45.467,0.891,40.887,0,36.187,0   C31.487,0,26.906,0.891,22.57,2.648z M9.044,51.419c-1.743-1.094-3.349-2.354-4.771-3.838c-2.172-6.112-2.54-12.729-1.101-19.01   c0.677-1.335,1.447-2.617,2.318-3.845c0.269-0.379,0.518-0.774,0.806-1.142l8.166,4.832c0,0.064,0,0.134,0,0.205   c-0.021,4.392,0.425,8.752,1.313,13.049c0.003,0.02,0.006,0.031,0.01,0.049l-6.333,9.93C9.314,51.579,9.177,51.503,9.044,51.419z    M33.324,68.206c1.409,0.719,2.858,1.326,4.347,1.82c-6.325,0.275-12.713-1.207-18.36-4.447L33,68.018   C33.105,68.085,33.212,68.149,33.324,68.206z M33.274,65.735L17.12,62.856c-1.89-2.295-3.59-4.723-5.051-7.318   c-0.372-0.66-0.787-1.301-1.102-1.99l6.327-9.92c0.14,0.035,0.296,0.072,0.473,0.119c3.958,1.059,7.986,1.812,12.042,2.402   c0.237,0.033,0.435,0.062,0.604,0.08l7.584,13.113c-1.316,1.85-2.647,3.69-4.007,5.51C33.764,65.155,33.524,65.446,33.274,65.735z    M60.15,60.149c-1.286,1.287-2.651,2.447-4.08,3.481c-0.237-1.894-0.646-3.75-1.223-5.563l8.092-15.096   c2.229-1.015,4.379-2.166,6.375-3.593c0.261-0.185,0.478-0.392,0.646-0.618C69.374,46.561,66.104,54.196,60.15,60.149z    M59.791,40.571c0.301,0.574,0.598,1.154,0.896,1.742l-7.816,14.58c-0.045,0.01-0.088,0.02-0.133,0.026   c-4.225,0.789-8.484,1.209-12.779,1.229l-7.8-13.487c1.214-2.254,2.417-4.517,3.61-6.781c0.81-1.536,1.606-3.082,2.401-4.627   l16.143-1.658C56.29,34.495,58.163,37.457,59.791,40.571z M56.516,23.277c-0.766,2.023-1.586,4.025-2.401,6.031l-15.726,1.615   c-0.188-0.248-0.383-0.492-0.588-0.725c-1.857-2.103-3.726-4.193-5.592-6.289c0.017-0.021,0.034-0.037,0.051-0.056   c-0.753-0.752-1.508-1.504-2.261-2.258l4.378-13.181c0.302-0.08,0.606-0.147,0.913-0.18c2.38-0.242,4.763-0.516,7.149-0.654   c1.461-0.082,2.93-0.129,4.416-0.024l10.832,12.209C57.314,20.943,56.95,22.124,56.516,23.277z M60.15,12.221   c2.988,2.99,5.302,6.402,6.938,10.047c-2.024-1.393-4.188-2.539-6.463-3.473c-0.354-0.146-0.717-0.275-1.086-0.402L48.877,6.376   c0.074-0.519,0.113-1.039,0.129-1.563C53.062,6.464,56.864,8.936,60.15,12.221z M25.334,4.182c0.042,0.031,0.062,0.057,0.086,0.064   c2.437,0.842,4.654,2.082,6.744,3.553l-4.09,12.317c-0.021,0.006-0.041,0.012-0.061,0.021c-0.837,0.346-1.69,0.656-2.514,1.031   c-3.395,1.543-6.705,3.252-9.823,5.301l-8.071-4.775c0.012-0.252,0.055-0.508,0.141-0.736c0.542-1.444,1.075-2.896,1.688-4.311   c0.472-1.09,1.01-2.143,1.597-3.172c0.384-0.424,0.782-0.844,1.192-1.254c3.833-3.832,8.363-6.553,13.186-8.162   C25.384,4.098,25.358,4.139,25.334,4.182z"/>
                             </g>
                          </svg>`;
        icon.style.width = '10px';
        topLeft.appendChild(icon);
      }
    }

    const hasSub = actions.some(a => a.action?.name === 'Substitution');
    if (hasSub) {
      const subIcon = document.createElement('span');
      subIcon.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" height="100%" viewBox="0 0 20 20" version="1.1">
                                        <g id="layer1">
                                        <path d="M 4 2.5 L 3 3.5 L 3 8 L 7.5 8 L 8.5 7 L 4.6601562 7 L 5.4628906 6.0722656 L 5.7695312 5.7441406 L 6.0996094 5.4414062 L 6.4492188 5.1621094 L 6.8203125 4.9101562 L 7.2089844 4.6875 L 7.6152344 4.4941406 L 8.0332031 4.3300781 L 8.4609375 4.2011719 L 8.8984375 4.1015625 L 9.3417969 4.0351562 L 9.7890625 4.0039062 L 10.238281 4.0058594 L 10.685547 4.0390625 L 11.128906 4.1054688 L 11.564453 4.2070312 L 11.994141 4.3398438 L 12.410156 4.5058594 L 12.814453 4.7011719 L 13.201172 4.9257812 L 13.572266 5.1777344 L 13.921875 5.4589844 L 14.25 5.7636719 L 14.554688 6.09375 L 14.833984 6.4453125 L 15.083984 6.8164062 L 15.310547 7.2050781 L 15.501953 7.609375 L 15.666016 8.0273438 L 15.796875 8.4550781 L 15.896484 8.8925781 L 15.962891 9.3359375 L 15.994141 9.7851562 L 15.994141 10 L 17 10 L 17 9.9902344 L 16.982422 9.5058594 L 16.931641 9.0214844 L 16.847656 8.5449219 L 16.728516 8.0742188 L 16.580078 7.6113281 L 16.398438 7.1621094 L 16.185547 6.7265625 L 15.945312 6.3046875 L 15.675781 5.9023438 L 15.376953 5.5175781 L 15.054688 5.15625 L 14.707031 4.8183594 L 14.335938 4.5058594 L 13.945312 4.2167969 L 13.535156 3.9570312 L 13.109375 3.7285156 L 12.666016 3.5273438 L 12.210938 3.3574219 L 11.746094 3.2207031 L 11.271484 3.1152344 L 10.792969 3.0449219 L 10.306641 3.0058594 L 9.8222656 3 L 9.3378906 3.0292969 L 8.8574219 3.0917969 L 8.3808594 3.1894531 L 7.9140625 3.3183594 L 7.4550781 3.4785156 L 7.0097656 3.6699219 L 6.578125 3.8925781 L 6.1640625 4.1445312 L 5.7675781 4.4238281 L 5.390625 4.7304688 L 5.0371094 5.0605469 L 4.7070312 5.4179688 L 4 6.234375 L 4 2.5 z M 3 10 L 3 10.007812 L 3.0175781 10.492188 L 3.0683594 10.976562 L 3.1523438 11.453125 L 3.2714844 11.923828 L 3.4199219 12.386719 L 3.6015625 12.835938 L 3.8144531 13.271484 L 4.0546875 13.693359 L 4.3242188 14.095703 L 4.6230469 14.480469 L 4.9453125 14.841797 L 5.2929688 15.179688 L 5.6640625 15.492188 L 6.0546875 15.78125 L 6.4648438 16.041016 L 6.890625 16.269531 L 7.3339844 16.470703 L 7.7890625 16.640625 L 8.2539062 16.777344 L 8.7285156 16.882812 L 9.2070312 16.953125 L 9.6933594 16.992188 L 10.177734 16.998047 L 10.662109 16.96875 L 11.142578 16.90625 L 11.619141 16.808594 L 12.085938 16.679688 L 12.544922 16.519531 L 12.990234 16.328125 L 13.421875 16.105469 L 13.835938 15.853516 L 14.232422 15.574219 L 14.609375 15.267578 L 14.962891 14.9375 L 15.292969 14.580078 L 16 13.763672 L 16 17.498047 L 17 16.498047 L 17 11.998047 L 12.5 11.998047 L 11.5 12.998047 L 15.339844 12.998047 L 14.537109 13.925781 L 14.230469 14.253906 L 13.900391 14.556641 L 13.550781 14.835938 L 13.179688 15.087891 L 12.791016 15.310547 L 12.384766 15.503906 L 11.966797 15.667969 L 11.539062 15.796875 L 11.101562 15.896484 L 10.658203 15.962891 L 10.210938 15.994141 L 9.7617188 15.992188 L 9.3144531 15.958984 L 8.8710938 15.892578 L 8.4355469 15.791016 L 8.0058594 15.658203 L 7.5898438 15.492188 L 7.1855469 15.296875 L 6.7988281 15.072266 L 6.4277344 14.820312 L 6.078125 14.539062 L 5.75 14.234375 L 5.4453125 13.904297 L 5.1660156 13.552734 L 4.9160156 13.181641 L 4.6894531 12.792969 L 4.4980469 12.388672 L 4.3339844 11.970703 L 4.203125 11.542969 L 4.1035156 11.105469 L 4.0371094 10.662109 L 4.0058594 10.212891 L 4.0058594 10 L 3 10 z " style="fill:#222222; fill-opacity:1; stroke:none; stroke-width:0px;"/>
                                        </g>
                                    </svg>`;
      topRight.appendChild(subIcon);

    }

    container.appendChild(topLeft);
    container.appendChild(topRight);
    container.appendChild(bottomCenter);
  };

  // Вратарь
  const goalkeeper = leftTeamPlayers[0];
  goalkeeper.style.left = `${fieldWidth * 0.1 - (playerWidth / 2)}px`;
  goalkeeper.style.top = `${fieldHeight * 0.5 - (playerWidth / 2)}px`;

  if (home_placement) {
    if (home_placement[0][0].player) {
      const playerData = home_placement[0][0].player;
      goalkeeper.style.backgroundImage = `url('${playerData.photo_url}')`;
      goalkeeper.querySelector('.player-name').innerText = `${playerData.surname} ${playerData.name}`;
      goalkeeper.setAttribute('onclick', `open_player_statistic(${playerData.id})`);
      goalkeeper.dataset.position_id = home_placement[0][0].position_id;
      goalkeeper.dataset.player_id = playerData.id;
      addIconsAndRating(goalkeeper.querySelector('.pitch-player-info'), playerData.actions);
    }
  }

  // Остальные игроки
  let totalLines = formation.length;
  let xStart = 0.2;
  let xEnd = 0.45;
  let xStep = (xEnd - xStart) / (totalLines - 1 || 1);

  let currentIndex = 1;

  for (let lineIndex = 0; lineIndex < totalLines; lineIndex++) {
    const playersInLine = formation[lineIndex];
    let x = xStart + xStep * lineIndex;
    let yStep = 1 / (playersInLine + 1);

    for (let p = 0; p < playersInLine; p++) {
      const player = leftTeamPlayers[currentIndex];
      // ИСПРАВЛЕНИЕ: инвертируем порядок игроков по Y координате
      // Вместо y = yStep * (p + 1) используем обратный порядок
      let y = yStep * (playersInLine - p);
      player.style.left = `${fieldWidth * x - (playerWidth / 2)}px`;
      player.style.top = `${fieldHeight * y - (playerWidth / 2)}px`;

      if (home_placement && home_placement[lineIndex + 1][p].player) {
        const playerData = home_placement[lineIndex + 1][p].player;
        player.style.backgroundImage = `url('${playerData.photo_url}')`;
        player.querySelector('.player-name').innerText = `${playerData.surname} ${playerData.name}`;
        player.setAttribute('onclick', `open_player_statistic(${playerData.id})`);
        player.dataset.position_id = home_placement[lineIndex + 1][p].position_id;
        player.dataset.player_id = playerData.id;
        addIconsAndRating(player.querySelector('.pitch-player-info'), playerData.actions);
      }

      currentIndex++;
    }
  }
}

/**
 * Расставляем правую команду строго на правой половине поля (50% - 100%).
 * @param {Array<number>} formation - массив вида [3,4,3], суммарно 10
 */
function placeRightTeam(formation, away_placement) {
  const fieldWidth = field.clientWidth;
  const fieldHeight = field.clientHeight;
  if (away_placement) {
    away_placement = [away_placement[0], ...away_placement.slice(1).reverse()];
  }
  const playerWidth = field.querySelector('.player').offsetWidth;

  const addIconsAndRating = (container, actions = [], rating = null) => {
    const topLeft = document.createElement('div');
    topLeft.className = 'player-icon-top-left';
    const topRight = document.createElement('div');
    topRight.className = 'player-icon-top-right';
    const bottomCenter = document.createElement('div');

    const goals = actions.filter(a => a.action?.name === 'Goal').length;
    for (let i = 0; i < goals; i++) {
      const icon = document.createElement('span');
      icon.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" fill="#000000" version="1.1" id="Capa_1" height="80%" viewBox="0 0 72.371 72.372" xml:space="preserve">
                          <g>
                              <path d="M22.57,2.648c-4.489,1.82-8.517,4.496-11.971,7.949C7.144,14.051,4.471,18.08,2.65,22.568C0.892,26.904,0,31.486,0,36.186   c0,4.699,0.892,9.281,2.65,13.615c1.821,4.489,4.495,8.518,7.949,11.971c3.454,3.455,7.481,6.129,11.971,7.949   c4.336,1.76,8.917,2.649,13.617,2.649c4.7,0,9.28-0.892,13.616-2.649c4.488-1.82,8.518-4.494,11.971-7.949   c3.455-3.453,6.129-7.48,7.949-11.971c1.758-4.334,2.648-8.916,2.648-13.615c0-4.7-0.891-9.282-2.648-13.618   c-1.82-4.488-4.496-8.518-7.949-11.971s-7.479-6.129-11.971-7.949C45.467,0.891,40.887,0,36.187,0   C31.487,0,26.906,0.891,22.57,2.648z M9.044,51.419c-1.743-1.094-3.349-2.354-4.771-3.838c-2.172-6.112-2.54-12.729-1.101-19.01   c0.677-1.335,1.447-2.617,2.318-3.845c0.269-0.379,0.518-0.774,0.806-1.142l8.166,4.832c0,0.064,0,0.134,0,0.205   c-0.021,4.392,0.425,8.752,1.313,13.049c0.003,0.02,0.006,0.031,0.01,0.049l-6.333,9.93C9.314,51.579,9.177,51.503,9.044,51.419z    M33.324,68.206c1.409,0.719,2.858,1.326,4.347,1.82c-6.325,0.275-12.713-1.207-18.36-4.447L33,68.018   C33.105,68.085,33.212,68.149,33.324,68.206z M33.274,65.735L17.12,62.856c-1.89-2.295-3.59-4.723-5.051-7.318   c-0.372-0.66-0.787-1.301-1.102-1.99l6.327-9.92c0.14,0.035,0.296,0.072,0.473,0.119c3.958,1.059,7.986,1.812,12.042,2.402   c0.237,0.033,0.435,0.062,0.604,0.08l7.584,13.113c-1.316,1.85-2.647,3.69-4.007,5.51C33.764,65.155,33.524,65.446,33.274,65.735z    M60.15,60.149c-1.286,1.287-2.651,2.447-4.08,3.481c-0.237-1.894-0.646-3.75-1.223-5.563l8.092-15.096   c2.229-1.015,4.379-2.166,6.375-3.593c0.261-0.185,0.478-0.392,0.646-0.618C69.374,46.561,66.104,54.196,60.15,60.149z    M59.791,40.571c0.301,0.574,0.598,1.154,0.896,1.742l-7.816,14.58c-0.045,0.01-0.088,0.02-0.133,0.026   c-4.225,0.789-8.484,1.209-12.779,1.229l-7.8-13.487c1.214-2.254,2.417-4.517,3.61-6.781c0.81-1.536,1.606-3.082,2.401-4.627   l16.143-1.658C56.29,34.495,58.163,37.457,59.791,40.571z M56.516,23.277c-0.766,2.023-1.586,4.025-2.401,6.031l-15.726,1.615   c-0.188-0.248-0.383-0.492-0.588-0.725c-1.857-2.103-3.726-4.193-5.592-6.289c0.017-0.021,0.034-0.037,0.051-0.056   c-0.753-0.752-1.508-1.504-2.261-2.258l4.378-13.181c0.302-0.08,0.606-0.147,0.913-0.18c2.38-0.242,4.763-0.516,7.149-0.654   c1.461-0.082,2.93-0.129,4.416-0.024l10.832,12.209C57.314,20.943,56.95,22.124,56.516,23.277z M60.15,12.221   c2.988,2.99,5.302,6.402,6.938,10.047c-2.024-1.393-4.188-2.539-6.463-3.473c-0.354-0.146-0.717-0.275-1.086-0.402L48.877,6.376   c0.074-0.519,0.113-1.039,0.129-1.563C53.062,6.464,56.864,8.936,60.15,12.221z M25.334,4.182c0.042,0.031,0.062,0.057,0.086,0.064   c2.437,0.842,4.654,2.082,6.744,3.553l-4.09,12.317c-0.021,0.006-0.041,0.012-0.061,0.021c-0.837,0.346-1.69,0.656-2.514,1.031   c-3.395,1.543-6.705,3.252-9.823,5.301l-8.071-4.775c0.012-0.252,0.055-0.508,0.141-0.736c0.542-1.444,1.075-2.896,1.688-4.311   c0.472-1.09,1.01-2.143,1.597-3.172c0.384-0.424,0.782-0.844,1.192-1.254c3.833-3.832,8.363-6.553,13.186-8.162   C25.384,4.098,25.358,4.139,25.334,4.182z"/>
                          </g>
                        </svg>`;
      topLeft.appendChild(icon);
      icon.style.width = '10px';
    }

    const hasSub = actions.some(a => a.action?.name === 'Substitution');
    if (hasSub) {
      const subIcon = document.createElement('span');
      subIcon.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg"height="100%" viewBox="0 0 20 20" version="1.1">
                              <g id="layer1">
                              <path d="M 4 2.5 L 3 3.5 L 3 8 L 7.5 8 L 8.5 7 L 4.6601562 7 L 5.4628906 6.0722656 L 5.7695312 5.7441406 L 6.0996094 5.4414062 L 6.4492188 5.1621094 L 6.8203125 4.9101562 L 7.2089844 4.6875 L 7.6152344 4.4941406 L 8.0332031 4.3300781 L 8.4609375 4.2011719 L 8.8984375 4.1015625 L 9.3417969 4.0351562 L 9.7890625 4.0039062 L 10.238281 4.0058594 L 10.685547 4.0390625 L 11.128906 4.1054688 L 11.564453 4.2070312 L 11.994141 4.3398438 L 12.410156 4.5058594 L 12.814453 4.7011719 L 13.201172 4.9257812 L 13.572266 5.1777344 L 13.921875 5.4589844 L 14.25 5.7636719 L 14.554688 6.09375 L 14.833984 6.4453125 L 15.083984 6.8164062 L 15.310547 7.2050781 L 15.501953 7.609375 L 15.666016 8.0273438 L 15.796875 8.4550781 L 15.896484 8.8925781 L 15.962891 9.3359375 L 15.994141 9.7851562 L 15.994141 10 L 17 10 L 17 9.9902344 L 16.982422 9.5058594 L 16.931641 9.0214844 L 16.847656 8.5449219 L 16.728516 8.0742188 L 16.580078 7.6113281 L 16.398438 7.1621094 L 16.185547 6.7265625 L 15.945312 6.3046875 L 15.675781 5.9023438 L 15.376953 5.5175781 L 15.054688 5.15625 L 14.707031 4.8183594 L 14.335938 4.5058594 L 13.945312 4.2167969 L 13.535156 3.9570312 L 13.109375 3.7285156 L 12.666016 3.5273438 L 12.210938 3.3574219 L 11.746094 3.2207031 L 11.271484 3.1152344 L 10.792969 3.0449219 L 10.306641 3.0058594 L 9.8222656 3 L 9.3378906 3.0292969 L 8.8574219 3.0917969 L 8.3808594 3.1894531 L 7.9140625 3.3183594 L 7.4550781 3.4785156 L 7.0097656 3.6699219 L 6.578125 3.8925781 L 6.1640625 4.1445312 L 5.7675781 4.4238281 L 5.390625 4.7304688 L 5.0371094 5.0605469 L 4.7070312 5.4179688 L 4 6.234375 L 4 2.5 z M 3 10 L 3 10.007812 L 3.0175781 10.492188 L 3.0683594 10.976562 L 3.1523438 11.453125 L 3.2714844 11.923828 L 3.4199219 12.386719 L 3.6015625 12.835938 L 3.8144531 13.271484 L 4.0546875 13.693359 L 4.3242188 14.095703 L 4.6230469 14.480469 L 4.9453125 14.841797 L 5.2929688 15.179688 L 5.6640625 15.492188 L 6.0546875 15.78125 L 6.4648438 16.041016 L 6.890625 16.269531 L 7.3339844 16.470703 L 7.7890625 16.640625 L 8.2539062 16.777344 L 8.7285156 16.882812 L 9.2070312 16.953125 L 9.6933594 16.992188 L 10.177734 16.998047 L 10.662109 16.96875 L 11.142578 16.90625 L 11.619141 16.808594 L 12.085938 16.679688 L 12.544922 16.519531 L 12.990234 16.328125 L 13.421875 16.105469 L 13.835938 15.853516 L 14.232422 15.574219 L 14.609375 15.267578 L 14.962891 14.9375 L 15.292969 14.580078 L 16 13.763672 L 16 17.498047 L 17 16.498047 L 17 11.998047 L 12.5 11.998047 L 11.5 12.998047 L 15.339844 12.998047 L 14.537109 13.925781 L 14.230469 14.253906 L 13.900391 14.556641 L 13.550781 14.835938 L 13.179688 15.087891 L 12.791016 15.310547 L 12.384766 15.503906 L 11.966797 15.667969 L 11.539062 15.796875 L 11.101562 15.896484 L 10.658203 15.962891 L 10.210938 15.994141 L 9.7617188 15.992188 L 9.3144531 15.958984 L 8.8710938 15.892578 L 8.4355469 15.791016 L 8.0058594 15.658203 L 7.5898438 15.492188 L 7.1855469 15.296875 L 6.7988281 15.072266 L 6.4277344 14.820312 L 6.078125 14.539062 L 5.75 14.234375 L 5.4453125 13.904297 L 5.1660156 13.552734 L 4.9160156 13.181641 L 4.6894531 12.792969 L 4.4980469 12.388672 L 4.3339844 11.970703 L 4.203125 11.542969 L 4.1035156 11.105469 L 4.0371094 10.662109 L 4.0058594 10.212891 L 4.0058594 10 L 3 10 z " style="fill:#222222; fill-opacity:1; stroke:none; stroke-width:0px;"/>
                              </g>
                            </svg>`;
      topRight.appendChild(subIcon);
    }

    if (rating !== null) {
      bottomCenter.textContent = `★ ${rating.toFixed(1)}`;
    }

    container.appendChild(topLeft);
    container.appendChild(topRight);
    container.appendChild(bottomCenter);
  };

  // Вратарь
  const goalkeeper = rightTeamPlayers[0];
  goalkeeper.style.left = `${fieldWidth * 0.9 - (playerWidth / 2)}px`;
  goalkeeper.style.top = `${fieldHeight * 0.5 - (playerWidth / 2)}px`;

  if (away_placement) {
    if (away_placement[0][0].player) {
    const playerData = away_placement[0][0].player;
    goalkeeper.style.backgroundImage = `url('${playerData.photo_url}')`;
    goalkeeper.querySelector('.player-name').innerText = `${playerData.surname} ${playerData.name}`;
    goalkeeper.setAttribute('onclick', `open_player_statistic(${playerData.id})`);
    goalkeeper.dataset.position_id = away_placement[0][0].position_id;
    goalkeeper.dataset.player_id = playerData.id;
    addIconsAndRating(goalkeeper.querySelector('.pitch-player-info'), playerData.actions, playerData.rating);
    }
  }


  // Остальные игроки
  let totalLines = formation.length;
  let xStart = 0.55;
  let xEnd = 0.8;
  let xStep = (xEnd - xStart) / (totalLines - 1 || 1);
  let currentIndex = 1;

  for (let lineIndex = 0; lineIndex < totalLines; lineIndex++) {
    const playersInLine = formation[lineIndex];
    let x = xStart + xStep * lineIndex;
    let yStep = 1 / (playersInLine + 1);

    for (let p = 0; p < playersInLine; p++) {
      const player = rightTeamPlayers[currentIndex];
      let y = yStep * (p + 1);
      player.style.left = `${fieldWidth * x - (playerWidth / 2)}px`;
      player.style.top = `${fieldHeight * y - (playerWidth / 2)}px`;

      if (away_placement && away_placement[lineIndex + 1][p].player) {
        const playerData = away_placement[lineIndex + 1][p].player;
        player.style.backgroundImage = `url('${playerData.photo_url}')`;
        player.querySelector('.player-name').innerText = `${playerData.surname} ${playerData.name}`;
        player.setAttribute('onclick', `open_player_statistic(${playerData.id})`);
        player.dataset.position_id = away_placement[lineIndex + 1][p].position_id;
        player.dataset.player_id = playerData.id;
        addIconsAndRating(player.querySelector('.pitch-player-info'), playerData.actions, playerData.rating);
      }

      currentIndex++;
    }
  }
}


// Вызываем расстановку для обеих команд
function updateFormation(home_placement=null, away_placement=null) {
  let first_team_block = document.querySelector (".first_team_block span");
  let second_team_block = document.querySelector (".second_team_block span");

  first_team_block.innerText = leftFormation.join("-");
  second_team_block.innerText = [...rightFormation].reverse().join("-");
  placeLeftTeam(leftFormation, home_placement);
  placeRightTeam(rightFormation, away_placement);
}

// ------------------------ Модальное окно и ввод данных ------------------------

// Функция для обновления (отрисовки) инпутов в модальном окне при изменении числа линий
function updateLinesInputs(linesCount, containerId) {
  const container = document.getElementById(containerId);
  container.innerHTML = ''; // очистим

  for (let i = 0; i < linesCount; i++) {
    const label = document.createElement('label');
    label.textContent = `Игроков в линии ${i + 1}: `;

    const input = document.createElement('input');
    input.type = 'number';
    input.min = '1';
    input.max = '10'; // но общая сумма по-прежнему не должна превышать 10
    input.value = '3';
    input.className = 'line-input';

    container.appendChild(label);
    container.appendChild(input);
    container.appendChild(document.createElement('br'));
  }
}

// События при изменении кол-ва линий (левая команда)
leftLinesCountInput.addEventListener('change', () => {
  let val = parseInt(leftLinesCountInput.value, 10);
  if (val < 1) val = 1;
  if (val > 5) val = 5;
  leftLinesCountInput.value = val;
  updateLinesInputs(val, 'left-lines-inputs');
});

// События при изменении кол-ва линий (правая команда)
rightLinesCountInput.addEventListener('change', () => {
  let val = parseInt(rightLinesCountInput.value, 10);
  if (val < 1) val = 1;
  if (val > 5) val = 5;
  rightLinesCountInput.value = val;
  updateLinesInputs(val, 'right-lines-inputs');
});

// Открыть модальное окно
changeFormationBtn.addEventListener('click', () => {
  modal.style.display = 'flex';

  // Заполним поля ввода под текущую расстановку (левая команда)
  leftLinesCountInput.value = leftFormation.length;
  updateLinesInputs(leftFormation.length, 'left-lines-inputs');
  const leftInputs = leftLinesInputsContainer.querySelectorAll('.line-input');
  leftFormation.forEach((val, i) => {
    if (leftInputs[i]) leftInputs[i].value = val;
  });

  // Заполним поля ввода под текущую расстановку (правая команда)
  rightLinesCountInput.value = rightFormation.length;
  updateLinesInputs(rightFormation.length, 'right-lines-inputs');
  const rightInputs = rightLinesInputsContainer.querySelectorAll('.line-input');
  rightFormation.forEach((val, i) => {
    if (rightInputs[i]) rightInputs[i].value = val;
  });
});

// Закрыть модальное окно
closeModalBtn.addEventListener('click', () => {
  modal.style.display = 'none';
});

// Применить новую расстановку
applyFormationBtn.addEventListener('click', () => {
  // Считаем значения из левой части
  const leftInputs = leftLinesInputsContainer.querySelectorAll('.line-input');
  let newLeftFormation = [];
  let sumLeft = 0;
  leftInputs.forEach(input => {
    let val = parseInt(input.value, 10);
    if (isNaN(val) || val < 1) val = 1;
    newLeftFormation.push(val);
    sumLeft += val;
  });

  if (sumLeft > 10) {
    alert('Суммарное количество полевых игроков в левой команде не может превышать 10!');
    return;
  }

  // Считаем значения из правой части
  const rightInputs = rightLinesInputsContainer.querySelectorAll('.line-input');
  let newRightFormation = [];
  let sumRight = 0;
  rightInputs.forEach(input => {
    let val = parseInt(input.value, 10);
    if (isNaN(val) || val < 1) val = 1;
    newRightFormation.push(val);
    sumRight += val;
  });

  if (sumRight > 10) {
    alert('Суммарное количество полевых игроков в правой команде не может превышать 10!');
    return;
  }

  // Если всё ок, обновляем formation и перестраиваем
  leftFormation = newLeftFormation;
  rightFormation = newRightFormation;

  updateFormation();
  modal.style.display = 'none';
});

// ------------------------ Запуск ------------------------
createPlayers();     // Создаём DOM-элементы игроков
