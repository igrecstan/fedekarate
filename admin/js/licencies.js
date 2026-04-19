// admin/js/licencies.js - Gestion des licenciés

// Variables globales
let allLicencies = [];
let filteredLicencies = [];
let currentPage = 1;
let itemsPerPage = 20;
let totalPages = 1;
let currentSecteur = '';
let currentClub = '';
let currentSaison = '';
let currentStatut = '';
let currentSearchTerm = '';
let deleteId = null;

// Données de référence
let secteursList = [];
let clubsList = [];
let saisonsList = [];

// Fonction pour vérifier l'authentification
function checkLicenciesAuth() {
    const isLoggedIn = sessionStorage.getItem('admin_logged_in');
    if (!isLoggedIn) {
        window.location.href = 'admin-login.html';
        return false;
    }
    return true;
}

// Afficher le nom de l'utilisateur
function updateUserDisplay() {
    const adminNom = sessionStorage.getItem('admin_nom') || 'Administrateur';
    const adminPrenom = sessionStorage.getItem('admin_prenom') || '';
    const userNameSpan = document.getElementById('userName');
    const userAvatar = document.getElementById('userAvatar');
    if (userNameSpan) userNameSpan.textContent = `${adminPrenom} ${adminNom}`.trim() || 'Administrateur';
    if (userAvatar) userAvatar.textContent = (adminNom.charAt(0) + adminPrenom.charAt(0)).toUpperCase() || 'AD';
}

function showLoading(show) {
    let overlay = document.getElementById('loadingOverlay');
    if (show) {
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'loadingOverlay';
            overlay.className = 'loading-overlay';
            overlay.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-pulse"></i> Chargement en cours...</div>';
            document.body.appendChild(overlay);
        }
        overlay.style.display = 'flex';
    } else if (overlay) {
        overlay.style.display = 'none';
    }
}

