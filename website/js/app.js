// ---- Login ----
// Einfacher clientseitiger Passwortschutz. WICHTIG: das ist keine
// echte Sicherheit (GitHub Pages liefert nur statische Dateien, es
// gibt keinen Server, der ein Passwort pruefen koennte) - jeder mit
// Entwicklertools kann den Hash und die Daten trotzdem sehen. Der
// Login haelt nur zufaellige Besucher/Suchmaschinen fern.

const AUTH_STORAGE_KEY = "comunio_authed_v1";
// SHA-256-Hash des Passworts (nicht das Passwort selbst im Code).
const AUTH_PASSWORD_HASH = "a121a65d2c98355cadc7e8d103b29f9a72799967b07d85b6eddb11b89a067a27";

async function sha256Hex(text) {
  const data = new TextEncoder().encode(text);
  const hashBuffer = await crypto.subtle.digest("SHA-256", data);
  return [...new Uint8Array(hashBuffer)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

function isAuthenticated() {
  return localStorage.getItem(AUTH_STORAGE_KEY) === "1";
}

function hideLoginOverlay() {
  document.getElementById("login-overlay")?.remove();
}

function setupLoginForm() {
  const form = document.getElementById("login-form");
  const input = document.getElementById("login-password");
  const error = document.getElementById("login-error");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const hash = await sha256Hex(input.value);
    if (hash === AUTH_PASSWORD_HASH) {
      localStorage.setItem(AUTH_STORAGE_KEY, "1");
      hideLoginOverlay();
      init();
    } else {
      error.hidden = false;
      input.value = "";
      input.focus();
    }
  });
}

function startApp() {
  if (isAuthenticated()) {
    hideLoginOverlay();
    init();
    return;
  }
  setupLoginForm();
}

// Spalten-Definition: Spielername/Verein/Position + Gesamtscore +
// die vier Kategorie-Scores (mit aufklappbaren KPI-Unterspalten) +
// Link zur letzten News. Fuer die Kategorie- und Watch-Tabellen wird
// dieselbe Struktur verwendet, nur die Felder im Spieler-Objekt
// unterscheiden sich (siehe buildColumns).

const KATEGORIE_HELP = {
  preis_leistung: "Preis/Leistung: Punkte, Punkte pro Spiel, Marktwert/Punkt, Form.",
  konstanz: "Konstanz: gespielte Spiele (letzte 5 & Saison), Standardabweichung der Punkte, Punkte pro Spiel.",
  leistungspotenzial: "Leistungspotenzial: Form, Gegnerstärke, gewichtete Punkte pro Spiel (jüngere Spiele zählen mehr), Trend.",
  mw_entwicklung: "MW-Entwicklung: Anzahl News, Transfernews, Stammplatznews, Trend, Form.",
};

const KATEGORIE_ORDER = ["preis_leistung", "konstanz", "leistungspotenzial", "mw_entwicklung"];

const KATEGORIE_META = {
  preis_leistung: { label: "Preis / Leistung", kpis: ["punkte", "punkte_pro_spiel", "mw_pro_punkt", "form"] },
  konstanz: { label: "Konstanz", kpis: ["gespielt", "anteil_spiele_saison", "std_abweichung", "punkte_pro_spiel"] },
  leistungspotenzial: { label: "Leistungspotenzial", kpis: ["form", "gegnerstaerke", "gewichtete_punkte_pro_spiel", "trend"] },
  mw_entwicklung: { label: "MW-Entwicklung", kpis: ["news_count_7d", "transfernews", "stammplatznews", "trend", "form"] },
};

