// --- Admin Auth (Login) ---
function getAuthToken() {
    return localStorage.getItem('admin_token');
}

function getAuthHeaders() {
    const token = getAuthToken();
    return token ? { 'Authorization': 'Bearer ' + token } : {};
}

function logoutAdmin() {
    localStorage.removeItem('admin_token');
    window.location.href = 'login.html?next=admin.html';
}

// --- Dark Mode ---
function initDarkMode() {
    var saved = localStorage.getItem('dark_mode');
    var isDark = saved === '1';
    document.body.classList.toggle('dark-mode', isDark);
    var cb = document.getElementById('darkModeToggle');
    if (cb) {
        cb.checked = isDark;
        cb.addEventListener('change', function () {
            isDark = cb.checked;
            localStorage.setItem('dark_mode', isDark ? '1' : '0');
            document.body.classList.toggle('dark-mode', isDark);
        });
    }
}
initDarkMode();

// Utility to update time
function updateTime() {
    const now = new Date();
    const dateString = now.toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
    const timeString = now.toLocaleTimeString();
    const el = document.getElementById('datetime');
    if (el) el.textContent = `${dateString} | ${timeString}`;
}
setInterval(updateTime, 1000);
updateTime(); // Initial call

// Toast Notification (with icon and slide animation)
var toastIconSuccess = '<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>';
var toastIconError = '<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>';

function showToast(message, type = 'success') {
    var toast = document.getElementById("toast");
    if (!toast) return;
    var icon = type === 'success' ? toastIconSuccess : toastIconError;
    toast.innerHTML = icon + '<span>' + message + '</span>';
    toast.className = 'show ' + type;
    toast.classList.remove('hide');
    clearTimeout(toast._hideTimer);
    toast._hideTimer = setTimeout(function () {
        toast.classList.add('hide');
        setTimeout(function () {
            toast.className = '';
        }, 350);
    }, 3000);
}

// Index: store current attendance data for search/sort
var liveAttendanceData = [];
var liveAttendanceSort = { col: 'time', dir: -1 };
var selectedAttendanceDate = null; // null = today

function renderAttendanceTable(tbody, data, searchTerm, sortCol, sortDir) {
    var filtered = data;
    if (searchTerm) {
        var q = searchTerm.toLowerCase().trim();
        filtered = data.filter(function (row) { return (row.name || '').toLowerCase().indexOf(q) !== -1; });
    }
    var sorted = filtered.slice();
    if (sortCol === 'name') {
        sorted.sort(function (a, b) {
            var x = (a.name || '').localeCompare(b.name || '');
            return sortDir > 0 ? x : -x;
        });
    } else if (sortCol === 'time') {
        sorted.sort(function (a, b) {
            var x = (a.time || '').localeCompare(b.time || '');
            return sortDir > 0 ? x : -x;
        });
    }
    tbody.innerHTML = '';
    if (sorted.length === 0) {
        tbody.innerHTML = '<tr><td colspan="2" class="table-empty">' + (data.length === 0 ? 'No attendance records yet.' : 'No matches.') + '</td></tr>';
    } else {
        sorted.forEach(function (row) {
            var tr = document.createElement('tr');
            tr.innerHTML = '<td>' + (row.name || '') + '</td><td>' + (row.time || '') + '</td>';
            tbody.appendChild(tr);
        });
    }
}

async function fetchLiveAttendance() {
    var tbody = document.querySelector('#attendanceTable tbody');
    if (!tbody) return;
    var dateParam = selectedAttendanceDate || '';
    var url = dateParam ? '/attendance?date=' + encodeURIComponent(dateParam) : '/attendance';
    try {
        var response = await fetch(url);
        var data = await response.json();
        liveAttendanceData = Array.isArray(data) ? data : [];
        var searchEl = document.getElementById('searchAttendance');
        var q = searchEl ? searchEl.value : '';
        renderAttendanceTable(tbody, liveAttendanceData, q, liveAttendanceSort.col, liveAttendanceSort.dir);
        var statEl = document.getElementById('statTodayCount');
        if (statEl) statEl.textContent = liveAttendanceData.length;
    } catch (error) {
        console.error('Error fetching attendance:', error);
        tbody.innerHTML = '<tr><td colspan="2" class="table-empty">Unable to load attendance.</td></tr>';
        var statEl = document.getElementById('statTodayCount');
        if (statEl) statEl.textContent = '—';
    }
}

