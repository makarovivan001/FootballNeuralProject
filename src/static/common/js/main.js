function go_to_page(element, href) {
    const id = element.dataset.id;
    href = href.replace('<id>', id);

    window.location.href = href;
}