const KPI_META = {
  punkte: { label: "Punkte (Saison)", help: "Gesamtpunkte in dieser Saison." },
  punkte_pro_spiel: { label: "Punkte/Spiel", help: "Durchschnittliche Punkte pro gespieltem Spiel (0, wenn weniger als 5 Spiele absolviert wurden)." },
  gewichtete_punkte_pro_spiel: { label: "Gew. Punkte/Spiel", help: "Punkte pro Spiel, wobei aktuellere Spiele stärker gewichtet werden als ältere." },
  mw_pro_punkt: { label: "MW/Punkt", help: "Marktwert geteilt durch erzielte Punkte – je niedriger, desto besser das Preis-Leistungs-Verhältnis." },
  marktwert: { label: "Marktwert", help: "Aktueller Marktwert des Spielers – ein niedrigerer Marktwert schneidet hier besser ab." },
  form: { label: "Form", help: "Durchschnittliche Punkte der letzten 5 gespielten Spiele." },
  gespielt: { label: "Gespielt (letzte 5)", help: "Anteil der letzten 5 Spiele, in denen der Spieler tatsächlich eingesetzt wurde." },
  anteil_spiele_saison: { label: "Anteil Spiele (Saison)", help: "Anteil aller bisherigen Saisonspiele, in denen der Spieler eingesetzt wurde." },
  std_abweichung: { label: "Standardabw.", help: "Schwankung der Punkte über die Saison – niedriger bedeutet konstantere Leistungen." },
  gegnerstaerke: { label: "Gegnerstärke", help: "Stärke der nächsten 4 Gegner – leichtere Gegner ergeben einen höheren Score." },
  trend: { label: "Marktwerttrend", help: "Entwicklung des Marktwerts – ein steigender Marktwert ergibt einen höheren Score." },
  news_count_7d: { label: "News (7 Tage)", help: "Anzahl der News-Meldungen zu diesem Spieler in den letzten 7 Tagen." },
  transfernews: { label: "Transfernews", help: "1, wenn in den letzten 7 Tagen über einen möglichen Wechsel berichtet wurde, sonst 0." },
  stammplatznews: { label: "Stammplatznews", help: "1, wenn in den letzten 7 Tagen über einen Stammplatz berichtet wurde, sonst 0." },
};

const SCALE_HELP = " Skala 0-10 (gerundet). Ampel: grün > 7, gelb 3-7, rot < 3.";

function scoreDisplay(score, ampel, decimals = 0) {
  if (score === null || score === undefined) return { display: "–", sort: null };
  const value = decimals > 0 ? score.toFixed(decimals) : Math.round(score);
  return {
    display: `<span class="ampel-badge ampel-${ampel}">&nbsp;</span> <span class="gesamtscore-value">${value} / 10</span>`,
    sort: score,
  };
}

function formatValue(value) {
  if (value === null || value === undefined || value === "") return "–";
  return value;
}

function buildColumns(gesamtField, gesamtAmpelField, katField, katAmpelField, kpiField, kpiAmpelField) {
  const columns = [
    {
      key: "name",
      label: "Spieler",
      sticky: "col-name",
      help: "Name des Spielers.",
      value: (p) => ({ display: `<div class="player-name">${p.name}</div>`, sort: p.name.toLowerCase() }),
    },
    {
      key: "verein",
      label: "Verein",
      help: "Aktueller Verein des Spielers.",
      value: (p) => ({ display: formatValue(p.verein), sort: (p.verein || "").toLowerCase() }),
    },
    {
      key: "position",
      label: "Position",
      help: "Spielposition: Torwart, Abwehr, Mittelfeld oder Sturm.",
      value: (p) => ({ display: formatValue(p.position), sort: (p.position || "").toLowerCase() }),
    },
    {
      key: "gesamtscore",
      label: "Gesamtscore",
      help: "Gewichteter Gesamtwert aus allen vier Kategorien." + SCALE_HELP,
      value: (p) => scoreDisplay(p[gesamtField], p[gesamtAmpelField], 1),
    },
  ];

  KATEGORIE_ORDER.forEach((katKey) => {
    const meta = KATEGORIE_META[katKey];
    columns.push({
      key: `kategorie__${katKey}`,
      label: meta.label,
      help: KATEGORIE_HELP[katKey] + SCALE_HELP,
      expandable: true,
      kategorieKey: katKey,
      value: (p) => (p[katField] ? scoreDisplay(p[katField][katKey], p[katAmpelField][katKey]) : { display: "–", sort: null }),
    });

    meta.kpis.forEach((kpiKey) => {
      const kpiMeta = KPI_META[kpiKey];
      columns.push({
        key: `kpi__${katKey}__${kpiKey}`,
        label: kpiMeta.label,
        help: kpiMeta.help + SCALE_HELP,
        sub: true,
        subOf: katKey,
        value: (p) => (p[kpiField] ? scoreDisplay(p[kpiField][kpiKey], p[kpiAmpelField][kpiKey]) : { display: "–", sort: null }),
      });
    });
  });

  columns.push({
    key: "news",
    label: "Letzte News",
    help: "Aktuellste Schlagzeile zu diesem Spieler von ligainsider.de, z.B. zu Verletzungen, Sperren oder Transfers.",
    value: (p) => {
      if (!p.detail.news_link) return { display: "–", sort: "" };
      return {
        display: `<a href="${p.detail.news_link}" target="_blank" rel="noopener">${p.detail.news_headline}</a>`,
        sort: (p.detail.news_headline || "").toLowerCase(),
      };
    },
  });

  return columns;
}

