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
let gradesList = [];

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
        const isNewOrAffilie = window.location.pathname.includes('licencies-new.html') || window.location.pathname.includes('licencies-affilie.html');
        let url = '/api/admin/secteurs';
        if (isNewOrAffilie) {
            url += '?saison_id=5'; // Saison 2026 par défaut
        }

        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        if (data.success) {
            secteursList = data.secteurs || [];

            // Peupler le filtre (liste) et le champ (édition)
            const selects = [document.getElementById('secteurSelect'), document.getElementById('id_secteur')];
            selects.forEach(select => {
                if (select) {
                    const defaultText = select.id === 'secteurSelect' ? 'Tous les secteurs' : 'Sélectionner un secteur';
                    select.innerHTML = `<option value="">${defaultText}</option>`;
                    secteursList.forEach(s => {
                        select.innerHTML += `<option value="${s.id_secteur}">${escapeHtml(s.nom_secteur)}</option>`;
                    });
                }
            });
        }
    } catch (error) {
        console.error('Erreur chargement secteurs:', error);
    }
}

// Charger les clubs
async function loadClubs() {
    try {
        const isNewOrAffilie = window.location.pathname.includes('licencies-new.html') || window.location.pathname.includes('licencies-affilie.html');
        let url = '/api/admin/clubs/all';
        if (isNewOrAffilie) {
            url += '?saison_id=5'; // Saison 2026 par défaut
        }

        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        if (data.success) {
            clubsList = data.clubs || [];
            // Les clubs sont peuplés dynamiquement par updateClubSelect()
            updateClubSelect();
        }
    } catch (error) {
        console.error('Erreur chargement clubs:', error);
    }
}

// Charger les grades
async function loadGrades() {
    try {
        const response = await fetch('/api/admin/grades');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        if (data.success) {
            gradesList = data.grades || [];
            const select = document.getElementById('grade');
            if (select) {
                select.innerHTML = '<option value="">Sélectionner un grade</option>';
                gradesList.forEach(g => {
                    select.innerHTML += `<option value="${g.id_grade}">${escapeHtml(g.libelle)}</option>`;
                });
            }
        }
    } catch (error) {
        console.error('Erreur chargement grades:', error);
    }
}

// Mettre à jour la liste des clubs en fonction du secteur sélectionné
function updateClubSelect() {
    const secteurSelect = document.getElementById('secteurSelect') || document.getElementById('id_secteur');
    const clubSelect = document.getElementById('clubSelect') || document.getElementById('id_club');

    if (!clubSelect) return;

    const secteurValue = secteurSelect ? secteurSelect.value : '';
    let filteredClubs = clubsList;

    if (secteurValue) {
        filteredClubs = clubsList.filter(club => club.List_sect && club.List_sect.toString() === secteurValue);
    }

    const defaultText = clubSelect.id === 'clubSelect' ? 'Tous les clubs' : 'Sélectionner un club';
    clubSelect.innerHTML = `<option value="">${defaultText}</option>`;
    filteredClubs.forEach(club => {
        clubSelect.innerHTML += `<option value="${club.id_club}">${escapeHtml(club.nom_club)} (${club.identif_club || ''})</option>`;
    });
}

