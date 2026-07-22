document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".auto-dismiss").forEach(function (alertElement) {
        setTimeout(function () {
            bootstrap.Alert.getOrCreateInstance(alertElement).close();
        }, 2800);
    });

    document.querySelectorAll("[data-confirm]").forEach(function (element) {
        if (element.tagName === "FORM") {
            element.addEventListener("submit", function (event) {
                if (!window.confirm(element.dataset.confirm || "Are you sure?")) {
                    event.preventDefault();
                }
            });
            return;
        }

        element.addEventListener("click", function (event) {
            if (!window.confirm(element.dataset.confirm || "Are you sure?")) {
                event.preventDefault();
            }
        });
    });

    document.querySelectorAll("[data-password-toggle]").forEach(function (button) {
        button.addEventListener("click", function () {
            const input = button.closest(".input-group").querySelector("input");
            const isHidden = input.type === "password";
            input.type = isHidden ? "text" : "password";
            button.innerHTML = isHidden ? '<i class="bi bi-eye-slash"></i>' : '<i class="bi bi-eye"></i>';
        });
    });

    document.querySelectorAll(".js-submit-with-spinner").forEach(function (form) {
        form.addEventListener("submit", function () {
            const button = form.querySelector("button[type='submit']");
            if (!button) {
                return;
            }
            button.disabled = true;
            button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Please wait...';
        });
    });
});

