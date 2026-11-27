"use strict";

const byId = (id) => document.getElementById(id);

const I18N_KEYS = ["workspace","home","threat","malware","assistant","operations","account","soc","title","loginTitle","loginSub","login","email","password","submit","choose","chooseSub","developer","mcpTools","mcpSub","registerLink"];
const I18N = {
fr:["ESPACE SÉCURISÉ","Accueil","Threat Intelligence","IA et malwares","Assistant et outils","Opérations et développement","Compte","CENTRE DES OPÉRATIONS DE SÉCURITÉ","Centre de cybersécurité","Connexion et compte","Compte sécurisé, sessions révocables et accès par rôle.","Connexion","Adresse e-mail","Mot de passe","Se connecter","Que souhaitez-vous ouvrir ?","Choisissez une catégorie pour accéder à ses outils et détails.","Centre développeur","Outils MCP disponibles","Outils enregistrés et limités par autorisation.","Pas encore de compte ? Créer un compte détaillé"],
en:["SECURE WORKSPACE","Home","Threat Intelligence","AI & Malware","Assistant & Tools","Operations & Developer","Account","SECURITY OPERATIONS CENTER","Cyber Defense Center","Sign in to your account","Secure account, revocable sessions and role-based access.","Sign in","Email address","Password","Sign in","What would you like to open?","Choose a category to access its tools and details.","Developer Center","Available MCP tools","Registered tools with scoped permissions.","New here? Create a detailed account"],
mg:["TOERANA VOARO","Fandraisana","Threat Intelligence","AI sy Malware","Assistant sy fitaovana","Operations sy Developer","Kaonty","FOIBE FITANTANANA NY FIAROVANA","Foibe fiarovana nomerika","Fidirana amin'ny kaonty","Kaonty voaaro, session azo foanana ary alalana araka ny andraikitra.","Hiditra","Adiresy mailaka","Tenimiafina","Hiditra","Inona no tianao hosokafana?","Safidio ny sokajy hahitana ny fitaovana sy antsipiriany.","Foibe ho an'ny développeur","Fitaovana MCP misy","Fitaovana voasoratra sy voafehin'ny alalana.","Mbola tsy manana kaonty? Hamorona kaonty feno"],
es:["ESPACIO SEGURO","Inicio","Inteligencia de amenazas","IA y malware","Asistente y herramientas","Operaciones y desarrollo","Cuenta","CENTRO DE OPERACIONES DE SEGURIDAD","Centro de ciberdefensa","Acceso a la cuenta","Cuenta segura, sesiones revocables y acceso por roles.","Iniciar sesión","Correo electrónico","Contraseña","Entrar","¿Qué deseas abrir?","Elige una categoría para acceder a sus herramientas y detalles.","Centro de desarrollo","Herramientas MCP disponibles","Herramientas registradas con permisos limitados.","¿No tienes cuenta? Crear una cuenta detallada"],
pt:["ESPAÇO SEGURO","Início","Inteligência de ameaças","IA e malware","Assistente e ferramentas","Operações e desenvolvimento","Conta","CENTRO DE OPERAÇÕES DE SEGURANÇA","Centro de ciberdefesa","Entrar na conta","Conta segura, sessões revogáveis e acesso por função.","Entrar","E-mail","Senha","Entrar","O que deseja abrir?","Escolha uma categoria para acessar ferramentas e detalhes.","Centro do desenvolvedor","Ferramentas MCP disponíveis","Ferramentas registradas com permissões limitadas.","Ainda não tem conta? Criar conta detalhada"],
de:["SICHERER ARBEITSBEREICH","Startseite","Bedrohungsanalyse","KI und Malware","Assistent und Tools","Betrieb und Entwicklung","Konto","SICHERHEITSZENTRUM","Cyber-Abwehrzentrum","Bei Ihrem Konto anmelden","Sicheres Konto, widerrufbare Sitzungen und rollenbasierter Zugriff.","Anmelden","E-Mail-Adresse","Passwort","Anmelden","Was möchten Sie öffnen?","Wählen Sie eine Kategorie für Werkzeuge und Details.","Developer Center","Verfügbare MCP-Tools","Registrierte Tools mit begrenzten Berechtigungen.","Noch kein Konto? Detailliertes Konto erstellen"],
it:["AREA DI LAVORO SICURA","Home","Threat Intelligence","IA e malware","Assistente e strumenti","Operazioni e sviluppo","Account","CENTRO OPERATIVO DI SICUREZZA","Centro di cyber difesa","Accedi al tuo account","Account protetto, sessioni revocabili e accesso basato sui ruoli.","Accedi","Indirizzo e-mail","Password","Accedi","Che cosa vuoi aprire?","Scegli una categoria per accedere a strumenti e dettagli.","Developer Center","Strumenti MCP disponibili","Strumenti registrati con autorizzazioni limitate.","Non hai un account? Crea un account dettagliato"],
ar:["مساحة عمل آمنة","الرئيسية","معلومات التهديدات","الذكاء الاصطناعي والبرمجيات الخبيثة","المساعد والأدوات","العمليات والتطوير","الحساب","مركز عمليات الأمن","مركز الدفاع السيبراني","تسجيل الدخول إلى الحساب","حساب آمن وجلسات قابلة للإلغاء وصلاحيات حسب الدور.","تسجيل الدخول","البريد الإلكتروني","كلمة المرور","دخول","ماذا تريد أن تفتح؟","اختر فئة للوصول إلى أدواتها وتفاصيلها.","مركز المطور","أدوات MCP المتاحة","أدوات مسجلة بصلاحيات محددة.","ليس لديك حساب؟ إنشاء حساب مفصل"],
zh:["安全工作区","首页","威胁情报","人工智能与恶意软件","助手与工具","运维与开发","账户","安全运营中心","网络防御中心","登录账户","安全账户、可撤销会话和基于角色的访问。","登录","电子邮箱","密码","登录","您想打开什么？","选择一个类别以访问其工具和详细信息。","开发者中心","可用的 MCP 工具","已注册且受权限限制的工具。","还没有账户？创建详细账户"],
ja:["セキュアワークスペース","ホーム","脅威インテリジェンス","AI とマルウェア","アシスタントとツール","運用と開発","アカウント","セキュリティオペレーションセンター","サイバー防御センター","アカウントにログイン","安全なアカウント、取り消し可能なセッション、役割ベースのアクセス。","ログイン","メールアドレス","パスワード","ログイン","何を開きますか？","カテゴリを選択してツールと詳細を表示します。","開発者センター","利用可能な MCP ツール","権限で制限された登録済みツール。","アカウントがありませんか？詳細登録"],
hi:["सुरक्षित कार्यक्षेत्र","होम","खतरा जानकारी","AI और मैलवेयर","सहायक और उपकरण","संचालन और विकास","खाता","सुरक्षा संचालन केंद्र","साइबर रक्षा केंद्र","अपने खाते में लॉग इन करें","सुरक्षित खाता, रद्द करने योग्य सत्र और भूमिका-आधारित पहुँच।","लॉग इन","ईमेल पता","पासवर्ड","साइन इन","आप क्या खोलना चाहते हैं?","उपकरण और विवरण देखने के लिए श्रेणी चुनें।","डेवलपर केंद्र","उपलब्ध MCP उपकरण","सीमित अनुमतियों वाले पंजीकृत उपकरण।","खाता नहीं है? विस्तृत खाता बनाएँ"],
ru:["ЗАЩИЩЁННОЕ ПРОСТРАНСТВО","Главная","Аналитика угроз","ИИ и вредоносное ПО","Ассистент и инструменты","Операции и разработка","Аккаунт","ЦЕНТР ИНФОРМАЦИОННОЙ БЕЗОПАСНОСТИ","Центр киберзащиты","Вход в аккаунт","Защищённый аккаунт, отзыв сессий и доступ по ролям.","Войти","Электронная почта","Пароль","Войти","Что вы хотите открыть?","Выберите категорию, чтобы открыть инструменты и сведения.","Центр разработчика","Доступные инструменты MCP","Зарегистрированные инструменты с ограниченными правами.","Нет аккаунта? Создать подробную учётную запись"]
};
function translate(key){const i=I18N_KEYS.indexOf(key);const lang=document.documentElement.lang;return i>=0?(I18N[lang]||I18N.fr)[i]:key}
function applyLocale(locale){const lang=I18N[locale]?locale:"fr";const values=I18N[lang];document.documentElement.lang=lang;document.documentElement.dir=lang==="ar"?"rtl":"ltr";document.querySelectorAll("[data-i18n]").forEach(el=>{const i=I18N_KEYS.indexOf(el.dataset.i18n);if(i>=0)el.textContent=values[i]});const select=byId("language-select");if(select&&select.value!==lang)select.value=lang;try{localStorage.setItem("nanou-locale",lang)}catch{/* private mode */}}
let csrfToken = "";
let currentUser = null;
let configuredMalwareModel = null;
let adminUsersCache = [];
let adminAuditCache = [];
let currentCategory = "home";
const loadedCategories = new Set();
let googleCredentialAction = "signin";

