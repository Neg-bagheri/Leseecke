let books = [];
let selectedId = null;
let currentStatus = "";
let currentCategory = "";

const searchInput = document.getElementById("search");
const sortSelect = document.getElementById("sort");
const hero = document.getElementById("hero");
const shelf = document.getElementById("shelf");
const addDialog = document.getElementById("addDialog");
const borrowDialog = document.getElementById("borrowDialog");

const coverColors = [
  ["#7f7cf2", "#b3a6ff"],
  ["#e0576d", "#f7a1a8"],
  ["#3d8bd9", "#8ec5f5"],
  ["#e48a4a", "#f7c58e"],
  ["#4aa88a", "#9fdcc4"],
  ["#a45bc9", "#dca8f0"],
  ["#2b2d5c", "#6b6fb3"],
  ["#c9a227", "#f1d98a"],
];


// ---------- helpers ----------

// escape user text so nobody can inject html into the page
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function highlight(text, word) {
  text = escapeHtml(text);
  if (word === "") return text;
  const regex = new RegExp(word.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "gi");
  return text.replace(regex, (match) => `<mark>${match}</mark>`);
}

// "2026-10-24" -> "24.10.2026"
function formatDate(isoDate) {
  const parts = isoDate.split("-");
  return `${parts[2]}.${parts[1]}.${parts[0]}`;
}

function showToast(message, isError = false) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.classList.toggle("error", isError);
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2500);
}

async function sendRequest(url, method, data = null) {
  const options = { method: method, headers: { "Content-Type": "application/json" } };
  if (data !== null) {
    options.body = JSON.stringify(data);
  }

  const res = await fetch(url, options);
  const result = await res.json();

  if (!res.ok) {
    const message = typeof result.detail === "string" ? result.detail : "Bitte Eingaben prüfen";
    showToast(message, true);
    return null;
  }
  return result;
}

function getSelectedBook() {
  return books.find((book) => book.id === selectedId);
}


// ---------- show books on the page ----------

function coverHtml(book) {
  const colors = coverColors[book.id % coverColors.length];
  const lastName = book.author.split(" ").pop();
  return `
    <div class="cover" style="background: linear-gradient(160deg, ${colors[0]}, ${colors[1]})">
      <span class="cover-title">${escapeHtml(book.title)}</span>
      <span class="cover-author">${escapeHtml(lastName)}</span>
    </div>`;
}

function statusHtml(book) {
  if (book.available) {
    return `<span class="status">Status <strong class="green">Verfügbar</strong></span>`;
  }
  if (book.overdue) {
    return `<span class="status">Ausgeliehen von ${escapeHtml(book.borrower)}
      <strong class="red">Überfällig seit ${formatDate(book.due_date)}</strong></span>`;
  }
  return `<span class="status">Ausgeliehen von ${escapeHtml(book.borrower)}
    <strong class="orange">Fällig am ${formatDate(book.due_date)}</strong></span>`;
}

function showHero() {
  const book = getSelectedBook();

  if (!book) {
    hero.innerHTML = `<p class="empty">Keine Bücher gefunden.</p>`;
    return;
  }

  let actionButton = `<button class="btn btn-dark" onclick="openBorrowDialog()">Ausleihen</button>`;
  if (!book.available) {
    actionButton = `<button class="btn btn-dark" onclick="returnBook()">Zurückgeben</button>`;
  }

  hero.innerHTML = `
    <div>
      <h1>${escapeHtml(book.title)}</h1>
      <p class="author">${escapeHtml(book.author)}</p>
      <div class="tags">
        <span class="tag">${escapeHtml(book.category)}</span>
        <span class="tag">${book.year}</span>
      </div>
      <p class="desc">${escapeHtml(book.description || "Keine Beschreibung vorhanden.")}</p>
      <div class="hero-actions">
        ${statusHtml(book)}
        ${actionButton}
        <button class="btn btn-delete" onclick="deleteBook()">Löschen</button>
      </div>
    </div>
    ${coverHtml(book)}
  `;
}

function showShelf() {
  if (books.length === 0) {
    shelf.innerHTML = `<p class="empty">Keine Bücher gefunden.</p>`;
    return;
  }

  const word = searchInput.value.trim();
  let html = "";

  for (const book of books) {
    let dotClass = "";
    if (book.overdue) dotClass = "overdue";
    else if (!book.available) dotClass = "borrowed";

    html += `
      <div class="item ${book.id === selectedId ? "selected" : ""}" onclick="selectBook(${book.id})">
        ${coverHtml(book)}
        <p class="item-title">${highlight(book.title, word)}</p>
        <p class="item-author"><span class="dot ${dotClass}"></span>${highlight(book.author, word)}</p>
      </div>`;
  }

  shelf.innerHTML = html;
}

