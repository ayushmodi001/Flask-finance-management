document.addEventListener("DOMContentLoaded", function () {
    const loginForm = document.getElementById("login-form");
    const errorMessage = document.getElementById("error-message"); // 🔹 Select error message element

    if (loginForm) {
        loginForm.addEventListener("submit", async function (event) {
            event.preventDefault();  // ✅ Prevent default form submission

            const email = document.getElementById("email").value.trim();
            const password = document.getElementById("password").value.trim();

            if (!email || !password) {
                showError("Email and password are required!");
                return;
            }

            try {
                const response = await fetch("/login", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",  // ✅ Ensure JSON request
                    },
                    body: JSON.stringify({ email, password }),  // ✅ Send JSON data
                });

                const data = await response.json();

                if (response.ok) {
                    window.location.href = data.redirect;  // ✅ Redirect on success
                } else {
                    showError(data.error); // ✅ Show error message in UI
                }
            } catch (error) {
                console.error("Login error:", error);
                showError("An error occurred. Please try again later.");
            }
        });
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = "block";  // 🔹 Show error message
    }
});
