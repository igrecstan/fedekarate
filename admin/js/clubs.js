// admin/js/clubs.js - Gestion des clubs avec filtres style Excel

let allClubs = []; // Tous les clubs (sans pagination)
let filteredClubs = []; // Clubs après filtrage
let currentPage = 1;
let currentSearch = '';
let itemsPerPage = 20;
let totalPages = 1;
let clubToDelete = null;
let secteursList = [];
let gradesList = [];

// Filtres par colonne
let columnFilters = {
    numero: '',
    secteur: '',
    nom: '',
    numClub: '',
    representant: '',
    contact: '',
    statut: ''
};

// Colonne active pour le filtre
let activeFilterColumn = null;
let filterOptions = [];
let tempFilterValue = '';

// Valeurs uniques pour chaque colonne
let uniqueValues = {
    secteur: [],
    representant: [],
    statut: ['actif', 'inactif']
};

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

// Charger les secteurs
async function loadSecteurs() {
    try {
        const response = await fetch('/api/admin/secteurs');
        const data = await response.json();
        if (data.success) {
            secteursList = data.secteurs;
            const select = document.getElementById('secteur');
            if (select) {
                select.innerHTML = '<option value="">Sélectionner un secteur</option>';
                secteursList.forEach(s => {
                    select.innerHTML += `<option value="${s.id_secteur}">${s.nom_secteur}</option>`;
                });
            }
        }
    } catch (e) {
        console.error('Erreur chargement secteurs:', e);
    }
}

// Charger les grades
async function loadGrades() {
    try {
        const response = await fetch('/api/admin/grades');
        const data = await response.json();
        if (data.success) {
            gradesList = data.grades;
            const select = document.getElementById('grade');
            if (select) {
                select.innerHTML = '<option value="">Sélectionner un grade</option>';
                gradesList.forEach(g => {
                    select.innerHTML += `<option value="${g.id_grade}">${g.designation}</option>`;
                });
            }
        }
    } catch (e) {
        console.error('Erreur chargement grades:', e);
    }
}

// Charger TOUS les clubs (sans pagination pour le filtrage)
async function loadAllClubs() {
    try {
        const response = await fetch('/api/admin/clubs/all');
        const data = await response.json();
        
        if (data.success) {
            allClubs = data.clubs || [];
            // Extraire les valeurs uniques pour les filtres
            extractUniqueValues(allClubs);
            // Appliquer les filtres
            applyFiltersAndDisplay();
        } else {
            console.error('Erreur chargement clubs:', data.message);
            allClubs = [];
        }
    } catch (error) {
        console.error('Erreur:', error);
        allClubs = [];
    }
}

// Extraire les valeurs uniques pour chaque colonne
function extractUniqueValues(clubs) {
    const secteursSet = new Set();
    const representantsSet = new Set();
    const nomsSet = new Set();
    const numClubsSet = new Set();
    const contactsSet = new Set();
    
    clubs.forEach(club => {
        if (club.secteur && club.secteur.trim()) {
            secteursSet.add(club.secteur);
        }
        if (club.representant && club.representant.trim()) {
            representantsSet.add(club.representant);
        }
        if (club.nom_club && club.nom_club.trim()) {
            nomsSet.add(club.nom_club);
        }
        if (club.identif_club && club.identif_club.trim()) {
            numClubsSet.add(club.identif_club);
        }
        if (club.contact && club.contact.trim()) {
            contactsSet.add(club.contact);
        }
    });
    
    uniqueValues.secteur = Array.from(secteursSet).sort();
    uniqueValues.representant = Array.from(representantsSet).sort();
    uniqueValues.nom = Array.from(nomsSet).sort();
    uniqueValues.numClub = Array.from(numClubsSet).sort();
    uniqueValues.contact = Array.from(contactsSet).sort();
}

