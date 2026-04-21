
let allClubs = [];
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

// Charger les secteurs (filtrés par saison si une saison est sélectionnée)
async function loadSecteurs(saisonId) {
    try {
        let url = '/api/admin/secteurs';
        if (saisonId) {
            url = `/api/admin/secteurs/saison/${saisonId}`;
        }
        const response = await fetch(url);
        const data = await response.json();
        if (data.success) {
            const select = document.getElementById('secteurSelect');
            const currentValue = select.value;
            select.innerHTML = '<option value="">Tous les secteurs</option>';
            data.secteurs.forEach(s => {
                select.innerHTML += `<option value="${s.id_secteur}">${s.nom_secteur}</option>`;
            });
            // Restaurer la valeur si elle existe encore dans la nouvelle liste
            if (currentValue) {
                const optionExists = Array.from(select.options).some(opt => opt.value === currentValue);
                if (optionExists) {
                    select.value = currentValue;
                } else {
                    select.value = '';
                }
            }
        }
    } catch (error) {
        console.error('Erreur chargement secteurs:', error);
    }
}

// Charger les clubs depuis la route /api/admin/clubs-saison avec les filtres
async function loadClubs() {
    const saisonValue = document.getElementById('saisonSelect').value;
    const secteurValue = document.getElementById('secteurSelect').value;

    currentSaison = saisonValue;
    currentSecteur = secteurValue;

    // Afficher le loader pendant le chargement
    const tbody = document.getElementById('clubsTableBody');
    if (tbody) {
        tbody.innerHTML = '<tr class="loader"><td colspan="8"><i class="fas fa-spinner"></i> Chargement des clubs...</td></tr>';
    }

    try {
        // Construire l'URL avec les paramètres de filtre
        const params = new URLSearchParams();
        if (saisonValue) params.append('saison', saisonValue);
        if (secteurValue) params.append('secteur', secteurValue);

        const url = '/api/admin/clubs-saison' + (params.toString() ? '?' + params.toString() : '');
        const response = await fetch(url);
        const data = await response.json();

        if (data.success) {
            allClubs = data.clubs || [];
        } else {
            console.error('Erreur chargement clubs:', data.message);
            allClubs = [];
        }
    } catch (error) {
        console.error('Erreur:', error);
        allClubs = [];
    }

    totalPages = Math.ceil(allClubs.length / itemsPerPage);
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
    const clubsToShow = allClubs.slice(startIndex, endIndex);

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
        const gradeValue = club.grade_name || '-';

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

    if (totalPages <= 1 && allClubs.length <= itemsPerPage) {
        paginationDiv.innerHTML = '';
        return;
    }

    let html = '<div class="pagination-controls">';
    html += `<button class="page-btn" onclick="changePage(1)" ${currentPage === 1 ? 'disabled' : ''}>&laquo;</button>`;
    html += `<button class="page-btn" onclick="changePage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>&lsaquo;</button>`;
    html += `<span class="page-info">Page ${currentPage} / ${totalPages}</span>`;
    html += `<span class="page-count">(${allClubs.length} clubs)</span>`;
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
        totalCountDiv.innerHTML = `<i class="fas fa-users"></i> Total : ${allClubs.length} club(s) ${filterText}`;
    }
}

function changePage(page) {
    currentPage = page;
    displayClubs();
    displayPagination();
}

async function onSaisonChange() {
    const saisonId = document.getElementById('saisonSelect').value;
    // Recharger les secteurs filtrés par la saison sélectionnée
    await loadSecteurs(saisonId || null);
    currentPage = 1;
    await loadClubs();
}

async function onSecteurChange() {
    currentPage = 1;
    await loadClubs();
}

async function resetFilters() {
    document.getElementById('saisonSelect').value = '';
    document.getElementById('secteurSelect').value = '';
    // Recharger tous les secteurs
    await loadSecteurs();
    currentPage = 1;
    await loadClubs();
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
    await loadClubs();

    const saisonSelect = document.getElementById('saisonSelect');
    const secteurSelect = document.getElementById('secteurSelect');

    if (saisonSelect) {
        saisonSelect.addEventListener('change', onSaisonChange);
    }
    if (secteurSelect) {
        secteurSelect.addEventListener('change', onSecteurChange);
    }
});

// Export Excel
function exportToExcel() {
    if (!allClubs || allClubs.length === 0) {
        alert("Aucune donnée à exporter.");
        return;
    }

    const saisonLabel = document.getElementById('saisonSelect').options[document.getElementById('saisonSelect').selectedIndex].text;
    const secteurLabel = document.getElementById('secteurSelect').options[document.getElementById('secteurSelect').selectedIndex].text;

    // Préparer les données pour l'export
    const dataToExport = allClubs.map((club, index) => ({
        'N°': index + 1,
        'Secteur': club.secteur || '-',
        'Nom du Club': club.nom_club || '-',
        'Identifiant': club.identif_club || '-',
        'Représentant': club.representant || '-',
        'Grade': club.grade || '-',
        'Contact': club.contact || '-',
        'Date Affiliation': formatDate(club.date_affiliation)
    }));

    // Créer un classeur Excel
    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.json_to_sheet(dataToExport);

    // Ajouter la feuille au classeur
    XLSX.utils.book_append_sheet(wb, ws, "Clubs par Saison");

    // Générer le fichier et déclencher le téléchargement
    const date = new Date().toISOString().split('T')[0];
    const fileName = `Clubs_${saisonLabel.replace(/\s+/g, '_')}_${secteurLabel.replace(/\s+/g, '_')}_${date}.xlsx`;
    XLSX.writeFile(wb, fileName);
}
