const projectsEl = document.getElementById('projects');
const tasksEl = document.getElementById('tasks');
const activityEl = document.getElementById('activity');
const scheduleEl = document.getElementById('schedule');
const updatedAtEl = document.getElementById('updatedAt');
const refreshBtn = document.getElementById('refreshBtn');

function badge(text) {
  return `<span class="badge">${text}</span>`;
}

function card(title, body, meta = []) {
  return `
    <div class="item">
      <h3>${title}</h3>
      ${meta.length ? `<div class="badges">${meta.map(badge).join('')}</div>` : ''}
      <p class="meta">${body}</p>
    </div>
  `;
}

function formatDate(value) {
  if (!value) return 'No updates yet';
  return new Date(value).toLocaleString();
}

async function loadState() {
  const res = await fetch('/api/state');
  const state = await res.json();

  updatedAtEl.textContent = formatDate(state.meta.updatedAt);

  projectsEl.innerHTML = state.projects
    .map(project => card(project.name, project.summary, [project.status, project.priority]))
    .join('');

  scheduleEl.innerHTML = state.schedule
    .map(item => card(item.title, `${item.cadence} • ${item.time}`, [item.status]))
    .join('');

  tasksEl.innerHTML = state.tasks
    .map(task => card(task.title, task.notes || 'No notes', [task.status, task.priority, task.owner]))
    .join('');

  activityEl.innerHTML = state.activity
    .map(entry => card(entry.message, formatDate(entry.timestamp), [entry.type]))
    .join('');
}

refreshBtn.addEventListener('click', loadState);
loadState();
setInterval(loadState, 5000);