// Appliquer tous les filtres
function applyFiltersAndDisplay() {
    // Appliquer les filtres de colonne
    let result = [...allClubs];
    
// Filtre secteur
if (columnFilters.secteur) {
    result = result.filter(club => club.secteur === columnFilters.secteur);
}

// Filtre statut
if (columnFilters.statut) {
    result = result.filter(club => {
        const clubStatut = club.statut && club.statut.toLowerCase() === 'actif' ? 'actif' : 'inactif';
        return clubStatut === columnFilters.statut.toLowerCase();
    });
}
    
    // Filtre nom
    if (columnFilters.nom) {
        result = result.filter(club => club.nom_club && club.nom_club.toLowerCase().includes(columnFilters.nom.toLowerCase()));
    }
    
    // Filtre numClub
    if (columnFilters.numClub) {
        result = result.filter(club => club.identif_club && club.identif_club.toLowerCase().includes(columnFilters.numClub.toLowerCase()));
    }
    
    // Filtre représentant
    if (columnFilters.representant) {
        result = result.filter(club => club.representant === columnFilters.representant);
    }
    
    // Filtre contact
    if (columnFilters.contact) {
        result = result.filter(club => club.contact && club.contact.toLowerCase().includes(columnFilters.contact.toLowerCase()));
    }
    
    // Filtre recherche globale
    if (currentSearch) {
        const searchLower = currentSearch.toLowerCase();
        result = result.filter(club => 
            (club.nom_club && club.nom_club.toLowerCase().includes(searchLower)) ||
            (club.representant && club.representant.toLowerCase().includes(searchLower)) ||
            (club.contact && club.contact.toLowerCase().includes(searchLower)) ||
            (club.identif_club && club.identif_club.toLowerCase().includes(searchLower)) ||
            (club.secteur && club.secteur.toLowerCase().includes(searchLower))
        );
    }
    
    filteredClubs = result;
    
    // Recalculer la pagination
    totalPages = Math.ceil(filteredClubs.length / itemsPerPage);
    if (currentPage > totalPages) currentPage = 1;
    if (totalPages === 0) totalPages = 1;
    
    // Afficher les clubs paginés
    displayClubs();
    displayPagination();
    updateFilterIndicators();
    
    // Mettre à jour les options des filtres déroulants
    updateFilterDropdowns();
}

// Mettre à jour les listes déroulantes des filtres
function updateFilterDropdowns() {
    // Les valeurs uniques sont déjà extraites de allClubs
    // On met à jour les options du menu au moment de l'ouverture
}

