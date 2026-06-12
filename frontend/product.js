
console.log("🚀 ERP Products Engine — Extended Inventory Mode Active");

let allCategories = [];
let allVendors    = [];

// Boot sequence
document.addEventListener("DOMContentLoaded", () => {
    loadCategories();
    loadVendors();
    loadProducts();
    loadExpiryAlerts();
});

// ══════════════════════════════════════════
//  EXPIRY ALERTS BANNER
// ══════════════════════════════════════════
function loadExpiryAlerts() {
    fetch(`${API_BASE_URL}/products/expiry-alerts`, {
        headers: { "Authorization": "Bearer " + (localStorage.getItem("auth_token") || "") }
    })
    .then(r => r.json())
    .then(data => {
        if (!data.length) return;
        const banner = document.getElementById("expiryAlertBanner");
        if (!banner) return;
        banner.style.display = "block";
        banner.innerHTML = `
            <i class="fa-solid fa-triangle-exclamation" style="color:#f59e0b;"></i>
            <strong style="color:#fbbf24;"> ${data.length} product(s) expiring within 30 days!</strong>
            <span style="color:#94a3b8;margin-left:8px;">
                ${data.map(p => `<b style="color:#fff">${p.product_name}</b> (${p.days_remaining}d)`).join(', ')}
            </span>`;
    })
    .catch(() => {});
}

// ══════════════════════════════════════════
//  CATEGORIES
// ══════════════════════════════════════════
function loadCategories() {
    fetch(`${API_BASE_URL}/categories`)
    .then(r => r.json())
    .then(data => {
        allCategories = data;

        // Populate Add Product category dropdown
        const catSelect = document.getElementById("prod_category");
        if (catSelect) {
            catSelect.innerHTML = `<option value="">— Select Category —</option>`;
            data.forEach(c => {
                catSelect.innerHTML += `<option value="${c.category_id}">${c.category_name}</option>`;
            });
        }

        // Populate filter dropdown if exists
        const catFilter = document.getElementById("filter_category");
        if (catFilter) {
            catFilter.innerHTML = `<option value="">All Categories</option>`;
            data.forEach(c => {
                catFilter.innerHTML += `<option value="${c.category_id}">${c.category_name}</option>`;
            });
        }

        renderCategoryManager(data);
    })
    .catch(() => {});
}

function onCategoryChange() {
    const catId  = document.getElementById("prod_category").value;
    const subSel = document.getElementById("prod_subcategory");
    subSel.innerHTML = `<option value="">— Select Subcategory —</option>`;
    if (!catId) return;
    const cat = allCategories.find(c => c.category_id == catId);
    if (cat && cat.subcategories) {
        cat.subcategories.forEach(s => {
            subSel.innerHTML += `<option value="${s.subcategory_id}">${s.subcategory_name}</option>`;
        });
    }
}

function addCategory() {
    const name = document.getElementById("new_category_name").value.trim();
    if (!name) return showToast("Category name required.", "error");
    fetch(`${API_BASE_URL}/categories`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + (localStorage.getItem("auth_token") || "")
        },
        body: JSON.stringify({ category_name: name })
    })
    .then(r => r.json())
    .then(d => {
        if (d.error) return showToast(d.error, "error");
        showToast(d.message || "Category added!");
        document.getElementById("new_category_name").value = "";
        loadCategories();
    })
    .catch(() => showToast("Failed to add category.", "error"));
}

function addSubcategory() {
    const name  = document.getElementById("new_subcategory_name").value.trim();
    const catId = document.getElementById("sub_category_select").value;
    if (!name)  return showToast("Subcategory name is required.", "error");
    if (!catId) return showToast("Please select a parent category.", "error");
    fetch(`${API_BASE_URL}/subcategories`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + (localStorage.getItem("auth_token") || "")
        },
        body: JSON.stringify({ subcategory_name: name, category_id: parseInt(catId) })
    })
    .then(r => r.json())
    .then(d => {
        if (d.error) return showToast(d.error, "error");
        showToast(d.message || "Subcategory added!");
        document.getElementById("new_subcategory_name").value = "";
        loadCategories();
    })
    .catch(() => showToast("Failed to add subcategory.", "error"));
}

