document.getElementById('burger-btn').addEventListener('click', function() {
    this.classList.toggle('open');
    document.getElementById('menu').classList.toggle('active');
});