const canAnalyze = () => Boolean(currentUser && ["admin", "analyst"].includes(currentUser.role));

const ROLE_WORKSPACES = {
  admin: {
    title: "Administrator control room",
    summary: "Fitantanana ny kaonty, fanaraha-maso ny asa ary fidirana amin'ny fitaovana fiarovana.",
    badge: "ADMIN",
    guidance: "Ny fanovana andraikitra sy ny fankatoavana mpampiasa dia hita ao amin'ny Kaonty sy fidirana. Voarakitra ao amin'ny audit log ny hetsika mifandraika amin'izany.",
    permissions: [
      ["Governance", "Manaiky na manafoana kaonty, manendry rôles ary mijery ny audit log."],
      ["Threat intelligence", "Mikaroka CVE ao amin'ny NVD sy mijery ny CISA KEV."],
      ["Malware laboratory", "Manampy metadata ary mampiasa feature analysis rehefa misy modely voamarina."]
    ],
  },
  analyst: {
    title: "Analyst operations",
    summary: "Fikarohana threat intelligence sy fanomanana angona ho an'ny fanadihadiana.",
    badge: "ANALYST",
    guidance: "Afaka manomana CSV feature voafetra sy mampiditra metadata ianao. Tsy afaka mitantana kaonty na mijery ny audit log Admin.",
    permissions: [
      ["Threat intelligence", "Mikaroka CVE sy mandinika ny lisitra CISA KEV."],
      ["Feature analysis", "Manamarina CSV feature iray (1 MiB max) ary manao inference raha misy modely voamarina."],
      ["Malware metadata", "Manampy SHA-256, label ary loharano; tsy mandray APK na executable."]
    ],
  },
  viewer: {
    title: "Read-only security workspace",
    summary: "Fijerena vaovao sy metadata amin'ny fomba read-only.",
    badge: "VIEWER",
    guidance: "Read-only ny fidiranao. Tsy misy fanovana metadata, inference, fitantanana kaonty na fidirana amin'ny audit log.",
    permissions: [
      ["Threat intelligence", "Mijery CVE/NVD sy ny CISA KEV."],
      ["Malware metadata", "Mijery ny hashes sy labels efa voatahiry."],
      ["Restricted actions", "Tsy afaka mampiditra metadata, manomana features na mitantana kaonty."]
    ],
  },
};

function updateRoleVisibility() {
  const activeRoles = currentUser ? [currentUser.role, "authenticated"] : ["public"];
  document.querySelectorAll("[data-role-visibility]").forEach((element) => {
    const allowedRoles = element.dataset.roleVisibility.split(",").map((role) => role.trim());
    const allowed = allowedRoles.some((role) => activeRoles.includes(role));
    element.dataset.roleAllowed = String(allowed);
    element.hidden = !allowed;
  });
  document.querySelectorAll(".nav-group").forEach((group) => {
    const links = Array.from(group.querySelectorAll(".nav-link"));
    if (links.length) group.hidden = !links.some((link) => !link.hidden);
  });
  if (currentUser) showCategory(currentCategory);
}

const CATEGORY_TITLES = {
  home: "Accueil",
  threat: "Renseignement sur les menaces",
  malware: "Analyse IA et malwares",
  assistant: "Assistant et outils",
  operations: "Opérations et développement",
  account: "Compte et gouvernance",
};