// Dedicated function — called on boot AND every time Categories tab opens
function populateSubCategorySelect(data) {
    const subCatSel = document.getElementById("sub_category_select");
    if (!subCatSel) return;
    subCatSel.innerHTML = `<option value="">— Select Category —</option>`;
    (data || allCategories).forEach(c => {
        subCatSel.innerHTML += `<option value="${c.category_id}">${c.category_name}</option>`;
    });
}

function renderCategoryManager(data) {
    const container = document.getElementById("categoryManagerList");
    if (container) {
        if (!data.length) {
            container.innerHTML = `<p style="color:#64748b;">No categories yet.</p>`;
        } else {
            container.innerHTML = data.map(c => `
                <div style="background:#25293c;border-radius:8px;padding:12px 16px;margin-bottom:10px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <span style="color:#fff;font-weight:600;">
                            <i class="fa-solid fa-folder" style="color:#f59e0b;margin-right:8px;"></i>
                            ${c.category_name}
                        </span>
                        <button onclick="deleteCategory(${c.category_id})"
                            style="background:rgba(239,68,68,0.1);color:#f87171;
                                   border:1px solid rgba(239,68,68,0.3);
                                   padding:4px 10px;border-radius:4px;
                                   font-size:0.8rem;cursor:pointer;">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </div>
                    ${c.subcategories && c.subcategories.length ? `
                    <div style="margin-top:8px;padding-left:16px;">
                        ${c.subcategories.map(s => `
                            <span style="display:inline-flex;align-items:center;gap:6px;
                                         background:#1a1d29;color:#94a3b8;
                                         padding:3px 10px;border-radius:20px;
                                         font-size:0.8rem;margin:3px;">
                                <i class="fa-solid fa-tag" style="color:#38bdf8;font-size:0.7rem;"></i>
                                ${s.subcategory_name}
                                <i class="fa-solid fa-xmark"
                                   style="cursor:pointer;color:#ef4444;"
                                   onclick="deleteSubcategory(${s.subcategory_id})"></i>
                            </span>`).join('')}
                    </div>` :
                    `<div style="margin-top:6px;padding-left:16px;color:#475569;font-size:0.78rem;">
                        No subcategories yet
                    </div>`}
                </div>`).join('');
        }
    }

    // Always repopulate sub_category_select with latest data
    populateSubCategorySelect(data);
}

function deleteCategory(id) {
    if (!confirm("Delete this category and all its subcategories?")) return;
    fetch(`${API_BASE_URL}/categories/${id}`, {
        method: "DELETE",
        headers: { "Authorization": "Bearer " + (localStorage.getItem("auth_token") || "") }
    })
    .then(r => r.json())
    .then(d => { showToast(d.message || "Category deleted."); loadCategories(); })
    .catch(() => showToast("Failed to delete category.", "error"));
}

function deleteSubcategory(id) {
    fetch(`${API_BASE_URL}/subcategories/${id}`, {
        method: "DELETE",
        headers: { "Authorization": "Bearer " + (localStorage.getItem("auth_token") || "") }
    })
    .then(r => r.json())
    .then(d => { showToast(d.message || "Subcategory deleted."); loadCategories(); })
    .catch(() => showToast("Failed to delete subcategory.", "error"));
}

// ══════════════════════════════════════════
//  VENDORS
// ══════════════════════════════════════════
function loadVendors() {
    fetch(`${API_BASE_URL}/vendors`)
    .then(r => r.json())
    .then(data => {
        allVendors = data;
        const sel = document.getElementById("prod_vendor");
        if (sel) {
            sel.innerHTML = `<option value="">— Select Vendor —</option>`;
            data.forEach(v => {
                sel.innerHTML += `<option value="${v.vendor_id}">[${v.vendor_code}] ${v.vendor_name}</option>`;
            });
        }
        renderVendorTable(data);
    })
    .catch(() => {});
}

