let map, heatmap;
window.initMap = initMap

console.log("JavaScript file loaded successfully.");

async function fetchHeatmapData() {
    try {
        const response = await fetch('http://127.0.0.1:5000/heatmap');
        if (!response.ok) {
            throw new Error(`Error fetching heatmap data: ${response.statusText}`);
        }
        const data = await response.json();
        return data.map(item => ({
            location: new google.maps.LatLng(item.latitude, item.longitude),
            weight: item.job_count, // Use job count as weight for heatmap
        }));
    } catch (error) {
        console.error("Failed to fetch heatmap data:", error);
        return [];
    }
}

async function initMap() {
    const heatmapData = await fetchHeatmapData();
    console.log("Heatmap Data for Map:", heatmapData);
    const centerPoint = heatmapData.length
        ? heatmapData[0].location
        : { lat: 37.775, lng: -122.434 }; // Default center if no data

    map = new google.maps.Map(document.getElementById("map"), {
        zoom: 13,
        center: centerPoint,
        mapTypeId: "satellite",
    });

    heatmap = new google.maps.visualization.HeatmapLayer({
        data: heatmapData,
        map: map,
    });
}

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

        // Clear any existing user data
        localStorage.removeItem('user');

        // Store user info in localStorage
        localStorage.setItem('user', JSON.stringify({
            firstName: data.user.FirstName,
            lastName: data.user.LastName,
            email: email,
            resume: data.user.Resume || '', // Default to empty string if Resume is not present
            password: password
        }));

        console.log("Logged in user info stored in localStorage:", {
            firstName: data.user.FirstName,
            lastName: data.user.LastName,
            email: email,
            resume: data.user.Resume || '',
            password: password
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

function fetchRecommendedJobs() {
    console.log("Fetching recommended jobs...", localStorage);
    const storedUser = localStorage.getItem('user');
    
    if (!storedUser) {
        console.error("User info not found in localStorage");
        return
    }
    localStorage.setItem('userInfo', JSON.stringify(storedUser));
    const userInfo = JSON.parse(localStorage.getItem('userInfo'));
    console.log("User info from localStorage:", userInfo);
    const firstName = JSON.parse(userInfo).firstName;
    console.log(firstName);
    
    const url = `http://127.0.0.1:5000/recommended?firstName=${firstName}`;
    fetch(url)
        .then((response) => {
            if (!response.ok) {
                throw new Error(`Error fetching recommended jobs: ${response.statusText}`);
            }
            return response.json();
        })
        .then((jobs) => {
            console.log("Recommended Jobs Fetched:", jobs);
            const top5Jobs = jobs.slice(0, 5); // Take top 5 jobs
            populateJobsTable(top5Jobs, 'recommended-jobs-table');
        })
        // .catch((error) => console.error('Error:', error));
        .catch((error) => {
            console.warn("Recommended jobs fetch failed:", error.message); // Log the error instead of alerting
        })
}

function populateJobsTable(jobs, tableId) {
    const tableElement = document.getElementById(tableId);
    if (!tableElement) {
        console.error(`Table with ID '${tableId}' not found.`);
        return;
    }
    const tbody = tableElement.querySelector('tbody');
    tbody.innerHTML = ''; // Clear existing rows

    if (!jobs || jobs.length === 0) {
        const noDataRow = document.createElement('tr');
        // Adjust colspan based on the number of table columns
        const colspan = tableId === 'all-jobs-table' ? 6 : 5;
        noDataRow.innerHTML = `<td colspan="${colspan}">No jobs found.</td>`;
        tbody.appendChild(noDataRow);
        return;
    }

    jobs.forEach((job) => {
        const row = document.createElement('tr');
        
        if (tableId === 'all-jobs-table') {
            row.innerHTML = `
                <td>${job.JobId}</td>
                <td>${job.CompanyName}</td>
                <td>${job.JobRole}</td>
                <td>${job.City}</td>
                <td>${job.State}</td>
                <td>${job.ZipCode}</td>
            `;
        } else if (tableId === 'recommended-jobs-table') {
            row.innerHTML = `
                <td>${job.JobId}</td>
                <td>${job.CompanyName}</td>
                <td>${job.JobRole}</td>
                <td>${job.Description}</td>
                <td>${job.Similarity.toFixed(2)}</td>
            `;
        }
        
        tbody.appendChild(row);
    });
}

async function refreshJobs() {
    try {
        const response = await fetch('http://127.0.0.1:5000/jobs/random');
        if (!response.ok) {
            throw new Error(`Error fetching random jobs: ${response.statusText}`);
        }
        const jobs = await response.json();
        populateJobsTable(jobs, 'all-jobs-table');
    } catch (error) {
        console.error("Failed to refresh jobs:", error);
        alert(`Failed to refresh jobs: ${error.message}`);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const refreshJobsBtn = document.getElementById('refresh-jobs-btn');
    if (refreshJobsBtn) {
        refreshJobsBtn.addEventListener('click', refreshJobs);
    }
});
// Update the document with user information
function fetchUserInfo() {
    try {
        const storedUser = localStorage.getItem('user');
        if (!storedUser) {
            console.log("User info not found in localStorage");
            throw new Error("User information not found. Please log in again.");
        }

        const { firstName, lastName, email, resume } = JSON.parse(storedUser);

        // Update the document fields with user information
        document.getElementById("firstName").value = firstName || '';
        document.getElementById("lastName").value = lastName || '';
        document.getElementById("email").value = email || '';
        document.getElementById("resume").value = resume || '';

        console.log("User information updated in the UI from localStorage:", {
            firstName,
            lastName,
            email,
            resume
        });

        fetchRecommendedJobs(); // Fetch recommended jobs if user info is available
    } catch (error) {
        console.error("Error updating user info:", error);
        alert("Error fetching user information. Please log in again.");
        localStorage.clear();
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

// Save user information to the database
async function saveUserInfo(event) {
    event.preventDefault(); // Prevent default form submission

    const firstName = document.getElementById("firstName").value.trim();
    const lastName = document.getElementById("lastName").value.trim();
    const email = document.getElementById("email").value.trim();
    const resume = document.getElementById("resume").value.trim();

    try {
        const storedUser = JSON.parse(localStorage.getItem("user")) || {};

        // Check if there's a change in user data
        if (
            storedUser.firstName === firstName &&
            storedUser.lastName === lastName &&
            storedUser.email === email &&
            storedUser.resume === resume
        ) {
            console.log("No changes detected in user information.");
            alert("No changes made to update.");
            return;
        }

        // Prepare payload
        const payload = {
            OldEmail: storedUser.email, // Current email in the database
            Email: email, // New email to update
            FirstName: firstName,
            LastName: lastName,
            Resume: resume,
            Password: storedUser.password // Include the stored password
        };

        const method = storedUser.email ? "PUT" : "POST"; // Use PUT if updating, POST if inserting

        const response = await fetch("http://127.0.0.1:5000/user", {
            method: method,
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(payload),
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Failed to save user information");

        // Update localStorage with the latest user info
        const updatedUser = {
            ...storedUser,
            firstName,
            lastName,
            email,
            resume
        };
        localStorage.setItem("user", JSON.stringify(updatedUser));

        console.log("User information saved successfully:", data);
        alert("User information saved successfully!");

    } catch (error) {
        console.error("Error saving user information:", error.message);
        alert(`Error saving user information: ${error.message}`);
    }
}

// Attach the saveUserInfo function to the form submission event
document.addEventListener("DOMContentLoaded", () => {
    const personalInfoForm = document.getElementById("personal-info-form");
    if (personalInfoForm) {
        personalInfoForm.addEventListener("submit", saveUserInfo);
    }
});

async function deleteAccount() {
    const confirmation = confirm("Are you sure you want to delete this account? This action cannot be undone.");
    if (!confirmation) return;

    const storedUser = JSON.parse(localStorage.getItem("user"));
    if (!storedUser || !storedUser.email) {
        alert("User not found. Please log in again.");
        window.location.href = "index.html"; // Redirect to login page
        return;
    }

    const email = storedUser.email;

    try {
        // Temporarily disable any other listeners or forms related to user info
        const personalInfoForm = document.getElementById("personal-info-form");
        if (personalInfoForm) {
            personalInfoForm.removeEventListener("submit", saveUserInfo);
        }

        const response = await fetch(`http://127.0.0.1:5000/user?email=${encodeURIComponent(email)}`, {
            method: "DELETE",
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Failed to delete the account");

        // Clear localStorage after successful deletion
        localStorage.clear();

        alert("Account deleted successfully.");
        // Redirect to the index.html (login page)
        window.location.replace("index.html");
    } catch (error) {
        console.error("Error deleting account:", error.message);
        alert(`Error deleting account: ${error.message}`);
    } finally {
        // Ensure no additional data fetching or form-related processes occur
        localStorage.clear(); // Additional cleanup in case of error
        window.location.replace("index.html"); // Ensure redirection
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const deleteAccountBtn = document.getElementById("delete-account-btn");
    if (deleteAccountBtn) {
        deleteAccountBtn.addEventListener("click", deleteAccount);
    }
});

document.addEventListener("DOMContentLoaded", () => {

    const showAddJobFormBtn = document.getElementById("show-add-job-form-btn");
    const addJobForm = document.getElementById("add-job-form");
    const cancelAddJobBtn = document.getElementById("cancel-add-job-btn");

    if (showAddJobFormBtn) {
        showAddJobFormBtn.addEventListener("click", () => {
            addJobForm.style.display = "block";
        });
    }

    if (cancelAddJobBtn) {
        cancelAddJobBtn.addEventListener("click", () => {
            addJobForm.reset();
            addJobForm.style.display = "none";
        });
    }

    if (addJobForm) {
        addJobForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            const companyName = document.getElementById('add-company').value.trim();
            const jobRole = document.getElementById('add-job-role').value.trim();
            const city = document.getElementById('add-city').value.trim();
            const state = document.getElementById('add-state').value.trim();
            const zipCode = document.getElementById('add-zipcode').value.trim();
            const description = document.getElementById('add-description').value.trim();

            const requestBody = {
                CompanyName: companyName,
                JobRole: jobRole,
                City: city,
                State: state,
                ZipCode: zipCode,
                Description: description
            };

            try {
                const response = await fetch('http://127.0.0.1:5000/jobs/add', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(requestBody)
                });

                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.error || 'Error adding job');
                }

                alert("Job added successfully!");
                // Hide the form and reset it
                addJobForm.reset();
                addJobForm.style.display = "none";

                // Refresh the jobs list
                fetchAllJobs();

            } catch (error) {
                console.error('Error adding job:', error.message);
                alert(`Error adding job: ${error.message}`);
            }
        });
    }


    const loginForm = document.getElementById("login-form");
    if (loginForm) {
        loginForm.addEventListener("submit", loginAccount);
    }

    function fetchAllJobs(searchParams = {}) {
        let url = 'http://127.0.0.1:5000/jobs';
        const queryParameters = new URLSearchParams();

        // Append search parameters to the query
        for (const key in searchParams) {
            if (searchParams[key]) {
                queryParameters.append(key, searchParams[key]);
            }
        }

        if ([...queryParameters].length > 0) {
            url += `?${queryParameters.toString()}`;
        }

        console.log(`Fetching jobs with URL: ${url}`);

        fetch(url)
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`Error fetching jobs: ${response.statusText}`);
                }
                return response.json();
            })
            .then((jobs) => {
                console.log("All Jobs Fetched:", jobs);
                populateJobsTable(jobs, 'all-jobs-table');
            })
            .catch((error) => console.error('Error:', error));
    }

    // Handle Search Form Submission
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', (event) => {
            event.preventDefault();

            // Collect search input values
            const companyName = document.getElementById('search-company').value.trim();
            const jobRole = document.getElementById('search-role').value.trim();
            const city = document.getElementById('search-city').value.trim();
            const state = document.getElementById('search-state').value.trim();
            const zipCode = document.getElementById('search-zipcode').value.trim();

            const searchParams = {};

            if (companyName) searchParams.company_name = companyName;
            if (jobRole) searchParams.job_role = jobRole;
            if (city) searchParams.city = city;
            if (state) searchParams.state = state;
            if (zipCode) searchParams.zip_code = zipCode;

            console.log("Search Parameters:", searchParams);

            fetchAllJobs(searchParams);
        });

        // Handle Clear Search Button
        const clearSearchBtn = document.getElementById('clear-search-btn');
        if (clearSearchBtn) {
            clearSearchBtn.addEventListener('click', () => {
                // Clear all search inputs
                document.getElementById('search-company').value = '';
                document.getElementById('search-role').value = '';
                document.getElementById('search-city').value = '';
                document.getElementById('search-state').value = '';
                document.getElementById('search-zipcode').value = '';

                // Fetch all jobs without filters
                fetchAllJobs();
            });
        }
    }

    // Attach event listeners
    document.getElementById('refresh-jobs-btn').addEventListener('click', () => fetchAllJobs());
    // document.getElementById('toggle-heatmap-btn').addEventListener('click', toggleHeatmap);

    // Assuming there's a button with ID 'refresh-recommended-jobs-btn'
    const refreshRecommendedBtn = document.getElementById('refresh-recommended-jobs-btn');
    if (refreshRecommendedBtn) {
        refreshRecommendedBtn.addEventListener('click', fetchRecommendedJobs);
    }

    fetchAllJobs();

    // If on home.html, initialize and fetch user info
    if (window.location.pathname.includes("home.html")) {
        fetchUserInfo(); // Populate the form with the data
        fetchRecommendedJobs(); // Fetch recommended jobs
    }
});