function showCategory(category) {
  if (!currentUser) return;
  if (!Object.hasOwn(CATEGORY_TITLES, category)) category = "home";
  if (category === "operations" && !canAnalyze()) category = "home";
  currentCategory = category;
  const home = byId("category-home");
  home.hidden = category !== "home";
  const backbar = byId("category-backbar");
  backbar.hidden = category === "home";
  byId("category-current-title").textContent = CATEGORY_TITLES[category] || "";

  document.querySelectorAll("[data-category-view]").forEach((element) => {
    const roleAllowed = element.dataset.roleAllowed !== "false";
    element.hidden = element.dataset.categoryView !== category || !roleAllowed;
  });
  document.querySelectorAll("[data-category-target]").forEach((link) => {
    const active = link.dataset.categoryTarget === category;
    link.classList.toggle("active", active);
    if (active) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
  window.dispatchEvent(new CustomEvent("nanou:category-changed", {
    detail: { category },
  }));
  loadCategoryData(category);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

async function loadCategoryData(category) {
  if (loadedCategories.has(category)) return;
  loadedCategories.add(category);
  if (category === "home") {
    await loadHealth();
  } else if (category === "threat") {
    await Promise.all([loadHealth(), loadKev()]);
  } else if (category === "malware") {
    await Promise.all([loadMalwareModelStatus(), loadMetadata()]);
  } else if (category === "assistant") {
    await loadTools();
  } else if (category === "account" && currentUser?.role === "admin") {
    await loadAdminConsole();
  }
}

function openRegistrationDetails(event) {
  event.preventDefault();
  byId("login-form").hidden = true;
  byId("register-form").hidden = false;
  byId("google-auth-block").hidden = true;
  byId("register-open-link").hidden = true;
  byId("auth-message").textContent = "Complétez votre inscription. Le rôle initial est Viewer et le compte doit être approuvé par un administrateur.";
}

function closeRegistrationDetails(event) {
  event.preventDefault();
  byId("register-form").hidden = true;
  byId("login-form").hidden = false;
  byId("google-auth-block").hidden = false;
  byId("register-open-link").hidden = false;
}

async function handleGoogleCredential(response) {
  const credential = response?.credential;
  if (typeof credential !== "string" || credential.length < 20 || credential.length > 16384) {
    byId("google-auth-status").textContent = "Identifiant Google non reçu. Veuillez réessayer.";
    return;
  }
  const linking = googleCredentialAction === "link";
  const status = linking ? byId("google-link-status") : byId("google-auth-status");
  setMessage(status, linking ? "Mampifandray ny Google account…" : "Manamarina ny kaonty Google…");
  try {
    const result = await apiRequest(linking ? "/api/auth/google/link" : "/api/auth/google", {
      method: "POST",
      body: { credential },
    });
    if (linking) {
      googleCredentialAction = "signin";
      byId("google-link-status").textContent = "Google account tafifandray soa aman-tsara.";
      await loadGoogleLinkStatus();
      return;
    }
    if (result.pending_approval) {
      byId("auth-message").textContent = result.message || "Compte Google reçu. En attente de l'approbation de l'administrateur.";
      byId("google-auth-status").textContent = "Demande reçue ; la connexion sera disponible après approbation de l’administrateur.";
      return;
    }
    await loadAuth();
  } catch (error) {
    googleCredentialAction = "signin";
    const status = linking ? byId("google-link-status") : byId("google-auth-status");
    status.textContent = error.message || "Tsy nahomby ny fanamarinana Google.";
  }
}

async function loadGoogleLinkStatus() {
  if (!currentUser) return;
  const slot = byId("google-link-button-slot");
  try {
    const status = await apiRequest("/api/auth/google/status");
    if (!status.available) {
      slot.hidden = true;
      byId("google-link-status").textContent = "Mbola tsy napetraka ny Google identity migration ao amin'ny database.";
      return;
    }
    if (status.linked) {
      slot.hidden = true;
      byId("google-link-status").textContent = "Google account efa tafifandray.";
      return;
    }
    slot.hidden = false;
    if (window.google?.accounts?.id && slot.dataset.rendered !== "true") {
      window.google.accounts.id.renderButton(slot, {
        type: "standard",
        theme: "filled_black",
        size: "large",
        text: "continue_with",
        shape: "rectangular",
        width: 250,
        click_listener: () => { googleCredentialAction = "link"; },
      });
      slot.dataset.rendered = "true";
    }
    byId("google-link-status").textContent = "Ampifandraiso ny Google mitovy amin'ny email an'ity kaonty ity.";
  } catch (error) {
    byId("google-link-status").textContent = error.message || "Tsy azo hamarinina ny Google link.";
  }
}

async function loadAuthProviders() {
  const slot = byId("google-button-slot");
  try {
    const providers = await apiRequest("/api/auth/providers");
    const google = providers?.google;
    if (!google?.enabled || typeof google.client_id !== "string") {
      byId("google-auth-status").textContent = google?.reason === "identity_storage_migration_required"
        ? "Google Sign-In miandry ny database migration; mbola miasa ny fidirana amin'ny email sy tenimiafina."
        : "Google Sign-In mbola tsy voa-configurer: mila OAuth Web Client ID sy authorized origin ao amin'ny Google Cloud.";
      if (currentUser) loadGoogleLinkStatus();
      return;
    }
    const renderGoogleButton = () => {
      if (!window.google?.accounts?.id) {
        byId("google-auth-status").textContent = "Le service Google Identity Services n’est pas chargé.";
        return;
      }
      window.google.accounts.id.initialize({
        client_id: google.client_id,
        callback: handleGoogleCredential,
        auto_select: false,
        cancel_on_tap_outside: true,
      });
      googleCredentialAction = "signin";
      window.google.accounts.id.renderButton(slot, {
        type: "standard",
        theme: "filled_black",
        size: "large",
        text: "continue_with",
        shape: "rectangular",
        width: 290,
        click_listener: () => { googleCredentialAction = "signin"; },
      });
      byId("google-auth-status").textContent = "Inscrivez-vous ou connectez-vous avec un compte Google vérifié.";
      if (currentUser) loadGoogleLinkStatus();
    };
    if (window.google?.accounts?.id) {
      renderGoogleButton();
      return;
    }
    let script = document.querySelector('script[data-google-identity="true"]');
    if (!script) {
      script = document.createElement("script");
      script.src = "https://accounts.google.com/gsi/client";
      script.async = true;
      script.defer = true;
      script.dataset.googleIdentity = "true";
      script.onload = renderGoogleButton;
      script.onerror = () => {
        byId("google-auth-status").textContent = "Impossible de charger Google Identity Services.";
      };
      document.head.append(script);
    } else {
      script.addEventListener("load", renderGoogleButton, { once: true });
    }
  } catch (error) {
    slot.replaceChildren();
    byId("google-auth-status").textContent = error.message || "Impossible de vérifier le fournisseur Google.";
  }
}

function renderRoleWorkspace() {
  const workspace = byId("role-workspace");
  if (!currentUser) {
    workspace.hidden = true;
    return;
  }
  const config = ROLE_WORKSPACES[currentUser.role];
  if (!config) {
    workspace.hidden = true;
    return;
  }
  workspace.hidden = false;
  byId("role-workspace-title").textContent = config.title;
  byId("role-workspace-summary").textContent = config.summary;
  byId("role-workspace-badge").textContent = config.badge;
  byId("role-workspace-guidance").textContent = config.guidance;
  const permissions = byId("role-workspace-permissions");
  permissions.replaceChildren();
  for (const [title, description] of config.permissions) {
    const card = document.createElement("article");
    card.className = "role-permission";
    const heading = document.createElement("strong");
    heading.textContent = title;
    const detail = document.createElement("p");
    detail.textContent = description;
    card.append(heading, detail);
    permissions.append(card);
  }
}

function setMessage(element, message, kind = "") {
  element.textContent = message;
  element.className = kind ? `form-message ${kind}` : "form-message";
}

function setLoading(element, message) {
  element.replaceChildren();
  const node = document.createElement("div");
  node.className = "loading-line";
  node.textContent = message;
  element.append(node);
}

function setError(element, message) {
  element.replaceChildren();
  const node = document.createElement("div");
  node.className = "error-line";
  node.textContent = message;
  element.append(node);
}

async function ensureCsrf() {
  const response = await fetch("/api/auth/csrf", {
    method: "GET",
    credentials: "same-origin",
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  const payload = await response.json().catch(() => null);
  if (!response.ok || typeof payload?.csrf_token !== "string") {
    throw new Error("Tsy afaka nanokatra CSRF session.");
  }
  csrfToken = payload.csrf_token;
  return csrfToken;
}

async function apiRequest(path, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  const headers = {
    Accept: "application/json",
    ...(options.contentType ? { "Content-Type": options.contentType } : {}),
    ...(options.body !== undefined && !options.contentType
      ? { "Content-Type": "application/json" }
      : {}),
  };
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
    if (!csrfToken) await ensureCsrf();
    headers["X-CSRF-Token"] = csrfToken;
  }
  const body = options.rawBody !== undefined
    ? options.rawBody
    : options.body !== undefined
      ? JSON.stringify(options.body)
      : undefined;
  const response = await fetch(path, {
    method,
    headers,
    body,
    credentials: "same-origin",
    cache: "no-store",
    redirect: "error",
  });
  let payload = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }
  if (!response.ok) {
    if (response.status === 403 && payload?.detail?.startsWith("CSRF") && method !== "GET") {
      await ensureCsrf();
    }
    const detail = typeof payload?.detail === "string" ? payload.detail : `HTTP ${response.status}`;
    throw new Error(detail);
  }
  return payload;
}

function safeExternalUrl(value) {
  try {
    const url = new URL(value);
    return ["https:", "http:"].includes(url.protocol) ? url.href : null;
  } catch {
    return null;
  }
}

function setApiState(state, message) {
  const status = byId("api-status");
  status.dataset.state = state;
  byId("api-status-text").textContent = message;
  byId("metric-api").textContent = state === "ok" ? "Online" : state === "error" ? "Offline" : "…";
  byId("metric-api-detail").textContent = state === "ok" ? "Service mamaly" : state === "error" ? "Tsy tratra ny service" : "Miandry fanamarinana";
}

async function loadHealth() {
  try {
    const data = await apiRequest("/health");
    if (data?.status !== "ok") throw new Error("Valin'ny health tsy fantatra.");
    setApiState("ok", "API opérationnel");
  } catch (error) {
    setApiState("error", "API tsy tratra");
    setError(byId("cve-result"), error.message || "Tsy afaka nifandray tamin'ny API.");
  }
}

function selectCvss(cve) {
  const metrics = cve?.metrics || {};
  for (const key of ["cvssMetricV40", "cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]) {
    if (Array.isArray(metrics[key]) && metrics[key].length) {
      const item = metrics[key][0];
      return {
        score: item?.cvssData?.baseScore,
        severity: item?.cvssData?.baseSeverity || item?.baseSeverity || "Tsy voafaritra",
      };
    }
  }
  return null;
}

function renderCve(payload) {
  const result = byId("cve-result");
  result.replaceChildren();
  const cve = payload?.vulnerabilities?.[0]?.cve;
  if (!cve) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    const msg = document.createElement("p");
    msg.textContent = "Tsy nahitana CVE mifanaraka amin'io ID io.";
    empty.append(msg);
    result.append(empty);
    return;
  }

  const header = document.createElement("div");
  header.className = "result-header";
  const id = document.createElement("strong");
  id.textContent = cve.id || "CVE tsy fantatra";
  header.append(id);
  const cvss = selectCvss(cve);
  if (cvss && Number.isFinite(Number(cvss.score))) {
    const pill = document.createElement("span");
    pill.className = `score-pill${Number(cvss.score) >= 7 ? " high" : ""}`;
    pill.textContent = `CVSS ${cvss.score} · ${cvss.severity}`;
    header.append(pill);
  }
  result.append(header);

  const description = Array.isArray(cve.descriptions)
    ? cve.descriptions.find((item) => item.lang === "en")?.value || cve.descriptions[0]?.value
    : "";
  const paragraph = document.createElement("p");
  paragraph.className = "result-description";
  paragraph.textContent = description || "Tsy misy famaritana.";
  result.append(paragraph);

  const meta = document.createElement("div");
  meta.className = "result-meta";
  const published = document.createElement("span");
  published.textContent = `Published: ${cve.published || "—"}`;
  const modified = document.createElement("span");
  modified.textContent = `Modified: ${cve.lastModified || "—"}`;
  meta.append(published, modified);
  result.append(meta);

  const links = document.createElement("div");
  links.className = "result-links";
  for (const reference of (cve.references || []).slice(0, 4)) {
    const href = safeExternalUrl(reference.url);
    if (!href) continue;
    const link = document.createElement("a");
    link.href = href;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = "Reference ↗";
    links.append(link);
  }
  if (links.childElementCount) result.append(links);
}

async function searchCve(event) {
  event.preventDefault();
  const id = byId("cve-id").value.trim().toUpperCase();
  if (!/^CVE-[0-9]{4}-[0-9]{4,}$/.test(id)) {
    setError(byId("cve-result"), "Ampidiro amin'ny endrika CVE-YYYY-NNNN ny ID.");
    return;
  }
  setLoading(byId("cve-result"), "Mitady ao amin'ny NVD…");
  try {
    const payload = await apiRequest(`/api/cve/${encodeURIComponent(id)}`);
    renderCve(payload);
  } catch (error) {
    setError(byId("cve-result"), error.message || "Tsy nahomby ny fikarohana CVE.");
  }
}

function renderKev(data) {
  const vulnerabilities = Array.isArray(data?.vulnerabilities) ? data.vulnerabilities : [];
  byId("kev-count").textContent = vulnerabilities.length.toLocaleString();
  byId("metric-kev").textContent = vulnerabilities.length.toLocaleString();
  const list = byId("kev-list");
  list.replaceChildren();
  for (const item of vulnerabilities.slice(0, 8)) {
    const row = document.createElement("article");
    row.className = "kev-item";
    const id = document.createElement("span");
    id.textContent = item.cveID || "CVE";
    const title = document.createElement("strong");
    title.textContent = item.vulnerabilityName || item.product || "Vulnerability";
    const detail = document.createElement("p");
    detail.textContent = [item.vendorProject, item.product, item.dateAdded ? `Added ${item.dateAdded}` : ""].filter(Boolean).join(" · ");
    row.append(id, title, detail);
    list.append(row);
  }
  if (!vulnerabilities.length) setError(list, "Tsy misy firaketana azo aseho amin'izao fotoana izao.");
}

async function loadKev() {
  setLoading(byId("kev-list"), "Maka ny CISA KEV feed…");
  try {
    const data = await apiRequest("/api/kev");
    renderKev(data);
  } catch (error) {
    byId("kev-count").textContent = "—";
    byId("metric-kev").textContent = "—";
    setError(byId("kev-list"), error.message || "Tsy hita ny CISA KEV feed.");
  }
}

async function loadTools() {
  const list = byId("tools-list");
  setLoading(list, "Maka ny lisitry ny tools…");
  try {
    const tools = await apiRequest("/api/mcp/tools");
    byId("metric-tools").textContent = Array.isArray(tools) ? tools.length : "—";
    byId("tools-count").textContent = Array.isArray(tools) ? String(tools.length) : "—";
    list.replaceChildren();
    for (const item of (Array.isArray(tools) ? tools : [])) {
      const card = document.createElement("article");
      card.className = "tool-item";
      const name = document.createElement("strong");
      name.textContent = item.name || "Tool";
      const description = document.createElement("p");
      description.textContent = item.description || "Tsy misy famaritana.";
      const meta = document.createElement("div");
      meta.className = "tool-meta";
      for (const value of [item.access, item.required_scope].filter(Boolean)) {
        const chip = document.createElement("span");
        chip.textContent = value;
        meta.append(chip);
      }
      card.append(name, description, meta);
      list.append(card);
    }
  } catch (error) {
    setError(list, error.message || "Tsy nahazo ny lisitry ny MCP tools.");
  }
}

function setAuthPanels(mode) {
  document.body.dataset.authState = currentUser ? "authenticated" : mode === "bootstrap" ? "bootstrap" : "anonymous";
  byId("bootstrap-panel").hidden = mode !== "bootstrap";
  byId("login-panel").hidden = mode !== "login";
  byId("register-form").hidden = true;
  byId("login-form").hidden = false;
  byId("google-auth-block").hidden = false;
  byId("register-open-link").hidden = false;
  byId("account-panel").hidden = mode !== "account";
  byId("admin-panel").hidden = mode !== "account" || currentUser?.role !== "admin";
  const badge = byId("user-badge");
  badge.hidden = !currentUser;
  badge.textContent = currentUser ? `${currentUser.display_name} · ${currentUser.role}` : "";
  byId("auth-state-pill").textContent = currentUser ? "Vérifié" : mode === "bootstrap" ? "Configuration initiale" : "Déconnecté";
  byId("metadata-workspace").hidden = !currentUser;
  updateRoleVisibility();
  renderRoleWorkspace();
  byId("metadata-auth-status").textContent = currentUser
    ? `Miditra amin'ny metadata amin'ny andraikitra ${currentUser.role}.`
    : "Midira amin'ny kaonty voa-approve raha hijery na hitahiry metadata.";
  const canWriteMetadata = canAnalyze();
  byId("metadata-create-form").hidden = !canWriteMetadata;
  byId("metadata-write-access").textContent = canWriteMetadata
    ? "Fahazoan-dalana: Admin / Analyst — afaka manampy SHA-256 metadata."
    : "Read-only: afaka mijery metadata ianao fa tsy afaka manampy na manova azy.";
  updateInferenceAccess();
  window.dispatchEvent(new CustomEvent("nanou:auth-changed", {
    detail: { role: currentUser?.role || null },
  }));
}

async function loadAuth() {
  try {
    const status = await apiRequest("/api/auth/me");
    currentUser = status.user || null;
    currentCategory = "home";
    loadedCategories.clear();
    if (currentUser) {
      setAuthPanels("account");
      byId("account-name").textContent = currentUser.display_name;
      byId("account-email").textContent = currentUser.email;
      byId("account-role").textContent = currentUser.role.toUpperCase();
      byId("auth-message").textContent = "Votre session est protégée et sera révoquée automatiquement à son expiration.";
    } else if (status.bootstrap_required) {
      setAuthPanels("bootstrap");
      updateRoleVisibility();
      byId("auth-message").textContent = "Aucun administrateur n’existe encore. Seul le premier compte peut devenir administrateur.";
    } else {
      setAuthPanels("login");
      updateRoleVisibility();
      byId("auth-message").textContent = "Connectez-vous avec un compte approuvé. Toute nouvelle inscription nécessite une validation administrateur.";
      byId("metadata-list").replaceChildren();
      byId("metadata-total").textContent = "0";
    }
  } catch (error) {
    currentUser = null;
    setAuthPanels("login");
    updateRoleVisibility();
    byId("auth-message").textContent = error.message || "Impossible de vérifier le compte. Vérifiez la connexion à la base de données.";
  }
}

async function submitBootstrap(event) {
  event.preventDefault();
  const submit = byId("bootstrap-form").querySelector("button[type=submit]");
  submit.disabled = true;
  try {
    await apiRequest("/api/auth/bootstrap", {
      method: "POST",
      body: {
        display_name: byId("bootstrap-name").value.trim(),
        email: byId("bootstrap-email").value.trim(),
        password: byId("bootstrap-password").value,
        bootstrap_token: byId("bootstrap-token").value,
      },
    });
    byId("bootstrap-form").reset();
    await loadAuth();
  } catch (error) {
    byId("auth-message").textContent = error.message || "Tsy nahomby ny fametrahana Admin.";
  } finally {
    submit.disabled = false;
  }
}

async function submitLogin(event) {
  event.preventDefault();
  const submit = byId("login-form").querySelector("button[type=submit]");
  submit.disabled = true;
  try {
    await apiRequest("/api/auth/login", {
      method: "POST",
      body: {
        email: byId("login-email").value.trim(),
        password: byId("login-password").value,
      },
    });
    byId("login-form").reset();
    await loadAuth();
  } catch (error) {
    byId("auth-message").textContent = error.message || "Échec de la connexion.";
  } finally {
    submit.disabled = false;
  }
}

async function submitRegistration(event) {
  event.preventDefault();
  const submit = byId("register-form").querySelector("button[type=submit]");
  submit.disabled = true;
  try {
    const result = await apiRequest("/api/auth/register", {
      method: "POST",
      body: {
        display_name: byId("register-name").value.trim(),
        email: byId("register-email").value.trim(),
        password: byId("register-password").value,
      },
    });
    byId("register-form").reset();
    byId("auth-message").textContent = result.message || "Demande reçue. En attente de l’approbation administrateur.";
  } catch (error) {
    byId("auth-message").textContent = error.message || "Échec de l’inscription.";
  } finally {
    submit.disabled = false;
  }
}

async function submitPasswordChange(event) {
  event.preventDefault();
  const form = byId("password-change-form");
  const submit = form.querySelector("button[type=submit]");
  const currentPassword = byId("current-password").value;
  const newPassword = byId("new-password").value;
  if (newPassword !== byId("confirm-password").value) {
    byId("password-change-status").textContent = "Tsy mitovy ny fanamafisana ny tenimiafina vaovao.";
    return;
  }
  if (currentPassword === newPassword) {
    byId("password-change-status").textContent = "Mila tenimiafina vaovao tsy mitovy amin'ny taloha.";
    return;
  }
  submit.disabled = true;
  byId("password-change-status").textContent = "Manavao ny tenimiafina…";
  try {
    await apiRequest("/api/auth/password", {
      method: "POST",
      body: {
        current_password: currentPassword,
        new_password: newPassword,
      },
    });
    form.reset();
    byId("password-change-status").textContent = "Voavao ny tenimiafina. Nesorina ny session taloha rehetra.";
    await loadAuth();
  } catch (error) {
    byId("password-change-status").textContent = error.message || "Tsy nahomby ny fanovana tenimiafina.";
  } finally {
    submit.disabled = false;
  }
}

async function logoutAccount() {
  try {
    await apiRequest("/api/auth/logout", { method: "POST" });
  } catch (error) {
    byId("auth-message").textContent = error.message || "Échec de la déconnexion.";
    return;
  }
  currentUser = null;
  byId("metadata-create-form").reset();
  byId("metadata-list").replaceChildren();
  byId("metadata-total").textContent = "0";
  byId("inference-features").value = "";
  byId("inference-result").replaceChildren();
  await loadAuth();
}

function adminUserState(item) {
  if (!item.is_approved) return "pending";
  return item.is_active ? "active" : "disabled";
}

function renderAdminUsers(items) {
  const list = byId("admin-users");
  list.replaceChildren();
  const users = Array.isArray(items) ? items : [];
  const counts = {
    active: users.filter((item) => adminUserState(item) === "active").length,
    pending: users.filter((item) => adminUserState(item) === "pending").length,
    disabled: users.filter((item) => adminUserState(item) === "disabled").length,
  };
  byId("admin-total-users").textContent = String(users.length);
  byId("admin-active-users").textContent = String(counts.active);
  byId("admin-pending-users").textContent = String(counts.pending);
  byId("admin-disabled-users").textContent = String(counts.disabled);

  const query = byId("admin-user-search").value.trim().toLocaleLowerCase();
  const stateFilter = byId("admin-user-filter").value;
  const filtered = users.filter((item) => {
    const state = adminUserState(item);
    const matchesState = stateFilter === "all" || state === stateFilter;
    const searchable = [item.display_name, item.email, item.role, state].join(" ").toLocaleLowerCase();
    return matchesState && (!query || searchable.includes(query));
  });
  byId("admin-user-result-count").textContent = `${filtered.length} / ${users.length} kaonty aseho`;

  for (const item of filtered) {
    const row = document.createElement("article");
    row.className = "admin-user-row";
    const identity = document.createElement("div");
    identity.className = "admin-user-identity";
    const name = document.createElement("strong");
    name.textContent = item.display_name;
    const email = document.createElement("span");
    email.textContent = item.email;
    const state = adminUserState(item);
    const status = document.createElement("small");
    status.className = `admin-user-status status-${state}`;
    status.textContent = state === "pending"
      ? "Miandry fankatoavana"
      : state === "active" ? "Mavitrika" : "Voasakana / tsy mavitrika";
    identity.append(name, email, status);

    const controls = document.createElement("div");
    controls.className = "admin-user-controls";
    const role = document.createElement("select");
    role.setAttribute("aria-label", `Andraikitry ny ${item.email}`);
    for (const value of ["viewer", "analyst", "admin"]) {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = value.toUpperCase();
      option.selected = item.role === value;
      role.append(option);
    }
    const activeLabel = document.createElement("label");
    activeLabel.className = "active-toggle";
    const active = document.createElement("input");
    active.type = "checkbox";
    active.checked = item.is_active && item.is_approved;
    activeLabel.append(active, document.createTextNode(" Mankatoaka / mampavitrika"));
    const save = document.createElement("button");
    save.className = "button button-secondary";
    save.type = "button";
    save.textContent = "Tehirizo";
    const isSelf = item.id === currentUser?.id;
    if (isSelf) {
      role.disabled = true;
      active.disabled = true;
      save.disabled = true;
      save.title = "Tsy azo ovaina eto ny kaontinao manokana.";
    }
    save.addEventListener("click", async () => {
      save.disabled = true;
      try {
        await apiRequest(`/api/admin/users/${encodeURIComponent(item.id)}`, {
          method: "PATCH",
          body: { role: role.value, is_active: active.checked },
        });
        await loadAdminConsole();
      } catch (error) {
        byId("auth-message").textContent = error.message || "Impossible d’enregistrer les modifications.";
      } finally {
        save.disabled = isSelf;
      }
    });
    controls.append(role, activeLabel, save);
    row.append(identity, controls);
    list.append(row);
  }
  if (!filtered.length) {
    const empty = document.createElement("p");
    empty.className = "loading-line";
    empty.textContent = users.length
      ? "Tsy misy kaonty mifanaraka amin'ny fikarohana na sivana."
      : "Tsy mbola misy kaonty voasoratra.";
    list.append(empty);
  }
}

function formatAuditDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value || "Daty tsy fantatra";
  try {
    return new Intl.DateTimeFormat("fr-FR", {
      dateStyle: "medium",
      timeStyle: "short",
      timeZone: "Indian/Antananarivo",
    }).format(date);
  } catch {
    return date.toLocaleString();
  }
}

function auditOutcomeLabel(value) {
  const labels = {
    success: "Tafita",
    pending: "Miandry",
    failed: "Tsy tafita",
    blocked: "Voasakana",
    invalid_bootstrap_token: "Token diso",
    pending_or_disabled: "Kaonty tsy mavitrika",
  };
  return labels[value] || value || "Tsy fantatra";
}

function renderAudit(items) {
  const list = byId("audit-list");
  list.replaceChildren();
  const events = Array.isArray(items) ? items : [];
  const query = byId("audit-search").value.trim().toLocaleLowerCase();
  const outcomeFilter = byId("audit-outcome-filter").value;
  const filtered = events.filter((item) => {
    const outcome = item.outcome || "unknown";
    const searchable = [item.action, outcome, item.target_type, item.target_id, item.request_id]
      .filter(Boolean).join(" ").toLocaleLowerCase();
    return (outcomeFilter === "all" || outcome === outcomeFilter)
      && (!query || searchable.includes(query));
  });

  for (const item of filtered) {
    const row = document.createElement("article");
    row.className = "audit-row";
    const main = document.createElement("div");
    main.className = "audit-row-main";
    const action = document.createElement("strong");
    action.textContent = item.action || "Hetsika tsy fantatra";
    const outcome = item.outcome || "unknown";
    const badge = document.createElement("span");
    const outcomeClass = outcome.toLowerCase().replace(/[^a-z0-9_-]/g, "");
    badge.className = `audit-outcome outcome-${outcomeClass}`;
    badge.textContent = auditOutcomeLabel(outcome);
    main.append(action, badge);

    const detail = document.createElement("span");
    detail.className = "audit-row-detail";
    const target = item.target_type ? `Target: ${item.target_type}` : "";
    const request = item.request_id ? `Ref: ${item.request_id.slice(0, 14)}` : "";
    detail.textContent = [target, request].filter(Boolean).join(" · ") || "Tsy misy antsipiriany fanampiny";

    const timestamp = document.createElement("time");
    timestamp.dateTime = item.created_at || "";
    timestamp.textContent = formatAuditDate(item.created_at);
    row.append(main, detail, timestamp);
    list.append(row);
  }
  if (!filtered.length) {
    const empty = document.createElement("p");
    empty.className = "loading-line";
    empty.textContent = events.length
      ? "Tsy misy hetsika mifanaraka amin'ny fikarohana na sivana."
      : "Mbola tsy misy audit event voarakitra.";
    list.append(empty);
  }
}

async function createAdminPairing() {
  const button = byId("admin-bridge-create");
  const status = byId("admin-bridge-status");
  button.disabled = true;
  byId("admin-bridge-code-wrap").hidden = true;
  byId("admin-bridge-code").textContent = "";
  setMessage(status, "Mamorona pairing code voafetra…");
  try {
    const result = await apiRequest("/api/auth/pairing", { method: "POST" });
    byId("admin-bridge-code").textContent = result.pairing_code;
    byId("admin-bridge-code-wrap").hidden = false;
    setMessage(
      status,
      "Vita. Adikao ary ampidiro ao amin'ny Termux ao anatin'ny " +
        result.expires_in_seconds +
        " segondra. Read-only mandritra ny 15 minitra ny bridge.",
      "success",
    );
    window.clearTimeout(window.nanouAdminPairingExpiry);
    window.nanouAdminPairingExpiry = window.setTimeout(() => {
      byId("admin-bridge-code").textContent = "";
      byId("admin-bridge-code-wrap").hidden = true;
      setMessage(status, "Lany daty ny code. Mamoròna pairing code vaovao raha ilaina.");
    }, result.expires_in_seconds * 1000);
  } catch (error) {
    setMessage(status, error.message || "Tsy afaka namorona pairing code.", "error");
  } finally {
    button.disabled = false;
  }
}

async function copyAdminPairingCode() {
  const code = byId("admin-bridge-code").textContent;
  if (!code) return;
  try {
    await navigator.clipboard.writeText(code);
    setMessage(byId("admin-bridge-status"), "Voadika. Apetaho ao amin'ny Termux rehefa angatahina.", "success");
  } catch (_error) {
    setMessage(byId("admin-bridge-status"), "Tsy nahazo clipboard. Safidio ary adikao ilay code hita eo ambony.", "error");
  }
}

async function loadAdminConsole() {
  if (currentUser?.role !== "admin") return;
  try {
    const [users, audit] = await Promise.all([
      apiRequest("/api/admin/users"),
      apiRequest("/api/admin/audit?limit=100"),
    ]);
    adminUsersCache = Array.isArray(users) ? users : [];
    adminAuditCache = Array.isArray(audit) ? audit : [];
    renderAdminUsers(adminUsersCache);
    renderAudit(adminAuditCache);
  } catch (error) {
    byId("admin-users").textContent = error.message || "Tsy afaka namaky ny admin workspace.";
  }
}

function renderCvePlaceholder() {
  const result = byId("cve-result");
  if (!result.childElementCount) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    const icon = document.createElement("span");
    icon.textContent = "⌕";
    const message = document.createElement("p");
    message.textContent = "Ampidiro ny ID CVE hahitana ny antsipiriany sy ny isa CVSS.";
    empty.append(icon, message);
    result.append(empty);
  }
}

function renderMetadata(items) {
  const list = byId("metadata-list");
  list.replaceChildren();
  byId("metadata-total").textContent = String(items.length);
  for (const item of items) {
    const row = document.createElement("div");
    row.className = "metadata-row";
    const hash = document.createElement("strong");
    hash.textContent = item.sha256 || "Hash tsy fantatra";
    const label = document.createElement("span");
    label.className = `label-${["benign", "malicious", "unknown"].includes(item.label) ? item.label : "unknown"}`;
    label.textContent = item.label || "unknown";
    row.append(hash, label);
    list.append(row);
  }
  if (!items.length) {
    const empty = document.createElement("div");
    empty.className = "loading-line";
    empty.textContent = "Mbola tsy misy metadata voatahiry.";
    list.append(empty);
  }
}

async function loadMetadata() {
  if (!currentUser) return;
  try {
    const items = await apiRequest("/api/malware/metadata?limit=100");
    renderMetadata(Array.isArray(items) ? items : []);
  } catch (error) {
    setMessage(byId("metadata-auth-status"), error.message || "Tsy afaka namaky metadata.", "error");
  }
}

async function createMetadata(event) {
  event.preventDefault();
  if (!canAnalyze()) {
    setMessage(byId("metadata-auth-status"), "Admin na Analyst ihany no afaka manampy metadata.", "error");
    return;
  }
  const payload = {
    sha256: byId("sample-hash").value.trim(),
    label: byId("sample-label").value,
    source: byId("sample-source").value.trim(),
    family: byId("sample-family").value.trim() || null,
  };
  try {
    await apiRequest("/api/malware/metadata", { method: "POST", body: payload });
    byId("metadata-create-form").reset();
    setMessage(byId("metadata-auth-status"), "Voatahiry ny metadata.", "success");
    await loadMetadata();
  } catch (error) {
    setMessage(byId("metadata-auth-status"), error.message || "Tsy voatahiry ny metadata.", "error");
  }
}

function updateInferenceAccess() {
  const ready = Boolean(configuredMalwareModel?.available);
  const authenticated = canAnalyze();
  byId("inference-fields").disabled = !(ready && authenticated);
  const status = byId("model-status");
  if (!ready) {
    status.dataset.state = "error";
    status.textContent = configuredMalwareModel?.reason || "Tsy mbola misy modely voamarina napetraka ao amin'ny server.";
    return;
  }
  status.dataset.state = "ready";
  const selected = configuredMalwareModel.dataset_id;
  byId("inference-dataset").value = selected;
  const datasetName = selected === "ember2024-apk" ? "EMBER2024" : "LAMDA";
  status.textContent = authenticated
    ? `Modely ${datasetName} voamarina · ${configuredMalwareModel.feature_count} features · afaka manao inference.`
    : "Midira amin'ny kaonty Analyst na Admin mba hampiasa inference.";
}

async function loadMalwareModelStatus() {
  try {
    configuredMalwareModel = await apiRequest("/api/malware/inference/status");
  } catch {
    configuredMalwareModel = { available: false, reason: "Tsy azo nohamarinina ny toetry ny modely." };
  }
  updateInferenceAccess();
}


async function readFileAsText(file) {
  if (typeof file.text === "function") return file.text();
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(new Error("Tsy afaka namaky ny CSV."));
    reader.readAsText(file, "UTF-8");
  });
}