const COLUMNS = buildColumns("gesamtscore", "gesamtscore_ampel", "kategorie_scores", "kategorie_scores_ampel", "kpi_scores", "kpi_scores_ampel");
const WATCH_COLUMNS = buildColumns("watch_score", "watch_score_ampel", "watch_kategorie_scores", "watch_kategorie_scores_ampel", "watch_kpi_scores", "watch_kpi_scores_ampel");

const WATCH_MARKTWERT_MAX = 8_000_000;

const COLUMN_SETS = {
  watch: WATCH_COLUMNS,
  stars: COLUMNS,
  punktehamster: COLUMNS,
  schnaeppchen: COLUMNS,
};

const ROW_LIMITS = { watch: 15, stars: 15, punktehamster: 15, schnaeppchen: 15 };

const expandedState = {
  watch: new Set(),
  stars: new Set(),
  punktehamster: new Set(),
  schnaeppchen: new Set(),
};

function getColumns(section) {
  return COLUMN_SETS[section].filter((c) => !c.sub || expandedState[section].has(c.subOf));
}

const sortState = {}; // { sectionKey: { columnKey, direction } }
const filterState = { verein: "alle", position: "alle" };
let ALL_PLAYERS = [];

function buildTableHead(columns, section) {
  const cells = columns
    .map((c) => `<th class="${c.sticky || ""}${c.sub ? " col-sub" : ""}">${headerCell(c, section)}</th>`)
    .join("");
  return `<thead><tr>${cells}</tr></thead>`;
}

function headerCell(col, section) {
  const expandBtn = col.expandable
    ? `<button type="button" class="expand-btn" data-expand-key="${col.kategorieKey}" aria-label="Details ein-/ausblenden">${expandedState[section].has(col.kategorieKey) ? "−" : "+"}</button>`
    : "";
  return `
    <span class="th-inner${col.sub ? " th-sub" : ""}" data-section="${section}" data-key="${col.key}">
      <span class="th-label">${col.label}<span class="sort-indicator"></span></span>
      ${expandBtn}
      <button type="button" class="help-btn" data-help="${escapeAttr(col.help)}" aria-label="Erklärung">?</button>
    </span>`;
}

function escapeAttr(text) {
  return text.replace(/"/g, "&quot;");
}

function buildTableBody(columns, players) {
  const rows = players
    .map((p) => {
      const cells = columns
        .map((c) => {
          const { display } = c.value(p);
          const classes = [c.sticky, c.sub ? "col-sub" : null].filter(Boolean).join(" ");
          return `<td${classes ? ` class="${classes}"` : ""}>${display}</td>`;
        })
        .join("");
      return `<tr>${cells}</tr>`;
    })
    .join("");

  return `<tbody>${rows || `<tr><td colspan="${columns.length}" class="section-empty">Keine Spieler in dieser Kategorie.</td></tr>`}</tbody>`;
}

function sortPlayers(players, columns, columnKey, direction) {
  const col = columns.find((c) => c.key === columnKey);
  const sorted = [...players].sort((a, b) => {
    const av = col.value(a).sort;
    const bv = col.value(b).sort;

    if (av === null || av === undefined) return 1;
    if (bv === null || bv === undefined) return -1;

    let cmp;
    if (typeof av === "number" && typeof bv === "number") {
      cmp = av - bv;
    } else {
      cmp = String(av).localeCompare(String(bv), "de");
    }
    return direction === "asc" ? cmp : -cmp;
  });
  return sorted;
}

const SECTIONS = {
  watch: { data: [], defaultKey: "gesamtscore" },
  stars: { data: [], defaultKey: "gesamtscore" },
  punktehamster: { data: [], defaultKey: "gesamtscore" },
  schnaeppchen: { data: [], defaultKey: "gesamtscore" },
};

function renderTable(section) {
  const table = document.querySelector(`table.player-table[data-section="${section}"]`);
  const columns = getColumns(section);
  const state = sortState[section];

  if (!columns.find((c) => c.key === state.columnKey)) {
    state.columnKey = SECTIONS[section].defaultKey;
    state.direction = "desc";
  }

  const sorted = sortPlayers(SECTIONS[section].data, columns, state.columnKey, state.direction);
  const limited = sorted.slice(0, ROW_LIMITS[section]);

  table.innerHTML = buildTableHead(columns, section) + buildTableBody(columns, limited);

  const countEl = document.getElementById(`count-${section}`);
  if (countEl) {
    countEl.textContent = sorted.length > limited.length
      ? `· zeigt Top ${limited.length} von ${sorted.length}`
      : `· ${sorted.length} Spieler`;
  }

  const activeHeader = table.querySelector(`.th-inner[data-key="${state.columnKey}"] .sort-indicator`);
  if (activeHeader) {
    activeHeader.textContent = state.direction === "asc" ? " ▲" : " ▼";
  }

  table.querySelectorAll(".th-inner").forEach((el) => {
    el.addEventListener("click", (e) => {
      if (e.target.classList.contains("help-btn") || e.target.classList.contains("expand-btn")) return;
      const key = el.dataset.key;
      if (state.columnKey === key) {
        state.direction = state.direction === "asc" ? "desc" : "asc";
      } else {
        state.columnKey = key;
        state.direction = "asc";
      }
      renderTable(section);
    });
  });

  table.querySelectorAll(".expand-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const katKey = btn.dataset.expandKey;
      const set = expandedState[section];
      if (set.has(katKey)) {
        set.delete(katKey);
      } else {
        set.add(katKey);
      }
      renderTable(section);
    });
  });

  table.querySelectorAll(".help-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      showTooltip(btn);
    });
  });
}

