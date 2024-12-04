document.addEventListener('DOMContentLoaded', () => {
    let map, heatmap;

    // TODO: finish map initialization (looks to be possible API error)
    function initMap() {
        // const map = new google.maps.Map(document.getElementById('map'), {
        //     center: { lat: 39.5, lng: -98.35 },
        //     zoom: 4,
        // });
        console.log("Map initialized successfully!");
    }

    // TODO: Figure out how to toggle heatmap
    function toggleHeatmap() {
        console.log("toggle heatmap");
        // if (heatmap) {
        //     if (heatmap.getMap()) {
        //         heatmap.setMap(null); // Hide heatmap
        //         console.log("Heatmap hidden");
        //     } else {
        //         heatmap.setMap(map); // Show heatmap
        //         console.log("Heatmap displayed");
        //     }
        // } else {
        //     console.error("Heatmap is not initialized.");
        // }
    }

    // TODO: replace current mock data with real data (endpoint on backend, this is also the format we will need)
    // Good Reference: https://developers.google.com/maps/documentation/javascript/examples/layer-heatmap#maps_layer_heatmap-javascript
    function getPoints() {
        return [
            new google.maps.LatLng(37.782551, -122.445368),
            new google.maps.LatLng(37.782745, -122.444586),
            new google.maps.LatLng(37.782842, -122.443688),
            { location: new google.maps.LatLng(37.782919, -122.442815), weight: 2 },
            { location: new google.maps.LatLng(37.782992, -122.442112), weight: 3 },
            new google.maps.LatLng(37.7831, -122.441461),
        ];
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

    // TODO: Change endpoint to a new endpoint returning recommended jobs
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

    // TODO: get specific user data, return it, and display it 

    // Attach event listeners
    document.getElementById('refresh-jobs-btn').addEventListener('click', fetchAllJobs);
    document.getElementById('refresh-recommended-jobs-btn').addEventListener('click', fetchRecommendedJobs);
    document.getElementById('toggle-heatmap-btn').addEventListener('click', toggleHeatmap);

    // Initialize everything
    if (typeof google !== 'undefined' && google.maps) {
        initMap();
    } else {
        console.error("Google Maps API failed to load.");
    }

    fetchAllJobs();
    fetchRecommendedJobs();
});