/**
 * Lead Management System — frontend logic (vanilla JS + fetch).
 *
 * - Home page: validate + POST /api/leads
 * - Dashboard: GET /api/leads with filters, PUT /api/leads/:id for status
 */

"use strict";

/** Same rules as Flask backend (keep in sync for predictable UX). */
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const PHONE_RE = /^\+?[\d\s().-]{10,22}$/;
const NAME_RE =/^[A-Za-z]+(?:[A-Z][a-z]+)*$/;

function digitsOnly(str) {
  return (str || "").replace(/\D/g, "");
}

function isValidPhone(phone) {
  if (!phone || !PHONE_RE.test(phone.trim())) return false;
  const n = digitsOnly(phone).length;
  return n >= 10 && n <= 15;
}
function isValidName(name){
   return NAME_RE.test(name.trim());

 }

/**
 * Show a Bootstrap-styled alert in a container (replaces previous message).
 * @param {"success"|"danger"|"warning"|"info"} kind
 */
function showAlert(container, kind, message, { autohideMs = 0 } = {}) {
  if (!container) return;
  container.className = `alert alert-${kind}`;
  container.textContent = message;
  container.classList.remove("d-none");
  if (autohideMs > 0) {
    window.clearTimeout(container._hideT);
    container._hideT = window.setTimeout(() => {
      container.classList.add("d-none");
    }, autohideMs);
  }
}

function hideAlert(container) {
  if (!container) return;
  container.classList.add("d-none");
}

function validateLeadClient(payload) {
  const errors = [];
  if (!payload.name.trim()) errors.push("Name is required.");
  else if (!NAME_RE.test(payload.name.trim())) errors.push("Name must start with capital letter and contain only alphabet.");
  if (!payload.email.trim()) errors.push("Email is required.");
  else if (!EMAIL_RE.test(payload.email.trim())) errors.push("Enter a valid email address.");
  if (!payload.phone.trim()) errors.push("Phone number is required.");
  else if (!isValidPhone(payload.phone)) {
    errors.push("Phone must be 10–15 digits; spaces/dashes/parentheses allowed.");
  }
  if (!payload.business_type.trim()) errors.push("Business type is required.");
  if (!payload.message.trim()) errors.push("Message is required.");
  return errors;
}

// --- Home: lead form ----------------------------------------------------------

function initLeadForm() {
  const form = document.getElementById("leadForm");
  if (!form) return;

  const alertEl = document.getElementById("formAlert");
  const autoBox = document.getElementById("autoReplyBox");
  const autoText = document.getElementById("autoReplyText");
  const submitBtn = document.getElementById("submitBtn");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    hideAlert(alertEl);
    if (autoBox) autoBox.classList.add("d-none");

    const payload = {
      name: form.name.value,
      email: form.email.value,
      phone: form.phone.value,
      business_type: form.business_type.value,
      message: form.message.value,
    };

    const clientErrors = validateLeadClient(payload);
    if (clientErrors.length) {
      form.classList.add("was-validated");
      showAlert(alertEl, "danger", clientErrors.join(" "));
      return;
    }

    submitBtn.disabled = true;
    try {
      const res = await fetch("/api/leads", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json().catch(() => ({}));

      if (!res.ok || !data.ok) {
        const msg = (data.errors && data.errors.join(" ")) || "Could not save lead.";
        showAlert(alertEl, "danger", msg);
        return;
      }

      form.reset();
      form.classList.remove("was-validated");
      showAlert(alertEl, "success", "Lead submitted successfully. Thank you!", { autohideMs: 6000 });

      if (autoBox && autoText && data.auto_reply) {
        autoText.textContent = data.auto_reply;
        autoBox.classList.remove("d-none");
      }
    } catch {
      showAlert(alertEl, "danger", "Network error — please try again.");
    } finally {
      submitBtn.disabled = false;
    }
  });

  // Live Bootstrap validation hints
  const inputs = form.querySelectorAll("input, select, textarea");
  inputs.forEach((el) => {
    el.addEventListener("input", () => {
      if (el.checkValidity()) el.classList.remove("is-invalid");
    });
  });
}

// --- Dashboard --------------------------------------------------------------

function formatWhen(iso) {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    return d.toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return iso;
  }
}