// Index: date picker, search, sort, poll
if (document.getElementById('attendanceTable')) {
    var datePicker = document.getElementById('attendanceDatePicker');
    if (datePicker) {
        var today = new Date();
        datePicker.value = today.getFullYear() + '-' + String(today.getMonth() + 1).padStart(2, '0') + '-' + String(today.getDate()).padStart(2, '0');
        datePicker.addEventListener('change', function () {
            selectedAttendanceDate = datePicker.value || null;
            var tbody = document.querySelector('#attendanceTable tbody');
            if (tbody) tbody.innerHTML = '<tr><td colspan="2" class="table-loading"><span class="skeleton-line" style="width:60%"></span></td></tr>';
            fetchLiveAttendance();
        });
    }
    var searchAttendance = document.getElementById('searchAttendance');
    if (searchAttendance) {
        searchAttendance.addEventListener('input', function () {
            var tbody = document.querySelector('#attendanceTable tbody');
            if (tbody) renderAttendanceTable(tbody, liveAttendanceData, searchAttendance.value, liveAttendanceSort.col, liveAttendanceSort.dir);
        });
    }
    var thead = document.querySelector('#attendanceTable thead');
    if (thead) {
        thead.addEventListener('click', function (e) {
            var th = e.target.closest('th.sortable');
            if (!th) return;
            var col = th.getAttribute('data-sort');
            if (!col) return;
            liveAttendanceSort.dir = (liveAttendanceSort.col === col) ? -liveAttendanceSort.dir : 1;
            liveAttendanceSort.col = col;
            var tbody = document.querySelector('#attendanceTable tbody');
            var searchEl = document.getElementById('searchAttendance');
            if (tbody) renderAttendanceTable(tbody, liveAttendanceData, searchEl ? searchEl.value : '', liveAttendanceSort.col, liveAttendanceSort.dir);
        });
    }
    var tbodyLive = document.querySelector('#attendanceTable tbody');
    if (tbodyLive) tbodyLive.innerHTML = '<tr><td colspan="2" class="table-loading"><span class="skeleton-line" style="width:60%"></span></td></tr>';
    setInterval(fetchLiveAttendance, 2000);
    fetchLiveAttendance();
}

// Handle Registration
const registerForm = document.getElementById('registerForm');
if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(registerForm);
        const submitBtn = registerForm.querySelector('button');
        const originalText = submitBtn.textContent;
        
        submitBtn.textContent = "Processing...";
        submitBtn.disabled = true;
        
        try {
            const response = await fetch('/register', {
                method: 'POST',
                headers: getAuthHeaders(),
                body: formData
            });
            const result = await response.json();
            
            if (response.ok) {
                showToast(result.message, 'success');
                registerForm.reset();
                if (typeof fetchStudents === 'function') fetchStudents();
            } else {
                showToast(result.message, 'error');
            }
        } catch (error) {
            showToast("Error connecting to server", 'error');
        } finally {
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
        }
    });
}

// Admin: store all attendance for search/sort
var allAttendanceData = [];
var allAttendanceSort = { col: 'date', dir: -1 };

function todayStr() {
    var d = new Date();
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
}

function updateAdminStats(data) {
    var today = todayStr();
    var todayCount = (data || []).filter(function (r) { return r.date === today; }).length;
    var totalEl = document.getElementById('adminStatTotal');
    var todayEl = document.getElementById('adminStatToday');
    if (totalEl) totalEl.textContent = (data || []).length;
    if (todayEl) todayEl.textContent = todayCount;
}

function renderAllAttendanceTable(tbody, data, searchTerm, sortCol, sortDir) {
    var filtered = data || [];
    if (searchTerm) {
        var q = searchTerm.toLowerCase().trim();
        filtered = data.filter(function (row) {
            return (row.name || '').toLowerCase().indexOf(q) !== -1 ||
                (row.date || '').toLowerCase().indexOf(q) !== -1 ||
                (row.time || '').toLowerCase().indexOf(q) !== -1;
        });
    }
    var sorted = filtered.slice();
    sorted.sort(function (a, b) {
        var va = a[sortCol] || '';
        var vb = b[sortCol] || '';
        var x = String(va).localeCompare(String(vb));
        return sortDir > 0 ? x : -x;
    });
    tbody.innerHTML = '';
    if (sorted.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" class="table-empty">' + ((data || []).length === 0 ? 'No attendance records yet.' : 'No matches.') + '</td></tr>';
    } else {
        sorted.forEach(function (row) {
            var tr = document.createElement('tr');
            tr.innerHTML = '<td>' + (row.date || '') + '</td><td>' + (row.time || '') + '</td><td>' + (row.name || '') + '</td>';
            tbody.appendChild(tr);
        });
    }
}

