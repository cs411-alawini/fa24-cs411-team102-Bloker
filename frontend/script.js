// script.js - Updated to implement delete functionality

let jobOffset = 0;
let jobCity = '';

document.addEventListener('DOMContentLoaded', () => {
    const userLimitInput = document.getElementById('user-limit');
    const citySearchInput = document.getElementById('city-search');

    fetchUsers(userLimitInput.value || 10);
    fetchJobs();

    // Handle Add User Form Submission
    const addUserForm = document.getElementById('add-user-form');
    addUserForm.addEventListener('submit', (e) => {
        e.preventDefault();
        addUser();
    });

    // Handle Refresh Users Button
    const refreshUsersBtn = document.getElementById('refresh-users-btn');
    refreshUsersBtn.addEventListener('click', () => {
        const limit = userLimitInput.value || 10;
        fetchUsers(limit);
    });

    // Handle Search Jobs Button
    const searchJobsBtn = document.getElementById('search-jobs-btn');
    searchJobsBtn.addEventListener('click', () => {
        jobCity = citySearchInput.value;
        jobOffset = 0; // reset offset when new search
        fetchJobs(jobCity, jobOffset);
    });

    // Handle Refresh Jobs Button
    const refreshJobsBtn = document.getElementById('refresh-jobs-btn');
    refreshJobsBtn.addEventListener('click', () => {
        jobOffset += 10; // increment offset to get next 10 jobs
        fetchJobs(jobCity, jobOffset);
    });
});

function fetchUsers(limit = 10) {
    fetch(`http://127.0.0.1:5000/user?limit=${limit}`)
        .then(response => response.json())
        .then(data => populateUsersTable(data))
        .catch(error => console.error('Error fetching users:', error));
}

function populateUsersTable(users) {
    const tbody = document.querySelector('#users-table tbody');
    tbody.innerHTML = '';

    users.forEach(user => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${user.UserId}</td>
            <td>${user.Email}</td>
            <td>${user.FirstName || ''}</td>
            <td>${user.LastName || ''}</td>
            <td>${user.Resume || ''}</td>
            <td class="actions">
                <button onclick="showUpdateForm(${user.UserId}, '${user.Email}')">Edit</button>
                <button class="delete-btn" onclick="deleteUser('${user.Email}')">Delete</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function addUser() {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const firstName = document.getElementById('firstName').value || null;
    const lastName = document.getElementById('lastName').value || null;
    const resume = document.getElementById('resume').value || null;

    const userData = {
        Email: email,
        Password: password,
        FirstName: firstName,
        LastName: lastName,
        Resume: resume
    };

    fetch('http://127.0.0.1:5000/user', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(userData)
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message || 'User added successfully');
        fetchUsers(document.getElementById('user-limit').value || 10);
        document.getElementById('add-user-form').reset();
    })
    .catch(error => console.error('Error:', error));
}

function showUpdateForm(userId, email) {
    // For simplicity, we'll prompt the user for new data
    const firstName = prompt('Enter new first name:');
    const lastName = prompt('Enter new last name:');
    const password = prompt('Enter new password:');
    const resume = prompt('Enter new resume:');

    const userData = {
        Email: email,
        Password: password,
        FirstName: firstName,
        LastName: lastName,
        Resume: resume
    };

    fetch('http://127.0.0.1:5000/user', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(userData)
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message || 'User updated successfully');
        fetchUsers(document.getElementById('user-limit').value || 10);
    })
    .catch(error => console.error('Error:', error));
}

function deleteUser(email) {
    if (confirm(`Are you sure you want to delete the user with email: ${email}?`)) {
        fetch(`http://127.0.0.1:5000/user?email=${encodeURIComponent(email)}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message || 'User deleted successfully');
            fetchUsers(document.getElementById('user-limit').value || 10);
        })
        .catch(error => console.error('Error:', error));
    }
}

function fetchJobs(city = '', offset = 0) {
    let url = `http://127.0.0.1:5000/jobs?offset=${offset}`;
    if (city) {
        url += `&city=${encodeURIComponent(city)}`;
    }
    fetch(url)
        .then(response => response.json())
        .then(data => populateJobsTable(data))
        .catch(error => console.error('Error fetching jobs:', error));
}

function populateJobsTable(jobs) {
    const tbody = document.querySelector('#jobs-table tbody');
    tbody.innerHTML = '';

    jobs.forEach(job => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${job[0]}</td>
            <td>${job[1]}</td>
            <td>${job[2]}</td>
            <td>${job[3]}</td>
            <td>${job[4]}</td>
            <td>${job[5]}</td>
        `;
        tbody.appendChild(tr);
    });
}
