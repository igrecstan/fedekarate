
let allClubs = [];
let filteredClubs = [];
let currentPage = 1;
let itemsPerPage = 20;
let totalPages = 1;
let currentSaison = '';
let currentSecteur = '';

// Vérifier authentification
if (!sessionStorage.getItem('admin_logged_in')) {
    window.location.href = 'admin-login.html';
}

// Afficher le nom de l'utilisateur
const adminNom = sessionStorage.getItem('admin_nom') || 'Administrateur';
const adminPrenom = sessionStorage.getItem('admin_prenom') || '';
const userNameSpan = document.getElementById('userName');
const userAvatar = document.getElementById('userAvatar');
if (userNameSpan) userNameSpan.textContent = `${adminPrenom} ${adminNom}`.trim() || 'Administrateur';
if (userAvatar) userAvatar.textContent = (adminNom.charAt(0) + adminPrenom.charAt(0)).toUpperCase() || 'AD';

// Charger les saisons (route spécifique pour les clubs)
async function loadSaisons() {
    try {
        const response = await fetch('/api/admin/saisons/clubs');
        const data = await response.json();
        if (data.success) {
            const select = document.getElementById('saisonSelect');
            select.innerHTML = '<option value="">Toutes les saisons</option>';
            data.saisons.forEach(s => {
                select.innerHTML += `<option value="${s.id_saison}">${s.libelle_saison}</option>`;
            });
        }
    } catch (error) {
        console.error('Erreur chargement saisons:', error);
    }
}

// Charger les secteurs
async function loadSecteurs() {
    try {
        const response = await fetch('/api/admin/secteurs');
        const data = await response.json();
        if (data.success) {
            const select = document.getElementById('secteurSelect');
            select.innerHTML = '<option value="">Tous les secteurs</option>';
            data.secteurs.forEach(s => {
                select.innerHTML += `<option value="${s.id_secteur}">${s.nom_secteur}</option>`;
            });
        }
    } catch (error) {
        console.error('Erreur chargement secteurs:', error);
    }
}

// Charger tous les clubs
async function loadAllClubs() {
    try {
        const response = await fetch('/api/admin/clubs/all');
        const data = await response.json();
        if (data.success) {
            allClubs = data.clubs || [];
            applyFilterAndDisplay();
        } else {
            console.error('Erreur chargement clubs:', data.message);
            allClubs = [];
        }
    } catch (error) {
        console.error('Erreur:', error);
        allClubs = [];
    }
}

// Appliquer les filtres
function applyFilterAndDisplay() {
    const saisonValue = document.getElementById('saisonSelect').value;
    const secteurValue = document.getElementById('secteurSelect').value;

    currentSaison = saisonValue;
    currentSecteur = secteurValue;

    let result = [...allClubs];

    // Filtre par saison
    if (currentSaison) {
        result = result.filter(club => {
            return club.id_saison && club.id_saison.toString() === currentSaison;
        });
    }

    // Filtre par secteur
    if (currentSecteur) {
        result = result.filter(club => {
            return club.List_sect && club.List_sect.toString() === currentSecteur;
        });
    }

    filteredClubs = result;

    // Trier par date d'inscription décroissante
    filteredClubs.sort((a, b) => {
        const dateA = a.created_At ? new Date(a.created_At) : new Date(0);
        const dateB = b.created_At ? new Date(b.created_At) : new Date(0);
        return dateB - dateA;
    });

    totalPages = Math.ceil(filteredClubs.length / itemsPerPage);
    if (currentPage > totalPages) currentPage = 1;
    if (totalPages === 0) totalPages = 1;

    displayClubs();
    displayPagination();
    updateTotalCount();
}

function formatDate(dateString) {
    if (!dateString) return '-';
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

function displayClubs() {
    const tbody = document.getElementById('clubsTableBody');
    if (!tbody) return;

    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const clubsToShow = filteredClubs.slice(startIndex, endIndex);

    if (clubsToShow.length === 0) {
        tbody.innerHTML = '<tr class="empty-row"><td colspan="8">Aucun club trouvé avec les filtres sélectionnés</td></tr>';
        return;
    }

    const startNumber = startIndex + 1;
    tbody.innerHTML = '';

    clubsToShow.forEach((club, index) => {
        const row = tbody.insertRow();
        const orderNumber = startNumber + index;
        const dateInscription = formatDate(club.created_At);
        const gradeValue = club.grade || '-';

        row.className = 'club-row';
        row.innerHTML = `
                    <td><span class="row-number">${orderNumber}</span></td>
                    <td><span class="cell-text">${escapeHtml(club.secteur || '-')}</span></td>
                    <td><span class="cell-text club-name">${escapeHtml(club.nom_club || '-')}</span></td>
                    <td><span class="cell-text">${escapeHtml(club.identif_club || '-')}</span></td>
                    <td><span class="cell-text">${escapeHtml(club.representant || '-')}</span></td>
                    <td><span class="badge-grade">${escapeHtml(gradeValue)}</span></td>
                    <td><span class="cell-text">${escapeHtml(club.contact || '-')}</span></td>
                    <td><span class="cell-text">${dateInscription}</span></td>
                `;
    });
}

function displayPagination() {
    const paginationDiv = document.getElementById('pagination');
    if (!paginationDiv) return;

    if (totalPages <= 1 && filteredClubs.length <= itemsPerPage) {
        paginationDiv.innerHTML = '';
        return;
    }

    let html = '<div class="pagination-controls">';
    html += `<button class="page-btn" onclick="changePage(1)" ${currentPage === 1 ? 'disabled' : ''}>&laquo;</button>`;
    html += `<button class="page-btn" onclick="changePage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>&lsaquo;</button>`;
    html += `<span class="page-info">Page ${currentPage} / ${totalPages}</span>`;
    html += `<span class="page-count">(${filteredClubs.length} clubs)</span>`;
    html += `<button class="page-btn" onclick="changePage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>&rsaquo;</button>`;
    html += `<button class="page-btn" onclick="changePage(${totalPages})" ${currentPage === totalPages ? 'disabled' : ''}>&raquo;</button>`;
    html += '</div>';

    paginationDiv.innerHTML = html;
}

function updateTotalCount() {
    const totalCountDiv = document.getElementById('totalCount');
    if (totalCountDiv) {
        let filterText = '';
        if (currentSaison && currentSecteur) {
            filterText = 'pour la saison et le secteur sélectionnés';
        } else if (currentSaison) {
            filterText = 'pour la saison sélectionnée';
        } else if (currentSecteur) {
            filterText = 'pour le secteur sélectionné';
        } else {
            filterText = 'toutes saisons et secteurs confondus';
        }
        totalCountDiv.innerHTML = `<i class="fas fa-users"></i> Total : ${filteredClubs.length} club(s) ${filterText}`;
    }
}

function changePage(page) {
    currentPage = page;
    displayClubs();
    displayPagination();
}

function onFilterChange() {
    currentPage = 1;
    applyFilterAndDisplay();
}

function resetFilters() {
    document.getElementById('saisonSelect').value = '';
    document.getElementById('secteurSelect').value = '';
    currentPage = 1;
    applyFilterAndDisplay();
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialisation
document.addEventListener('DOMContentLoaded', async () => {
    await loadSaisons();
    await loadSecteurs();
    await loadAllClubs();

    const saisonSelect = document.getElementById('saisonSelect');
    const secteurSelect = document.getElementById('secteurSelect');

    if (saisonSelect) {
        saisonSelect.addEventListener('change', onFilterChange);
    }
    if (secteurSelect) {
        secteurSelect.addEventListener('change', onFilterChange);
    }
});