async function fetchAllAttendance() {
    var tbody = document.querySelector('#allAttendanceTable tbody');
    if (!tbody) return [];
    tbody.innerHTML = '<tr><td colspan="3" class="table-loading"><span class="skeleton-line" style="width:50%"></span></td></tr>';
    try {
        var response = await fetch('/attendance/all', { headers: getAuthHeaders() });
        if (response.status === 401) {
            localStorage.removeItem('admin_token');
            window.location.href = 'login.html?next=admin.html';
            return [];
        }
        var data = await response.json();
        allAttendanceData = Array.isArray(data) ? data : [];
        updateAdminStats(allAttendanceData);
        var searchEl = document.getElementById('searchAllAttendance');
        var q = searchEl ? searchEl.value : '';
        renderAllAttendanceTable(tbody, allAttendanceData, q, allAttendanceSort.col, allAttendanceSort.dir);
        return allAttendanceData;
    } catch (error) {
        console.error('Error fetching all records:', error);
        tbody.innerHTML = '<tr><td colspan="3" class="table-empty">Unable to load records.</td></tr>';
        return [];
    }
}

// Admin: students list
async function fetchStudents() {
    var listEl = document.getElementById('studentsList');
    var emptyEl = document.getElementById('studentsListEmpty');
    if (!listEl) return;
    if (emptyEl) emptyEl.textContent = 'Loading…';
    if (listEl) listEl.innerHTML = '';
    try {
        var response = await fetch('/students', { headers: getAuthHeaders() });
        if (response.status === 401) {
            if (emptyEl) emptyEl.textContent = 'Sign in required.';
            return;
        }
        var data = await response.json();
        var students = (data && data.students) ? data.students : [];
        if (emptyEl) {
            emptyEl.style.display = students.length === 0 ? 'block' : 'none';
            emptyEl.textContent = 'No students registered.';
        }
        listEl.innerHTML = '';
        students.forEach(function (name) {
            var li = document.createElement('li');
            li.innerHTML = '<span>' + (name || '') + '</span><button type="button" class="btn-remove" data-name="' + (name || '').replace(/"/g, '&quot;') + '">Remove</button>';
            listEl.appendChild(li);
            li.querySelector('.btn-remove').addEventListener('click', function () {
                deleteStudent(name);
            });
        });
    } catch (e) {
        if (emptyEl) emptyEl.textContent = 'Unable to load.';
    }
}

function deleteStudent(name) {
    if (!name) return;
    fetch('/students/' + encodeURIComponent(name), { method: 'DELETE', headers: getAuthHeaders() })
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (res.status === 'success') {
                showToast(res.message, 'success');
                fetchStudents();
            } else {
                showToast(res.message || 'Failed to remove.', 'error');
            }
        })
        .catch(function () {
            showToast('Error removing student.', 'error');
        });
}

// Chart.js Initialization (gradient, rounded bars). Pass data from fetchAllAttendance to avoid double fetch.
async function initChart(dataFromFetch) {
    var ctx = document.getElementById('attendanceChart');
    if (!ctx) return;
    var data = dataFromFetch && dataFromFetch.length >= 0 ? dataFromFetch : await fetchAllAttendance();
    var counts = {};
    data.forEach(function (row) {
        counts[row.date] = (counts[row.date] || 0) + 1;
    });
    var sortedDates = Object.keys(counts).sort();
    var values = sortedDates.map(function (date) { return counts[date]; });
    var gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(52, 152, 219, 0.8)');
    gradient.addColorStop(1, 'rgba(52, 152, 219, 0.3)');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: sortedDates,
            datasets: [{
                label: 'Students Present',
                data: values,
                backgroundColor: gradient,
                borderColor: 'rgba(52, 152, 219, 1)',
                borderWidth: 1,
                borderRadius: 8,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { stepSize: 1 },
                    grid: { color: 'rgba(0,0,0,0.06)' }
                },
                x: {
                    grid: { display: false }
                }
            }
        }
    });
}

async function downloadReport() {
    try {
        const response = await fetch('/export', { headers: getAuthHeaders() });
        if (response.status === 401) {
            localStorage.removeItem('admin_token');
            window.location.href = 'login.html?next=admin.html';
            return;
        }
        if (!response.ok) throw new Error('Export failed');
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'attendance_report.xlsx';
        a.click();
        URL.revokeObjectURL(url);
        if (typeof showToast === 'function') showToast('Report downloaded.', 'success');
    } catch (e) {
        if (typeof showToast === 'function') showToast('Download failed.', 'error');
    }
}
