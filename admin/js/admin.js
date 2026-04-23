// ========================================
// ADMIN.JS - FI-ADEKASH
// Scripts unifiés pour l'espace administration
// ========================================

// Vérification de l'authentification
function checkAdminAuth() {
    const isLoggedIn = sessionStorage.getItem('admin_logged_in');
    if (!isLoggedIn && !window.location.pathname.includes('admin-login.html')) {
        window.location.href = 'admin-login.html';
        return false;
    }
    return true;
}

// Formatage des dates
function formatDate(dateString) {
    if (!dateString) return '';
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    } catch (e) {
        return dateString;
    }
}

function formatDateTime(dateString) {
    if (!dateString) return '';
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (e) {
        return dateString;
    }
}

// Échappement HTML
function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>]/g, function(m) {
        if (m === '&') return '&amp;';
        if (m === '<') return '&lt;';
        if (m === '>') return '&gt;';
        return m;
    });
}

// Notification toast
function showNotification(message, type = 'success') {
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: ${type === 'success' ? '#48bb78' : '#f56565'};
        color: white;
        padding: 12px 20px;
        border-radius: 12px;
        z-index: 10000;
        font-size: 0.85rem;
        animation: slideIn 0.3s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;
    toast.innerHTML = `<i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i> ${message}`;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Requête API générique
async function apiRequest(endpoint, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(`/api/admin${endpoint}`, options);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.message || 'Erreur serveur');
        }
        
        return result;
    } catch (error) {
        console.error('API Error:', error);
        showNotification(error.message || 'Erreur de connexion', 'error');
        throw error;
    }
}

// Fonction toggleSubmenu globale
window.toggleSubmenu = function(event) {
    event.preventDefault();
    event.stopPropagation();
    const parent = event.currentTarget.closest('.has-submenu');
    if (parent) {
        parent.classList.toggle('open');
    }
};

// Charger la sidebar et initialiser les événements
function loadSidebar() {
    const sidebarContainer = document.getElementById('sidebar-container');
    if (!sidebarContainer) return;
    
    fetch('sidebar.html')
        .then(response => response.text())
        .then(html => {
            sidebarContainer.innerHTML = html;
            
            // Initialiser la sidebar après injection
            initSidebarAfterLoad();
        })
        .catch(err => console.error('Erreur chargement sidebar:', err));
}

function initSidebarAfterLoad() {
    // Mettre à jour le nom de l'admin
    const adminLogin = sessionStorage.getItem('admin_login') || 'Admin';
    const adminNom = sessionStorage.getItem('admin_nom') || '';
    const adminPrenom = sessionStorage.getItem('admin_prenom') || '';
    
    const adminNameSpan = document.querySelector('.sidebar-logo small');
    if (adminNameSpan && (adminPrenom || adminNom)) {
        adminNameSpan.textContent = adminPrenom ? `${adminPrenom} ${adminNom}` : adminLogin;
    }
    
    // Charger le nombre de messages non lus
    async function loadUnreadCount() {
        try {
            const response = await fetch('/api/admin/messages/unread/count');
            const data = await response.json();
            if (data.success && data.count > 0) {
                const badge = document.getElementById('unreadBadge');
                if (badge) badge.textContent = data.count;
            }
        } catch (e) {
            console.error('Erreur chargement compteur messages:', e);
        }
    }
    loadUnreadCount();
    
    // Surligner la page active
    const currentPage = window.location.pathname.split('/').pop();
    
    // Menu principal
    document.querySelectorAll('.nav-main').forEach(link => {
        if (link.getAttribute('href') === currentPage) {
            link.classList.add('active');
        }
    });
    
    // Sous-menu
    let activeSubmenuFound = false;
    document.querySelectorAll('.submenu-link').forEach(link => {
        if (link.getAttribute('href') === currentPage) {
            link.classList.add('active');
            activeSubmenuFound = true;
        }
    });
    
    // Ouvrir le sous-menu Clubs si actif
    if (activeSubmenuFound && ['clubs.html', 'clubs-saison.html', 'clubs-new.html'].includes(currentPage)) {
        const clubsMenu = document.getElementById('clubsMenu');
        if (clubsMenu) clubsMenu.classList.add('open');
    }
    
    // Ouvrir le sous-menu Licenciés si actif
    if (activeSubmenuFound && ['licencies-club.html', 'licencies-new.html', 'licencies-edit.html', 'licencies-affilie.html'].includes(currentPage)) {
        const licenciesMenu = document.getElementById('licenciesMenu');
        if (licenciesMenu) licenciesMenu.classList.add('open');
    }

    // Ouvrir le sous-menu Statistiques si actif
    if (activeSubmenuFound && ['statistiques-liste.html', 'statistiques-carte.html'].includes(currentPage)) {
        const statsMenu = document.getElementById('statsMenu');
        if (statsMenu) statsMenu.classList.add('open');
    }
    
    // Déconnexion
    const logoutBtn = document.getElementById('btnDeconnexion');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async () => {
            try {
                await fetch('/api/admin/logout', { method: 'POST' });
            } catch (e) {
                console.error('Erreur déconnexion:', e);
            }
            sessionStorage.clear();
            window.location.href = 'admin-login.html';
        });
    }
}

// Initialisation générale
function initAdmin() {
    // Vérifier auth sauf sur la page login
    if (!window.location.pathname.includes('admin-login.html')) {
        checkAdminAuth();
    }
    
    // Charger la sidebar
    const sidebarContainer = document.getElementById('sidebar-container');
    if (sidebarContainer) {
        loadSidebar();
    }
}

// Démarrer au chargement
document.addEventListener('DOMContentLoaded', initAdmin);