async function prepareFeatureCsv() {
  if (!canAnalyze()) {
    setMessage(byId("feature-prepare-status"), "Admin na Analyst ihany no afaka manomana features.", "error");
    return;
  }
  const file = byId("feature-csv").files?.[0];
  if (!file) {
    setMessage(byId("feature-prepare-status"), "Safidio aloha ny CSV feature.", "error");
    return;
  }
  if (!file.name.toLowerCase().endsWith(".csv") || file.size > 1_048_576) {
    setMessage(byId("feature-prepare-status"), "CSV ihany no azo atao ary 1 MiB no fetra.", "error");
    return;
  }
  const datasetId = byId("inference-dataset").value;
  const button = byId("prepare-features");
  button.disabled = true;
  setMessage(byId("feature-prepare-status"), "Manamarina ny schema sy ny feature values…");
  try {
    const csvText = await readFileAsText(file);
    const prepared = await apiRequest(`/api/malware/features/prepare/${encodeURIComponent(datasetId)}`, {
      method: "POST",
      contentType: "text/csv",
      rawBody: csvText,
    });
    byId("inference-features").value = JSON.stringify(prepared.features);
    setMessage(
      byId("feature-prepare-status"),
      `PASS · ${prepared.feature_count} features · CSV SHA-256: ${prepared.source_content_sha256}`,
      "success",
    );
  } catch (error) {
    byId("inference-features").value = "";
    setMessage(byId("feature-prepare-status"), error.message || "Tsy nety ny feature CSV.", "error");
  } finally {
    button.disabled = false;
  }
}

