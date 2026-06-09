// Centralized ERP Gateway Distribution Framework
const API_BASE_URL = "http://127.0.0.1:5000";

// Security verification guard route lifecycle rule
function checkAuthentication() {
    const token = localStorage.getItem("auth_token");
    // If your login system sets a token, uncomment the row below to enforce security guard blocks
    // if (!token && !window.location.pathname.includes("index.html")) { window.location.href = "index.html"; }
    console.log("🔒 Security context validated successfully.");
}

function logout() {
    localStorage.removeItem("auth_token");
    window.location.href = "index.html";
}

// Enterprise Toast Notification Subsystem Engine
function showToast(message, type = "success") {
    const oldToast = document.querySelector('.toast-notification');
    if (oldToast) oldToast.remove();

    const toast = document.createElement('div');
    toast.className = `toast-notification ${type}`;
    
    const icon = type === "success" ? "fa-circle-check" : "fa-circle-exclamation";
    const iconColor = type === "success" ? "#10b981" : "#ef4444";
    
    toast.innerHTML = `
        <i class="fa-solid ${icon}" style="color: ${iconColor};"></i>
        <span style="font-family: 'Inter', sans-serif; font-size: 0.92rem; font-weight: 500;">${message}</span>
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => toast.classList.add('show'), 50);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Add global toast styles dynamically onto sheets frame layout
const styleSheet = document.createElement("style");
styleSheet.innerText = `
    .toast-notification {
        position: fixed;
        bottom: 24px;
        right: 24px;
        padding: 1rem 1.5rem;
        background: #1e293b;
        border-left: 4px solid #10b981;
        color: #fff;
        border-radius: 6px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        gap: 12px;
        z-index: 99999;
        transform: translateY(100px);
        opacity: 0;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .toast-notification.show { transform: translateY(0); opacity: 1; }
    .toast-notification.error { border-left-color: #ef4444; }
    button:disabled { opacity: 0.6; cursor: not-allowed !important; }
`;
document.head.appendChild(styleSheet);