function selectBook(id) {
  selectedId = id;
  showHero();
  showShelf();
  hero.scrollIntoView({ behavior: "smooth" });
}


// ---------- load data from the server ----------

async function loadBooks() {
  const params = new URLSearchParams({
    q: searchInput.value.trim(),
    category: currentCategory,
    status: currentStatus,
    sort: sortSelect.value,
  });

  const res = await fetch("/api/books?" + params);
  books = await res.json();

  // if the selected book is not in the list anymore, select the first one
  if (!getSelectedBook()) {
    selectedId = books.length > 0 ? books[0].id : null;
  }

  document.getElementById("shelfTitle").textContent = `${currentCategory || "Alle Bücher"} (${books.length})`;
  showHero();
  showShelf();
}

async function loadStats() {
  const res = await fetch("/api/stats");
  const stats = await res.json();

  document.getElementById("nTotal").textContent = stats.total;
  document.getElementById("nAvailable").textContent = stats.available;
  document.getElementById("nBorrowed").textContent = stats.borrowed;
  document.getElementById("nOverdue").textContent = stats.overdue > 0 ? stats.overdue : "";
  document.getElementById("stats").textContent = `${stats.total} Bücher · ${stats.available} verfügbar`;
}

async function loadCategories() {
  const res = await fetch("/api/categories");
  const categories = await res.json();

  // the selected category can disappear after deleting its last book
  if (!categories.includes(currentCategory)) {
    currentCategory = "";
  }

  let navHtml = `<button onclick="filterCategory(this)" data-category="" class="${currentCategory === "" ? "active" : ""}">Alle</button>`;
  let listHtml = "";

  for (const category of categories) {
    const active = category === currentCategory ? "active" : "";
    navHtml += `<button onclick="filterCategory(this)" data-category="${escapeHtml(category)}" class="${active}">${escapeHtml(category)}</button>`;
    listHtml += `<option value="${escapeHtml(category)}">`;
  }

  document.getElementById("categoryNav").innerHTML = navHtml;
  document.getElementById("categoryList").innerHTML = listHtml;
}

async function refresh() {
  await loadCategories();
  loadBooks();
  loadStats();
}


// ---------- filters ----------

function filterStatus(button, status) {
  currentStatus = status;
  document.querySelectorAll("#statusNav button").forEach((b) => b.classList.remove("active"));
  button.classList.add("active");
  loadBooks();
}

function filterCategory(button) {
  currentCategory = button.dataset.category;
  document.querySelectorAll("#categoryNav button").forEach((b) => b.classList.remove("active"));
  button.classList.add("active");
  loadBooks();
}

searchInput.addEventListener("input", loadBooks);
sortSelect.addEventListener("change", loadBooks);


// ---------- actions ----------

function openAddDialog() {
  document.getElementById("addForm").reset();
  addDialog.showModal();
}

function openBorrowDialog() {
  const book = getSelectedBook();
  document.getElementById("borrowForm").reset();
  document.getElementById("borrowBookTitle").textContent = `„${book.title}" von ${book.author}`;
  borrowDialog.showModal();
}

function closeDialogs() {
  addDialog.close();
  borrowDialog.close();
}

document.getElementById("addForm").addEventListener("submit", async (event) => {
  event.preventDefault();

  const newBook = {
    title: document.getElementById("fTitle").value,
    author: document.getElementById("fAuthor").value,
    year: Number(document.getElementById("fYear").value),
    category: document.getElementById("fCategory").value,
    description: document.getElementById("fDescription").value,
  };

  const saved = await sendRequest("/api/books", "POST", newBook);
  if (saved) {
    closeDialogs();
    showToast(`„${saved.title}" hinzugefügt`);
    selectedId = saved.id;
    refresh();
  }
});

document.getElementById("borrowForm").addEventListener("submit", async (event) => {
  event.preventDefault();

  const data = {
    borrower: document.getElementById("fBorrower").value,
    days: Number(document.getElementById("fDays").value),
  };

  const book = await sendRequest(`/api/books/${selectedId}/borrow`, "POST", data);
  if (book) {
    closeDialogs();
    showToast(`Ausgeliehen bis ${formatDate(book.due_date)}`);
    refresh();
  }
});

async function returnBook() {
  const book = await sendRequest(`/api/books/${selectedId}/return`, "POST");
  if (book) {
    showToast(`„${book.title}" zurückgegeben`);
    refresh();
  }
}

async function deleteBook() {
  if (!confirm("Dieses Buch wirklich löschen?")) return;

  const result = await sendRequest(`/api/books/${selectedId}`, "DELETE");
  if (result) {
    showToast("Buch gelöscht");
    selectedId = null;
    refresh();
  }
}


refresh();