// Afficher le menu de filtre
function showFilterMenu(event, column) {
    event.stopPropagation();
    activeFilterColumn = column;
    tempFilterValue = columnFilters[column] || '';
    
    const filterMenu = document.getElementById('filterMenu');
    const filterMenuTitle = document.getElementById('filterMenuTitle');
    const filterSearchInput = document.getElementById('filterSearchInput');
    
    // Titre du menu
    const columnNames = {
        numero: 'N°',
        secteur: 'Secteur',
        nom: 'Nom du Club',
        numClub: 'Numéro Club',
        representant: 'Représentant',
        contact: 'Contact',
        statut: 'Statut'
    };
    filterMenuTitle.textContent = `Filtrer - ${columnNames[column]}`;
    
    // Générer les options basées sur les données de tous les clubs
    let options = [];
    
  if (column === 'statut') {
    options = ['actif', 'inactif'];
} else if (column === 'secteur') {
        options = uniqueValues.secteur;
    } else if (column === 'representant') {
        options = uniqueValues.representant;
    } else if (column === 'nom') {
        options = uniqueValues.nom;
    } else if (column === 'numClub') {
        options = uniqueValues.numClub;
    } else if (column === 'contact') {
        options = uniqueValues.contact;
    }
    
    filterOptions = options;
    
    // Remplir les options
    const filterOptionsDiv = document.getElementById('filterOptions');
    filterOptionsDiv.innerHTML = '';
    
    // Option "Tous"
    const allOption = document.createElement('label');
    allOption.className = 'filter-option';
    allOption.innerHTML = `
        <input type="radio" name="filterValue" value="" ${tempFilterValue === '' ? 'checked' : ''}>
        <span>Tous (${allClubs.length})</span>
    `;
    filterOptionsDiv.appendChild(allOption);
    
    // Ajouter une barre de séparation
    const separator = document.createElement('div');
    separator.className = 'filter-separator';
    filterOptionsDiv.appendChild(separator);
    
    // Ajouter les options
    options.forEach(option => {
        // Compter le nombre d'occurrences
        const count = allClubs.filter(club => {
            if (column === 'statut') {
                const clubStatut = club.statut === 1 ? 'Actif' : 'Inactif';
                return clubStatut === option;
            } else if (column === 'secteur') {
                return club.secteur === option;
            } else if (column === 'representant') {
                return club.representant === option;
            } else if (column === 'nom') {
                return club.nom_club === option;
            } else if (column === 'numClub') {
                return club.identif_club === option;
            } else if (column === 'contact') {
                return club.contact === option;
            }
            return false;
        }).length;
        
        const label = document.createElement('label');
        label.className = 'filter-option';
        label.innerHTML = `
            <input type="radio" name="filterValue" value="${escapeHtml(option)}" ${tempFilterValue === option ? 'checked' : ''}>
            <span>${escapeHtml(option)} <span style="color:#94a3b8; font-size:10px;">(${count})</span></span>
        `;
        filterOptionsDiv.appendChild(label);
    });
    
    // Fonction de recherche
    filterSearchInput.value = '';
    filterSearchInput.oninput = function() {
        const searchTerm = this.value.toLowerCase();
        const labels = filterOptionsDiv.querySelectorAll('.filter-option');
        labels.forEach(label => {
            const text = label.querySelector('span').textContent.toLowerCase();
            if (text.includes(searchTerm) || label.querySelector('input').value === '') {
                label.style.display = 'flex';
            } else {
                label.style.display = 'none';
            }
        });
    };
    
    // Positionner le menu
    const target = event.target.closest('th');
    const rect = target.getBoundingClientRect();
    
    filterMenu.style.display = 'block';
    filterMenu.style.position = 'fixed';
    filterMenu.style.top = `${rect.bottom + window.scrollY}px`;
    filterMenu.style.left = `${rect.left + window.scrollX}px`;
    filterMenu.style.minWidth = `${rect.width}px`;
    
    // Fermer le menu si on clique ailleurs
    setTimeout(() => {
        document.addEventListener('click', handleClickOutside);
    }, 100);
}

// Gérer le clic à l'extérieur
function handleClickOutside(event) {
    const filterMenu = document.getElementById('filterMenu');
    if (!filterMenu.contains(event.target) && !event.target.closest('.filter-icon')) {
        hideFilterMenu();
        document.removeEventListener('click', handleClickOutside);
    }
}

// Cacher le menu de filtre
function hideFilterMenu() {
    const filterMenu = document.getElementById('filterMenu');
    filterMenu.style.display = 'none';
    activeFilterColumn = null;
}

// Effacer le filtre actuel
function clearCurrentFilter() {
    if (activeFilterColumn) {
        columnFilters[activeFilterColumn] = '';
        tempFilterValue = '';
        
        // Mettre à jour le radio bouton "Tous"
        const radioTous = document.querySelector('#filterOptions input[value=""]');
        if (radioTous) radioTous.checked = true;
        
        applyFilter();
    }
}

// Appliquer le filtre
function applyFilter() {
    if (activeFilterColumn) {
        const selectedRadio = document.querySelector('#filterOptions input[name="filterValue"]:checked');
        if (selectedRadio) {
            columnFilters[activeFilterColumn] = selectedRadio.value;
        }
        currentPage = 1;
        applyFiltersAndDisplay();
    }
    hideFilterMenu();
}

// Mettre à jour l'indicateur de filtre actif
function updateFilterIndicators() {
    const headers = document.querySelectorAll('#headerRow th');
    const columns = ['numero', 'secteur', 'nom', 'numClub', 'representant', 'contact', 'statut'];
    
    headers.forEach((header, index) => {
        if (index < columns.length) {
            const filterIcon = header.querySelector('.filter-icon');
            if (filterIcon) {
                if (columnFilters[columns[index]]) {
                    filterIcon.classList.add('active');
                } else {
                    filterIcon.classList.remove('active');
                }
            }
        }
    });
}

