const state = {
  snapshot: null,
  pingTimer: null,
  query: "",
  topic: "All",
  region: "All",
  segment: "All",
  view: "overview",
  selectedStory: null,
  savedViews: JSON.parse(localStorage.getItem("signalfeed.savedViews") || "[]"),
  alertRules: JSON.parse(localStorage.getItem("signalfeed.alertRules") || "[]"),
};

const el = (id) => document.getElementById(id);
const storyCount = el("story-count");
const lastUpdated = el("last-updated");
const socketStatus = el("socket-status");
const summaryCards = el("summary-cards");
const sentiment = el("sentiment");
const topics = el("topics");
const regions = el("regions");
const sources = el("sources");
const trending = el("trending");
const hashtags = el("hashtags");
const socialLeaders = el("social-leaders");
const headlines = el("headlines");
const headlineCount = el("headline-count");
const spotlightStory = el("spotlight-story");
const segmentTabs = el("segment-tabs");
const viewTabs = el("view-tabs");
const topicFilter = el("topic-filter");
const regionFilter = el("region-filter");
const searchInput = el("search-input");
const globalSpotlight = el("global-spotlight");
const globalSummary = el("global-summary");
const globalTopics = el("global-topics");
const globalSources = el("global-sources");
const globalKeywords = el("global-keywords");
const globalHeadlines = el("global-headlines");
const globalCount = el("global-count");
const deepDiveCards = el("deep-dive-cards");
const clusterList = el("cluster-list");
const savedViews = el("saved-views");
const alertRules = el("alert-rules");
const sourceTrust = el("source-trust");
const saveViewBtn = el("save-view-btn");
const saveAlertBtn = el("save-alert-btn");
const themeToggle = el("theme-toggle");
const expertToggle = el("expert-toggle");
const expertPanel = el("expert-panel");
const dialog = el("story-dialog");
const storyDetail = el("story-detail");
const canvas = el("timeline");
const ctx = canvas.getContext("2d");
const viewPanels = Array.from(document.querySelectorAll("[data-view-panel]"));

state.expertMode = false;
state.theme = localStorage.getItem("signalfeed.theme") || "light";

const VIEW_OPTIONS = [
  { id: "overview", label: "Overview" },
  { id: "analytics", label: "Analytics" },
  { id: "stream", label: "Stream" },
  { id: "global", label: "Global" },
];

const SEGMENT_PRESETS = [
  { id: "All", label: "All Desk", matcher: () => true },
  { id: "India", label: "India", matcher: (item) => item.topics.includes("India") || item.source_category === "India" },
  { id: "Governance", label: "Governance", matcher: (item) => item.topics.includes("Governance") || item.topics.includes("Politics") },
  { id: "Economy", label: "Economy", matcher: (item) => item.topics.includes("Economy") || item.source_category === "Business" },
  { id: "Startups", label: "Startups", matcher: (item) => item.topics.includes("Startups") || item.topics.includes("AI & Tech") },
  { id: "Cricket", label: "Cricket", matcher: (item) => item.topics.includes("Cricket") || item.source_category === "Sports" },
  { id: "Global", label: "Global", matcher: (item) => item.regions.includes("Global") || item.source_category === "Global" },
];

const DEEP_DIVE_TRACKS = [
  { id: "politics", label: "Politics", matcher: (item) => item.topics.includes("Governance") || item.topics.includes("Politics") || /election|president|prime minister|parliament|cabinet|policy/i.test(`${item.title} ${item.summary}`) },
  { id: "markets", label: "Markets", matcher: (item) => item.topics.includes("Economy") || /market|stocks|inflation|bank|trade|oil|tariff|currency/i.test(`${item.title} ${item.summary}`) },
  { id: "conflict", label: "Conflict", matcher: (item) => item.topics.includes("Geopolitics") || /war|attack|military|missile|ceasefire|troops|border/i.test(`${item.title} ${item.summary}`) },
  { id: "tech", label: "Tech", matcher: (item) => item.topics.includes("AI & Tech") || item.topics.includes("Startups") || /ai|chip|software|startup|cyber|cloud|platform/i.test(`${item.title} ${item.summary}`) },
  { id: "sports", label: "Sports", matcher: (item) => item.topics.includes("Sports") || item.topics.includes("Cricket") || /match|league|tournament|cup|goal|innings/i.test(`${item.title} ${item.summary}`) },
];