function renderVendorTable(data) {
    const tbody = document.getElementById("vendorTableBody");
    if (!tbody) return;
    if (!data.length) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;color:#64748b;padding:2rem;">No vendors registered yet.</td></tr>`;
        return;
    }
    tbody.innerHTML = data.map(v => `
        <tr>
            <td><span class="id-badge">#${v.vendor_id}</span></td>
            <td style="font-weight:600;color:#fff;">${v.vendor_name}</td>
            <td><span style="color:#38bdf8;font-family:monospace;">${v.vendor_code}</span></td>
            <td style="color:#94a3b8;">${v.contact_person || 'N/A'}</td>
            <td style="color:#94a3b8;">${v.phone || 'N/A'}</td>
            <td style="color:#38bdf8;">${v.email || 'N/A'}</td>
            <td>
                <button onclick="deleteVendor(${v.vendor_id})"
                    style="background:rgba(239,68,68,0.1);color:#f87171;
                           border:1px solid rgba(239,68,68,0.3);
                           padding:5px 10px;border-radius:4px;
                           font-size:0.8rem;cursor:pointer;">
                    <i class="fa-solid fa-trash"></i>
                </button>
            </td>
        </tr>`).join('');
}

function addVendor() {
    const payload = {
        vendor_name:    document.getElementById("v_name").value.trim(),
        vendor_code:    document.getElementById("v_code").value.trim(),
        contact_person: document.getElementById("v_contact").value.trim(),
        phone:          document.getElementById("v_phone").value.trim(),
        email:          document.getElementById("v_email").value.trim(),
        address:        document.getElementById("v_address").value.trim()
    };
    if (!payload.vendor_name) return showToast("Vendor name is required.", "error");
    if (!payload.vendor_code) return showToast("Vendor code is required.", "error");

    fetch(`${API_BASE_URL}/vendors`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + (localStorage.getItem("auth_token") || "")
        },
        body: JSON.stringify(payload)
    })
    .then(r => r.json())
    .then(d => {
        if (d.error) return showToast(d.error, "error");
        showToast(d.message || "Vendor added!");
        ["v_name","v_code","v_contact","v_phone","v_email","v_address"].forEach(id => {
            document.getElementById(id).value = "";
        });
        loadVendors();
    })
    .catch(() => showToast("Failed to add vendor.", "error"));
}

function deleteVendor(id) {
    if (!confirm("Delete this vendor?")) return;
    fetch(`${API_BASE_URL}/vendors/${id}`, {
        method: "DELETE",
        headers: { "Authorization": "Bearer " + (localStorage.getItem("auth_token") || "") }
    })
    .then(r => r.json())
    .then(d => { showToast(d.message || "Vendor deleted."); loadVendors(); })
    .catch(() => showToast("Failed to delete vendor.", "error"));
}

// ══════════════════════════════════════════
//  PRODUCTS TABLE
// ══════════════════════════════════════════
function loadProducts() {
    const table = document.getElementById("productsTable");
    if (!table) return;
    table.innerHTML = `<tr><td colspan="10" style="text-align:center;color:#94a3b8;padding:2rem;">
        <i class="fa-solid fa-spinner fa-spin"></i> Loading inventory...</td></tr>`;

    fetch(`${API_BASE_URL}/products`)
    .then(r => r.json())
    .then(data => {
        table.innerHTML = "";
        if (!data.length) {
            table.innerHTML = `<tr><td colspan="10" style="text-align:center;color:#94a3b8;padding:2rem;">No products found.</td></tr>`;
            return;
        }
        const today = new Date();
        data.forEach(p => {
            const expiry      = p.expiry_date ? new Date(p.expiry_date) : null;
            const daysLeft    = expiry ? Math.ceil((expiry - today) / 86400000) : null;
            const expiryColor = daysLeft === null ? '#94a3b8'
                              : daysLeft <= 7     ? '#ef4444'
                              : daysLeft <= 30    ? '#f59e0b' : '#10b981';
            const expiryBadge = daysLeft === null
                ? '<span style="color:#64748b;">N/A</span>'
                : `<span style="color:${expiryColor};font-weight:600;">
                       ${p.expiry_date} <small>(${daysLeft}d)</small>
                   </span>`;

            table.innerHTML += `
            <tr>
                <td><span class="id-badge">#${p.product_id}</span></td>
                <td>
                    <div style="font-weight:600;color:#fff;">${p.product_name}</div>
                    <div style="color:#64748b;font-size:0.78rem;">${p.description || ''}</div>
                </td>
                <td style="color:#94a3b8;font-size:0.82rem;">${p.challan_no || 'N/A'}</td>
                <td>
                    <div style="color:#fff;">${p.vendor_name || 'N/A'}</div>
                    <div style="color:#38bdf8;font-size:0.78rem;font-family:monospace;">${p.vendor_code || ''}</div>
                </td>
                <td>
                    <div style="color:#cbd5e1;">${p.category_name || 'N/A'}</div>
                    <div style="color:#64748b;font-size:0.78rem;">${p.subcategory_name || ''}</div>
                </td>
                <td style="font-weight:600;color:#38bdf8;">₹${parseFloat(p.price || 0).toFixed(2)}</td>
                <td>
                    <span style="color:${p.stock_quantity > 5 ? '#10b981' : '#ef4444'};font-weight:600;">
                        ${p.stock_quantity} units
                    </span>
                </td>
                <td>${expiryBadge}</td>
                <td>
                    <div style="font-family:monospace;font-size:0.75rem;color:#94a3b8;
                                background:#25293c;padding:3px 6px;border-radius:4px;
                                max-width:130px;overflow:hidden;text-overflow:ellipsis;">
                        ${p.barcode || 'N/A'}
                    </div>
                </td>
                <td>
                    <button onclick="deleteProduct(${p.product_id})"
                        style="background:rgba(239,68,68,0.1);color:#f87171;
                               border:1px solid rgba(239,68,68,0.3);
                               padding:5px 10px;border-radius:4px;
                               font-size:0.8rem;cursor:pointer;">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </td>
            </tr>`;
        });
    })
    .catch(() => {
        table.innerHTML = `<tr><td colspan="10" style="text-align:center;color:#ef4444;padding:2rem;">
            <i class="fa-solid fa-triangle-exclamation"></i> Failed to load products.</td></tr>`;
    });
}

