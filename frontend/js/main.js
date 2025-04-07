document.addEventListener('DOMContentLoaded', () => {
    const connectTelegramBtn = document.getElementById('connectTelegram');
    const createTaskBtn = document.getElementById('createTaskBtn');
    const createTaskSubmit = document.getElementById('createTaskSubmit');
    const taskForm = document.getElementById('taskForm');
    const tasksList = document.getElementById('tasksList');
    const newTaskModal = document.getElementById('newTaskModal');
    const modalCloseButtons = document.querySelectorAll('.modal-close');
    const stats = {
        activeTasks: document.getElementById('activeTasks'),
        completedTasks: document.getElementById('completedTasks'),
        activeIPs: document.getElementById('activeIPs')
    };

    // Initialize WebSocket connection
    const ws = new WebSocket('ws://localhost:5000/ws');
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        updateStats(data);
        updateTasks(data);
    };

    function updateStats(data) {
        if (data.stats) {
            stats.activeTasks.textContent = data.stats.activeTasks;
            stats.completedTasks.textContent = data.stats.completedTasks;
            stats.activeIPs.textContent = data.stats.activeIPs;
        }
    }

    function updateTasks(data) {
        if (data.tasks) {
            tasksList.innerHTML = '';
            data.tasks.forEach(task => {
                const taskElement = createTaskElement(task);
                tasksList.appendChild(taskElement);
            });
        }
    }

    function createTaskElement(task) {
        const div = document.createElement('div');
        div.className = 'task-card';
        div.innerHTML = `
            <div class="task-header">
                <div class="task-id">TASK #${task.id}</div>
                <div class="task-status status-${task.status}">
                    <i class="fas fa-circle-notch fa-spin"></i>
                    <span>${task.status}</span>
                </div>
            </div>
            <div class="task-content">
                <a href="${task.url}" target="_blank" class="task-url">${task.url}</a>
                <div class="task-meta">
                    <div class="task-meta-item">
                        <div class="task-meta-label">Progress</div>
                        <div class="task-meta-value">${task.progress}%</div>
                    </div>
                    <div class="task-meta-item">
                        <div class="task-meta-label">Status</div>
                        <div class="task-meta-value">${task.status}</div>
                    </div>
                </div>
                <div class="progress-container">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${task.progress}%"></div>
                    </div>
                </div>
            </div>
            <div class="task-actions">
                <button class="btn btn-success" onclick="resumeTask('${task.id}')">
                    <i class="fas fa-play"></i> Resume
                </button>
                <button class="btn btn-outline" onclick="pauseTask('${task.id}')">
                    <i class="fas fa-pause"></i> Pause
                </button>
                <button class="btn btn-danger" onclick="stopTask('${task.id}')">
                    <i class="fas fa-stop"></i> Stop
                </button>
            </div>
        `;
        return div;
    }

    // Task creation
    createTaskBtn.addEventListener('click', () => {
        newTaskModal.classList.add('active');
    });

    createTaskSubmit.addEventListener('click', async (e) => {
        e.preventDefault();
        const formData = {
            name: document.getElementById('taskName').value,
            url: document.getElementById('taskUrl').value,
            actionsCount: document.getElementById('actionsCount').value,
            cyclesCount: document.getElementById('cyclesCount').value,
            actionType: document.querySelector('input[name="actionType"]:checked').value
        };

        try {
            const response = await fetch('/api/tasks', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                const task = await response.json();
                newTaskModal.classList.remove('active');
                taskForm.reset();
            }
        } catch (error) {
            console.error('Error creating task:', error);
        }
    });

    // Modal close functionality
    modalCloseButtons.forEach(button => {
        button.addEventListener('click', () => {
            newTaskModal.classList.remove('active');
            taskForm.reset();
        });
    });

    // Task control functions
    window.resumeTask = async (taskId) => {
        await fetch(`/api/tasks/${taskId}/resume`, { method: 'PUT' });
    };

    window.pauseTask = async (taskId) => {
        await fetch(`/api/tasks/${taskId}/pause`, { method: 'PUT' });
    };

    window.stopTask = async (taskId) => {
        if (confirm('Are you sure you want to stop this task?')) {
            await fetch(`/api/tasks/${taskId}`, { method: 'DELETE' });
        }
    };

    // Telegram connection
    connectTelegramBtn.addEventListener('click', async () => {
        try {
            const response = await fetch('/api/telegram/connect', {
                method: 'POST'
            });
            const data = await response.json();
            alert(data.message);
        } catch (error) {
            console.error('Error connecting to Telegram:', error);
            alert('Error connecting to Telegram bot');
        }
    });

    // Initial data fetch
    fetch('/api/tasks').then(response => 
        response.json().then(data => updateTasks({ tasks: data }))
    );
});