function persistLocalState() {
  localStorage.setItem("signalfeed.savedViews", JSON.stringify(state.savedViews));
  localStorage.setItem("signalfeed.alertRules", JSON.stringify(state.alertRules));
  localStorage.setItem("signalfeed.theme", state.theme);
}
function formatTime(iso) { return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }); }
function cleanSummary(text) { return text.replace(/<[^>]+>/g, "").trim(); }
function keywordCountsFromItems(items, limit = 12) {
  const counts = new Map();
  items.forEach((item) => `${item.title} ${item.summary}`.toLowerCase().split(/[^a-z0-9]+/).forEach((word) => {
    if (word.length < 5 || ["about","their","there","world","india","after","today","latest"].includes(word)) return;
    counts.set(word, (counts.get(word) || 0) + 1);
  }));
  return Array.from(counts.entries()).sort((a,b)=>b[1]-a[1]).slice(0,limit).map(([word,count])=>({word,count}));
}
function countBy(items, selector) {
  const map = new Map();
  items.forEach((item) => selector(item).forEach((value) => map.set(value, (map.get(value) || 0) + 1)));
  return Array.from(map.entries()).sort((a,b)=>b[1]-a[1]);
}
function globalItems() { return (state.snapshot?.headlines || []).filter((item) => item.regions.includes("Global") || item.source_category === "Global"); }
function matchesFilters(item) {
  const query = state.query.toLowerCase().trim();
  const haystack = `${item.title} ${item.summary} ${item.regions.join(" ")} ${item.topics.join(" ")} ${item.source}`.toLowerCase();
  const matchesQuery = !query || haystack.includes(query);
  const matchesTopic = state.topic === "All" || item.topics.includes(state.topic);
  const matchesRegion = state.region === "All" || item.regions.includes(state.region);
  const segment = SEGMENT_PRESETS.find((preset) => preset.id === state.segment) || SEGMENT_PRESETS[0];
  return matchesQuery && matchesTopic && matchesRegion && segment.matcher(item);
}
function filteredHeadlines() { return (state.snapshot?.headlines || []).filter(matchesFilters); }
function applyFilter({ topic, region, segment, query, view }) {
  if (topic !== undefined) state.topic = topic;
  if (region !== undefined) state.region = region;
  if (segment !== undefined) state.segment = segment;
  if (query !== undefined) state.query = query;
  if (view !== undefined) state.view = view;
  if (searchInput) searchInput.value = state.query;
  renderFilters(state.snapshot || { topic_totals: {}, region_totals: {} });
  renderViewTabs();
  applyViewState();
  renderExpertMode();
  if (state.snapshot) render(state.snapshot);
}
function renderBars(target, entries, colors, onClick) {
  const max = Math.max(1, ...entries.map((entry) => entry[1]), 1);
  target.innerHTML = entries.map(([label, count]) => `
    <div class="metric-row" data-label="${label}">
      <header><strong>${label}</strong><span>${count}</span></header>
      <div class="track"><div class="fill" style="width:${(count / max) * 100}%; background:${colors};"></div></div>
    </div>`).join("");
  if (onClick) target.querySelectorAll(".metric-row").forEach((node) => node.addEventListener("click", () => onClick(node.dataset.label)));
}
function renderSummary(cards) { summaryCards.innerHTML = cards.map((card) => `<article class="summary-card"><span class="status-label">${card.label}</span><strong>${card.value}</strong><p>${card.subtext}</p></article>`).join(""); }
function renderStoryCard(target, item, options = {}) {
  if (!item) { target.innerHTML = `<p class="spotlight-summary">${options.emptyText || "Waiting for a lead story."}</p>`; return; }
  target.innerHTML = `<article class="${options.className || "spotlight-card"}" data-story-id="${item.id}">
      <div class="${options.metaClass || "spotlight-meta"}">
        <span class="platform-pill">${item.source}</span><span class="platform-pill">${item.source_category}</span><span class="platform-pill">Pulse ${item.social_score}</span>
      </div>
      <h3><a href="${item.link}" target="_blank" rel="noreferrer">${item.title}</a></h3>
      <p class="${options.summaryClass || "spotlight-summary"}">${cleanSummary(item.summary).slice(0, 240)}</p>
      <div class="headline-footer">
        ${item.regions.map((region) => `<button class="filter-chip" data-region="${region}" type="button">${region}</button>`).join("")}
        ${item.topics.map((topic) => `<button class="filter-chip" data-topic="${topic}" type="button">${topic}</button>`).join("")}
        ${item.hashtags.map((tag) => `<span class="tag-pill">${tag}</span>`).join("")}
      </div>
      <div class="platforms">${item.social_platforms.map((platform) => `<span class="platform-pill">${platform}</span>`).join("")}<button class="action-btn story-detail-btn" data-open-story="${item.id}" type="button">Details</button></div>
    </article>`;
  bindFilterButtons(target);
  target.querySelector("[data-open-story]")?.addEventListener("click", (event) => { event.stopPropagation(); openStoryDetail(item); });
}
function bindFilterButtons(root = document) {
  root.querySelectorAll("[data-topic]").forEach((node) => node.addEventListener("click", (event) => { event.stopPropagation(); applyFilter({ topic: node.dataset.topic, view: state.view }); }));
  root.querySelectorAll("[data-region]").forEach((node) => node.addEventListener("click", (event) => { event.stopPropagation(); applyFilter({ region: node.dataset.region, view: state.view }); }));
  root.querySelectorAll("[data-source]").forEach((node) => node.addEventListener("click", (event) => { event.stopPropagation(); applyFilter({ query: node.dataset.source, view: state.view }); }));
}
function renderSegmentTabs(items) {
  segmentTabs.innerHTML = SEGMENT_PRESETS.map((preset) => { const count = items.filter((item) => preset.matcher(item)).length; return `<button class="segment-tab ${preset.id===state.segment?"active":""}" data-segment="${preset.id}"><span>${preset.label}</span><span class="segment-count">${count}</span></button>`; }).join("");
  segmentTabs.querySelectorAll("[data-segment]").forEach((button) => button.addEventListener("click", () => applyFilter({ segment: button.dataset.segment, view: button.dataset.segment === "Global" ? "global" : state.view })));
}
function renderViewTabs() {
  viewTabs.innerHTML = VIEW_OPTIONS.map((view) => `<button class="view-tab ${view.id===state.view?"active":""}" data-view="${view.id}">${view.label}</button>`).join("");
  viewTabs.querySelectorAll("[data-view]").forEach((button) => button.addEventListener("click", () => applyFilter({ view: button.dataset.view, segment: button.dataset.view === "global" ? "Global" : state.segment })));
}
function applyViewState() { viewPanels.forEach((panel) => panel.classList.toggle("hidden", !panel.dataset.viewPanel.split(" ").includes(state.view))); }
function renderExpertMode() {
  if (!expertPanel || !expertToggle) return;
  expertPanel.classList.toggle("hidden", !state.expertMode);
  expertToggle.textContent = state.expertMode ? "Pro Tools On" : "Pro Tools";
  expertToggle.setAttribute("aria-pressed", state.expertMode ? "true" : "false");
}
function renderTheme() {
  document.documentElement.setAttribute("data-theme", state.theme);
  if (themeToggle) themeToggle.textContent = state.theme === "dark" ? "Light" : "Dark";
}
function renderKeywords(target, items) {
  const max = Math.max(1, ...items.map((item) => item.count), 1);
  target.innerHTML = items.map((item, index) => `<span class="keyword" style="font-size:${0.88 + (item.count/max)*1.15}rem; color:hsl(${(index*41)%360}, 88%, 73%)">${item.word}</span>`).join("");
}
function renderHashtags(items) { hashtags.innerHTML = items.map((item) => `<span class="hashtag-chip"><strong>${item.tag}</strong><span>${item.count}</span></span>`).join(""); }
function renderSocialLeaders(items) {
  socialLeaders.innerHTML = items.map((item) => `<article class="social-item"><div class="social-top"><span class="social-score">${item.social_score}</span><strong>${item.title}</strong></div><div class="social-meta"><button class="filter-chip" data-source="${item.source}">${item.source}</button><span>${item.regions.join(" / ")}</span><span>${item.topics.join(" / ")}</span></div><div class="platforms">${item.hashtags.map((tag) => `<span class="tag-pill">${tag}</span>`).join("")}${item.social_platforms.map((platform) => `<span class="platform-pill">${platform}</span>`).join("")}<button class="action-btn story-detail-btn" data-open-story="${item.id}" type="button">Details</button></div></article>`).join("");
  bindFilterButtons(socialLeaders);
  socialLeaders.querySelectorAll("[data-open-story]").forEach((node) => node.addEventListener("click", (event) => { event.stopPropagation(); openStoryDetail(items.find((item)=>item.id===node.dataset.openStory)); }));
}
function renderHeadlineList(target, items) {
  target.innerHTML = items.map((item) => `<article class="headline"><div class="headline-meta"><button class="filter-chip" data-source="${item.source}">${item.source}</button><span>${item.source_category}</span><span>${item.regions.join(" / ")}</span><span>${formatTime(item.published_at)}</span></div><h3><a href="${item.link}" target="_blank" rel="noreferrer">${item.title}</a></h3><p>${cleanSummary(item.summary).slice(0, 220)}</p><div class="headline-footer">${item.topics.map((topic) => `<button class="filter-chip" data-topic="${topic}" type="button">${topic}</button>`).join("")}${item.hashtags.map((tag) => `<span class="tag-pill">${tag}</span>`).join("")}<span class="platform-pill">Pulse ${item.social_score}</span><button class="action-btn story-detail-btn" data-open-story="${item.id}" type="button">Details</button></div></article>`).join("");
  bindFilterButtons(target);
  target.querySelectorAll("[data-open-story]").forEach((node) => node.addEventListener("click", (event) => { event.stopPropagation(); openStoryDetail(items.find((item)=>item.id===node.dataset.openStory)); }));
}
function renderHeadlines(items) { headlineCount.textContent = `${items.length} stories visible`; renderHeadlineList(headlines, items); }
function renderFilters(snapshot) {
  const topicOptions = ["All", ...Object.keys(snapshot.topic_totals || {}).sort((a,b)=>(snapshot.topic_totals[b]||0)-(snapshot.topic_totals[a]||0))];
  const regionOptions = ["All", ...Object.keys(snapshot.region_totals || {}).sort((a,b)=>(snapshot.region_totals[b]||0)-(snapshot.region_totals[a]||0))];
  topicFilter.innerHTML = topicOptions.map((value) => `<option value="${value}" ${value===state.topic?"selected":""}>${value}</option>`).join("");
  regionFilter.innerHTML = regionOptions.map((value) => `<option value="${value}" ${value===state.region?"selected":""}>${value}</option>`).join("");
}
function renderTimeline(points) {
  const width = canvas.clientWidth, height = 260, ratio = globalThis.devicePixelRatio || 1;
  canvas.width = width * ratio; canvas.height = height * ratio; ctx.setTransform(ratio,0,0,ratio,0,0); ctx.clearRect(0,0,width,height);
  const max = Math.max(1, ...points.map((point) => point.total || 0), 1); const stepX = width / Math.max(1, points.length - 1);
  ctx.beginPath(); points.forEach((point, index) => { const x=index*stepX; const y=height-30-((point.total||0)/max)*(height-70); index===0?ctx.moveTo(x,y):ctx.lineTo(x,y); });
  ctx.strokeStyle="#36d1dc"; ctx.lineWidth=3; ctx.stroke(); ctx.lineTo(width,height-20); ctx.lineTo(0,height-20); ctx.closePath(); ctx.fillStyle="rgba(54, 209, 220, 0.10)"; ctx.fill();
  ctx.fillStyle="#90a5bf"; ctx.font='11px "IBM Plex Mono"'; points.forEach((point,index)=>{ if(index%4!==0 && index!==points.length-1) return; ctx.fillText(formatTime(point.minute || point.bucket), index*stepX, height-4); });
}
function renderClusters(items) {
  clusterList.innerHTML = items.map((item) => `<article class="stack-item" data-cluster-lead="${item.lead_story?.id || ""}"><div class="ops-head"><strong>${item.label}</strong><span>${item.story_count}</span></div><p class="stack-copy">${item.summary}</p><div class="headline-footer"><span class="platform-pill">Momentum ${item.momentum_score}</span></div></article>`).join("");
  clusterList.querySelectorAll("[data-cluster-lead]").forEach((node)=>node.addEventListener("click",()=>{ const lead=(state.snapshot?.headlines||[]).find((story)=>story.id===node.dataset.clusterLead); if(lead) applyFilter({ topic: lead.topics[0] || "All", region: lead.regions[0] || "All" }); }));
}
function renderSavedViews() {
  savedViews.innerHTML = state.savedViews.length ? state.savedViews.map((item, index) => `<article class="stack-item" data-saved-index="${index}"><div class="ops-head"><strong>${item.name}</strong><span>${item.segment || item.view}</span></div><p class="stack-copy">${item.topic || "All topics"} / ${item.region || "All regions"}</p></article>`).join("") : `<article class="stack-item"><p class="stack-copy">No saved views yet. Save your current setup here.</p></article>`;
  savedViews.querySelectorAll("[data-saved-index]").forEach((node)=>node.addEventListener("click",()=>applyFilter(state.savedViews[Number(node.dataset.savedIndex)])));
}
function renderAlertRules() {
  alertRules.innerHTML = state.alertRules.length ? state.alertRules.map((item) => `<article class="stack-item"><div class="ops-head"><strong>${item.name}</strong><span>${item.threshold}+</span></div><p class="stack-copy">${item.scope}</p></article>`).join("") : `<article class="stack-item"><p class="stack-copy">No alert rules yet. Add topic spike or high pulse alerts.</p></article>`;
}
function renderSourceTrust(items) {
  sourceTrust.innerHTML = items.slice(0, 6).map((item) => `<article class="trust-card"><div class="ops-head"><strong>${item.name}</strong><span>${Math.round(item.credibility_score*100)}</span></div><p class="trust-copy">${item.quality_tier} / ${item.bias_label}</p><p class="trust-copy">${item.transparency_note}</p><div class="headline-footer"><span class="platform-pill">${item.recent_story_count} recent stories</span></div></article>`).join("");
}
function renderDeepDiveCards(items) {
  deepDiveCards.innerHTML = DEEP_DIVE_TRACKS.map((track) => { const trackItems = items.filter(track.matcher); const lead = [...trackItems].sort((a,b)=>b.social_score-a.social_score)[0]; const keywords = keywordCountsFromItems(trackItems, 2); return `<article class="deep-dive-card" data-deep-dive="${track.id}"><div class="deep-dive-top"><span class="deep-dive-label">${track.label}</span><span class="deep-dive-score">${trackItems.length}</span></div><p class="deep-dive-kicker">${lead ? lead.source : "No active source"}</p><div class="deep-dive-title">${lead ? lead.title : `No strong ${track.label.toLowerCase()} signal yet`}</div><p class="deep-dive-copy">${lead ? cleanSummary(lead.summary).slice(0, 120) : "This track will populate automatically as global coverage updates."}</p><div class="deep-dive-tags">${(lead?.topics || []).slice(0,2).map((topic)=>`<span class="deep-dive-pill">${topic}</span>`).join("")}${keywords.map((item)=>`<span class="deep-dive-pill">${item.word}</span>`).join("")}</div></article>`; }).join("");
  deepDiveCards.querySelectorAll("[data-deep-dive]").forEach((node) => node.addEventListener("click", () => { const track = DEEP_DIVE_TRACKS.find((item) => item.id === node.dataset.deepDive); const items = globalItems().filter(track.matcher); state.view = "global"; renderViewTabs(); applyViewState(); renderHeadlineList(globalHeadlines, items); globalCount.textContent = `${items.length} ${track.label.toLowerCase()} stories`; }));
}
function renderGlobalDashboard() {
  const items = globalItems(); const leaders = [...items].sort((a,b)=>b.social_score-a.social_score); const globalTopicData = countBy(items, (item)=>item.topics).slice(0,8); const globalSourceData = countBy(items, (item)=>[item.source]).slice(0,8); const keywords = keywordCountsFromItems(items,14);
  renderStoryCard(globalSpotlight, leaders[0], { className:"global-spotlight-card", metaClass:"story-meta", summaryClass:"global-summary-copy", emptyText:"No global story is active right now." });
  globalSummary.innerHTML = [{label:"Global stories",value:items.length,copy:items.length?"World-news items currently in the dashboard":"Waiting for global feed items"},{label:"Lead source",value:globalSourceData[0]?.[0]||"No source",copy:globalSourceData[0]?`${globalSourceData[0][1]} active stories`:"No source mix yet"},{label:"Top world theme",value:globalTopicData[0]?.[0]||"General",copy:globalTopicData[0]?`${globalTopicData[0][1]} global matches`:"No topic cluster yet"}].map((card)=>`<article class="global-summary-card"><span class="global-card-label">${card.label}</span><strong>${card.value}</strong><p class="global-card-copy">${card.copy}</p></article>`).join("");
  renderDeepDiveCards(items); renderBars(globalTopics, globalTopicData, "linear-gradient(90deg, #36d1dc, #94a3ff)", (label)=>applyFilter({ topic: label, view: "global", segment: "Global" })); renderBars(globalSources, globalSourceData, "linear-gradient(90deg, #ff8a00, #ffd166)", (label)=>applyFilter({ query: label, view: "global", segment: "Global" })); renderKeywords(globalKeywords, keywords); globalCount.textContent = `${items.length} global stories`; renderHeadlineList(globalHeadlines, items);
}
async function openStoryDetail(item) {
  if (!item) return;
  let payload = null;
  try {
    const response = await fetch(`/api/v1/stories/${item.id}`);
    if (response.ok) payload = await response.json();
  } catch (_error) {
  }

  const story = payload?.story || item;
  const related = payload?.related || (state.snapshot?.headlines || []).filter((entry) => entry.id !== story.id && entry.topics.some((topic) => story.topics.includes(topic))).slice(0, 4);
  const sourceHistory = payload?.source_history || (state.snapshot?.headlines || []).filter((entry) => entry.source === story.source).slice(0, 4);
  const explanation = payload?.why_tagged || story.social_explanation || [];

  storyDetail.innerHTML = `<div class="story-detail-grid"><div class="story-meta"><span class="platform-pill">${story.source}</span><span class="platform-pill">${story.source_category}</span><span class="platform-pill">Bias ${story.source_bias_label}</span><span class="platform-pill">Trust ${Math.round(story.source_credibility_score*100)}</span><span class="platform-pill">Pulse ${story.social_score} / ${story.social_confidence_band}</span></div><h2>${story.title}</h2><p class="spotlight-summary">${cleanSummary(story.summary)}</p><div class="story-tags">${story.topics.map((topic)=>`<button class="filter-chip" data-topic="${topic}">${topic}</button>`).join("")}${story.regions.map((region)=>`<button class="filter-chip" data-region="${region}">${region}</button>`).join("")}${story.hashtags.map((tag)=>`<span class="tag-pill">${tag}</span>`).join("")}</div><div class="story-grid"><section><h3>Why this was tagged</h3><div class="stack-list">${explanation.map((entry)=>`<article class="stack-item"><div class="ops-head"><strong>${entry.factor.replaceAll("_", " ")}</strong><span>${entry.weight}</span></div><p class="stack-copy">${entry.reason}</p></article>`).join("") || `<article class="stack-item"><p class="stack-copy">No enrichment trace is available yet.</p></article>`}</div></section><aside class="story-sidebar"><section><h3>Related stories</h3><div class="stack-list">${related.length ? related.map((entry)=>`<article class="stack-item" data-related-id="${entry.id}"><strong>${entry.title}</strong><p class="stack-copy">${entry.source}</p></article>`).join("") : `<article class="stack-item"><p class="stack-copy">No related stories yet.</p></article>`}</div></section><section><h3>Source history</h3><div class="stack-list">${sourceHistory.length ? sourceHistory.map((entry)=>`<article class="stack-item" data-related-id="${entry.id}"><strong>${entry.title}</strong><p class="stack-copy">${formatTime(entry.published_at)}</p></article>`).join("") : `<article class="stack-item"><p class="stack-copy">No source history yet.</p></article>`}</div></section></aside></div></div>`;
  bindFilterButtons(storyDetail);
  storyDetail.querySelectorAll("[data-related-id]").forEach((node)=>node.addEventListener("click",()=>openStoryDetail((state.snapshot?.headlines||[]).find((entry)=>entry.id===node.dataset.relatedId) || related.find((entry)=>entry.id===node.dataset.relatedId) || sourceHistory.find((entry)=>entry.id===node.dataset.relatedId))));
  dialog.showModal();
}
function render(snapshot) {
  state.snapshot = snapshot; storyCount.textContent = snapshot.story_count; lastUpdated.textContent = formatTime(snapshot.generated_at);
  renderSummary(snapshot.summary_cards); renderStoryCard(spotlightStory, snapshot.social_leaders[0] || snapshot.headlines[0]); renderSegmentTabs(snapshot.headlines);
  renderBars(sentiment, Object.entries(snapshot.sentiment_totals), "linear-gradient(90deg, #1ed760, #ff5d73)", (label)=>applyFilter({ query: label }));
  renderBars(topics, Object.entries(snapshot.topic_totals).sort((a,b)=>b[1]-a[1]).slice(0,8), "linear-gradient(90deg, #36d1dc, #5b86e5)", (label)=>applyFilter({ topic: label }));
  renderBars(regions, Object.entries(snapshot.region_totals).sort((a,b)=>b[1]-a[1]).slice(0,8), "linear-gradient(90deg, #ff8a00, #ffd166)", (label)=>applyFilter({ region: label }));
  renderBars(sources, Object.entries(snapshot.source_totals).sort((a,b)=>b[1]-a[1]).slice(0,8), "linear-gradient(90deg, #7c3aed, #36d1dc)", (label)=>applyFilter({ query: label }));
  renderKeywords(trending, snapshot.trending); renderHashtags(snapshot.hashtags); renderSocialLeaders(snapshot.social_leaders); renderFilters(snapshot); renderHeadlines(filteredHeadlines()); renderTimeline(snapshot.timeline); renderClusters(snapshot.clusters || []); renderSourceTrust(snapshot.source_trust || []); renderSavedViews(); renderAlertRules(); renderGlobalDashboard();
}
async function hydrate() { const response = await fetch("/api/v1/snapshot").catch(()=>fetch("/api/snapshot")); render(await response.json()); }
function connect() {
  const protocol = globalThis.location.protocol === "https:" ? "wss" : "ws"; const socket = new WebSocket(`${protocol}://${globalThis.location.host}/ws`);
  socket.addEventListener("open", () => { socketStatus.textContent = "live"; if (state.pingTimer) clearInterval(state.pingTimer); state.pingTimer = setInterval(() => { if (socket.readyState === WebSocket.OPEN) socket.send("ping"); }, 15000); });
  socket.addEventListener("message", (event) => { const message = JSON.parse(event.data); if (message.type === "snapshot") render(message.payload); });
  socket.addEventListener("close", () => { socketStatus.textContent = "reconnecting"; if (state.pingTimer) { clearInterval(state.pingTimer); state.pingTimer = null; } setTimeout(connect, 1500); });
}
searchInput.addEventListener("input", (event) => applyFilter({ query: event.target.value }));
topicFilter.addEventListener("change", (event) => applyFilter({ topic: event.target.value }));
regionFilter.addEventListener("change", (event) => applyFilter({ region: event.target.value }));
saveViewBtn.addEventListener("click", () => { const name = prompt("Save this view as:", `${state.segment} Desk`); if (!name) return; state.savedViews.unshift({ name, topic: state.topic, region: state.region, query: state.query, segment: state.segment, view: state.view }); state.savedViews = state.savedViews.slice(0, 8); persistLocalState(); renderSavedViews(); });
saveAlertBtn.addEventListener("click", () => { const name = prompt("Alert name:", "High pulse monitor"); if (!name) return; const threshold = Number(prompt("Minimum pulse score (0-100):", "80") || 80); state.alertRules.unshift({ name, threshold, scope: `${state.segment} / ${state.topic} / ${state.region}` }); state.alertRules = state.alertRules.slice(0, 8); persistLocalState(); renderAlertRules(); });
if (expertToggle) expertToggle.addEventListener("click", () => { state.expertMode = !state.expertMode; persistLocalState(); renderExpertMode(); });
if (themeToggle) themeToggle.addEventListener("click", () => { state.theme = state.theme === "dark" ? "light" : "dark"; persistLocalState(); renderTheme(); });
globalThis.addEventListener("resize", () => { if (state.snapshot) renderTimeline(state.snapshot.timeline); });
hydrate().catch(() => { socketStatus.textContent = "offline"; }); renderViewTabs(); applyViewState(); renderExpertMode(); renderTheme(); connect();