function showTooltip(btn) {
  const tooltip = document.getElementById("help-tooltip");
  if (tooltip.dataset.for === btn.dataset.help && tooltip.classList.contains("visible")) {
    tooltip.classList.remove("visible");
    return;
  }
  tooltip.textContent = btn.dataset.help;
  tooltip.dataset.for = btn.dataset.help;

  const rect = btn.getBoundingClientRect();
  tooltip.style.top = `${rect.bottom + window.scrollY + 6}px`;
  tooltip.style.left = `${Math.max(8, rect.left + window.scrollX - 100)}px`;
  tooltip.classList.add("visible");
}

document.addEventListener("click", (e) => {
  if (!e.target.classList.contains("help-btn")) {
    document.getElementById("help-tooltip").classList.remove("visible");
  }
});

function setupTabs() {
  document.querySelectorAll("nav.tabs button").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("nav.tabs button").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(`view-${btn.dataset.view}`).classList.add("active");
    });
  });
}

function populateFilters(players) {
  const vereine = [...new Set(players.map((p) => p.verein))].sort((a, b) => a.localeCompare(b, "de"));
  const positionen = [...new Set(players.map((p) => p.position).filter(Boolean))].sort((a, b) => a.localeCompare(b, "de"));

  const vereinSelect = document.getElementById("filter-verein");
  vereine.forEach((v) => {
    const opt = document.createElement("option");
    opt.value = v;
    opt.textContent = v;
    vereinSelect.appendChild(opt);
  });

  const positionSelect = document.getElementById("filter-position");
  positionen.forEach((pos) => {
    const opt = document.createElement("option");
    opt.value = pos;
    opt.textContent = pos;
    positionSelect.appendChild(opt);
  });

  vereinSelect.addEventListener("change", (e) => {
    filterState.verein = e.target.value;
    applyFiltersAndRender();
  });

  positionSelect.addEventListener("change", (e) => {
    filterState.position = e.target.value;
    applyFiltersAndRender();
  });
}

function applyFiltersAndRender() {
  Object.keys(SECTIONS).forEach((section) => {
    SECTIONS[section].data = ALL_PLAYERS.filter((p) => {
      if (section === "watch") {
        if (p.marktwert === null || p.marktwert >= WATCH_MARKTWERT_MAX) return false;
      } else if (p.marktwert_sektion !== section) {
        return false;
      }
      if (filterState.verein !== "alle" && p.verein !== filterState.verein) return false;
      if (filterState.position !== "alle" && p.position !== filterState.position) return false;
      return true;
    });
    if (!sortState[section]) {
      sortState[section] = { columnKey: SECTIONS[section].defaultKey, direction: "desc" };
    }
    renderTable(section);
  });
}

// ---- Mein Team ----
// Die Auswahl wird nur lokal im Browser gespeichert (kein Server/Login
// vorhanden). Gespeichert wird nur die Spieler-ID + Startelf-Status;
// alle Spielerdaten selbst kommen weiterhin live aus ALL_PLAYERS.

const TEAM_STORAGE_KEY = "comunio_mein_team_v1";
const POSITION_ORDER = ["Torwart", "Abwehr", "Mittelfeld", "Sturm"];

