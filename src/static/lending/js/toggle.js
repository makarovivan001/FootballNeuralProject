const toggleContainer = document.getElementById('players_and_commands');
const buttons = toggleContainer.querySelectorAll('.toggle-button');
const slider = toggleContainer.querySelector('.slider');

// Set initial slider width and position
function initSlider() {
    const activeButton = toggleContainer.querySelector('.toggle-button.active');
    slider.style.width = `${activeButton.offsetWidth}px`;
    slider.style.transform = `translateX(${activeButton.offsetLeft - 6}px)`;
}

// Call init on load
initSlider();
window.addEventListener('resize', initSlider);

function handleTeams() {
    document.querySelector('.section-club-block').insertAdjacentHTML(
    'beforeend',
     `
      <div class="club-up-block"></div>
        <div class="club-middle-block"></div>
        <div class="club-down-block"></div>
      `);
      get_clubs();
}

function handlePlayers() {
    document.querySelector('.section-club-block').insertAdjacentHTML(
    'beforeend',
     `
      <div class="best-up-block"></div>
        <div class="best-middle-block"></div>
        <div class="best-down-block"></div>
      `);
    get_bests();
}

buttons.forEach(button => {
    button.addEventListener('click', () => {
        if (button.classList.contains('active')) return;

        // Remove active class from all buttons
        buttons.forEach(btn => btn.classList.remove('active'));
        // Add active class to clicked button
        button.classList.add('active');

        // Animate slider
        slider.style.width = `${button.offsetWidth}px`;
        slider.style.transform = `translateX(${button.offsetLeft - 6}px)`;

        // Call appropriate function based on button type
        document.querySelector('.section-club-block').innerHTML = '';
        if (button.dataset.type === 'teams') {
            handleTeams();
        } else if (button.dataset.type === 'players') {
            handlePlayers();
        }
    });
});