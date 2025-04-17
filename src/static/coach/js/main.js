function show_add_coach(id=null) {
    document.querySelector('.add-coach-window').style.display = "flex";

    get_coach_form();
    if (id) {
        get_coach_by_id(id);
        document.getElementById('coach_save_btn').dataset.id = id;
    }
}

function hide_add_coach() {
    document.querySelector('.add-coach-window').style.display = "none";

    document.getElementById("country_of_birth_id").innerHTML = '';
}

function get_coach_values() {
    let formData = new FormData();
    formData.append('surname', document.getElementById('surname').value);
    formData.append('name', document.getElementById('name').value);
    formData.append('middle_name', document.getElementById('middle_name').value);
    formData.append('number', document.getElementById('number').value);
    formData.append('country_of_birth_id', document.getElementById('country_of_birth_id').value);
    formData.append('club_id', document.getElementById('club_id').value);
    let coachPhotoInput = document.getElementById('coach_photo');
    let coachPhotoFile = coachPhotoInput.files[0];
    formData.append('photo', coachPhotoFile);

    return formData;
}

function add_coach() {
    let formData= get_coach_values();

    request({
        url: '/api/v1/coach/',
        data: formData,
        method: 'POST',
    }).then(data => {
        hide_add_coach();
    });
}

function edit_coach(id) {
    let formData = get_coach_values();
    formData.append('id', id);

    request({
        url: '/api/v1/coach/',
        data: formData,
        method: 'PATCH',
    }).then(data => {
        hide_add_coach();
    });
}

function get_coach_form() {
    request({
        url: '/api/v1/coach/form/',
    }).then(data => {
        let selectCountry = document.getElementById("country_of_birth_id");
        data.countries.forEach(country => {
            let option = document.createElement("option");
            option.value = country.id;
            option.text = country.name;
            selectCountry.appendChild(option);
        });
    });
}

function get_coach_by_id(id) {
    request({
        url: `/api/v1/coach/${id}/`,
    }).then(data => {
        console.log("coach data", data);
    });
}

function coach_save(elem) {
    let id = elem.dataset.id;
    if (id) {
        edit_coach(id);
    } else {
        add_coach();
    }
}