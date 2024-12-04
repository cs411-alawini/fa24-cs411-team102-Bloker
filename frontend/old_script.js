document.addEventListener('DOMContentLoaded', () => {
    // Initialize Map
    function initMap() {
        const map = new google.maps.Map(document.getElementById('map'), {
            center: { lat: 39.5, lng: -98.35 },
            zoom: 4,
        });
        console.log("Map initialized successfully!");
    }

    // Fetch and populate jobs
    function fetchAllJobs() {
        const url = 'http://localhost:5000/jobs';
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

    // TODO: Currently, this hits the jobs endpoint, but it should hit a new "recommended" endpoint. Create a new endpoint to serve recommended job data 

    function fetchRecommendedJobs() {
        const url = 'http://localhost:5000/jobs'; // Using the same endpoint
        fetch(url)
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`Error fetching recommended jobs: ${response.statusText}`);
                }
                return response.json();
            })
            .then((jobs) => {
                console.log("Recommended Jobs Fetched:", jobs);
                populateJobsTable(jobs, 'recommended-jobs-table');
            })
            .catch((error) => console.error('Error:', error));
    }

    function populateJobsTable(jobs, tableId) {
        const tbody = document.getElementById(tableId).querySelector('tbody');
        tbody.innerHTML = ''; // Clear existing rows

        if (!jobs || jobs.length === 0) {
            const noDataRow = document.createElement('tr');
            noDataRow.innerHTML = '<td colspan="6">No jobs found.</td>';
            tbody.appendChild(noDataRow);
            return;
        }

        jobs.forEach((job) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${job[0]}</td>
                <td>${job[1]}</td>
                <td>${job[2]}</td>
                <td>${job[3]}</td>
                <td>${job[4]}</td>
                <td>${job[5]}</td>
            `;
            tbody.appendChild(row);
        });
    }

    // Attach event listeners
    document.getElementById('refresh-jobs-btn').addEventListener('click', fetchAllJobs);
    document.getElementById('refresh-recommended-jobs-btn').addEventListener('click', fetchRecommendedJobs);

    // Initialize everything
    if (typeof google !== 'undefined' && google.maps) {
        initMap();
    } else {
        console.error("Google Maps API failed to load.");
    }
    fetchAllJobs();
    fetchRecommendedJobs();
});