function loadTeam() {
  try {
    const raw = localStorage.getItem(TEAM_STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function saveTeam() {
  localStorage.setItem(TEAM_STORAGE_KEY, JSON.stringify(MEIN_TEAM));
}

let MEIN_TEAM = loadTeam();

function isInTeam(spielerId) {
  return MEIN_TEAM.some((e) => e.spieler_id === spielerId);
}

function addToTeam(spielerId) {
  if (isInTeam(spielerId)) return;
  MEIN_TEAM.push({ spieler_id: spielerId, startelf: false });
  saveTeam();
  renderTeam();
}

function removeFromTeam(spielerId) {
  MEIN_TEAM = MEIN_TEAM.filter((e) => e.spieler_id !== spielerId);
  saveTeam();
  renderTeam();
}

// Erlaubte Formationen fuer die Startelf (Abwehr-Mittelfeld-Sturm,
// jeweils + 1 Torwart = 11): 3-5-2, 3-4-3, 4-3-3, 4-4-2, 4-5-1. Der
// Nutzer waehlt eines dieser Systeme explizit aus (Dropdown); dieses
// System ist dann fuer die Startelf-Zusammenstellung massgebend.
const STARTELF_SYSTEME = [
  { abwehr: 3, mittelfeld: 5, sturm: 2 },
  { abwehr: 3, mittelfeld: 4, sturm: 3 },
  { abwehr: 4, mittelfeld: 3, sturm: 3 },
  { abwehr: 4, mittelfeld: 4, sturm: 2 },
  { abwehr: 4, mittelfeld: 5, sturm: 1 },
];

const SYSTEM_STORAGE_KEY = "comunio_startelf_system_v1";
const POSITION_TO_SYSTEM_KEY = { Abwehr: "abwehr", Mittelfeld: "mittelfeld", Sturm: "sturm" };

function systemLabel(s) {
  return `${s.abwehr}-${s.mittelfeld}-${s.sturm}`;
}

function systemByLabel(label) {
  return STARTELF_SYSTEME.find((s) => systemLabel(s) === label) || STARTELF_SYSTEME.find((s) => systemLabel(s) === "4-4-2");
}

function loadSelectedSystem() {
  try {
    const raw = localStorage.getItem(SYSTEM_STORAGE_KEY);
    if (raw && STARTELF_SYSTEME.some((s) => systemLabel(s) === raw)) return raw;
  } catch {
    // ignore, fall through to default
  }
  return "4-4-2";
}

function saveSelectedSystem() {
  localStorage.setItem(SYSTEM_STORAGE_KEY, SELECTED_SYSTEM);
}

let SELECTED_SYSTEM = loadSelectedSystem();

function positionLimit(position) {
  if (position === "Torwart") return 1;
  const system = systemByLabel(SELECTED_SYSTEM);
  return system[POSITION_TO_SYSTEM_KEY[position]];
}

const STARTELF_FEHLERMELDUNG = "Max. Anzahl an Spielern erreicht. Entferne zunächst einen Spieler.";

function countStartelfByPosition(entries) {
  const counts = { Torwart: 0, Abwehr: 0, Mittelfeld: 0, Sturm: 0 };
  entries.forEach((e) => {
    if (e.startelf && counts[e.player.position] !== undefined) {
      counts[e.player.position] += 1;
    }
  });
  return counts;
}

function canAddToStartelf(entries, position) {
  if (entries.filter((e) => e.startelf).length >= 11) return false;
  const counts = countStartelfByPosition(entries);
  return counts[position] + 1 <= positionLimit(position);
}

// Wird beim Wechsel des Systems (oder beim Laden) aufgerufen: entfernt
// je Position ueberzaehlige Spieler aus der Startelf (auf die
// Ersatzbank), beginnend mit den Spielern mit den wenigsten
// Gesamtpunkten, bis die Anzahl zum neuen System passt.
function enforceSystemLimits() {
  const entries = currentTeamEntries();

  POSITION_ORDER.forEach((position) => {
    const limit = positionLimit(position);
    const startelfOfPosition = entries.filter((e) => e.startelf && e.player.position === position);
    if (startelfOfPosition.length <= limit) return;

    const sortedByPunkteAsc = [...startelfOfPosition].sort(
      (a, b) => (Number(a.player.detail.punkte_saison) || 0) - (Number(b.player.detail.punkte_saison) || 0)
    );
    const excess = sortedByPunkteAsc.slice(0, sortedByPunkteAsc.length - limit);
    excess.forEach((e) => {
      const entry = MEIN_TEAM.find((m) => m.spieler_id === e.spieler_id);
      if (entry) entry.startelf = false;
    });
  });

  saveTeam();
}

function showTeamError(message) {
  const banner = document.getElementById("team-error-banner");
  const text = document.getElementById("team-error-text");
  if (!banner || !text) return;
  text.textContent = message;
  banner.hidden = false;
}

function hideTeamError() {
  const banner = document.getElementById("team-error-banner");
  if (banner) banner.hidden = true;
}

function setupTeamErrorBanner() {
  document.querySelector(".team-error-close")?.addEventListener("click", hideTeamError);
}

function currentTeamEntries() {
  return MEIN_TEAM
    .map((e) => ({ ...e, player: ALL_PLAYERS.find((p) => p.spieler_id === e.spieler_id) }))
    .filter((e) => e.player);
}

function syncSystemSelect() {
  const select = document.getElementById("team-system-select");
  if (select && select.value !== SELECTED_SYSTEM) select.value = SELECTED_SYSTEM;
}

function setupSystemSelect() {
  const select = document.getElementById("team-system-select");
  if (!select) return;
  select.value = SELECTED_SYSTEM;
  select.addEventListener("change", () => {
    SELECTED_SYSTEM = select.value;
    saveSelectedSystem();
    enforceSystemLimits();
    hideTeamError();
    renderTeam();
  });
}

const PITCH_ROWS = [
  { position: "Sturm", key: "sturm" },
  { position: "Mittelfeld", key: "mittelfeld" },
  { position: "Abwehr", key: "abwehr" },
  { position: "Torwart", key: null },
];

function pitchTile(player) {
  return `
    <div class="pitch-tile${player ? "" : " pitch-tile-empty"}">
      <span class="pitch-tile-icon">🧑</span>
      <span class="pitch-tile-name">${player ? player.name : ""}</span>
    </div>`;
}

function renderPitch() {
  const pitch = document.getElementById("team-pitch");
  if (!pitch) return;

  const system = systemByLabel(SELECTED_SYSTEM);
  const startelf = currentTeamEntries().filter((e) => e.startelf);

  pitch.innerHTML = PITCH_ROWS.map(({ position, key }) => {
    const count = key ? system[key] : 1;
    const players = teamGroupSorted(startelf.filter((e) => e.player.position === position)).map((e) => e.player);
    const tiles = Array.from({ length: count }, (_, i) => pitchTile(players[i] || null)).join("");
    return `<div class="pitch-row pitch-row-${position.toLowerCase()}">${tiles}</div>`;
  }).join("");
}

function setStartelf(spielerId, value) {
  const entry = MEIN_TEAM.find((e) => e.spieler_id === spielerId);
  if (!entry) return;

  if (value) {
    const player = ALL_PLAYERS.find((p) => p.spieler_id === spielerId);
    if (!player || !canAddToStartelf(currentTeamEntries(), player.position)) {
      showTeamError(STARTELF_FEHLERMELDUNG);
      return;
    }
  }

  hideTeamError();
  entry.startelf = value;
  saveTeam();
  renderTeam();
}

function formatEuro(value) {
  if (value === null || value === undefined) return "–";
  return `${new Intl.NumberFormat("de-DE").format(value)} €`;
}

// Comunio liefert Dezimalwerte mit Komma (z.B. "2,86") - Number()
// wuerde das als NaN interpretieren, daher erst in Punkt umwandeln.
function parseGermanFloat(value) {
  if (value === null || value === undefined || value === "") return null;
  const num = Number(String(value).trim().replace(",", "."));
  return Number.isFinite(num) ? num : null;
}

function formatPunkteProSpiel(value) {
  const num = parseGermanFloat(value);
  return num === null ? "–" : num.toFixed(2);
}

function setupTeamSearch() {
  const input = document.getElementById("team-search-input");
  const results = document.getElementById("team-search-results");

  function closeResults() {
    results.innerHTML = "";
    results.classList.remove("visible");
  }

  input.addEventListener("input", () => {
    const query = input.value.trim().toLowerCase();
    if (query.length < 2) {
      closeResults();
      return;
    }

    const matches = ALL_PLAYERS.filter((p) => p.name.toLowerCase().includes(query)).slice(0, 8);

    if (matches.length === 0) {
      results.innerHTML = `<div class="search-empty">Keine Spieler gefunden.</div>`;
    } else {
      results.innerHTML = matches
        .map((p) => {
          const already = isInTeam(p.spieler_id);
          return `
            <button type="button" class="search-result${already ? " already-added" : ""}" data-id="${p.spieler_id}" ${already ? "disabled" : ""}>
              <span class="search-result-name">${p.name}</span>
              <span class="search-result-meta">${formatValue(p.verein)} · ${formatValue(p.position)}</span>
              ${already ? '<span class="search-result-flag">bereits im Team</span>' : ""}
            </button>`;
        })
        .join("");
    }
    results.classList.add("visible");
  });

  results.addEventListener("click", (e) => {
    const btn = e.target.closest(".search-result");
    if (!btn || btn.disabled) return;
    addToTeam(btn.dataset.id);
    input.value = "";
    closeResults();
  });

  document.addEventListener("click", (e) => {
    if (e.target !== input && !results.contains(e.target)) {
      closeResults();
    }
  });
}

function teamGroupSorted(entries) {
  return [...entries].sort((a, b) => {
    const posDiff = POSITION_ORDER.indexOf(a.player.position) - POSITION_ORDER.indexOf(b.player.position);
    if (posDiff !== 0) return posDiff;
    return a.player.name.localeCompare(b.player.name, "de");
  });
}

function teamDividerRow(label, key, entries) {
  const punkteSum = entries.reduce((sum, e) => sum + (Number(e.player.detail.punkte_saison) || 0), 0);
  const marktwertSum = entries.reduce((sum, e) => sum + (e.player.marktwert || 0), 0);
  const ppsSum = entries.reduce((sum, e) => sum + (parseGermanFloat(e.player.detail.punkte_pro_spiel) || 0), 0);

  return `
    <tr class="team-divider-row team-divider-${key}">
      <td class="team-divider-title">${label} <span class="team-divider-count">(${entries.length})</span></td>
      <td></td>
      <td></td>
      <td class="team-divider-value">${entries.length ? punkteSum : "–"}</td>
      <td class="team-divider-value">${entries.length ? ppsSum.toFixed(2) : "–"}</td>
      <td class="team-divider-value">${entries.length ? formatEuro(marktwertSum) : "–"}</td>
      <td></td>
    </tr>`;
}

function teamPlayerRow(entry) {
  const p = entry.player;
  const punkte = formatValue(p.detail.punkte_saison);
  const pps = formatPunkteProSpiel(p.detail.punkte_pro_spiel);
  return `
    <tr class="team-row-tr${entry.startelf ? " is-startelf" : ""}">
      <td><div class="player-name">${p.name}</div></td>
      <td>${formatValue(p.verein)}</td>
      <td>${formatValue(p.position)}</td>
      <td>${punkte}</td>
      <td>${pps}</td>
      <td>${formatEuro(p.marktwert)}</td>
      <td class="team-actions-cell">
        <button type="button" class="team-action" data-action="add-startelf" data-id="${p.spieler_id}" ${entry.startelf ? "disabled" : ""} title="Zur Startelf hinzufügen">+11</button>
        <button type="button" class="team-action" data-action="remove-startelf" data-id="${p.spieler_id}" ${!entry.startelf ? "disabled" : ""} title="Aus Startelf entfernen">-11</button>
        <button type="button" class="team-action team-action-remove" data-action="remove" data-id="${p.spieler_id}" title="Aus Liste entfernen">-</button>
      </td>
    </tr>`;
}

function renderTeam() {
  const tbody = document.getElementById("team-table-body");
  if (!tbody) return;

  syncSystemSelect();
  renderPitch();

  const entries = currentTeamEntries();

  if (entries.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="section-empty">Noch keine Spieler im Team. Nutze die Suche oben, um Spieler hinzuzufügen.</td></tr>`;
    return;
  }

  const startelf = teamGroupSorted(entries.filter((e) => e.startelf));
  const bank = teamGroupSorted(entries.filter((e) => !e.startelf));

  tbody.innerHTML =
    teamDividerRow("Startelf", "startelf", startelf) +
    (startelf.length ? startelf.map(teamPlayerRow).join("") : `<tr><td colspan="7" class="team-empty-row">Noch keine Spieler in der Startelf.</td></tr>`) +
    teamDividerRow("Ersatzbank", "bank", bank) +
    (bank.length ? bank.map(teamPlayerRow).join("") : `<tr><td colspan="7" class="team-empty-row">Keine Spieler auf der Ersatzbank.</td></tr>`);

  tbody.querySelectorAll(".team-action").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.dataset.id;
      const action = btn.dataset.action;
      if (action === "add-startelf") setStartelf(id, true);
      if (action === "remove-startelf") setStartelf(id, false);
      if (action === "remove") removeFromTeam(id);
    });
  });
}

// ---- Kaderoptimierung ----
// Schlaegt je Position bis zu 5 Spieler aus der gewaehlten Kategorie
// vor, die unter 90% des Kontostands kosten und (noch) nicht im
// eigenen Team stehen - sortiert nach dem zur Kategorie passenden
// Gesamtscore (Players to Watch nutzt den separaten Watch-Score).

function kaderoptScoreField(kategorie) {
  return kategorie === "watch" ? "watch_score" : "gesamtscore";
}

function kaderoptMatchesKategorie(player, kategorie) {
  if (kategorie === "watch") {
    return player.marktwert !== null && player.marktwert < WATCH_MARKTWERT_MAX && player.watch_score !== null;
  }
  return player.marktwert_sektion === kategorie && player.gesamtscore !== null;
}

function kaderoptSuggestions(position, kategorie, budgetLimit) {
  const scoreField = kaderoptScoreField(kategorie);
  return ALL_PLAYERS
    .filter((p) => p.position === position)
    .filter((p) => kaderoptMatchesKategorie(p, kategorie))
    .filter((p) => p.marktwert !== null && p.marktwert < budgetLimit)
    .filter((p) => !isInTeam(p.spieler_id))
    .sort((a, b) => (b[scoreField] ?? -Infinity) - (a[scoreField] ?? -Infinity))
    .slice(0, 5);
}

function kaderoptDividerRow(position, count) {
  return `
    <tr class="team-divider-row">
      <td class="team-divider-title" colspan="8">${position} <span class="team-divider-count">(${count} Vorschläge)</span></td>
    </tr>`;
}

function kaderoptPlayerRow(p, scoreField) {
  const score = p[scoreField];
  return `
    <tr class="team-row-tr">
      <td><div class="player-name">${p.name}</div></td>
      <td>${formatValue(p.verein)}</td>
      <td>${formatValue(p.position)}</td>
      <td>${formatEuro(p.marktwert)}</td>
      <td>${score !== null && score !== undefined ? score.toFixed(1) : "–"}</td>
      <td>${formatValue(p.detail.punkte_saison)}</td>
      <td>${formatPunkteProSpiel(p.detail.punkte_pro_spiel)}</td>
      <td>
        <button type="button" class="team-action kaderopt-add-btn" data-id="${p.spieler_id}" title="Zum Team hinzufügen (Ersatzbank)">Hinzufügen</button>
      </td>
    </tr>`;
}

function runKaderoptimierung() {
  const resultsEl = document.getElementById("kaderopt-results");
  const kontostandRaw = Number(document.getElementById("kaderopt-kontostand").value);
  const kontostand = Number.isFinite(kontostandRaw) && kontostandRaw > 0 ? kontostandRaw : 0;

  if (!kontostand) {
    resultsEl.innerHTML = `<div class="section-empty">Bitte gib zuerst deinen Kontostand ein.</div>`;
    return;
  }

  const budgetLimit = kontostand * 0.9;
  let bodyHtml = "";
  let anyPosition = false;

  document.querySelectorAll(".kaderopt-position-row").forEach((row) => {
    const position = row.dataset.position;
    const anzahl = Number(row.querySelector(".kaderopt-anzahl").value);
    if (!anzahl || anzahl <= 0) return;

    anyPosition = true;
    const kategorie = row.querySelector(".kaderopt-kategorie").value;
    const scoreField = kaderoptScoreField(kategorie);
    const suggestions = kaderoptSuggestions(position, kategorie, budgetLimit);

    bodyHtml += kaderoptDividerRow(position, suggestions.length);
    bodyHtml += suggestions.length
      ? suggestions.map((p) => kaderoptPlayerRow(p, scoreField)).join("")
      : `<tr><td colspan="8" class="team-empty-row">Keine passenden Spieler gefunden.</td></tr>`;
  });

  if (!anyPosition) {
    resultsEl.innerHTML = `<div class="section-empty">Gib bei mindestens einer Position eine Anzahl größer 0 ein.</div>`;
    return;
  }

  resultsEl.innerHTML = `
    <div class="table-scroll">
      <table class="player-table team-table">
        <thead>
          <tr>
            <th>Spieler</th>
            <th>Verein</th>
            <th>Position</th>
            <th>Marktwert</th>
            <th>Gesamtscore</th>
            <th>Punkte</th>
            <th>Punkte/Spiel</th>
            <th>Aktion</th>
          </tr>
        </thead>
        <tbody>${bodyHtml}</tbody>
      </table>
    </div>`;

  resultsEl.querySelectorAll(".kaderopt-add-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      addToTeam(btn.dataset.id);
      btn.textContent = "Hinzugefügt";
      btn.disabled = true;
    });
  });
}

function setupKaderoptimierung() {
  document.getElementById("kaderopt-submit")?.addEventListener("click", runKaderoptimierung);
}

async function init() {
  setupTabs();
  const response = await fetch("data/players.json");
  ALL_PLAYERS = await response.json();

  populateFilters(ALL_PLAYERS);
  applyFiltersAndRender();

  setupTeamSearch();
  setupTeamErrorBanner();
  setupSystemSelect();
  setupKaderoptimierung();
  enforceSystemLimits();
  renderTeam();
}

startApp();
