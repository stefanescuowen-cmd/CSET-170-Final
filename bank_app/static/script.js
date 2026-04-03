document.addEventListener("DOMContentLoaded", function() {
    // Sensitive info toggle for all pages
    document.querySelectorAll(".toggle-sensitive").forEach(button => {
        button.addEventListener("click", function() {
            console.log("Toggle button clicked!");  // debug
            document.querySelectorAll(".sensitive").forEach(el => {
                // Toggle 'unblurred' class instead of 'blurred'
                el.classList.toggle("unblurred");
            });
        });
    });

    // Password toggle logic
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
});