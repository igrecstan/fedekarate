// admin/js/evenements.js - Gestion des événements

let eventsData = [];

async function loadEvents() {
    const tbody = document.getElementById('eventsTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = '<tr><td colspan="6" class="loader"><i class="fas fa-spinner fa-spin"></i> Chargement...</td></tr>';
    
    try {
        const result = await apiRequest('/events');
        
        if (result.success) {
            eventsData = result.events || result.data || [];
            displayEvents();
        } else {
            tbody.innerHTML = `<tr><td colspan="6" class="loader">${result.message || 'Erreur de chargement'}</td></tr>`;
        }
    } catch (error) {
        console.error('Erreur:', error);
        tbody.innerHTML = '<tr><td colspan="6" class="loader">Erreur de chargement des données</td></tr>';
    }
}

function displayEvents() {
    const tbody = document.getElementById('eventsTableBody');
    if (!tbody) return;
    
    if (eventsData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="loader">Aucun événement trouvé</td></tr>';
        return;
    }
    
    tbody.innerHTML = eventsData.map(event => `
        <tr>
            <td>${formatDate(event.date)}</td>
            <td>${escapeHtml(event.name)}</td>
            <td>${escapeHtml(event.location)}</td>
            <td><span class="badge ${event.type === 'Compétition' ? 'badge-green' : 'badge-orange'}">${escapeHtml(event.type)}</span></td>
            <td>${escapeHtml(event.description || '-')}</td>
            <td>
                <button class="btn-action" onclick="editEvent(${event.id})"><i class="fas fa-pen"></i> Modifier</button>
                <button class="btn-action danger" onclick="deleteEvent(${event.id})"><i class="fas fa-trash"></i></button>
             </td>
        </tr>
    `).join('');
}

async function saveEvent() {
    const eventId = document.getElementById('eventId')?.value;
    const data = {
        name: document.getElementById('eventName').value,
        date: document.getElementById('eventDate').value,
        location: document.getElementById('eventLocation').value,
        type: document.getElementById('eventType').value,
        description: document.getElementById('eventDesc').value
    };
    
    if (!data.name || !data.date || !data.location) {
        showNotification('Veuillez remplir tous les champs obligatoires', 'error');
        return;
    }
    
    const url = eventId ? `/events/${eventId}` : '/events';
    const method = eventId ? 'PUT' : 'POST';
    
    try {
        const result = await apiRequest(url, method, data);
        if (result.success) {
            showNotification(eventId ? 'Événement modifié avec succès' : 'Événement ajouté avec succès');
            toggleEventForm();
            loadEvents();
        } else {
            showNotification(result.message || 'Erreur lors de l\'enregistrement', 'error');
        }
    } catch (error) {
        showNotification('Erreur lors de l\'enregistrement', 'error');
    }
}

async function deleteEvent(id) {
    if (confirm('Êtes-vous sûr de vouloir supprimer cet événement ?')) {
        try {
            const result = await apiRequest(`/events/${id}`, 'DELETE');
            if (result.success) {
                showNotification('Événement supprimé avec succès');
                loadEvents();
            } else {
                showNotification(result.message || 'Erreur lors de la suppression', 'error');
            }
        } catch (error) {
            showNotification('Erreur lors de la suppression', 'error');
        }
    }
}

async function editEvent(id) {
    try {
        const result = await apiRequest(`/events/${id}`);
        if (result.success) {
            const event = result.event || result.data;
            document.getElementById('modalTitle').textContent = 'Modifier l\'événement';
            document.getElementById('eventId').value = event.id;
            document.getElementById('eventName').value = event.name;
            document.getElementById('eventDate').value = event.date;
            document.getElementById('eventLocation').value = event.location;
            document.getElementById('eventType').value = event.type;
            document.getElementById('eventDesc').value = event.description || '';
            document.getElementById('eventModal').style.display = 'flex';
        }
    } catch (error) {
        showNotification('Erreur lors du chargement de l\'événement', 'error');
    }
}

function toggleEventForm() {
    const form = document.getElementById('formAddEvent');
    if (form) {
        form.classList.toggle('hidden');
        if (!form.classList.contains('hidden')) {
            document.getElementById('eventName').value = '';
            document.getElementById('eventDate').value = '';
            document.getElementById('eventLocation').value = '';
            document.getElementById('eventType').value = 'Compétition';
            document.getElementById('eventDesc').value = '';
            document.getElementById('eventId').value = '';
        }
    }
}

function closeEventModal() {
    document.getElementById('eventModal').style.display = 'none';
}

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
    loadEvents();
    
    const addBtn = document.getElementById('btnAddEvent');
    if (addBtn) addBtn.onclick = toggleEventForm;
    
    const saveBtn = document.getElementById('btnSaveEvent');
    if (saveBtn) saveBtn.onclick = saveEvent;
    
    const cancelBtn = document.getElementById('btnCancelEvent');
    if (cancelBtn) cancelBtn.onclick = toggleEventForm;
});