// Charger les saisons pour les licenciés
async function loadSaisons() {
    try {
        const urlParams = new URLSearchParams(window.location.search);
        const licencieId = urlParams.get('id');
        let url = '/api/admin/saisons/licencies';

        // Si on est sur la page d'affiliation, on exclut les saisons déjà prises
        if (window.location.pathname.includes('licencies-affilie.html') && licencieId) {
            url += `?exclude_athlete_id=${licencieId}`;
        }

        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        if (data.success && data.saisons) {
            saisonsList = data.saisons;

            const selects = [document.getElementById('saisonSelect'), document.getElementById('id_saison')];
            selects.forEach(select => {
                if (select) {
                    const defaultText = select.id === 'saisonSelect' ? 'Toutes les saisons' : 'Sélectionner une saison';
                    select.innerHTML = `<option value="">${defaultText}</option>`;
                    saisonsList.forEach(s => {
                        const libelle = s.libelle_saison ? s.libelle_saison.toString() : '';
                        select.innerHTML += `<option value="${s.id_saison}">${libelle}</option>`;
                    });
                }
            });
        }
    } catch (error) {
        console.error('Erreur chargement saisons:', error);
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
                    <button class="action-btn edit" onclick="editLicencie(${licencie.id_licencie})" title="Modifier"><i class="fas fa-edit"></i></button>
                    <button class="action-btn delete" onclick="confirmDelete(${licencie.id_licencie}, '${escapeHtml(fullName.replace(/'/g, "\\'"))}')" title="Supprimer"><i class="fas fa-trash-alt"></i></button>
                    <button class="action-btn details" onclick="showDetails(${licencie.id_licencie})" title="Affiliation"><i class="fas fa-plus-circle"></i></button>
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

function showDetails(id) {
    // Pour l'instant on redirige vers l'édition ou on pourra ouvrir une modal
    window.location.href = `licencies-affilie.html?id=${id}`;
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
// Initialisation
document.addEventListener('DOMContentLoaded', async () => {
    if (!checkLicenciesAuth()) return;
    updateUserDisplay();

    try {
        // Charger les données de référence en parallèle pour gagner du temps
        await Promise.all([
            loadSecteurs(),
            loadClubs(),
            loadSaisons(),
            loadGrades()
        ]);

        const isListPage = window.location.pathname.includes('licencies-club.html');
        const isEditPage = window.location.pathname.includes('licencies-edit.html');
        const isAffiliePage = window.location.pathname.includes('licencies-affilie.html');
        const isNewPage = window.location.pathname.includes('licencies-new.html');

        if (isListPage) {
            await loadAllLicencies();
        }

        // Configurer les écouteurs d'événements
        const sectSelect = document.getElementById('secteurSelect') || document.getElementById('id_secteur');
        if (sectSelect) {
            sectSelect.addEventListener('change', () => updateClubSelect());
        }

        const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
        if (confirmDeleteBtn) {
            confirmDeleteBtn.addEventListener('click', deleteLicencie);
        }

        const licencieForm = document.getElementById('licencieForm');
        if (licencieForm) {
            licencieForm.addEventListener('submit', saveLicencie);
            
            // Forcer les majuscules sur tous les champs sauf email
            licencieForm.querySelectorAll('input[type="text"], input[type="tel"]').forEach(input => {
                if (input.id !== 'email' && !input.readOnly) {
                    input.addEventListener('input', (e) => {
                        e.target.value = e.target.value.toUpperCase();
                    });
                }
            });
        }

        window.addEventListener('click', (e) => {
            const modal = document.getElementById('deleteConfirmModal');
            if (e.target === modal) closeDeleteModal();
        });

        // Si on est sur une page de modification ou d'affiliation, charger les données
        if (isEditPage || isAffiliePage) {
            await checkAndLoadEditData();
        }

        // Si on est sur la page de création, charger le prochain numéro
        if (isNewPage) {
            await loadNextLicenceNumber();
        }
    } catch (error) {
        console.error('Erreur initialisation:', error);
    }
});

// Charger les grades
async function loadGrades() {
    try {
        const response = await fetch('/api/admin/grades');
        const data = await response.json();
        if (data.success) {
            const select = document.getElementById('grade');
            if (select) {
                select.innerHTML = '<option value="">Sélectionner un grade</option>';
                data.grades.forEach(g => {
                    select.innerHTML += `<option value="${g.id_grade}">${escapeHtml(g.libelle)}</option>`;
                });
            }
        }
    } catch (error) {
        console.error('Erreur chargement grades:', error);
    }
}

async function checkAndLoadEditData() {
    const urlParams = new URLSearchParams(window.location.search);
    const licencieId = urlParams.get('id');

    if (!licencieId) return;

    showLoading(true);
    try {
        const response = await fetch(`/api/admin/licencies/${licencieId}`);
        if (!response.ok) throw new Error(`Erreur HTTP: ${response.status}`);

        const data = await response.json();

        if (data.success && data.licencie) {
            const l = data.licencie;
            console.log('Données licencié reçues:', l);

            // Remplir les champs texte
            const fields = {
                'num_licence': l.num_licence,
                'nom_prenoms': l.nom_prenoms,
                'contact': l.contact,
                'email': l.email,
                'date_naissance': l.date_naissance,
                'adresse': l.adresse
            };

            for (const [id, val] of Object.entries(fields)) {
                const el = document.getElementById(id);
                if (el) el.value = val || '';
            }

            // Gérer les selects avec dépendances (Secteur -> Club)
            const secteurSelect = document.getElementById('id_secteur');
            if (secteurSelect && l.id_secteur) {
                secteurSelect.value = l.id_secteur;
                updateClubSelect(); // Re-peupler la liste des clubs
            }

            // Remplir les autres selects
            const selects = {
                'id_club': l.id_club,
                'id_saison': l.id_saison,
                'grade': l.id_grade,
                'statut': l.statut || 'actif',
                'genre': l.genre
            };

            for (const [id, val] of Object.entries(selects)) {
                const el = document.getElementById(id);
                if (el && val) el.value = val.toString();
            }

            // Gérer les boutons radio ASSURE
            if (l.assure !== undefined) {
                const assureVal = l.assure ? "1" : "0";
                const radio = document.querySelector(`input[name="assure"][value="${assureVal}"]`);
                if (radio) radio.checked = true;
            }
            // Remplir les champs de texte additionnels
            const textFields = {
                'lieu_nais': l.lieu_nais,
                'nation': l.nation,
                'prof_ath': l.prof_ath,
                'person_prevenir': l.person_prevenir,
                'tel_person': l.tel_person
            };
            for (const [id, val] of Object.entries(textFields)) {
                const el = document.getElementById(id);
                if (el && val) el.value = val;
            }
        }
    } catch (error) {
        console.error('Erreur pre-remplissage:', error);
        showNotification('Erreur lors de la récupération des données', 'error');
    } finally {
        showLoading(false);
    }
}

// Charger le prochain numéro de licence disponible
async function loadNextLicenceNumber() {
    try {
        const response = await fetch('/api/admin/licencies/next-number');
        const data = await response.json();
        if (data.success && data.next_number) {
            const el = document.getElementById('num_licence');
            if (el) el.value = data.next_number;
        }
    } catch (error) {
        console.error('Erreur chargement prochain numéro:', error);
    }
}

// Valider le format du contact (10 chiffres, commence par 01, 05 ou 07)
function validateContact(phone) {
    const regex = /^(01|05|07)\d{8}$/;
    return regex.test(phone);
}

// Enregistrer un licencié (nouveau ou modification)
async function saveLicencie(e) {
    e.preventDefault();
    const urlParams = new URLSearchParams(window.location.search);
    const licencieId = urlParams.get('id');
    const isNew = window.location.pathname.includes('licencies-new.html');

    if (!isNew && !licencieId) {
        showNotification('ID du licencié manquant', 'error');
        return;
    }

    // Récupération sécurisée des valeurs
    const getVal = (id) => document.getElementById(id)?.value || '';

    const formData = {
        nom_prenoms: getVal('nom_prenoms'),
        id_club: getVal('id_club'),
        id_saison: getVal('id_saison') || null,
        list_grade: getVal('grade'),
        genre: getVal('genre'),
        date_naissance: getVal('date_naissance') || null,
        lieu_nais: getVal('lieu_nais'),
        nation: getVal('nation'),
        prof_ath: getVal('prof_ath'),
        contact: getVal('contact'),
        email: getVal('email'),
        person_prevenir: getVal('person_prevenir'),
        tel_person: getVal('tel_person'),
        assure: document.querySelector('input[name="assure"]:checked')?.value || 0
    };

    // Validation des contacts
    if (formData.contact && !validateContact(formData.contact)) {
        showNotification('Le contact de l\'athlète doit avoir 10 chiffres et commencer par 01, 05 ou 07', 'error');
        return;
    }
    if (formData.tel_person && !validateContact(formData.tel_person)) {
        showNotification('Le contact du parent doit avoir 10 chiffres et commencer par 01, 05 ou 07', 'error');
        return;
    }

    console.log('Tentative d\'enregistrement avec données:', formData);

    // Validation minimale
    if (!formData.nom_prenoms || !formData.id_club) {
        showNotification('Le nom et le club sont obligatoires', 'error');
        return;
    }

    showLoading(true);
    try {
        const url = isNew ? '/api/admin/licencies' : `/api/admin/licencies/${licencieId}`;
        const method = isNew ? 'POST' : 'PUT';

        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        const data = await response.json();
        console.log('Réponse du serveur:', data);

        if (data.success) {
            showNotification(isNew ? 'Licencié créé avec succès !' : 'Mise à jour réussie !', 'success');
            // Redirection après un court délai
            setTimeout(() => {
                window.location.href = 'licencies-club.html';
            }, 1500);
        } else {
            showNotification('Erreur serveur: ' + (data.message || 'Échec de l\'opération'), 'error');
        }
    } catch (error) {
        console.error('Erreur lors de l\'appel API:', error);
        showNotification('Erreur de connexion au serveur', 'error');
    } finally {
        showLoading(false);
    }
}

// Export Excel
function exportToExcel() {
    if (!filteredLicencies || filteredLicencies.length === 0) {
        showNotification("Aucune donnée à exporter.", "warning");
        return;
    }

    // Préparer les données pour l'export
    const dataToExport = filteredLicencies.map((l, index) => {
        return {
            'N°': index + 1,
            'Numéro Licence': l.num_licence || '-',
            'Nom et Prénom': `${l.nom || ''} ${l.prenom || ''}`.trim() || '-',
            'Club': l.nom_club || '-',
            'Secteur': l.nom_secteur || '-',
            'Grade': l.grade || '-',
            'Contact': l.contact || '-',
            'Statut': l.statut === 'actif' ? 'Actif' : (l.statut === 'inactif' ? 'Inactif' : 'En attente')
        };
    });

    // Créer un classeur Excel
    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.json_to_sheet(dataToExport);

    // Ajuster la largeur des colonnes
    const wscols = [
        { wch: 5 },  // N°
        { wch: 15 }, // Numéro Licence
        { wch: 35 }, // Nom et Prénom
        { wch: 25 }, // Club
        { wch: 20 }, // Secteur
        { wch: 15 }, // Grade
        { wch: 15 }, // Contact
        { wch: 12 }  // Statut
    ];
    ws['!cols'] = wscols;

    // Ajouter la feuille au classeur
    XLSX.utils.book_append_sheet(wb, ws, "Licencies");

    // Générer le fichier et déclencher le téléchargement
    const date = new Date().toISOString().split('T')[0];
    XLSX.writeFile(wb, `Liste_Licencies_${date}.xlsx`);
}

function exportToPDF() {
    if (!filteredLicencies || filteredLicencies.length === 0) {
        showNotification("Aucune donnée à exporter.", "warning");
        return;
    }

    const { jsPDF } = window.jspdf;
    const doc = new jsPDF('l', 'mm', 'a4'); // Paysage

    // Année de la saison
    const selectedSaison = saisonsList.find(s => s.id_saison.toString() === currentSaison);
    const anneeSaison = selectedSaison ? selectedSaison.libelle_saison : (new Date().getFullYear());

    // Titre principal centré
    doc.setFontSize(18);
    doc.setTextColor(40, 44, 52);
    doc.setFont(undefined, 'bold');
    const title = `LISTE DES LICENCIES DE LA SAISON ${anneeSaison}`;
    const pageWidth = doc.internal.pageSize.getWidth();
    const textWidth = doc.getTextWidth(title);
    doc.text(title, (pageWidth - textWidth) / 2, 20);

    let startY = 30;

    // Si un club est sélectionné, on affiche ses infos en 2 colonnes
    if (currentClub) {
        const clubInfo = clubsList.find(c => c.id_club.toString() === currentClub.toString());
        if (clubInfo) {
            // Ligne de séparation
            doc.setDrawColor(102, 126, 234);
            doc.setLineWidth(0.5);
            doc.line(14, 25, 283, 25);

            const nbrAffilies = filteredLicencies.length;
            const nbrAssures = filteredLicencies.filter(l => l.assure == 1 || l.assure === true).length;

            doc.setFontSize(11);
            doc.setTextColor(50);

            // Colonne GAUCHE
            doc.setFont(undefined, 'bold'); doc.text("Secteur : ", 14, 35);
            doc.setFont(undefined, 'normal'); doc.text(String(clubInfo.nom_secteur || clubInfo.secteur || '-'), 45, 35);

            doc.setFont(undefined, 'bold'); doc.text("Club : ", 14, 42);
            doc.setFont(undefined, 'normal'); doc.text(String(clubInfo.nom_club || '-'), 45, 42);

            doc.setFont(undefined, 'bold'); doc.text("Numero du club : ", 14, 49);
            doc.setFont(undefined, 'normal'); doc.text(String(clubInfo.identif_club || '-'), 45, 49);

            doc.setFont(undefined, 'bold'); doc.text("Nbr d'affilie : ", 14, 56);
            doc.setFont(undefined, 'normal'); doc.text(String(nbrAffilies), 45, 56);

            // Colonne DROITE (à partir du milieu de la page)
            const rightColX = 160;
            const rightValX = 200;

            doc.setFont(undefined, 'bold'); doc.text("Representant : ", rightColX, 35);
            doc.setFont(undefined, 'normal'); doc.text(String(clubInfo.representant || '-'), rightValX, 35);

            doc.setFont(undefined, 'bold'); doc.text("Grade : ", rightColX, 42);
            doc.setFont(undefined, 'normal'); doc.text(String(clubInfo.grade || '-'), rightValX, 42);

            doc.setFont(undefined, 'bold'); doc.text("Contact club : ", rightColX, 49);
            doc.setFont(undefined, 'normal'); doc.text(String(clubInfo.contact || '-'), rightValX, 49);

            doc.setFont(undefined, 'bold'); doc.text("Nbr d'assure : ", rightColX, 56);
            doc.setFont(undefined, 'normal'); doc.text(String(nbrAssures), rightValX, 56);

            startY = 70;
        }
    }

    // Tableau
    const columns = ["N°", "Licence", "Nom et Prenom", "Grade", "Contact", "OBSER."];
    const rows = filteredLicencies.map((l, index) => [
        index + 1,
        l.num_licence || '-',
        `${l.nom || ''} ${l.prenom || ''}`.trim() || '-',
        l.grade || '-',
        l.contact || '-',
        (l.assure == 1 || l.assure === true) ? 'ASSURE' : '-'
    ]);

    doc.autoTable({
        head: [columns],
        body: rows,
        startY: startY,
        theme: 'grid',
        headStyles: { fillColor: [102, 126, 234], textColor: 255, fontStyle: 'bold' },
        styles: { fontSize: 10, cellPadding: 3 },
        columnStyles: {
            0: { cellWidth: 12 },
            1: { cellWidth: 35 },
            2: { cellWidth: 100 },
            3: { cellWidth: 40 },
            4: { cellWidth: 40 },
            5: { cellWidth: 25 }
        }
    });

    // Pied de page
    const pageCount = doc.internal.getNumberOfPages();
    for (let i = 1; i <= pageCount; i++) {
        doc.setPage(i);
        doc.setFontSize(8);
        doc.setTextColor(150);
        doc.text(`Page ${i} sur ${pageCount} - Document généré le ${new Date().toLocaleDateString('fr-FR')} - FI-ADEKASH`, 14, 205);
    }

    // Sauvegarde
    const fileName = `Liste_Licencies_${anneeSaison}_${new Date().toISOString().split('T')[0]}.pdf`;
    doc.save(fileName);
}