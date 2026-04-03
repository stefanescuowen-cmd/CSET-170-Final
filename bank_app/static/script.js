document.addEventListener("DOMContentLoaded", function() {
    // Login password toggle
    const togglePassword = document.getElementById("toggle-password");
    if (togglePassword) {
        const passwordInput = document.getElementById("password");
        togglePassword.addEventListener("click", function() {
            if (passwordInput.type === "password") {
                passwordInput.type = "text";
                togglePassword.classList.replace("fa-eye", "fa-eye-slash");
            } else {
                passwordInput.type = "password";
                togglePassword.classList.replace("fa-eye-slash", "fa-eye");
            }
        });
    }

    // Dashboard / change password toggle
    document.querySelectorAll(".toggle-eye").forEach(icon => {
        icon.addEventListener("click", function() {
            const targetId = icon.getAttribute("data-target");
            const input = document.getElementById(targetId);
            if (input.type === "password") {
                input.type = "text";
                icon.classList.replace("fa-eye", "fa-eye-slash");
            } else {
                input.type = "password";
                icon.classList.replace("fa-eye-slash", "fa-eye");
            }
        });
    });

    // Dashboard blur toggle for sensitive data
    const toggleSensitiveBtn = document.getElementById("toggle-sensitive");
    if (toggleSensitiveBtn) {
        toggleSensitiveBtn.addEventListener("click", function() {
            document.querySelectorAll(".sensitive").forEach(el => {
                el.classList.toggle("blurred");
            });
        });
    }
});