function showNotification(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;
    toast.innerHTML = `<i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i> ${message}`;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Fonction pour extraire nom et prénom depuis nom_prenoms
function extractNomPrenom(nomPrenoms) {
    if (!nomPrenoms) return { nom: '', prenom: '' };
    const parts = nomPrenoms.trim().split(' ');
    if (parts.length === 1) {
        return { nom: parts[0], prenom: '' };
    }
    return { nom: parts[0], prenom: parts.slice(1).join(' ') };
}

// Charger les secteurs
async function loadSecteurs() {
    try {
        const response = await fetch('/api/admin/secteurs');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        if (data.success) {
            secteursList = data.secteurs || [];
            const select = document.getElementById('secteurSelect');
            if (select) {
                select.innerHTML = '<option value="">Tous les secteurs</option>';
                secteursList.forEach(s => {
                    select.innerHTML += `<option value="${s.id_secteur}">${escapeHtml(s.nom_secteur)}</option>`;
                });
            }
        }
    } catch (error) {
        console.error('Erreur chargement secteurs:', error);
        showNotification('Erreur chargement des secteurs', 'error');
    }
}

// Charger les clubs
async function loadClubs() {
    try {
        const response = await fetch('/api/admin/clubs/all');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        if (data.success) {
            clubsList = data.clubs || [];
            updateClubSelect();
        }
    } catch (error) {
        console.error('Erreur chargement clubs:', error);
        clubsList = [];
        showNotification('Erreur chargement des clubs', 'warning');
    }
}

// Mettre à jour la liste des clubs en fonction du secteur sélectionné
function updateClubSelect() {
    const secteurValue = document.getElementById('secteurSelect')?.value;
    const select = document.getElementById('clubSelect');
    if (!select) return;

    let filteredClubs = clubsList;
    if (secteurValue) {
        filteredClubs = clubsList.filter(club => club.List_sect && club.List_sect.toString() === secteurValue);
    }

    select.innerHTML = '<option value="">Tous les clubs</option>';
    filteredClubs.forEach(club => {
        select.innerHTML += `<option value="${club.id_club}">${escapeHtml(club.nom_club)} (${club.identif_club || ''})</option>`;
    });
}

// Charger les saisons pour les licenciés
async function loadSaisons() {
    try {
        const response = await fetch('/api/admin/saisons/licencies');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        if (data.success && data.saisons) {
            saisonsList = data.saisons;
            console.log('Saisons chargées pour licenciés:', saisonsList);

            const select = document.getElementById('saisonSelect');
            if (select) {
                select.innerHTML = '<option value="">Toutes les saisons</option>';
                saisonsList.forEach(s => {
                    select.innerHTML += `<option value="${s.id_saison}">${escapeHtml(s.libelle_saison)}</option>`;
                });
            }
        } else {
            console.warn('Aucune saison trouvée pour licenciés');
        }
    } catch (error) {
        console.error('Erreur chargement saisons:', error);
        showNotification('Erreur chargement des saisons', 'warning');
    }
}

// Charger tous les licenciés
async function loadAllLicencies() {
    showLoading(true);

    try {
        const response = await fetch('/api/admin/licencies/all');

        if (response.ok) {
            const data = await response.json();
            if (data.success && data.licencies) {
                // Transformer les données pour compatibilité (extraire nom/prénom)
                allLicencies = data.licencies.map(l => {
                    const { nom, prenom } = extractNomPrenom(l.nom_prenoms);
                    return {
                        ...l,
                        nom: nom,
                        prenom: prenom,
                        // S'assurer que id_saison est présent
                        id_saison: l.id_saison || (l.saisons && l.saisons.length > 0 ? l.saisons[0].id_saison : null)
                    };
                });
                console.log(`Chargement réussi: ${allLicencies.length} licenciés`);
                console.log('Premier licencié (avec saison):', allLicencies[0]);
                showLoading(false);
                applyFilterAndDisplay();
                return;
            }
        }

        throw new Error('Aucun endpoint accessible');

    } catch (error) {
        console.error('Erreur chargement licenciés:', error);
        allLicencies = [];
        showLoading(false);

        const tbody = document.getElementById('licenciesTableBody');
        if (tbody) {
            tbody.innerHTML = '<tr class="error-row"><td colspan="7"><i class="fas fa-exclamation-triangle"></i> Impossible de charger les licenciés.<br><button class="btn-primary" style="margin-top:10px" onclick="location.reload()"><i class="fas fa-sync-alt"></i> Réessayer</button><\/td><\/tr>';
        }
        showNotification('Erreur de connexion au serveur', 'error');
    }
}

// Appliquer les filtres (déclenchée par le bouton Appliquer)
function applyFilters() {
    currentSecteur = document.getElementById('secteurSelect')?.value || '';
    currentClub = document.getElementById('clubSelect')?.value || '';
    currentSaison = document.getElementById('saisonSelect')?.value || '';
    currentStatut = document.getElementById('statutSelect')?.value || '';
    currentPage = 1;
    console.log('Filtres appliqués:', { currentSecteur, currentClub, currentSaison, currentStatut });
    applyFilterAndDisplay();
}

// Appliquer tous les filtres
function applyFilterAndDisplay() {
    let result = [...allLicencies];

    if (currentSecteur) {
        result = result.filter(licencie => licencie.secteur && licencie.secteur.toString() === currentSecteur);
    }

    if (currentClub) {
        result = result.filter(licencie => licencie.id_club && licencie.id_club.toString() === currentClub);
    }

    if (currentSaison) {
        result = result.filter(licencie => licencie.id_saison && licencie.id_saison.toString() === currentSaison);
        console.log(`Filtre saison ${currentSaison}: ${result.length} licenciés`);
    }

    if (currentStatut) {
        result = result.filter(licencie => licencie.statut === currentStatut);
    }

    if (currentSearchTerm) {
        const searchLower = currentSearchTerm.toLowerCase();
        result = result.filter(licencie => {
            const fullName = `${licencie.nom || ''} ${licencie.prenom || ''}`.toLowerCase();
            return fullName.includes(searchLower) ||
                (licencie.num_licence && licencie.num_licence.toLowerCase().includes(searchLower));
        });
    }

    filteredLicencies = result;

    filteredLicencies.sort((a, b) => {
        const dateA = a.created_At ? new Date(a.created_At) : new Date(0);
        const dateB = b.created_At ? new Date(b.created_At) : new Date(0);
        return dateB - dateA;
    });

    totalPages = Math.ceil(filteredLicencies.length / itemsPerPage);
    if (currentPage > totalPages) currentPage = 1;
    if (totalPages === 0) totalPages = 1;

    displayLicencies();
    displayPagination();
    updateTotalCount();
}

function displayLicencies() {
    const tbody = document.getElementById('licenciesTableBody');
    if (!tbody) return;

    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const licenciesToShow = filteredLicencies.slice(startIndex, endIndex);

    if (licenciesToShow.length === 0) {
        tbody.innerHTML = '<tr class="empty-row"><td colspan="7">Aucun licencié trouvé<\/td><\/tr>';
        return;
    }

    const startNumber = startIndex + 1;
    tbody.innerHTML = '';

    licenciesToShow.forEach((licencie, index) => {
        const row = tbody.insertRow();
        const orderNumber = startNumber + index;

        let statutClass = '';
        let statutText = '';
        switch (licencie.statut) {
            case 'actif':
                statutClass = 'badge-actif';
                statutText = 'Actif';
                break;
            case 'inactif':
                statutClass = 'badge-inactif';
                statutText = 'Inactif';
                break;
            default:
                statutClass = 'badge-en-attente';
                statutText = 'En attente';
        }

        // Construire le nom complet
        const fullName = `${licencie.nom || ''} ${licencie.prenom || ''}`.trim() || '-';
        // Afficher le grade
        const gradeDisplay = licencie.grade || '-';
        // Numéro de licence
        const numLicence = licencie.num_licence || '-';
        // Contact
        const contact = licencie.contact || '-';

        row.className = 'licencie-row';
        row.innerHTML = `
            <td><span class="row-number">${orderNumber}</span></td>
            <td><span class="cell-text"><strong>${escapeHtml(numLicence)}</strong></span></td>
            <td><span class="cell-text licencie-name">${escapeHtml(fullName)}</span></td>
            <td><span class="cell-text">${escapeHtml(gradeDisplay)}</span></td>
            <td><span class="cell-text">${escapeHtml(contact)}</span></td>
            <td><span class="badge-statut ${statutClass}">${statutText}</span></td>
            <td>
                <div class="action-buttons">
                    <button class="action-btn edit" onclick="editLicencie(${licencie.id_licencie})"><i class="fas fa-edit"></i></button>
                    <button class="action-btn delete" onclick="confirmDelete(${licencie.id_licencie}, '${escapeHtml(fullName.replace(/'/g, "\\'"))}')"><i class="fas fa-trash-alt"></i></button>
                </div>
            </td>
        `;
    });
}

function displayPagination() {
    const paginationDiv = document.getElementById('pagination');
    if (!paginationDiv) return;
    if (totalPages <= 1 && filteredLicencies.length <= itemsPerPage) {
        paginationDiv.innerHTML = '';
        return;
    }
    let html = '<div class="pagination-controls">';
    html += `<button class="page-btn" onclick="changePage(1)" ${currentPage === 1 ? 'disabled' : ''}>&laquo;</button>`;
    html += `<button class="page-btn" onclick="changePage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>&lsaquo;</button>`;
    html += `<span class="page-info">Page ${currentPage} / ${totalPages}</span>`;
    html += `<span class="page-count">(${filteredLicencies.length} licenciés)</span>`;
    html += `<button class="page-btn" onclick="changePage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>&rsaquo;</button>`;
    html += `<button class="page-btn" onclick="changePage(${totalPages})" ${currentPage === totalPages ? 'disabled' : ''}>&raquo;</button>`;
    html += '</div>';
    paginationDiv.innerHTML = html;
}

function updateTotalCount() {
    const totalCountDiv = document.getElementById('totalCount');
    if (totalCountDiv) {
        totalCountDiv.innerHTML = `<i class="fas fa-users"></i> Total : ${filteredLicencies.length} licencié(s)`;
    }
}

function changePage(page) {
    currentPage = page;
    displayLicencies();
    displayPagination();
}

function resetFilters() {
    const secteurSelect = document.getElementById('secteurSelect');
    const clubSelect = document.getElementById('clubSelect');
    const saisonSelect = document.getElementById('saisonSelect');
    const statutSelect = document.getElementById('statutSelect');
    const searchInput = document.getElementById('searchInput');

    if (secteurSelect) secteurSelect.value = '';
    if (clubSelect) clubSelect.value = '';
    if (saisonSelect) saisonSelect.value = '';
    if (statutSelect) statutSelect.value = '';
    if (searchInput) searchInput.value = '';

    currentSecteur = currentClub = currentSaison = currentStatut = currentSearchTerm = '';
    currentPage = 1;
    updateClubSelect();
    applyFilterAndDisplay();
}

function handleSearch(e) {
    if (e.key === 'Enter') searchLicencies();
}

function searchLicencies() {
    currentSearchTerm = document.getElementById('searchInput')?.value || '';
    currentPage = 1;
    applyFilterAndDisplay();
}

function editLicencie(id) {
    window.location.href = `licencies-edit.html?id=${id}`;
}

function confirmDelete(id, name) {
    deleteId = id;
    const deleteMessage = document.getElementById('deleteMessage');
    if (deleteMessage) {
        deleteMessage.innerHTML = `<i class="fas fa-question-circle"></i> Supprimer "${name}" ?`;
    }
    const modal = document.getElementById('deleteConfirmModal');
    if (modal) modal.style.display = 'block';
}

function closeDeleteModal() {
    const modal = document.getElementById('deleteConfirmModal');
    if (modal) modal.style.display = 'none';
    deleteId = null;
}

async function deleteLicencie() {
    if (!deleteId) return;

    showLoading(true);
    try {
        const response = await fetch(`/api/admin/licencies/${deleteId}`, {
            method: 'DELETE'
        });
        const data = await response.json();
        if (data.success) {
            showNotification('Licencié supprimé avec succès', 'success');
            closeDeleteModal();
            await loadAllLicencies();
        } else {
            showNotification('Erreur: ' + (data.message || 'Suppression impossible'), 'error');
        }
    } catch (error) {
        console.error('Erreur suppression:', error);
        showNotification('Erreur lors de la suppression', 'error');
    } finally {
        showLoading(false);
    }
}

// Initialisation
document.addEventListener('DOMContentLoaded', async () => {
    setTimeout(async () => {
        if (!checkLicenciesAuth()) return;

        updateUserDisplay();

        await loadSecteurs();
        await loadClubs();
        await loadSaisons();  // Charger les saisons
        await loadAllLicencies();

        const secteurSelect = document.getElementById('secteurSelect');
        const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');

        if (secteurSelect) {
            secteurSelect.addEventListener('change', () => updateClubSelect());
        }
        if (confirmDeleteBtn) {
            confirmDeleteBtn.addEventListener('click', deleteLicencie);
        }

        window.addEventListener('click', (e) => {
            const modal = document.getElementById('deleteConfirmModal');
            if (e.target === modal) closeDeleteModal();
        });
    }, 100);
});