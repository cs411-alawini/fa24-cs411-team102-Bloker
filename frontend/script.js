
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

        // Store user info in localStorage
        localStorage.setItem('user', JSON.stringify({
            firstName: data.user.FirstName,
            lastName: data.user.LastName,
            resume: data.user.Resume || '' // Default to empty string if Resume is not present
        }));

        console.log("Logged in user info stored in localStorage:", {
            firstName: data.user.FirstName,
            lastName: data.user.LastName,
            resume: data.user.Resume || ''
        });

        alert("Login successful! Redirecting to homepage...");
        window.location.href = "home.html";
    } catch (error) {
        console.error('Error during login:', error.message);
        const errorMessage = document.getElementById("error-message");
        errorMessage.style.display = "block";
        errorMessage.innerText = `Error: ${error.message}`;
    }
}

// Update the document with user information
function fetchUserInfo() {
    console.log("Fetching user information from localStorage...");

    try {
        const storedUser = localStorage.getItem('user');
        if (!storedUser) {
            console.log("User info not found in localStorage");
            throw new Error("User information not found. Please log in again.");
        }

        const { firstName, lastName, resume } = JSON.parse(storedUser);

        // Update the document fields with user information
        document.getElementById("firstName").value = firstName || '';
        document.getElementById("lastName").value = lastName || '';
        document.getElementById("resume").value = resume || '';

        console.log("User information updated in the UI from localStorage:", {
            firstName,
            lastName,
            resume
        });
    } catch (error) {
        console.error("Error updating user info:", error);
        alert("Error fetching user information. Please log in again.");
        localStorage.removeItem("user");
        window.location.href = "index.html";
    }
}

// Initialize user information on page load
document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.getElementById("login-form");
    if (loginForm) {
        loginForm.addEventListener("submit", loginAccount);
    }

    // If on home.html, initialize and fetch user info
    if (window.location.pathname.includes("home.html")) {
        fetchUserInfo(); // Populate the form with the data
    }
});