const state = {
  snapshot: null,
  pingTimer: null,
  query: "",
  topic: "All",
  region: "All",
  segment: "All",
  view: "overview",
};

const storyCount = document.getElementById("story-count");
const lastUpdated = document.getElementById("last-updated");
const socketStatus = document.getElementById("socket-status");
const summaryCards = document.getElementById("summary-cards");
const sentiment = document.getElementById("sentiment");
const topics = document.getElementById("topics");
const regions = document.getElementById("regions");
const sources = document.getElementById("sources");
const trending = document.getElementById("trending");
const hashtags = document.getElementById("hashtags");
const socialLeaders = document.getElementById("social-leaders");
const headlines = document.getElementById("headlines");
const headlineCount = document.getElementById("headline-count");
const spotlightStory = document.getElementById("spotlight-story");
const segmentTabs = document.getElementById("segment-tabs");
const viewTabs = document.getElementById("view-tabs");
const topicFilter = document.getElementById("topic-filter");
const regionFilter = document.getElementById("region-filter");
const searchInput = document.getElementById("search-input");
const globalSpotlight = document.getElementById("global-spotlight");
const globalSummary = document.getElementById("global-summary");
const globalTopics = document.getElementById("global-topics");
const globalSources = document.getElementById("global-sources");
const globalKeywords = document.getElementById("global-keywords");
const globalHeadlines = document.getElementById("global-headlines");
const globalCount = document.getElementById("global-count");
const deepDiveCards = document.getElementById("deep-dive-cards");
const canvas = document.getElementById("timeline");
const ctx = canvas.getContext("2d");
const viewPanels = Array.from(document.querySelectorAll("[data-view-panel]"));

const VIEW_OPTIONS = [
  { id: "overview", label: "Overview" },
  { id: "analytics", label: "Analytics" },
  { id: "stream", label: "Stream" },
  { id: "global", label: "Global" },
];

const SEGMENT_PRESETS = [
  { id: "All", label: "All Desk", matcher: () => true },
  { id: "India", label: "India", matcher: (item) => item.topics.includes("India") || item.source_category === "India" },
  { id: "Governance", label: "Governance", matcher: (item) => item.topics.includes("Governance") },
  { id: "Economy", label: "Economy", matcher: (item) => item.topics.includes("Economy") || item.source_category === "Business" },
  { id: "Startups", label: "Startups", matcher: (item) => item.topics.includes("Startups") || item.topics.includes("AI & Tech") },
  { id: "Cricket", label: "Cricket", matcher: (item) => item.topics.includes("Cricket") || item.source_category === "Sports" },
  { id: "Global", label: "Global", matcher: (item) => item.regions.includes("Global") || item.source_category === "Global" },
];

const DEEP_DIVE_TRACKS = [
  {
    id: "politics",
    label: "Politics",
    matcher: (item) => item.topics.includes("Governance") || item.topics.includes("Politics") || /election|president|prime minister|parliament|cabinet|policy/i.test(`${item.title} ${item.summary}`),
  },
  {
    id: "markets",
    label: "Markets",
    matcher: (item) => item.topics.includes("Economy") || /market|stocks|inflation|bank|trade|oil|tariff|currency/i.test(`${item.title} ${item.summary}`),
  },
  {
    id: "conflict",
    label: "Conflict",
    matcher: (item) => item.topics.includes("Geopolitics") || /war|attack|military|missile|ceasefire|troops|border/i.test(`${item.title} ${item.summary}`),
  },
  {
    id: "tech",
    label: "Tech",
    matcher: (item) => item.topics.includes("AI & Tech") || item.topics.includes("Startups") || /ai|chip|software|startup|cyber|cloud|platform/i.test(`${item.title} ${item.summary}`),
  },
  {
    id: "sports",
    label: "Sports",
    matcher: (item) => item.topics.includes("Sports") || item.topics.includes("Cricket") || /match|league|tournament|cup|goal|innings/i.test(`${item.title} ${item.summary}`),
  },
];