async function runMalwareInference(event) {
  event.preventDefault();
  if (!canAnalyze() || !configuredMalwareModel?.available) {
    setError(byId("inference-result"), "Mila modely voamarina sy kaonty Analyst/Admin aloha.");
    return;
  }
  let features;
  try {
    features = JSON.parse(byId("inference-features").value);
  } catch {
    setError(byId("inference-result"), "Tsy JSON array marina ilay feature vector.");
    return;
  }
  if (!Array.isArray(features) || features.some((value) => typeof value !== "number" || !Number.isFinite(value))) {
    setError(byId("inference-result"), "Ny feature vector dia tsy maintsy array misy isa finite ihany.");
    return;
  }
  const datasetId = byId("inference-dataset").value;
  const expected = datasetId === "ember2024-apk" ? 2568 : 4561;
  if (features.length !== expected) {
    setError(byId("inference-result"), `Ity schema ity dia mitaky ${expected} features marina.`);
    return;
  }
  if (datasetId === "lamda-apk-2022-train-2023-test" &&
      features.some((value) => !Number.isInteger(value) || value < -128 || value > 127)) {
    setError(byId("inference-result"), "Ny LAMDA dia mitaky sanda integer signed int8 (-128 hatramin'ny 127).");
    return;
  }

  setLoading(byId("inference-result"), "Manao inference amin'ny modely voamarina…");
  try {
    const result = await apiRequest("/api/malware/inference", {
      method: "POST",
      body: { dataset_id: datasetId, schema_version: 1, features },
    });
    const area = byId("inference-result");
    area.replaceChildren();
    const wrapper = document.createElement("div");
    wrapper.className = "inference-result";
    const label = document.createElement("strong");
    label.textContent = result.classification === "malicious" ? "MALICIOUS — mila fanadihadiana" : "BENIGN — tsy nahitana famantarana araka ny modely";
    const probability = document.createElement("span");
    probability.className = "probability";
    probability.textContent = `${(result.malicious_probability * 100).toFixed(2)}% probability`;
    const note = document.createElement("p");
    note.textContent = `Dataset: ${result.dataset_id} · Features: ${result.feature_count} · Threshold: ${result.decision_threshold} · SHA-256 model: ${result.model_sha256.slice(0, 12)}…`;
    wrapper.append(label, probability, note);
    area.append(wrapper);
  } catch (error) {
    setError(byId("inference-result"), error.message || "Tsy nahomby ny inference.");
  }
}

