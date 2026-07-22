const API_BASE_URL =
    window.API_BASE_URL || "http://localhost:8001";

async function apiRequest(endpoint, method = "GET", body = null, auth = false) {

    const headers = {
        "Content-Type": "application/json"
    };

    if (auth) {
        const token = localStorage.getItem("access_token");
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }
    }

    try {

        console.log("Calling:", API_BASE_URL + endpoint);

        const response = await fetch(API_BASE_URL + endpoint, {
            method,
            headers,
            body: body ? JSON.stringify(body) : null
        });

        console.log("HTTP Status:", response.status);

        const text = await response.text();

        console.log("Raw Response:", text);

        let data = {};

        try {
            data = JSON.parse(text);
        } catch (e) {
            console.error("JSON Parse Error:", e);
        }

        if (!response.ok) {
            throw new Error(data.detail || text || "Request failed");
        }

        return data;

    } catch (err) {

        console.error("FETCH ERROR:", err);

        throw err;
    }
}