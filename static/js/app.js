const FALLBACK_PRODUCTS = [
  { id: "mango", name: "Mango Achar", hindi: "आम का आचार", description: "Sun-dried raw mangoes pickled with mustard oil, fenugreek and hand-ground spices.", pricePerKg: 650, emoji: "🥭", tag: "Bestseller" },
  { id: "lemon", name: "Lemon Achar", hindi: "नींबू का आचार", description: "Tangy lemon pickle cured with rock salt, turmeric and ajwain.", pricePerKg: 550, emoji: "🍋", tag: "Classic" },
  { id: "garlic", name: "Garlic Achar", hindi: "लहसुन का आचार", description: "Whole garlic cloves roasted and folded into a fiery red masala base.", pricePerKg: 750, emoji: "🧄", tag: "Spicy" },
];

const grid = document.getElementById("productGrid");
const modal = document.getElementById("bookingModal");
const form = document.getElementById("bookingForm");
const toast = document.getElementById("toast");
const formError = document.getElementById("formError");
const pickleSelect = document.getElementById("pickleType");
const modalPickle = document.getElementById("modalPickle");
const confirmBtn = document.getElementById("confirmBtn");
const hamburger = document.getElementById("hamburger");
const navLinks = document.getElementById("navLinks");

let products = [];
let lastFocus = null;

document.getElementById("year").textContent = new Date().getFullYear();

hamburger.addEventListener("click", () => navLinks.classList.toggle("open"));
navLinks.addEventListener("click", (e) => { if (e.target.tagName === "A") navLinks.classList.remove("open"); });

function inr(n) {
  return "₹" + Number(n).toLocaleString("en-IN");
}

function renderProducts(list) {
  grid.innerHTML = list.map(p => `
    <article class="product-card">
      <span class="product-tag">${p.tag || "Premium"}</span>
      <div class="product-emoji">${p.emoji}</div>
      <h3>${p.name}</h3>
      <p class="product-hindi">${p.hindi || ""}</p>
      <p class="product-desc">${p.description}</p>
      <p class="product-price">${inr(p.pricePerKg)} <small>/ kg</small></p>
      <button class="btn btn-primary add-btn" data-id="${p.id}">Add to Booking</button>
    </article>`).join("");

  pickleSelect.innerHTML = list.map(p => `<option value="${p.id}">${p.name}</option>`).join("");
}

function openModal(productId) {
  lastFocus = document.activeElement;
  if (productId) {
    pickleSelect.value = productId;
    const p = products.find(x => x.id === productId);
    modalPickle.textContent = p ? `${p.emoji}  ${p.name} — ${inr(p.pricePerKg)}/kg` : "";
  } else {
    modalPickle.textContent = "";
  }
  formError.classList.remove("show");
  formError.textContent = "";
  modal.hidden = false;
  requestAnimationFrame(() => modal.classList.add("open"));
  document.body.style.overflow = "hidden";
  document.getElementById("customerName").focus();
}

function closeModal() {
  modal.classList.remove("open");
  document.body.style.overflow = "";
  setTimeout(() => { modal.hidden = true; if (lastFocus) lastFocus.focus(); }, 280);
}

grid.addEventListener("click", (e) => {
  const btn = e.target.closest(".add-btn");
  if (btn) openModal(btn.dataset.id);
});

document.getElementById("closeModal").addEventListener("click", closeModal);
modal.addEventListener("click", (e) => { if (e.target === modal) closeModal(); });
document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !modal.hidden) closeModal(); });

pickleSelect.addEventListener("change", () => {
  const p = products.find(x => x.id === pickleSelect.value);
  modalPickle.textContent = p ? `${p.emoji}  ${p.name} — ${inr(p.pricePerKg)}/kg` : "";
});

function showToast(msg) {
  toast.textContent = msg;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 4200);
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  formError.classList.remove("show");

  const payload = {
    customerName: form.customerName.value.trim(),
    phoneNumber: form.phoneNumber.value.trim(),
    pickleType: form.pickleType.value,
    quantityInGrams: Number(form.quantityInGrams.value),
    deliveryAddress: form.deliveryAddress.value.trim(),
  };

  confirmBtn.disabled = true;
  confirmBtn.textContent = "Confirming…";

  try {
    const res = await fetch("/api/bookings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    if (!res.ok || !data.ok) {
      const msg = data.errors ? Object.values(data.errors)[0] : "Something went wrong. Please try again.";
      formError.textContent = msg;
      formError.classList.add("show");
      return;
    }

    closeModal();
    const b = data.booking;
    showToast(`Order #${b.id} confirmed! ${b.quantityInGrams} g ${b.pickleName} — approx. ${inr(b.estimatedAmount)}. We'll call you shortly. 🫙`);
    form.reset();
    form.quantityInGrams.value = "500";
  } catch (err) {
    formError.textContent = "Network error — please check your connection and try again.";
    formError.classList.add("show");
  } finally {
    confirmBtn.disabled = false;
    confirmBtn.textContent = "Confirm Order";
  }
});

(async function init() {
  try {
    const res = await fetch("/api/products");
    products = res.ok ? await res.json() : FALLBACK_PRODUCTS;
  } catch {
    products = FALLBACK_PRODUCTS;
  }
  renderProducts(products);
})();
