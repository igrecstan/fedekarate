// admin/js/clubs-new.js - Logique du formulaire d'ajout de club

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
if (userAvatar) {
    const initials = (adminNom.charAt(0) + adminPrenom.charAt(0)).toUpperCase() || 'AD';
    userAvatar.textContent = initials;
}

// Charger les secteurs depuis la table secteur
async function loadSecteurs() {
    try {
        const response = await fetch('/api/admin/secteurs');
        const data = await response.json();
        if (data.success) {
            const select = document.getElementById('List_sect');
            if (select) {
                select.innerHTML = '<option value="">Sélectionner un secteur</option>';
                data.secteurs.forEach(s => {
                    select.innerHTML += `<option value="${s.id_secteur}">${s.nom_secteur}</option>`;
                });
            }
        }
    } catch (error) {
        console.error('Erreur chargement secteurs:', error);
    }
}

// Charger les grades : SELECT id_grade, libelle FROM grade WHERE id_grade > 14
async function loadGrades() {
    try {
        const response = await fetch('/api/admin/grades/club');
        const data = await response.json();
        if (data.success) {
            const select = document.getElementById('grade');
            if (select) {
                select.innerHTML = '<option value="">Sélectionner un grade</option>';
                data.grades.forEach(g => {
                    select.innerHTML += `<option value="${g.id_grade}">${g.libelle}</option>`;
                });
            }
        }
    } catch (error) {
        console.error('Erreur chargement grades:', error);
    }
}

// Générer le numéro de club : AD-MMYY-XXXX
// Récupère le dernier identifiant, extrait les 4 derniers chiffres, incrémente de 1
async function generateClubNumber() {
    try {
        const response = await fetch('/api/admin/clubs/last-identif');
        const data = await response.json();

        const now = new Date();
        const month = String(now.getMonth() + 1).padStart(2, '0'); // MM
        const year = String(now.getFullYear()).slice(-2);           // YY (2 derniers chiffres)
        const prefix = `AD-${month}${year}`;

        let nextNumber = 1; // Par défaut si aucun club n'existe

        if (data.success && data.last_identif) {
            // Extraire les 4 derniers caractères du dernier identifiant
            const lastIdentif = data.last_identif;
            const lastFour = lastIdentif.slice(-4);
            const lastNum = parseInt(lastFour, 10);
            if (!isNaN(lastNum)) {
                nextNumber = lastNum + 1;
            }
        }

        const numberPart = String(nextNumber).padStart(4, '0');
        const identif = `${prefix}-${numberPart}`;

        document.getElementById('identif_club').value = identif;
    } catch (error) {
        console.error('Erreur génération numéro club:', error);
        // Fallback : générer avec timestamp
        const now = new Date();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const year = String(now.getFullYear()).slice(-2);
        document.getElementById('identif_club').value = `AD-${month}${year}-0001`;
    }
}

// Validation du contact (01, 05 ou 07 + 10 chiffres)
function validateContact(value) {
    const regex = /^(01|05|07)\d{8}$/;
    return regex.test(value);
}

// Soumission du formulaire
async function submitClubForm(event) {
    event.preventDefault();

    const contactInput = document.getElementById('contact');
    const contactError = document.getElementById('contactError');
    const contactValue = contactInput.value.trim();

    // Validation du contact
    if (contactValue && !validateContact(contactValue)) {
        contactInput.classList.add('error-border');
        if (contactError) contactError.style.display = 'block';
        return;
    } else {
        contactInput.classList.remove('error-border');
        if (contactError) contactError.style.display = 'none';
    }

    const clubData = {
        identif_club: document.getElementById('identif_club').value,
        nom_club: document.getElementById('nom_club').value.trim().toUpperCase(),
        List_sect: document.getElementById('List_sect').value || null,
        representant: document.getElementById('representant').value.trim().toUpperCase(),
        grade: document.getElementById('grade').value || null,
        contact: contactValue,
        whatsapp: document.getElementById('whatsapp').value.trim(),
        email: document.getElementById('email').value.trim().toLowerCase(),
        Num_declaration: document.getElementById('Num_declaration').value.trim().toUpperCase()
    };

    // Validation des champs obligatoires
    if (!clubData.nom_club) {
        alert('Le nom du club est obligatoire');
        return;
    }
    if (!clubData.List_sect) {
        alert('Le secteur est obligatoire');
        return;
    }
    if (!clubData.representant) {
        alert('Le représentant est obligatoire');
        return;
    }
    if (!clubData.contact) {
        alert('Le contact est obligatoire');
        return;
    }

    try {
        const response = await fetch('/api/admin/clubs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(clubData)
        });

        const data = await response.json();

        if (data.success) {
            alert(`Club créé avec succès !\nNuméro : ${clubData.identif_club}`);
            window.location.href = 'clubs.html';
        } else {
            alert('Erreur : ' + data.message);
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('Erreur lors de l\'enregistrement du club');
    }
}

// Initialisation
document.addEventListener('DOMContentLoaded', async () => {
    await loadSecteurs();
    await loadGrades();
    await generateClubNumber();

    // Attacher le handler du formulaire
    const form = document.getElementById('clubForm');
    if (form) {
        form.addEventListener('submit', submitClubForm);
    }

    // Validation en temps réel du contact
    const contactInput = document.getElementById('contact');
    const contactError = document.getElementById('contactError');
    if (contactInput) {
        contactInput.addEventListener('input', function () {
            const value = this.value.trim();
            if (value && !validateContact(value)) {
                this.classList.add('error-border');
                if (contactError) contactError.style.display = 'block';
            } else {
                this.classList.remove('error-border');
                if (contactError) contactError.style.display = 'none';
            }
        });
    }
});
