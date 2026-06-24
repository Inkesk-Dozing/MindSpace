document.addEventListener('DOMContentLoaded', function() {
    let rowIndex = 0;

    const addBtn = document.getElementById('add-row-btn');
    if (addBtn) {
        addBtn.onclick = function() {
            const tbody = document.getElementById('edit-tbody');
            const newRow = tbody.insertRow();
            const headers = Array.from(document.querySelectorAll('#edit-table th'));
            headers.forEach(function(th, index) {
                const cell = newRow.insertCell(index);
                const input = document.createElement('input');
                input.type = 'text';
                var colName = th.textContent.trim().replace(/\\s+/g, '_').replace(/[^a-zA-Z0-9_]/g, '');
                input.name = colName + '_' + rowIndex;
                input.placeholder = th.textContent.trim();
                cell.appendChild(input);
            });
            rowIndex = rowIndex + 1;
        };
    }

    const proceedBtn = document.getElementById('proceed-btn');
    if (proceedBtn) {
        proceedBtn.onclick = function() {
            window.location.href = '/dashboard';
        };
    }

    const toggleBtn = document.getElementById('theme-toggle');
    if (toggleBtn) {
        var savedTheme = localStorage.getItem('theme') || 'light';
        toggleBtn.textContent = savedTheme === 'dark' ? '☀️' : '🌙';
        toggleBtn.onclick = function() {
            var currentTheme = document.documentElement.getAttribute('data-theme');
            var newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            toggleBtn.textContent = newTheme === 'dark' ? '☀️' : '🌙';
        };
    }
});
