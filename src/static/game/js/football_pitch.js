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

// Текущие расстановки (массивы вида [3,4,3] - суммарно 10)
let leftFormation = [4, 3, 3];
let rightFormation = [2, 1, 4, 3];

// ------------------------ Инициализация игроков ------------------------

// Создаём 11 DOM-элементов для каждой команды (0-й — вратарь, остальные 10 — полевые)
function createPlayers() {
  // Левая команда
  for (let i = 0; i < 11; i++) {
    const player = document.createElement('div');
    const player_info = document.createElement('div');
    player.classList.add('player', 'team-left');
    player_info.classList.add('pitch-player-info');

    field.appendChild(player);
    player.appendChild(player_info);
    leftTeamPlayers.push(player);
  }
  
  // Правая команда
  for (let i = 0; i < 11; i++) {
    const player = document.createElement('div');
    const player_info = document.createElement('div');
    player.classList.add('player', 'team-right');
    player_info.classList.add('pitch-player-info');
    field.appendChild(player);
    player.appendChild(player_info);
    rightTeamPlayers.push(player);
  }
}

// ------------------------ Расстановка игроков на поле ------------------------
/**
 * Расставляем левую команду строго на левой половине поля (0% - 50%).
 * @param {Array<number>} formation - массив вида [3,4,3], суммарно 10
 */
function placeLeftTeam(formation) {
  const fieldWidth = field.clientWidth;
  const fieldHeight = field.clientHeight;

  const playerWidth = field.querySelector('.player').offsetWidth;

  // Вратарь (индекс 0)
  const goalkeeper = leftTeamPlayers[0];
  // Пусть вратарь стоит около 10% по X (т.е. 0.10) и по центру по Y
  goalkeeper.style.left = `${fieldWidth * 0.1 - (playerWidth / 2)}px`;
  goalkeeper.style.top = `${fieldHeight * 0.5 - (playerWidth / 2)}px`;
  
  // Остальные 10 полевых
  let totalLines = formation.length;
  // Распределим их от X=0.2 до X=0.45, например
  let xStart = 0.2; // где начинается первая линия
  let xEnd = 0.45;  // где заканчивается последняя
  let xRange = xEnd - xStart; // 0.25
  
  let xStep = xRange / (totalLines - 1 || 1); 
  // (totalLines - 1) — чтобы равномерно распределить линии от xStart до xEnd

  let currentIndex = 1; // начинаем с 1, т.к. 0 — вратарь

  for (let lineIndex = 0; lineIndex < totalLines; lineIndex++) {
    const playersInLine = formation[lineIndex];
    
    // Координата X для этой линии
    let x = xStart + xStep * lineIndex;
    
    // По оси Y игроков расставим равномерно
    let yStep = 1 / (playersInLine + 1);
    
    for (let p = 0; p < playersInLine; p++) {
      const player = leftTeamPlayers[currentIndex];
      let y = yStep * (p + 1); // например, если 3 игрока, они будут на ~25%, ~50%, ~75% высоты
      player.style.left = `${fieldWidth * x - (playerWidth / 2)}px`;
      player.style.top = `${fieldHeight * y - (playerWidth / 2)}px`;
      
      currentIndex++;
    }
  }
}

/**
 * Расставляем правую команду строго на правой половине поля (50% - 100%).
 * @param {Array<number>} formation - массив вида [3,4,3], суммарно 10
 */
function placeRightTeam(formation) {
  const fieldWidth = field.clientWidth;
  const fieldHeight = field.clientHeight;

  const playerWidth = field.querySelector('.player').offsetWidth;

  // Вратарь (индекс 0)
  const goalkeeper = rightTeamPlayers[0];
  // Пусть вратарь стоит около 90% по X (т.е. 0.90) и по центру по Y
  goalkeeper.style.left = `${fieldWidth * 0.9 - (playerWidth / 2)}px`;
  goalkeeper.style.top = `${fieldHeight * 0.5 - (playerWidth / 2)}px`;

  // Остальные 10 полевых
  let totalLines = formation.length;
  // Распределим их от X=0.55 до X=0.8, например
  let xStart = 0.55;
  let xEnd = 0.8;
  let xRange = xEnd - xStart; // 0.25

  let xStep = xRange / (totalLines - 1 || 1);

  let currentIndex = 1; // начинаем с 1, т.к. 0 — вратарь
  
  for (let lineIndex = 0; lineIndex < totalLines; lineIndex++) {
    const playersInLine = formation[lineIndex];
    
    // Координата X для этой линии
    let x = xStart + xStep * lineIndex;
    // Распределяем игроков по оси Y
    let yStep = 1 / (playersInLine + 1);

    for (let p = 0; p < playersInLine; p++) {
      const player = rightTeamPlayers[currentIndex];
      let y = yStep * (p + 1);
      player.style.left = `${fieldWidth * x - (playerWidth / 2)}px`;
      player.style.top = `${fieldHeight * y - (playerWidth / 2)}px`;
      
      currentIndex++;
    }
  }
}

// Вызываем расстановку для обеих команд
function updateFormation() {
  let first_team_block = document.querySelector (".first_team_block span"); 
  let second_team_block = document.querySelector (".second_team_block span");

  first_team_block.innerText = leftFormation.join("-");
  second_team_block.innerText = [...rightFormation].reverse().join("-");
  placeLeftTeam(leftFormation);
  placeRightTeam(rightFormation);
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
updateFormation();   // Ставим их по умолчанию (3-4-3 и 3-4-3)