for(const id of ["language-select","auth-language-select"]){byId(id).addEventListener("change", event => applyLocale(event.target.value));}
let locale="fr";try{locale=localStorage.getItem("nanou-locale")||"fr"}catch{/* private mode */}applyLocale(locale);
byId("cve-form").addEventListener("submit", searchCve);
byId("refresh-kev").addEventListener("click", loadKev);
byId("bootstrap-form").addEventListener("submit", submitBootstrap);
byId("login-form").addEventListener("submit", submitLogin);
byId("register-form").addEventListener("submit", submitRegistration);
byId("logout-button").addEventListener("click", logoutAccount);
byId("password-change-form").addEventListener("submit", submitPasswordChange);
byId("refresh-admin").addEventListener("click", loadAdminConsole);
byId("admin-bridge-create").addEventListener("click", createAdminPairing);
byId("admin-bridge-copy").addEventListener("click", copyAdminPairingCode);
byId("admin-user-search").addEventListener("input", () => renderAdminUsers(adminUsersCache));
byId("admin-user-filter").addEventListener("change", () => renderAdminUsers(adminUsersCache));
byId("audit-search").addEventListener("input", () => renderAudit(adminAuditCache));
byId("audit-outcome-filter").addEventListener("change", () => renderAudit(adminAuditCache));
byId("metadata-create-form").addEventListener("submit", createMetadata);
byId("prepare-features").addEventListener("click", prepareFeatureCsv);
byId("inference-dataset").addEventListener("change", () => {
  byId("feature-csv").value = "";
  byId("inference-features").value = "";
  setMessage(byId("feature-prepare-status"), "Miova ny dataset; safidio indray ny CSV mifanaraka.");
});
byId("malware-inference-form").addEventListener("submit", runMalwareInference);
byId("register-open-link").addEventListener("click", openRegistrationDetails);
byId("register-back-link").addEventListener("click", closeRegistrationDetails);
byId("category-back-button").addEventListener("click", () => showCategory("home"));
document.querySelectorAll("[data-category-target]").forEach((link) => {
  link.addEventListener("click", (event) => {
    event.preventDefault();
    showCategory(link.dataset.categoryTarget);
  });
});
document.querySelectorAll("[data-open-category]").forEach((button) => {
  button.addEventListener("click", () => showCategory(button.dataset.openCategory));
});

async function initializePlatform() {
  renderCvePlaceholder();
  try {
    await ensureCsrf();
  } catch (error) {
    byId("auth-message").textContent = error.message || "Impossible d’initialiser la session CSRF.";
  }
  await loadAuth();
  await loadAuthProviders();
}

initializePlatform();
