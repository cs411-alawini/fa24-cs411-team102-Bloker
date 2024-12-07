// Handle login
async function loginAccount(event) {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    try {
        const response = await fetch('http://127.0.0.1:5000/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Login failed');

        // Store user info in localStorage for future use
        localStorage.setItem('user', JSON.stringify(data.user));

        alert("Login successful! Redirecting to homepage...");
        window.location.href = "home.html";
    } catch (error) {
        console.error('Error during login:', error.message);
        const errorMessage = document.getElementById("error-message");
        errorMessage.style.display = "block";
        errorMessage.innerText = `Error: ${error.message}`;
    }
}

// Attach event listeners
document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.getElementById("login-form");
    if (loginForm) loginForm.addEventListener("submit", loginAccount);
});