function formatTime(iso) {
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function cleanSummary(text) {
  return text.replace(/<[^>]+>/g, "").trim();
}

function keywordCountsFromItems(items, limit = 12) {
  const counts = new Map();
  items.forEach((item) => {
    const text = `${item.title} ${item.summary}`.toLowerCase();
    text.split(/[^a-z0-9]+/).forEach((word) => {
      if (word.length < 5 || ["about", "their", "there", "world", "india", "after", "today", "latest"].includes(word)) {
        return;
      }
      counts.set(word, (counts.get(word) || 0) + 1);
    });
  });
  return Array.from(counts.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit)
    .map(([word, count]) => ({ word, count }));
}

function countBy(items, selector) {
  const map = new Map();
  items.forEach((item) => {
    selector(item).forEach((value) => {
      map.set(value, (map.get(value) || 0) + 1);
    });
  });
  return Array.from(map.entries()).sort((a, b) => b[1] - a[1]);
}

function globalItems() {
  return (state.snapshot?.headlines || []).filter((item) => item.regions.includes("Global") || item.source_category === "Global");
}

function matchesFilters(item) {
  const query = state.query.toLowerCase().trim();
  const haystack = `${item.title} ${item.summary} ${item.regions.join(" ")} ${item.topics.join(" ")}`.toLowerCase();
  const matchesQuery = !query || haystack.includes(query);
  const matchesTopic = state.topic === "All" || item.topics.includes(state.topic);
  const matchesRegion = state.region === "All" || item.regions.includes(state.region);
  const segment = SEGMENT_PRESETS.find((preset) => preset.id === state.segment) || SEGMENT_PRESETS[0];
  return matchesQuery && matchesTopic && matchesRegion && segment.matcher(item);
}

function filteredHeadlines() {
  return (state.snapshot?.headlines || []).filter(matchesFilters);
}

function renderBars(target, entries, colors) {
  const max = Math.max(1, ...entries.map((entry) => entry[1]));
  target.innerHTML = entries.map(([label, count]) => `
    <div class="metric-row">
      <header><strong>${label}</strong><span>${count}</span></header>
      <div class="track"><div class="fill" style="width:${(count / max) * 100}%; background:${colors};"></div></div>
    </div>
  `).join("");
}

function renderSummary(cards) {
  summaryCards.innerHTML = cards.map((card) => `
    <article class="summary-card">
      <span class="status-label">${card.label}</span>
      <strong>${card.value}</strong>
      <p>${card.subtext}</p>
    </article>
  `).join("");
}

function renderStoryCard(target, item, options = {}) {
  if (!item) {
    target.innerHTML = `<p class="spotlight-summary">${options.emptyText || "Waiting for a lead story."}</p>`;
    return;
  }
  target.innerHTML = `
    <article class="${options.className || "spotlight-card"}">
      <div class="${options.metaClass || "spotlight-meta"}">
        <span class="platform-pill">${item.source}</span>
        <span class="platform-pill">${item.source_category}</span>
        <span class="platform-pill">Pulse ${item.social_score}</span>
      </div>
      <h3><a href="${item.link}" target="_blank" rel="noreferrer">${item.title}</a></h3>
      <p class="${options.summaryClass || "spotlight-summary"}">${cleanSummary(item.summary).slice(0, 240)}</p>
      <div class="headline-footer">
        ${item.regions.map((region) => `<span class="tag-pill">${region}</span>`).join("")}
        ${item.topics.map((topic) => `<span class="tag-pill">${topic}</span>`).join("")}
        ${item.hashtags.map((tag) => `<span class="tag-pill">${tag}</span>`).join("")}
      </div>
      <div class="platforms">
        ${item.social_platforms.map((platform) => `<span class="platform-pill">${platform}</span>`).join("")}
      </div>
    </article>
  `;
}

function renderSegmentTabs(items) {
  segmentTabs.innerHTML = SEGMENT_PRESETS.map((preset) => {
    const count = items.filter((item) => preset.matcher(item)).length;
    return `
      <button class="segment-tab ${preset.id === state.segment ? "active" : ""}" data-segment="${preset.id}">
        <span>${preset.label}</span>
        <span class="segment-count">${count}</span>
      </button>
    `;
  }).join("");

  segmentTabs.querySelectorAll("[data-segment]").forEach((button) => {
    button.addEventListener("click", () => {
      state.segment = button.dataset.segment;
      if (button.dataset.segment === "Global") {
        state.view = "global";
        applyViewState();
        renderViewTabs();
      }
      if (state.snapshot) {
        render(state.snapshot);
      }
    });
  });
}

function renderViewTabs() {
  viewTabs.innerHTML = VIEW_OPTIONS.map((view) => `
    <button class="view-tab ${view.id === state.view ? "active" : ""}" data-view="${view.id}">
      ${view.label}
    </button>
  `).join("");

  viewTabs.querySelectorAll("[data-view]").forEach((button) => {
    button.addEventListener("click", () => {
      state.view = button.dataset.view;
      if (state.view === "global") {
        state.segment = "Global";
      }
      applyViewState();
      renderViewTabs();
      if (state.snapshot) {
        render(state.snapshot);
      }
    });
  });
}

function applyViewState() {
  viewPanels.forEach((panel) => {
    const supportedViews = panel.dataset.viewPanel.split(" ");
    panel.classList.toggle("hidden", !supportedViews.includes(state.view));
  });
}

function renderKeywords(target, items) {
  const max = Math.max(1, ...items.map((item) => item.count));
  target.innerHTML = items.map((item, index) => {
    const size = 0.88 + (item.count / max) * 1.15;
    const hue = (index * 41) % 360;
    return `<span class="keyword" style="font-size:${size}rem; color:hsl(${hue}, 88%, 73%)">${item.word}</span>`;
  }).join("");
}

function renderHashtags(items) {
  hashtags.innerHTML = items.map((item) => `
    <span class="hashtag-chip"><strong>${item.tag}</strong><span>${item.count}</span></span>
  `).join("");
}

function renderSocialLeaders(items) {
  socialLeaders.innerHTML = items.map((item) => `
    <article class="social-item">
      <div class="social-top">
        <span class="social-score">${item.social_score}</span>
        <strong>${item.title}</strong>
      </div>
      <div class="social-meta">
        <span>${item.source}</span>
        <span>${item.regions.join(" / ")}</span>
        <span>${item.topics.join(" / ")}</span>
      </div>
      <div class="platforms">
        ${item.hashtags.map((tag) => `<span class="tag-pill">${tag}</span>`).join("")}
        ${item.social_platforms.map((platform) => `<span class="platform-pill">${platform}</span>`).join("")}
      </div>
    </article>
  `).join("");
}

function renderHeadlineList(target, items) {
  target.innerHTML = items.map((item) => `
    <article class="headline">
      <div class="headline-meta">
        <span>${item.source}</span>
        <span>${item.source_category}</span>
        <span>${item.regions.join(" / ")}</span>
        <span>${formatTime(item.published_at)}</span>
      </div>
      <h3><a href="${item.link}" target="_blank" rel="noreferrer">${item.title}</a></h3>
      <p>${cleanSummary(item.summary).slice(0, 220)}</p>
      <div class="headline-footer">
        ${item.topics.map((topic) => `<span class="tag-pill">${topic}</span>`).join("")}
        ${item.hashtags.map((tag) => `<span class="tag-pill">${tag}</span>`).join("")}
        <span class="platform-pill">Pulse ${item.social_score}</span>
      </div>
    </article>
  `).join("");
}

function renderHeadlines(items) {
  headlineCount.textContent = `${items.length} stories visible`;
  renderHeadlineList(headlines, items);
}

function renderFilters(snapshot) {
  const topicOptions = ["All", ...Object.keys(snapshot.topic_totals).sort((a, b) => snapshot.topic_totals[b] - snapshot.topic_totals[a])];
  const regionOptions = ["All", ...Object.keys(snapshot.region_totals).sort((a, b) => snapshot.region_totals[b] - snapshot.region_totals[a])];

  topicFilter.innerHTML = topicOptions.map((value) => `<option value="${value}" ${value === state.topic ? "selected" : ""}>${value}</option>`).join("");
  regionFilter.innerHTML = regionOptions.map((value) => `<option value="${value}" ${value === state.region ? "selected" : ""}>${value}</option>`).join("");
}

function renderTimeline(points) {
  const width = canvas.clientWidth;
  const height = 260;
  const ratio = globalThis.devicePixelRatio || 1;
  canvas.width = width * ratio;
  canvas.height = height * ratio;
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  ctx.clearRect(0, 0, width, height);

  const max = Math.max(1, ...points.map((point) => point.total || 0));
  const stepX = width / Math.max(1, points.length - 1);

  ctx.beginPath();
  points.forEach((point, index) => {
    const x = index * stepX;
    const y = height - 30 - ((point.total || 0) / max) * (height - 70);
    if (index === 0) {
      ctx.moveTo(x, y);
    } else {
      ctx.lineTo(x, y);
    }
  });
  ctx.strokeStyle = "#36d1dc";
  ctx.lineWidth = 3;
  ctx.stroke();

  ctx.lineTo(width, height - 20);
  ctx.lineTo(0, height - 20);
  ctx.closePath();
  ctx.fillStyle = "rgba(54, 209, 220, 0.10)";
  ctx.fill();

  ctx.fillStyle = "#90a5bf";
  ctx.font = '11px "IBM Plex Mono"';
  points.forEach((point, index) => {
    if (index % 4 !== 0 && index !== points.length - 1) {
      return;
    }
    ctx.fillText(formatTime(point.minute), index * stepX, height - 4);
  });
}

function renderDeepDiveCards(items) {
  deepDiveCards.innerHTML = DEEP_DIVE_TRACKS.map((track) => {
    const trackItems = items.filter(track.matcher);
    const lead = [...trackItems].sort((a, b) => b.social_score - a.social_score)[0];
    const keywords = keywordCountsFromItems(trackItems, 2);
    return `
      <article class="deep-dive-card">
        <div class="deep-dive-top">
          <span class="deep-dive-label">${track.label}</span>
          <span class="deep-dive-score">${trackItems.length}</span>
        </div>
        <p class="deep-dive-kicker">${lead ? lead.source : "No active source"}</p>
        <div class="deep-dive-title">${lead ? lead.title : `No strong ${track.label.toLowerCase()} signal yet`}</div>
        <p class="deep-dive-copy">${lead ? cleanSummary(lead.summary).slice(0, 120) : "This track will populate automatically as global coverage updates."}</p>
        <div class="deep-dive-tags">
          ${(lead?.topics || []).slice(0, 2).map((topic) => `<span class="deep-dive-pill">${topic}</span>`).join("")}
          ${keywords.map((item) => `<span class="deep-dive-pill">${item.word}</span>`).join("")}
        </div>
      </article>
    `;
  }).join("");
}

function renderGlobalDashboard() {
  const items = globalItems();
  const leaders = [...items].sort((a, b) => b.social_score - a.social_score);
  const globalTopicData = countBy(items, (item) => item.topics).slice(0, 8);
  const globalSourceData = countBy(items, (item) => [item.source]).slice(0, 8);
  const keywords = keywordCountsFromItems(items, 14);

  renderStoryCard(globalSpotlight, leaders[0], {
    className: "global-spotlight-card",
    metaClass: "global-card-meta",
    summaryClass: "global-summary-copy",
    emptyText: "No global story is active right now.",
  });

  globalSummary.innerHTML = [
    {
      label: "Global stories",
      value: items.length,
      copy: items.length ? "World-news items currently in the dashboard" : "Waiting for global feed items",
    },
    {
      label: "Lead source",
      value: globalSourceData[0]?.[0] || "No source",
      copy: globalSourceData[0] ? `${globalSourceData[0][1]} active stories` : "No source mix yet",
    },
    {
      label: "Top world theme",
      value: globalTopicData[0]?.[0] || "General",
      copy: globalTopicData[0] ? `${globalTopicData[0][1]} global matches` : "No topic cluster yet",
    },
  ].map((card) => `
    <article class="global-summary-card">
      <span class="global-card-label">${card.label}</span>
      <strong>${card.value}</strong>
      <p class="global-card-copy">${card.copy}</p>
    </article>
  `).join("");

  renderDeepDiveCards(items);
  renderBars(globalTopics, globalTopicData, "linear-gradient(90deg, #36d1dc, #94a3ff)");
  renderBars(globalSources, globalSourceData, "linear-gradient(90deg, #ff8a00, #ffd166)");
  renderKeywords(globalKeywords, keywords);
  globalCount.textContent = `${items.length} global stories`;
  renderHeadlineList(globalHeadlines, items);
}

function render(snapshot) {
  state.snapshot = snapshot;
  storyCount.textContent = snapshot.story_count;
  lastUpdated.textContent = formatTime(snapshot.generated_at);
  renderSummary(snapshot.summary_cards);
  renderStoryCard(spotlightStory, snapshot.social_leaders[0] || snapshot.headlines[0]);
  renderSegmentTabs(snapshot.headlines);
  renderBars(sentiment, Object.entries(snapshot.sentiment_totals), "linear-gradient(90deg, #1ed760, #ff5d73)");
  renderBars(topics, Object.entries(snapshot.topic_totals).sort((a, b) => b[1] - a[1]).slice(0, 8), "linear-gradient(90deg, #36d1dc, #5b86e5)");
  renderBars(regions, Object.entries(snapshot.region_totals).sort((a, b) => b[1] - a[1]).slice(0, 8), "linear-gradient(90deg, #ff8a00, #ffd166)");
  renderBars(sources, Object.entries(snapshot.source_totals).sort((a, b) => b[1] - a[1]).slice(0, 8), "linear-gradient(90deg, #7c3aed, #36d1dc)");
  renderKeywords(trending, snapshot.trending);
  renderHashtags(snapshot.hashtags);
  renderSocialLeaders(snapshot.social_leaders);
  renderFilters(snapshot);
  renderHeadlines(filteredHeadlines());
  renderTimeline(snapshot.timeline);
  renderGlobalDashboard();
}

async function hydrate() {
  const response = await fetch("/api/snapshot");
  render(await response.json());
}

function connect() {
  const protocol = globalThis.location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(`${protocol}://${globalThis.location.host}/ws`);

  socket.addEventListener("open", () => {
    socketStatus.textContent = "live";
    if (state.pingTimer) {
      clearInterval(state.pingTimer);
    }
    state.pingTimer = setInterval(() => {
      if (socket.readyState === WebSocket.OPEN) {
        socket.send("ping");
      }
    }, 15000);
  });

  socket.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    if (message.type === "snapshot") {
      render(message.payload);
    }
  });

  socket.addEventListener("close", () => {
    socketStatus.textContent = "reconnecting";
    if (state.pingTimer) {
      clearInterval(state.pingTimer);
      state.pingTimer = null;
    }
    setTimeout(connect, 1500);
  });
}

searchInput.addEventListener("input", (event) => {
  state.query = event.target.value;
  if (state.snapshot) {
    renderHeadlines(filteredHeadlines());
  }
});

topicFilter.addEventListener("change", (event) => {
  state.topic = event.target.value;
  if (state.snapshot) {
    renderHeadlines(filteredHeadlines());
  }
});

regionFilter.addEventListener("change", (event) => {
  state.region = event.target.value;
  if (state.snapshot) {
    renderHeadlines(filteredHeadlines());
  }
});

globalThis.addEventListener("resize", () => {
  if (state.snapshot) {
    renderTimeline(state.snapshot.timeline);
  }
});

hydrate().catch(() => {
  socketStatus.textContent = "offline";
});
renderViewTabs();
applyViewState();
connect();

