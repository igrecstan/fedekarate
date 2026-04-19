// admin/js/documents.js - Gestion des documents

let documentsData = [];

async function loadDocuments() {
    const tbody = document.getElementById('documentsTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = '<tr><td colspan="5" class="loader"><i class="fas fa-spinner fa-spin"></i> Chargement...</td></tr>';
    
    try {
        const result = await apiRequest('/documents');
        
        if (result.success) {
            documentsData = result.documents || result.data || [];
            displayDocuments();
        } else {
            tbody.innerHTML = `<tr><td colspan="5" class="loader">${result.message || 'Erreur de chargement'}</td></tr>`;
        }
    } catch (error) {
        console.error('Erreur:', error);
        tbody.innerHTML = '<tr><td colspan="5" class="loader">Erreur de chargement des données</td></tr>';
    }
}

function displayDocuments() {
    const tbody = document.getElementById('documentsTableBody');
    if (!tbody) return;
    
    if (documentsData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="loader">Aucun document trouvé</td></tr>';
        return;
    }
    
    tbody.innerHTML = documentsData.map(doc => {
        const icon = doc.url?.includes('.pdf') ? 'fa-file-pdf' : (doc.url?.includes('.doc') ? 'fa-file-word' : 'fa-file');
        const iconColor = doc.url?.includes('.pdf') ? '#e63946' : '#1e6fbf';
        
        return `
            <tr>
                <td><i class="fas ${icon}" style="color:${iconColor}; margin-right:8px;"></i> ${escapeHtml(doc.title)}</td>
                <td>${escapeHtml(doc.category)}</td>
                <td>${formatDate(doc.date)}</td>
                <td><span class="badge badge-green">${doc.status || 'En ligne'}</span></td>
                <td>
                    <button class="btn-action" onclick="editDocument(${doc.id})"><i class="fas fa-pen"></i> Modifier</button>
                    <button class="btn-action danger" onclick="deleteDocument(${doc.id})"><i class="fas fa-trash"></i></button>
                 </td>
            </tr>
        `;
    }).join('');
}

async function saveDocument() {
    const docId = document.getElementById('docId')?.value;
    const data = {
        title: document.getElementById('docTitle').value,
        category: document.getElementById('docCategory').value,
        url: document.getElementById('docUrl').value
    };
    
    if (!data.title || !data.url) {
        showNotification('Veuillez remplir tous les champs obligatoires', 'error');
        return;
    }
    
    const url = docId ? `/documents/${docId}` : '/documents';
    const method = docId ? 'PUT' : 'POST';
    
    try {
        const result = await apiRequest(url, method, data);
        if (result.success) {
            showNotification(docId ? 'Document modifié avec succès' : 'Document ajouté avec succès');
            toggleDocForm();
            loadDocuments();
        } else {
            showNotification(result.message || 'Erreur lors de l\'enregistrement', 'error');
        }
    } catch (error) {
        showNotification('Erreur lors de l\'enregistrement', 'error');
    }
}

async function deleteDocument(id) {
    if (confirm('Êtes-vous sûr de vouloir supprimer ce document ?')) {
        try {
            const result = await apiRequest(`/documents/${id}`, 'DELETE');
            if (result.success) {
                showNotification('Document supprimé avec succès');
                loadDocuments();
            } else {
                showNotification(result.message || 'Erreur lors de la suppression', 'error');
            }
        } catch (error) {
            showNotification('Erreur lors de la suppression', 'error');
        }
    }
}

async function editDocument(id) {
    try {
        const result = await apiRequest(`/documents/${id}`);
        if (result.success) {
            const doc = result.document || result.data;
            document.getElementById('modalTitle').textContent = 'Modifier le document';
            document.getElementById('docId').value = doc.id;
            document.getElementById('docTitle').value = doc.title;
            document.getElementById('docCategory').value = doc.category;
            document.getElementById('docUrl').value = doc.url;
            document.getElementById('docModal').style.display = 'flex';
        }
    } catch (error) {
        showNotification('Erreur lors du chargement du document', 'error');
    }
}

function toggleDocForm() {
    const form = document.getElementById('formAddDoc');
    if (form) {
        form.classList.toggle('hidden');
        if (!form.classList.contains('hidden')) {
            document.getElementById('docTitle').value = '';
            document.getElementById('docCategory').value = 'Statuts & règlements';
            document.getElementById('docUrl').value = '';
            document.getElementById('docId').value = '';
        }
    }
}

function closeDocModal() {
    document.getElementById('docModal').style.display = 'none';
}

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
    loadDocuments();
    
    const addBtn = document.getElementById('btnAddDoc');
    if (addBtn) addBtn.onclick = toggleDocForm;
    
    const saveBtn = document.getElementById('btnSaveDoc');
    if (saveBtn) saveBtn.onclick = saveDocument;
    
    const cancelBtn = document.getElementById('btnCancelDoc');
    if (cancelBtn) cancelBtn.onclick = toggleDocForm;
});