// admin/js/clubs.js - Gestion des clubs

let allClubs = [];
let currentPage = 1;
let currentSearch = '';
let itemsPerPage = 20;
let totalPages = 1;
let clubToDelete = null;
let secteursList = [];
let gradesList = [];

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
    } catch(e) { 
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
    } catch(e) { 
        console.error('Erreur chargement grades:', e); 
    }
}

// Charger tous les clubs
async function loadClubs() {
    const tbody = document.getElementById('clubsTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = '<tr><td colspan="7" class="loader"><i class="fas fa-spinner fa-spin"></i> Chargement...<\/td><\/tr>';
    
    try {
        let url = `/api/admin/clubs?page=${currentPage}&limit=${itemsPerPage}`;
        if (currentSearch) {
            url += `&search=${encodeURIComponent(currentSearch)}`;
        }

        const response = await fetch(url);
        const data = await response.json();
        
        if (data.success) {
            allClubs = data.clubs || [];
            totalPages = data.totalPages || 1;
            displayClubs(allClubs);
            displayPagination();
        } else {
            tbody.innerHTML = `<tr><td colspan="7" class="loader">${data.message || 'Erreur de chargement'}<\/td><\/tr>`;
        }
    } catch (error) {
        console.error('Erreur:', error);
        tbody.innerHTML = '<tr><td colspan="7" class="loader">Erreur de chargement des données<\/td><\/tr>';
    }
}

// Afficher les clubs
function displayClubs(clubs) {
    const tbody = document.getElementById('clubsTableBody');
    tbody.innerHTML = '';

    if (!clubs || clubs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center;">Aucun club trouvé<\/td><\/tr>';
        return;
    }

    clubs.forEach(club => {
        const row = tbody.insertRow();
        row.innerHTML = `
            <td>${escapeHtml(club.identif_club || '-')}<\/td>
            <td><strong>${escapeHtml(club.nom_club || '-')}</strong><\/td>
            <td>${escapeHtml(club.representant || '-')}<\/td>
            <td>${escapeHtml(club.contact || '-')}<\/td>
            <td>${escapeHtml(club.secteur || '-')}<\/td>
            <td><span class="badge badge-active">Actif<\/span><\/td>
            <td class="actions">
                <button class="edit-btn" onclick="editClub(${club.id_club})"><i class="fas fa-edit"><\/i> Modifier<\/button>
                <button class="delete-btn" onclick="confirmDeleteClub(${club.id_club}, '${escapeHtml(club.nom_club)}')"><i class="fas fa-trash"><\/i> Supprimer<\/button>
            <\/td>
        `;
    });
}

// Pagination
function displayPagination() {
    const paginationDiv = document.getElementById('pagination');
    if (!paginationDiv) return;
    
    if (totalPages <= 1) {
        paginationDiv.innerHTML = '';
        return;
    }
    
    let html = '';
    html += `<button onclick="changePage(1)" ${currentPage === 1 ? 'disabled' : ''}>&laquo;<\/button>`;
    html += `<button onclick="changePage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>&lsaquo;<\/button>`;
    
    for (let i = Math.max(1, currentPage - 2); i <= Math.min(totalPages, currentPage + 2); i++) {
        html += `<button onclick="changePage(${i})" class="${i === currentPage ? 'active' : ''}">${i}<\/button>`;
    }
    
    html += `<button onclick="changePage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>&rsaquo;<\/button>`;
    html += `<button onclick="changePage(${totalPages})" ${currentPage === totalPages ? 'disabled' : ''}>&raquo;<\/button>`;
    
    paginationDiv.innerHTML = html;
}

function changePage(page) {
    currentPage = page;
    loadClubs();
}

function searchClubs() {
    currentSearch = document.getElementById('searchInput').value;
    currentPage = 1;
    loadClubs();
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
            loadClubs();
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
            loadClubs();
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
document.addEventListener('DOMContentLoaded', () => {
    loadSecteurs();
    loadGrades();
    loadClubs();
});

document.getElementById('confirmDeleteBtn').onclick = deleteClub;

window.onclick = function(event) {
    const modal = document.getElementById('clubModal');
    const deleteModal = document.getElementById('deleteConfirmModal');
    if (event.target === modal) {
        closeModal();
    }
    if (event.target === deleteModal) {
        closeDeleteModal();
    }
}