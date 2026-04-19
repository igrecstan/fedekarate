// admin/js/dashboard.js - Tableau de bord

async function loadDashboardStats() {
    try {
        // Clubs
        const clubsRes = await fetch('/api/admin/clubs/count');
        const clubsData = await clubsRes.json();
        if (clubsData.success) {
            document.getElementById('clubsCount').textContent = clubsData.count || 0;
        }
    } catch(e) { console.error('Erreur clubs:', e); }
    
    try {
        // Licenciés
        const licRes = await fetch('/api/admin/licencies/count');
        const licData = await licRes.json();
        if (licData.success) {
            document.getElementById('licenciesCount').textContent = licData.count || 0;
        }
    } catch(e) { console.error('Erreur licenciés:', e); }
    
    try {
        // Événements
        const eventsRes = await fetch('/api/admin/events/count');
        const eventsData = await eventsRes.json();
        if (eventsData.success) {
            document.getElementById('eventsCount').textContent = eventsData.count || 0;
        }
    } catch(e) { console.error('Erreur événements:', e); }
    
    try {
        // Messages non lus
        const msgRes = await fetch('/api/admin/messages/unread/count');
        const msgData = await msgRes.json();
        if (msgData.success) {
            document.getElementById('messagesCount').textContent = msgData.count || 0;
        }
    } catch(e) { console.error('Erreur messages:', e); }
}

// Charger l'activité récente
async function loadRecentActivity() {
    const tbody = document.getElementById('recentActivity');
    if (!tbody) return;
    
    try {
        const response = await fetch('/api/admin/activities/recent?limit=5');
        const data = await response.json();
        
        if (data.success && data.activities) {
            tbody.innerHTML = data.activities.map(activity => `
                <tr>
                    <td>${activity.action || '-'}</td>
                    <td>${activity.detail || '-'}</td>
                    <td>${formatDate(activity.date)}</td>
                    <td><span class="badge badge-${activity.status === 'validé' ? 'green' : 'orange'}">${activity.status || '-'}</span></td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="4" class="loader">Aucune activité récente</td></tr>';
        }
    } catch(e) {
        console.error('Erreur chargement activités:', e);
        tbody.innerHTML = '<tr><td colspan="4" class="loader">Erreur de chargement</td></tr>';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadDashboardStats();
    loadRecentActivity();
});