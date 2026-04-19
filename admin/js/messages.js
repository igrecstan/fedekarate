// admin/js/messages.js - Gestion des messages

let messagesData = [];

async function loadMessages() {
    const container = document.getElementById('messagesList');
    if (!container) return;
    
    container.innerHTML = '<div class="loader"><i class="fas fa-spinner fa-spin"></i> Chargement...</div>';
    
    try {
        const result = await apiRequest('/messages');
        
        if (result.success) {
            messagesData = result.messages || result.data || [];
            displayMessages();
        } else {
            container.innerHTML = `<div class="loader">${result.message || 'Erreur de chargement'}</div>`;
        }
    } catch (error) {
        console.error('Erreur:', error);
        container.innerHTML = '<div class="loader">Erreur de chargement des messages</div>';
    }
}

function displayMessages() {
    const container = document.getElementById('messagesList');
    if (!container) return;
    
    if (messagesData.length === 0) {
        container.innerHTML = '<div class="loader">Aucun message trouvé</div>';
        return;
    }
    
    container.innerHTML = messagesData.map(msg => {
        const initials = (msg.nom || msg.name || '?').split(' ').map(n => n[0]).join('').substring(0, 2);
        return `
            <div class="msg-item" style="opacity: ${msg.read ? '0.6' : '1'}">
                <div class="msg-avatar">${initials}</div>
                <div class="msg-body">
                    <div class="msg-name">
                        ${escapeHtml(msg.nom || msg.name)}
                        ${!msg.read ? '<span class="badge badge-orange" style="margin-left:6px;">Non lu</span>' : ''}
                    </div>
                    <div class="msg-email">${escapeHtml(msg.email)} · ${formatDate(msg.date)}</div>
                    <div class="msg-text">${escapeHtml(msg.message)}</div>
                    <div style="margin-top: 8px;">
                        ${!msg.read ? `<button class="btn-action" onclick="markAsRead(${msg.id})"><i class="fas fa-check"></i> Marquer comme lu</button>` : ''}
                        <button class="btn-action danger" onclick="deleteMessage(${msg.id})"><i class="fas fa-trash"></i> Supprimer</button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

async function markAsRead(id) {
    try {
        const result = await apiRequest(`/messages/${id}/read`, 'PUT');
        if (result.success) {
            showNotification('Message marqué comme lu');
            loadMessages();
            
            // Mettre à jour le compteur dans la sidebar
            const badge = document.getElementById('unreadBadge');
            if (badge) {
                const countRes = await fetch('/api/admin/messages/unread/count');
                const countData = await countRes.json();
                if (countData.success && countData.count > 0) {
                    badge.textContent = countData.count;
                } else {
                    badge.textContent = '0';
                }
            }
        }
    } catch (error) {
        showNotification('Erreur lors du marquage', 'error');
    }
}

async function deleteMessage(id) {
    if (confirm('Êtes-vous sûr de vouloir supprimer ce message ?')) {
        try {
            const result = await apiRequest(`/messages/${id}`, 'DELETE');
            if (result.success) {
                showNotification('Message supprimé avec succès');
                loadMessages();
            } else {
                showNotification(result.message || 'Erreur lors de la suppression', 'error');
            }
        } catch (error) {
            showNotification('Erreur lors de la suppression', 'error');
        }
    }
}

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
    loadMessages();
});