function renderLeadsTable(tbody, leads) {
  tbody.innerHTML = "";
  if (!leads.length) {
    const tr = document.createElement("tr");
    tr.innerHTML =
      '<td colspan="8" class="text-center text-muted py-5">No leads match your filters.</td>';
    tbody.appendChild(tr);
    return;
  }

  for (const lead of leads) {
    const tr = document.createElement("tr");
    tr.dataset.leadId = String(lead.id);
    tr.innerHTML = `
      <th scope="row">${lead.id}</th>
      <td>${escapeHtml(lead.name)}</td>
      <td><a href="mailto:${escapeHtml(lead.email)}">${escapeHtml(lead.email)}</a></td>
      <td>${escapeHtml(lead.phone)}</td>
      <td>${escapeHtml(lead.business_type)}</td>
      <td><span class="badge bg-secondary status-pill">${escapeHtml(lead.status)}</span></td>
      <td class="text-nowrap small">${formatWhen(lead.created_at)}</td>
      <td class="text-end text-nowrap">
        <div class="d-inline-flex gap-1 align-items-center justify-content-end flex-wrap">
          <select class="form-select form-select-sm status-select" style="width: 9rem" aria-label="New status">
            <option value="New" ${lead.status === "New" ? "selected" : ""}>New</option>
            <option value="Contacted" ${lead.status === "Contacted" ? "selected" : ""}>Contacted</option>
            <option value="Closed" ${lead.status === "Closed" ? "selected" : ""}>Closed</option>
          </select>
          <button type="button" class="btn btn-sm btn-primary update-btn">Update</button>
        </div>
      </td>
    `;
    tbody.appendChild(tr);
  }
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function statusBadgeClass(status) {
  if (status === "New") return "bg-primary";
  if (status === "Contacted") return "bg-warning text-dark";
  if (status === "Closed") return "bg-success";
  return "bg-secondary";
}

function decorateStatusPills(tbody) {
  tbody.querySelectorAll(".status-pill").forEach((pill) => {
    const s = pill.textContent.trim();
    pill.className = `badge status-pill ${statusBadgeClass(s)}`;
  });
}

async function fetchLeads(q, status) {
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  if (status) params.set("status", status);
  const url = `/api/leads${params.toString() ? `?${params}` : ""}`;
  const res = await fetch(url, { headers: { Accept: "application/json" } });
  const data = await res.json().catch(() => ({}));
  if (!res.ok || !data.ok) {
    const msg = (data.errors && data.errors.join(" ")) || "Failed to load leads.";
    throw new Error(msg);
  }
  return data.leads || [];
}

function initDashboard() {
  const tbody = document.getElementById("leadsTableBody");
  const searchInput = document.getElementById("searchInput");
  const statusFilter = document.getElementById("statusFilter");
  const refreshBtn = document.getElementById("refreshBtn");
  const meta = document.getElementById("leadsMeta");
  const alertEl = document.getElementById("dashAlert");

  if (!tbody) return;

  let debounceT = null;

  const load = async () => {
    hideAlert(alertEl);
    const q = searchInput ? searchInput.value.trim() : "";
    const status = statusFilter ? statusFilter.value : "";
    try {
      const leads = await fetchLeads(q, status);
      renderLeadsTable(tbody, leads);
      decorateStatusPills(tbody);
      if (meta) meta.textContent = `${leads.length} lead(s) shown`;
    } catch (err) {
      tbody.innerHTML =
        '<tr><td colspan="8" class="text-center text-danger py-4">Could not load leads.</td></tr>';
      showAlert(alertEl, "danger", err.message || String(err));
      if (meta) meta.textContent = "";
    }
  };

  tbody.addEventListener("click", async (e) => {
    const btn = e.target.closest(".update-btn");
    if (!btn) return;
    const tr = btn.closest("tr");
    if (!tr) return;
    const id = tr.dataset.leadId;
    const select = tr.querySelector(".status-select");
    if (!id || !select) return;

    btn.disabled = true;
    hideAlert(alertEl);
    try {
      const res = await fetch(`/api/leads/${encodeURIComponent(id)}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ status: select.value }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data.ok) {
        const msg = (data.errors && data.errors.join(" ")) || "Update failed.";
        showAlert(alertEl, "danger", msg);
        return;
      }
      showAlert(alertEl, "success", `Lead #${id} updated to “${data.lead.status}”.`, {
        autohideMs: 4000,
      });
      await load();
    } catch {
      showAlert(alertEl, "danger", "Network error — could not update lead.");
    } finally {
      btn.disabled = false;
    }
  });

  if (searchInput) {
    searchInput.addEventListener("input", () => {
      window.clearTimeout(debounceT);
      debounceT = window.setTimeout(load, 300);
    });
  }
  if (statusFilter) statusFilter.addEventListener("change", load);
  if (refreshBtn) refreshBtn.addEventListener("click", load);

  load();
}

document.addEventListener("DOMContentLoaded", () => {
  const page = document.body && document.body.dataset ? document.body.dataset.page : "";
  if (page === "home") initLeadForm();
  if (page === "dashboard") initDashboard();
});