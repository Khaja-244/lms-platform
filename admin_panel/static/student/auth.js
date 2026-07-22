document.addEventListener("DOMContentLoaded", () => {

    const loginForm = document.getElementById("loginForm");

    if (!loginForm) return;

    loginForm.addEventListener("submit", loginUser);

});


async function loginUser(e) {

    e.preventDefault();

    const email = document.getElementById("email").value.trim();

    const password = document.getElementById("password").value;

    const response = await apiRequest(
        "/auth/login/",
        "POST",
        {
            email,
            password
        }
    );

    if (response.ok) {

        localStorage.setItem(
            "access_token",
            response.data.access_token
        );

        window.location.href = "/student/dashboard/";

    }
    else {

        alert(response.data.detail || "Invalid email or password.");

    }

}


function logout() {

    localStorage.removeItem("access_token");

    window.location.href = "/student/";

}