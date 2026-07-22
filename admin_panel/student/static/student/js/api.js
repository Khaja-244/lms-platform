"use strict";

const API_BASE_URL = (window.API_BASE_URL || "http://localhost:8001").replace(/\/$/, "");
const TOKEN_KEY = "akr_lms_access_token";
const USER_KEY = "akr_lms_student_user";
const ENROLLMENT_KEY = "akr_lms_enrollments";

function getAccessToken() {
    return localStorage.getItem(TOKEN_KEY) || localStorage.getItem("access_token");
}

function setSession(token, user) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem("access_token", token);
    if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
}

function getStoredUser() {
    try {
        return JSON.parse(localStorage.getItem(USER_KEY) || "{}");
    } catch {
        return {};
    }
}

function setStoredUser(user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user || {}));
}

function clearSession() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem("access_token");
    localStorage.removeItem(USER_KEY);
}

function getEnrollmentMap() {
    try {
        return JSON.parse(localStorage.getItem(ENROLLMENT_KEY) || "{}");
    } catch {
        return {};
    }
}

function saveEnrollment(courseId, enrollmentId) {
    const map = getEnrollmentMap();
    map[String(courseId)] = enrollmentId;
    localStorage.setItem(ENROLLMENT_KEY, JSON.stringify(map));
}

async function apiRequest(endpoint, options = {}) {
    const method = options.method || "GET";
    const body = options.body;
    const auth = options.auth !== false;
    const responseType = options.responseType || "json";
    const headers = new Headers(options.headers || {});

    if (!(body instanceof FormData) && body !== undefined && body !== null) {
        headers.set("Content-Type", "application/json");
    }

    const token = getAccessToken();
    if (auth && token) headers.set("Authorization", `Bearer ${token}`);

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method,
        headers,
        body: body instanceof FormData ? body : body === undefined || body === null ? null : JSON.stringify(body),
    });

    if (responseType === "blob") {
        if (!response.ok) throw await buildApiError(response);
        return response.blob();
    }

    const text = await response.text();
    let data = {};
    if (text) {
        try {
            data = JSON.parse(text);
        } catch {
            data = { message: text };
        }
    }

    if (!response.ok) {
        if (response.status === 401) {
            clearSession();
            const page = document.body?.dataset?.page || "";
            if (!["login", "register"].includes(page)) {
                window.location.href = window.STUDENT_ROUTES?.login || "/student/";
                return {};
            }
        }
        const message = data.detail || data.message || data.error || response.statusText || "Request failed";
        if (Array.isArray(message)) {
            throw new Error(message.map((item) => item.msg || item.message || String(item)).join(", "));
        }
        throw new Error(message);
    }

    return data;
}

async function buildApiError(response) {
    try {
        const data = await response.json();
        return new Error(data.detail || data.message || response.statusText || "Request failed");
    } catch {
        return new Error(response.statusText || "Request failed");
    }
}

window.LMS = {
    apiBaseUrl: API_BASE_URL,
    tokenKey: TOKEN_KEY,
    getAccessToken,
    setSession,
    clearSession,
    getStoredUser,
    setStoredUser,
    getEnrollmentMap,
    saveEnrollment,
    request: apiRequest,
    get: (endpoint, auth = true) => apiRequest(endpoint, { method: "GET", auth }),
    post: (endpoint, body = {}, auth = true) => apiRequest(endpoint, { method: "POST", body, auth }),
    put: (endpoint, body = {}, auth = true) => apiRequest(endpoint, { method: "PUT", body, auth }),
    blob: (endpoint) => apiRequest(endpoint, { method: "GET", responseType: "blob", auth: true }),
};
