let ws = null;
let currentTaskId = null;

document.getElementById('submit-btn').onclick = async () => {
    const task = document.getElementById('task-text').value;
    const resp = await fetch('/api/tasks', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({task})
    });
    const data = await resp.json();
    currentTaskId = data.task_id;
    connectWs(currentTaskId);
};

function connectWs(taskId) {
    ws = new WebSocket(`ws://${location.host}/ws/tasks/${taskId}`);
    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.type === 'action') {
            addAction(msg);
        } else if (msg.type === 'hitl_request') {
            showHitl(msg);
        } else if (msg.type === 'feedback') {
            showFeedback(msg);
        } else if (msg.type === 'done') {
            addAction({tool: 'done', ...msg});
        }
    };
}

function addAction(msg) {
    const div = document.createElement('div');
    div.className = 'action-item';
    div.textContent = `[${msg.tool || msg.type}] ${JSON.stringify(msg.args || msg)}`;
    document.getElementById('actions').appendChild(div);
}

function showHitl(msg) {
    document.getElementById('hitl-panel').classList.remove('hidden');
    document.getElementById('hitl-action').textContent = JSON.stringify(msg.action);
}

document.getElementById('approve-btn').onclick = async () => {
    await fetch(`/api/tasks/${currentTaskId}/approve`, {method: 'POST'});
    document.getElementById('hitl-panel').classList.add('hidden');
};

document.getElementById('deny-btn').onclick = async () => {
    await fetch(`/api/tasks/${currentTaskId}/deny`, {method: 'POST'});
    document.getElementById('hitl-panel').classList.add('hidden');
};

function showFeedback(msg) {
    const div = document.getElementById('feedback');
    div.innerHTML = `通过: ${msg.passed}, 失败: ${msg.failed}`;
}

async function loadCredStatus() {
    const resp = await fetch('/api/credentials/status');
    const data = await resp.json();
    document.getElementById('cred-status').textContent = data.has_key ? '已设置' : '未设置';
}

document.getElementById('save-key').onclick = async () => {
    const key = document.getElementById('api-key').value;
    await fetch('/api/credentials', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({api_key: key})
    });
    loadCredStatus();
};

document.getElementById('delete-key').onclick = async () => {
    await fetch('/api/credentials', {method: 'DELETE'});
    loadCredStatus();
};

loadCredStatus();