function addProduct() {
    const name  = document.getElementById("name").value.trim();
    const price = document.getElementById("price").value;
    const stock = document.getElementById("stock").value;

    if (!name)                    return showToast("Product name is required.", "error");
    if (isNaN(parseFloat(price))) return showToast("Enter a valid price.", "error");
    if (isNaN(parseInt(stock)))   return showToast("Enter a valid stock quantity.", "error");

    const payload = {
        product_name:      name,
        description:       document.getElementById("prod_desc").value.trim(),
        price:             parseFloat(price),
        stock_quantity:    parseInt(stock),
        challan_no:        document.getElementById("prod_challan").value.trim(),
        vendor_id:         parseInt(document.getElementById("prod_vendor").value) || null,
        category_id:       parseInt(document.getElementById("prod_category").value) || null,
        subcategory_id:    parseInt(document.getElementById("prod_subcategory").value) || null,
        manufactured_date: document.getElementById("prod_mfg_date").value || null,
        expiry_date:       document.getElementById("prod_expiry").value || null,
        arrived_at:        document.getElementById("prod_arrived_at").value || null
    };

    const btn  = document.getElementById("productSubmitBtn");
    const orig = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Saving...`;

    fetch(`${API_BASE_URL}/products`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + (localStorage.getItem("auth_token") || "")
        },
        body: JSON.stringify(payload)
    })
    .then(r => r.json())
    .then(d => {
        if (d.error) return showToast(d.error, "error");
        showToast(`✅ Product added! Barcode: ${d.barcode}`);
        document.getElementById("productForm").reset();
        document.getElementById("prod_subcategory").innerHTML = `<option value="">— Select Subcategory —</option>`;
        loadProducts();
        loadExpiryAlerts();
    })
    .catch(() => showToast("Failed to add product. Make sure you are logged in.", "error"))
    .finally(() => { btn.disabled = false; btn.innerHTML = orig; });
}

function deleteProduct(id) {
    if (!confirm("Delete this product from inventory?")) return;
    fetch(`${API_BASE_URL}/products/${id}`, {
        method: "DELETE",
        headers: { "Authorization": "Bearer " + (localStorage.getItem("auth_token") || "") }
    })
    .then(r => r.json())
    .then(d => { showToast(d.message || "Product deleted."); loadProducts(); })
    .catch(() => showToast("Delete failed.", "error"));
}

// ══════════════════════════════════════════
//  TAB SWITCHER
// ══════════════════════════════════════════
function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(t => t.style.display = 'none');
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(tabId).style.display = 'block';
    event.target.classList.add('active');

    // Re-populate sub_category_select every time Categories tab opens
    // because it may not have existed or been hidden during initial load
    if (tabId === 'tab-categories') {
        populateSubCategorySelect(allCategories);
    }
}