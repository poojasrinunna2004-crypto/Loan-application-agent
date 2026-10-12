const form = document.querySelector("#application-form");
const customerSelect = document.querySelector("#customer");
const loanType = document.querySelector("#loan-type");
const amountInput = document.querySelector("#amount");
const termInput = document.querySelector("#term");
const purposeInput = document.querySelector("#purpose");
const createButton = document.querySelector("#create-draft");
const confirmButton = document.querySelector("#confirm-submit");
const startOverButton = document.querySelector("#start-over");
const feedback = document.querySelector("#form-feedback");
const draftBadge = document.querySelector("#draft-badge");
const reviewActions = document.querySelector("#review-actions");
const confirmationDialog = document.querySelector("#confirmation-dialog");
const dialogSummary = document.querySelector("#dialog-summary");
const dialogConfirmButton = document.querySelector("#dialog-confirm");

const customersById = new Map();
let currentDraft = null;
let busy = false;

function currency(value) {
    return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: 2,
    }).format(value);
}

function selectedCustomer() {
    return customersById.get(Number(customerSelect.value));
}

function setFeedback(message, kind = "success") {
    feedback.textContent = message;
    feedback.dataset.kind = kind;
}

function setBusy(value) {
    busy = value;
    createButton.disabled = value || Boolean(currentDraft) || customersById.size === 0;
    confirmButton.disabled = value || !currentDraft || currentDraft.status === "submitted";
    startOverButton.disabled = value;
}

function updatePreview() {
    const customer = selectedCustomer();
    document.querySelector("#review-customer").textContent = customer?.name ?? "Choose a sample customer";
    document.querySelector("#review-income").textContent = customer
        ? currency(customer.annual_income)
        : "-";
    document.querySelector("#review-type").textContent = loanType.value[0].toUpperCase() + loanType.value.slice(1);
    const amount = Number(amountInput.value);
    document.querySelector("#review-amount").textContent = amount > 0 ? currency(amount) : "-";
    const term = Number(termInput.value);
    document.querySelector("#review-term").textContent = term > 0 ? `${term} months` : "-";
    document.querySelector("#review-purpose").textContent = purposeInput.value.trim() || "-";
}

async function request(path, options = {}) {
    const response = await fetch(path, {
        ...options,
        headers: { "Content-Type": "application/json", ...options.headers },
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(body.detail || `Request failed (${response.status}).`);
    }
    return body;
}

async function loadCustomers() {
    try {
        const customers = await request("/customers");
        customerSelect.replaceChildren(new Option("Choose a sample customer", ""));
        for (const customer of customers) {
            customersById.set(customer.id, customer);
            customerSelect.add(new Option(`${customer.name} · sample ${customer.id}`, customer.id));
        }
        customerSelect.disabled = customers.length === 0;
        createButton.disabled = customers.length === 0;
        if (customers.length > 0) {
            customerSelect.value = String(customers[0].id);
            setFeedback("Connected to the mock service. Sample records are ready.");
        } else {
            setFeedback("No sample customers are available.", "error");
        }
        updatePreview();
    } catch (error) {
        customerSelect.replaceChildren(new Option("Could not load sample customers", ""));
        setFeedback(`${error.message} Refresh to try again.`, "error");
    }
}

function validateDraft() {
    if (!form.reportValidity()) return false;
    const amount = Number(amountInput.value);
    const term = Number(termInput.value);
    if (amount <= 0 || amount > 2_000_000) {
        setFeedback("Enter an amount greater than $0 and no more than $2,000,000.", "error");
        amountInput.focus();
        return false;
    }
    if (!Number.isInteger(term) || term < 1 || term > 480) {
        setFeedback("Choose a whole-number repayment period from 1 to 480 months.", "error");
        termInput.focus();
        return false;
    }
    return true;
}

function draftSummary() {
    const customer = selectedCustomer();
    return [
        `Draft #${currentDraft.id}`,
        `Customer: ${customer.name}`,
        `Loan: ${loanType.options[loanType.selectedIndex].text} · ${currency(currentDraft.amount)} · ${currentDraft.term_months} months`,
        `Purpose: ${currentDraft.purpose}`,
    ].join("\n");
}

form.addEventListener("input", updatePreview);
form.addEventListener("change", updatePreview);

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (busy || currentDraft || !validateDraft()) return;
    setBusy(true);
    setFeedback("Saving your draft...");
    const payload = {
        customer_id: Number(customerSelect.value),
        loan_type: loanType.value,
        amount: Number(amountInput.value),
        term_months: Number(termInput.value),
        purpose: purposeInput.value.trim(),
    };
    try {
        currentDraft = await request("/applications", {
            method: "POST",
            body: JSON.stringify(payload),
        });
        for (const control of form.elements) control.disabled = true;
        draftBadge.textContent = `Draft #${currentDraft.id} · Not submitted`;
        draftBadge.dataset.state = "draft";
        reviewActions.hidden = false;
        confirmButton.disabled = false;
        setFeedback("Draft saved. Review the summary before confirming.");
    } catch (error) {
        setFeedback(`Could not save the draft: ${error.message}`, "error");
    } finally {
        setBusy(false);
    }
});

confirmButton.addEventListener("click", () => {
    if (!currentDraft || busy) return;
    dialogSummary.textContent = draftSummary();
    if (typeof confirmationDialog.showModal === "function") {
        confirmationDialog.showModal();
    } else if (window.confirm(`${draftSummary()}\n\nSubmit to the local mock database?`)) {
        submitDraft();
    }
});

dialogConfirmButton.addEventListener("click", async () => {
    confirmationDialog.close();
    await submitDraft();
});

async function submitDraft() {
    if (!currentDraft || busy) return;
    setBusy(true);
    setFeedback("Submitting to the local mock database...");
    try {
        currentDraft = await request(`/applications/${currentDraft.id}/submit`, {
            method: "POST",
            body: JSON.stringify({ confirmation: true }),
        });
        draftBadge.textContent = `Application #${currentDraft.id} · Submitted`;
        draftBadge.dataset.state = "submitted";
        setFeedback("Mock application submitted successfully.");
    } catch (error) {
        setFeedback(`Could not submit the application: ${error.message}`, "error");
    } finally {
        setBusy(false);
    }
}

startOverButton.addEventListener("click", () => {
    if (currentDraft?.status === "draft" && !window.confirm(
        `Draft #${currentDraft.id} will remain unsubmitted. Start a new application?`,
    )) return;

    currentDraft = null;
    form.reset();
    for (const control of form.elements) control.disabled = false;
    if (customersById.size === 0) customerSelect.disabled = true;
    termInput.value = "36";
    reviewActions.hidden = true;
    draftBadge.textContent = "Not saved";
    draftBadge.dataset.state = "empty";
    setFeedback("Ready for a new mock application.");
    setBusy(false);
    updatePreview();
});

loadCustomers();