// Afficher les clubs (version paginée)
function displayClubs() {
    const tbody = document.getElementById('clubsTableBody');
    if (!tbody) return;

    // Calculer les clubs à afficher pour la page courante
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const clubsToShow = filteredClubs.slice(startIndex, endIndex);

    if (clubsToShow.length === 0 && filteredClubs.length > 0) {
        // Ajuster la page si nécessaire
        currentPage = Math.ceil(filteredClubs.length / itemsPerPage);
        displayClubs();
        return;
    }

    tbody.innerHTML = '';

    if (clubsToShow.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 30px;">Aucun club trouvé<\/td><\/tr>';
        return;
    }

    const startNumber = startIndex + 1;
    
    clubsToShow.forEach((club, index) => {
        const row = tbody.insertRow();
        const orderNumber = startNumber + index;
        row.className = 'club-row';
        row.innerHTML = `
            <td><span class="row-number">${orderNumber}</span></td>
            <td><span class="cell-text">${escapeHtml(club.secteur || '-')}</span></td>
            <td><span class="cell-text club-name">${escapeHtml(club.nom_club || '-')}</span></td>
            <td><span class="cell-text">${escapeHtml(club.identif_club || '-')}</span></td>
            <td><span class="cell-text">${escapeHtml(club.representant || '-')}</span></td>
            <td><span class="cell-text">${escapeHtml(club.contact || '-')}</span></td>
            <td><span class="badge-sm ${club.statut === 'actif' ? 'badge-active' : 'badge-inactive'}">${club.statut === 'actif' ? 'Actif' : 'Inactif'}</span></td>
            <td class="actions-cell">
                <div class="action-buttons">
                    <button class="action-btn edit-btn-sm" onclick="editClub(${club.id_club})" title="Modifier">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="action-btn delete-btn-sm" onclick="confirmDeleteClub(${club.id_club}, '${escapeHtml(club.nom_club)}')" title="Supprimer">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </div>
            </td>
        `;
    });
}

// Pagination
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

function changePage(page) {
    currentPage = page;
    displayClubs();
    displayPagination();
}

function searchClubs() {
    currentSearch = document.getElementById('searchInput').value;
    currentPage = 1;
    applyFiltersAndDisplay();
}

// Réinitialiser tous les filtres
function resetFilters() {
    columnFilters = {
        numero: '',
        secteur: '',
        nom: '',
        numClub: '',
        representant: '',
        contact: '',
        statut: ''
    };
    currentSearch = '';
    document.getElementById('searchInput').value = '';
    currentPage = 1;
    applyFiltersAndDisplay();
}

// Ouvrir modal d'ajout
function openAddModal() {
    document.getElementById('modalTitle').textContent = 'Ajouter un Club';
    document.getElementById('clubForm').reset();
    document.getElementById('clubId').value = '';
    document.getElementById('identifClub').value = '';
    document.getElementById('clubModal').style.display = 'flex';
}

// Éditer un club
async function editClub(id) {
    try {
        const response = await fetch(`/api/admin/clubs/${id}`);
        const data = await response.json();

        if (data.success) {
            const club = data.club;
            document.getElementById('modalTitle').textContent = 'Modifier le Club';
            document.getElementById('clubId').value = club.id_club;
            document.getElementById('nomClub').value = club.nom_club || '';
            document.getElementById('representant').value = club.representant || '';
            document.getElementById('contact').value = club.contact || '';
            document.getElementById('whatsapp').value = club.whatsapp || '';
            document.getElementById('email').value = club.email || '';
            document.getElementById('numDeclaration').value = club.Num_declaration || '';
            document.getElementById('identifClub').value = club.identif_club || '';

            if (club.List_sect) {
                document.getElementById('secteur').value = club.List_sect;
            }
            if (club.grade) {
                document.getElementById('grade').value = club.grade;
            }

            document.getElementById('clubModal').style.display = 'flex';
        } else {
            alert('Erreur lors du chargement du club');
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('Erreur lors du chargement du club');
    }
}



// Sauvegarder un club
async function saveClub() {
    const id = document.getElementById('clubId').value;
    const nomClub = document.getElementById('nomClub').value.trim();

    if (!nomClub) {
        alert('Le nom du club est obligatoire');
        return;
    }

    let identifiant = document.getElementById('identifClub').value;
    if (!identifiant) {
        identifiant = 'CLUB' + Date.now().toString().slice(-6);
        document.getElementById('identifClub').value = identifiant;
    }

    const clubData = {
        identif_club: identifiant,
        nom_club: nomClub,
        representant: document.getElementById('representant').value.trim(),
        contact: document.getElementById('contact').value.trim(),
        whatsapp: document.getElementById('whatsapp').value.trim(),
        email: document.getElementById('email').value.trim(),
        List_sect: document.getElementById('secteur').value || null,
        grade: document.getElementById('grade').value || null,
        Num_declaration: document.getElementById('numDeclaration').value.trim()
    };

    try {
        let url = '/api/admin/clubs';
        let method = 'POST';

        if (id) {
            url = `/api/admin/clubs/${id}`;
            method = 'PUT';
        }

        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(clubData)
        });

        const data = await response.json();

        if (data.success) {
            alert(id ? 'Club modifié avec succès' : 'Club créé avec succès');
            closeModal();
            await loadAllClubs();
        } else {
            alert('Erreur: ' + data.message);
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('Erreur lors de l\'enregistrement');
    }
}




