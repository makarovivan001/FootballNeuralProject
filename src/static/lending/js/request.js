function request({url, func=null, data = {}, form_data = null, method = 'GET'}) {
    method = method.toUpperCase();

    let options = {
        method: method,
        headers: {
            'X-CSRFToken': document.querySelector('input[name=csrfmiddlewaretoken]').value,
        }
    };

    if (!form_data) {
        options.headers['Content-Type'] = 'application/json';
    }

    if (method === 'GET') {
        const params = new URLSearchParams(data).toString();
        url += '?' + params;
    }
    else {
        if (form_data) {
            options.body = form_data;
        }
        else {
            options.body = JSON.stringify(data);
        }
    }

    return fetch(url, options)
        .then(async (responce) => {
            if (!responce.ok) {
                let errorText = await responce.text();
                throw {status: responce.status, message: JSON.parse(errorText)};
            }
            try {
                if (responce.status !== 204) {
                    return responce.json();
                }
            }
            catch (error) {}
        })
        .then(data => {
            if (func) {
                func(data);
            }
            return data;
        })
        .catch((error) => {
            console.info("status:", error.status);
            console.info("detail:", error.message.detail);
        });
}