document.addEventListener("DOMContentLoaded", function () {
    const signupForm = document.getElementById("signup-form");

    if (signupForm) {
        signupForm.addEventListener("submit", async function (event) {
            event.preventDefault();

            const data = {
                fullname: document.getElementById("fullname").value.trim(),
                username: document.getElementById("username").value.trim(),
                email: document.getElementById("email").value.trim(),
                phone: document.getElementById("phone").value.trim(),
                gender: document.getElementById("gender").value,
                dob: document.getElementById("dob").value,
                password: document.getElementById("password").value
            };

            console.log("🔹 Sending JSON:", JSON.stringify(data)); // Debugging

            try {
                const response = await fetch("/signup", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",  // Important!
                        "Accept": "application/json" // Ensure JSON response
                    },
                    body: JSON.stringify(data) // Convert to JSON
                });

                const result = await response.json();
                console.log("🔹 Response:", result); // Debugging

                if (response.ok) {
                    alert(result.message);
                    window.location.href = result.redirect;
                } else {
                    alert(result.error);
                }
            } catch (error) {
                alert("Signup failed! Please try again.");
            }
        });
    }
});