function confirmDeleteClub(id, nom) {
    clubToDelete = id;
    document.getElementById('deleteMessage').innerHTML = `Êtes-vous sûr de vouloir supprimer définitivement le club <strong>${escapeHtml(nom)}</strong> ?`;
    document.getElementById('deleteConfirmModal').style.display = 'flex';
}

function closeDeleteModal() {
    document.getElementById('deleteConfirmModal').style.display = 'none';
    clubToDelete = null;
}

async function deleteClub() {
    if (!clubToDelete) return;

    try {
        const response = await fetch(`/api/admin/clubs/${clubToDelete}`, {
            method: 'DELETE'
        });
        const data = await response.json();

        if (data.success) {
            alert('Club supprimé avec succès');
            closeDeleteModal();
            await loadAllClubs();
        } else {
            alert('Erreur: ' + data.message);
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('Erreur lors de la suppression');
    }
}

function closeModal() {
    document.getElementById('clubModal').style.display = 'none';
    document.getElementById('clubForm').reset();
    document.getElementById('clubId').value = '';
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialisation
document.addEventListener('DOMContentLoaded', async () => {
    await loadSecteurs();
    await loadGrades();
    await loadAllClubs();
    
    // Ajouter bouton reset filters
    const toolbar = document.querySelector('.toolbar');
    if (toolbar && !document.querySelector('.btn-reset-filters')) {
        const resetBtn = document.createElement('button');
        resetBtn.className = 'btn-reset-filters';
        resetBtn.innerHTML = '<i class="fas fa-undo-alt"></i> Réinitialiser';
        resetBtn.onclick = resetFilters;
        toolbar.appendChild(resetBtn);
    }
});

document.getElementById('confirmDeleteBtn').onclick = deleteClub;

window.onclick = function (event) {
    const modal = document.getElementById('clubModal');
    const deleteModal = document.getElementById('deleteConfirmModal');
    if (event.target === modal) {
        closeModal();
    }
    if (event.target === deleteModal) {
        closeDeleteModal();
    }
}

// Export Excel
function exportToExcel() {
    if (!filteredClubs || filteredClubs.length === 0) {
        alert("Aucune donnée à exporter.");
        return;
    }

    // Préparer les données pour l'export
    const dataToExport = filteredClubs.map((club, index) => ({
        'N°': index + 1,
        'Secteur': club.secteur || '-',
        'Nom du Club': club.nom_club || '-',
        'Identifiant': club.identif_club || '-',
        'Représentant': club.representant || '-',
        'Contact': club.contact || '-',
        'Grade': club.grade || '-',
        'Email': club.email || '-',
        'Statut': club.statut === 'actif' ? 'Actif' : 'Inactif'
    }));

    // Créer un classeur Excel
    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.json_to_sheet(dataToExport);

    // Ajouter la feuille au classeur
    XLSX.utils.book_append_sheet(wb, ws, "Clubs");

    // Générer le fichier et déclencher le téléchargement
    const date = new Date().toISOString().split('T')[0];
    XLSX.writeFile(wb, `Liste_Clubs_${date}.xlsx`);
}