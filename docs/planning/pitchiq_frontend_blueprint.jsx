import { useState } from "react";

const ACCENT = "#b5ff47";
const CYAN = "#00e5ff";
const AMBER = "#ffb300";
const ROSE = "#ff4d6d";
const MUTED = "#3a4a5a";
const SURFACE = "#0e1520";
const CARD = "#111c2a";
const BORDER = "#1e2e40";

const pages = [
  {
    id: "landing",
    number: "01",
    name: "Landing / Command Centre",
    icon: "⚡",
    role: "Entry point. Establishes context, surfaces live data, drives users into a league.",
    apiCalls: ["GET /api/live-scores", "GET /api/leagues", "GET /api/featured-predictions"],
    layout: {
      description: "Full-viewport dark hero with a live data ticker pinned at the very top. Centre contains a bold league selector grid. Below it, a live scores strip animates in real time. Featured prediction cards sit at the bottom as the CTA.",
      sections: [
        { name: "Live Data Ticker", pos: "TOP EDGE · Full width · 32px tall", color: CYAN, desc: "Horizontally scrolling marquee of live scores and recent results. Pulls from GET /api/live-scores every 30s. Format: 'EPL · Arsenal 2–1 Chelsea  |  UCL · PSG 0–0 Man City ·'. Colour-coded: green = home win, red = away win, amber = in-play." },
        { name: "NavBar", pos: "TOP · 56px", color: MUTED, desc: "Left: PitchIQ wordmark + version tag. Right: Leagues, Predictions, Model Health, Settings icon. Active page underlined with ACCENT colour. On scroll, background blurs (backdrop-filter)." },
        { name: "Hero Headline", pos: "CENTRE · Full width", color: ACCENT, desc: "Large editorial type: 'PREDICT THE PITCH.' Sub-line: 'Real-time football intelligence powered by stacked ensemble ML.' No animation — static and confident. Font: Syne ExtraBold at 64px." },
        { name: "League Selector Grid", pos: "CENTRE · 6-column card grid", color: "#e040fb", desc: "One card per competition: EPL, La Liga, Bundesliga, Serie A, Ligue 1, Champions League. Each card shows: competition logo placeholder, name, season, and a live match count badge if games are in progress. Hover lifts card with glow. Click navigates to /league/:id. Data from GET /api/leagues." },
        { name: "Live Scores Strip", pos: "BELOW GRID · Full width horizontal scroll", color: AMBER, desc: "Cards for all matches played today or in the last 24h. Each card: home team, score, away team, minute or FT, xG bars underneath. Auto-refreshes every 60s. Skeleton loaders on initial load." },
        { name: "Featured Predictions", pos: "BOTTOM · 3-column cards", color: ROSE, desc: "3 high-confidence upcoming matches chosen by the model (probability > 70% on one outcome). Each card: teams, kickoff time, outcome probability bar, confidence label (HIGH / MEDIUM). CTA button: 'See Full Prediction' → /predict/:matchId." }
      ]
    },
    behaviour: [
      "On mount: fetch leagues, live scores, and featured predictions in parallel (Promise.all).",
      "Live ticker auto-scrolls via CSS animation; re-fetches every 30s and splices in new data without resetting scroll position.",
      "League card hover triggers a CSS glow pulse using the competition's brand colour (stored in config).",
      "If a match is live (in-play), its score card pulses with an amber ring every 2s.",
      "Featured prediction cards display a skeleton loader for 400ms then fade in with staggered animation-delay."
    ]
  },
  {
    id: "league",
    number: "02",
    name: "League Hub",
    icon: "🏆",
    role: "Central page for a selected competition. Surfaces league table, top scorers, team cards, and live fixture list.",
    apiCalls: ["GET /api/league/:id/table", "GET /api/league/:id/top-scorers", "GET /api/league/:id/fixtures?status=upcoming", "GET /api/league/:id/fixtures?status=recent"],
    layout: {
      description: "Two-column master layout. Left sidebar (280px) holds league meta and navigation. Main panel (flex-1) renders tabbed content: TABLE · FIXTURES · TOP SCORERS · TEAMS.",
      sections: [
        { name: "League Sidebar", pos: "LEFT · 280px fixed", color: CYAN, desc: "Top: competition badge, full name, season label (e.g. '2024/25'), country flag. Below: stat pills — Total Teams, Matches Played, Goals Scored, Avg Goals/Game. Bottom: Quick links to each team in the league as clickable chips. All data from GET /api/league/:id." },
        { name: "Tab Bar", pos: "MAIN · TOP · 48px", color: ACCENT, desc: "4 tabs: TABLE | FIXTURES | TOP SCORERS | TEAMS. Tabs are underline-style with ACCENT colour. Active tab re-renders the content panel without page navigation (client-side tab switch)." },
        { name: "League Table (default tab)", pos: "MAIN · Full width table", color: "#e040fb", desc: "Columns: Pos, Team (logo + name), P, W, D, L, GF, GA, GD, Pts, Form (last 5 results as coloured dots: G=green W, R=red L, Y=amber D). Top 4 rows highlighted with Champions League blue left border. Relegation zone: red left border. Rows are clickable — navigates to /team/:id. Data: GET /api/league/:id/table, refreshed every 5 min." },
        { name: "Fixtures Panel (tab)", pos: "MAIN · Grouped by matchweek", color: AMBER, desc: "Groups: LIVE NOW (if any), TODAY, UPCOMING, RECENT. Each fixture row: home team logo + name, score or kickoff time, away team name + logo, predict button. Live matches show minute ticker. Upcoming matches show a 'PREDICT' chip that routes to /predict/:matchId. Recent matches show xG comparison bar on hover." },
        { name: "Top Scorers (tab)", pos: "MAIN · Ranked list", color: ROSE, desc: "Rank, player photo placeholder, player name, team, goals, assists, xG. Sorted by goals desc. Top 3 rows get a gold/silver/bronze rank badge. Data: GET /api/league/:id/top-scorers." },
        { name: "Teams Grid (tab)", pos: "MAIN · 4-column card grid", color: CYAN, desc: "One card per team: badge placeholder, team name, current position, form string (WWDLW), goals for/against, and a 'VIEW TEAM' button. Clicking opens /team/:id. Cards animate in with staggered fade on tab open." }
      ]
    },
    behaviour: [
      "On route mount, fire all 4 API calls in parallel. Show skeleton loaders per section independently.",
      "League table rows highlight on hover. Clicking a team row pushes /team/:id to router.",
      "Live fixtures (in-play) auto-refresh every 60s via setInterval. A 'LIVE' badge pulses green next to the tab label when matches are in progress.",
      "Fixtures tab remembers scroll position when user returns from a team page (sessionStorage).",
      "Top Scorers tab: each row expands on click to show a mini xG vs Goals chart (bar comparison inline)."
    ]
  },
  {
    id: "team",
    number: "03",
    name: "Team Profile",
    icon: "👕",
    role: "Deep-dive into a single team. Shows full match history, upcoming fixtures with prediction CTAs, form analysis, and key stats.",
    apiCalls: ["GET /api/team/:id", "GET /api/team/:id/matches?type=recent&limit=10", "GET /api/team/:id/matches?type=upcoming&limit=5", "GET /api/team/:id/stats/rolling"],
    layout: {
      description: "Three-zone layout. Top hero band with team identity. Below: two-column split — left is a narrow stats panel, right is a wide scrollable match feed.",
      sections: [
        { name: "Team Hero Band", pos: "TOP · Full width · 180px", color: ACCENT, desc: "Dark background with team colour overlay (fetched from config). Left: team badge (large, 96px), team name in Syne ExtraBold, league + season. Right: 4 headline KPIs in large number format — League Position, Points, Goals Scored, Goals Conceded. All live from GET /api/team/:id." },
        { name: "Form Ribbon", pos: "BELOW HERO · Full width · 40px", color: AMBER, desc: "Last 10 match outcomes as colour-coded blocks: W (green), D (amber), L (red). Each block is a square with the scoreline on hover. Built from recent matches data. Animates in left-to-right on page load." },
        { name: "Stats Panel", pos: "LEFT · 300px", color: CYAN, desc: "Rolling stats section (last 5 games): Avg xG For, Avg xG Against, Avg Goals, Clean Sheets, PPDA. Displayed as labelled metric tiles with directional trend arrows (up/down vs prior 5). Source: GET /api/team/:id/stats/rolling. Below: Head-to-head mini table for last 5 H2H meetings (if viewing a specific opponent context)." },
        { name: "Match Feed", pos: "RIGHT · Flex-1 · Scrollable", color: "#e040fb", desc: "Divided into two labelled sections: RECENT MATCHES and UPCOMING FIXTURES. RECENT: each row shows date, opponent, venue (H/A), score, xG home vs xG away as bar, result badge. UPCOMING: each row shows date, opponent, venue, kickoff time, and a large 'PREDICT THIS MATCH' button styled with ACCENT colour. Clicking PREDICT routes to /predict/:matchId with team context pre-filled." },
        { name: "Season Chart", pos: "BOTTOM · Full width", color: ROSE, desc: "Line chart: xG For and xG Against plotted across all played matchweeks this season. Two lines, colour-coded. Tooltip on hover shows matchweek, opponent, result, and exact xG values. Built with recharts LineChart. Data from GET /api/team/:id/stats/rolling expanded to season scope." }
      ]
    },
    behaviour: [
      "Form ribbon builds left-to-right with 40ms stagger per block on mount.",
      "Recent match rows expand on click to reveal a shot map placeholder and full match stats (goals, xG, possession, shots on target).",
      "PREDICT THIS MATCH button is disabled with a 'Insufficient data' tooltip if the match is within 24h and rolling stats are stale.",
      "Stats panel rolling metrics show a sparkline (7-match trend) on hover of each metric tile.",
      "Upcoming fixtures section shows a countdown timer (days:hours) next to each kickoff time."
    ]
  },
  {
    id: "predict",
    number: "04",
    name: "Match Prediction",
    icon: "🎯",
    role: "The core ML interface. Takes a specific upcoming fixture and returns full prediction output: probabilities, SHAP explanations, H2H context, and confidence.",
    apiCalls: ["GET /api/match/:id", "POST /api/predict { home_team, away_team, matchweek, league, date }", "GET /api/match/:id/h2h", "GET /api/match/:id/odds (betting baseline)"],
    layout: {
      description: "Cinematic single-match layout. Top: match header. Centre: split prediction panel. Bottom: explanation and supporting context in tabs.",
      sections: [
        { name: "Match Header", pos: "TOP · Full width · 140px", color: ACCENT, desc: "The two teams facing off. Centre: VS. Left block: home team badge, name, current league position, form dots (last 5). Right block: mirrored for away team. Kickoff date and time centred under VS. League badge top-left. All live from GET /api/match/:id." },
        { name: "Prediction Output Panel", pos: "CENTRE · Full width · Primary visual", color: "#b5ff47", desc: "THE HERO of the page. Three-column probability display: HOME WIN | DRAW | AWAY WIN. Each column shows: outcome label, probability percentage in massive Syne type (e.g. '64%'), a vertical filled bar representing the probability, and a confidence label (HIGH / MEDIUM / LOW). The highest probability outcome glows with ACCENT colour. The model's top pick is labelled 'MODEL PICK' with a small badge. Data from POST /api/predict." },
        { name: "vs Betting Odds Strip", pos: "BELOW PREDICTION PANEL · Slim row", color: AMBER, desc: "Side-by-side: Model probabilities vs Implied probabilities from betting odds (Bet365 via football-data.co.uk). Shows where the model diverges from market consensus — the 'edge'. If model probability > odds probability by >5%, show a green 'VALUE' tag. Data from GET /api/match/:id/odds." },
        { name: "SHAP Explanation Panel (tab)", pos: "BOTTOM · Default tab", color: CYAN, desc: "Horizontal bar chart of top 8 SHAP features driving this prediction. Bars go left (pushes toward away win) or right (pushes toward home win) from a centre zero line. Feature names as labels: rolling_xg_for_5_home, rest_days_away, h2h_home_win_rate, etc. Colour: green = favours prediction, red = works against. From POST /api/predict response (shap_values field)." },
        { name: "Head-to-Head Tab", pos: "BOTTOM · Tab 2", color: ROSE, desc: "Last 5 meetings between the two sides. Table rows: date, competition, home team, score, away team, venue. Summary bar: H2H win rates as a horizontal split bar (e.g. 60% home / 20% draw / 20% away). From GET /api/match/:id/h2h." },
        { name: "Team Form Tab", pos: "BOTTOM · Tab 3", color: "#e040fb", desc: "Two-column side by side. Home team last 5 results (result, opponent, score, xG). Away team last 5 results mirrored. Rolling xG chart for both teams overlaid on same axis for the last 8 games. Pulls from team rolling stats." },
        { name: "Prediction Confidence Meter", pos: "RIGHT SIDE · Sticky", color: AMBER, desc: "A vertical gauge (like a fuel meter) showing overall model confidence score (0–100). Derived from the max probability + calibration score. Below it: data quality indicator — how many features had sufficient historical data (e.g. '23/26 features populated'). Below that: 'Last updated' timestamp." }
      ]
    },
    behaviour: [
      "On mount: GET /api/match/:id fires first to populate the match header. Then POST /api/predict fires — while waiting, the probability columns show animated counting-up placeholders.",
      "Probabilities animate from 0% to final value over 800ms with an easing curve on page load.",
      "SHAP bars animate in from centre outward with 60ms stagger per feature.",
      "If POST /api/predict returns an error (model unavailable), show a fallback panel: 'Model offline — showing statistical baseline only' using just rolling averages.",
      "Tabs remember their position when user navigates away and returns (React state persisted in router location state).",
      "Share button generates a prediction card image (html2canvas) that can be shared — shows teams, probabilities, and 'Powered by PitchIQ'.",
      "Model confidence gauge colour shifts: green >65%, amber 45–65%, red <45%."
    ]
  },
  {
    id: "dashboard",
    number: "05",
    name: "Predictions Dashboard",
    icon: "📊",
    role: "Model performance tracking. Shows historical prediction accuracy, calibration, and per-league breakdown. Used to validate and monitor the ML system over time.",
    apiCalls: ["GET /api/predictions/history?limit=50", "GET /api/model/performance", "GET /api/model/calibration", "GET /api/model/feature-importance"],
    layout: {
      description: "Analytics-grid layout. Top row: 4 headline KPI tiles. Middle: prediction history table + accuracy chart side by side. Bottom: calibration curve + feature importance chart.",
      sections: [
        { name: "KPI Tile Row", pos: "TOP · 4 equal tiles", color: ACCENT, desc: "Tile 1: Total Predictions Made. Tile 2: Overall Accuracy (correct outcome / total). Tile 3: Log Loss (lower = better). Tile 4: ROI vs Betting Baseline (if model beats implied odds). Each tile: large metric number, label, trend arrow vs prior 30 days, small sparkline. From GET /api/model/performance." },
        { name: "Accuracy Over Time Chart", pos: "MIDDLE LEFT · 55% width", color: CYAN, desc: "Line chart: rolling 10-prediction accuracy plotted over time (x = date, y = accuracy %). Two lines: Model accuracy vs Betting odds baseline accuracy. Threshold line at 50% (random baseline). recharts LineChart with custom tooltip. Source: GET /api/predictions/history." },
        { name: "Prediction History Table", pos: "MIDDLE RIGHT · 45% width", color: AMBER, desc: "Scrollable table of last 50 predictions. Columns: Date, Match, Predicted, Actual, Correct (checkmark/cross), Confidence. Rows filterable by league dropdown. Correct predictions have subtle green left border. Wrong predictions: red. Clicking a row opens a side drawer with the full SHAP breakdown for that prediction." },
        { name: "Calibration Curve", pos: "BOTTOM LEFT · 45% width", color: ROSE, desc: "Reliability diagram. X-axis: predicted probability bins (0–10%, 10–20%, ... 90–100%). Y-axis: actual empirical frequency. Perfect calibration = diagonal line shown as dashed reference. Model curve plotted over it. Deviations highlighted. If model is overconfident in a bin, that bin bar is red. From GET /api/model/calibration." },
        { name: "Feature Importance Chart", pos: "BOTTOM RIGHT · 55% width", color: "#e040fb", desc: "Horizontal bar chart of global SHAP feature importances across all predictions. Top 12 features. Bars coloured by feature category: form features (green), contextual (blue), H2H (amber), xG-based (cyan). From GET /api/model/feature-importance. Sort toggle: by importance desc or by feature category." },
        { name: "Per-League Breakdown", pos: "BELOW CHARTS · Full width table", color: MUTED, desc: "Table: League name, Predictions, Accuracy, Log Loss, vs Odds baseline delta. Rows sorted by accuracy desc. EPL typically has most rows. Champions League often lower accuracy (higher variance). Allows the team to see which competitions the model performs best in." }
      ]
    },
    behaviour: [
      "KPI tiles count up from 0 on mount (animated number roll, 600ms).",
      "Accuracy chart renders with a draw animation — the line draws from left to right over 1s.",
      "Prediction history table supports client-side filtering by league (no new API call).",
      "Clicking a history table row opens a right-side drawer (300px wide) with the SHAP waterfall chart for that specific match.",
      "Calibration curve bins highlight on hover with a tooltip: 'N predictions in this bin, X% were correct'.",
      "Feature importance bars animate from width 0 to full on tab-in with 30ms stagger."
    ]
  },
  {
    id: "modelhealth",
    number: "06",
    name: "Model Health Monitor",
    icon: "🩺",
    role: "Internal operational page. Shows data pipeline status, model version, feature store freshness, and API source health. For the engineering team, not end users.",
    apiCalls: ["GET /api/admin/pipeline-status", "GET /api/admin/model-registry", "GET /api/admin/source-health", "GET /api/admin/feature-store"],
    layout: {
      description: "Dense status-board layout. No decorative elements — pure information density. Terminal-inspired. Left: pipeline stage statuses. Right: source health and model registry.",
      sections: [
        { name: "Pipeline Stage Monitor", pos: "LEFT · 50% · Vertical list", color: CYAN, desc: "Each pipeline stage as a status row: Ingestion → Validation → Feature Engineering → Training → Evaluation → Serving. Each shows: last run timestamp, duration, status (OK / WARN / ERROR), record counts. Status badge: green circle = OK, amber = WARN, red = ERROR. Clicking a row shows the last run log in an expandable panel." },
        { name: "Data Source Health", pos: "RIGHT TOP · 50%", color: AMBER, desc: "One row per data source: football-data.co.uk, Understat, FBref, API-Football. Columns: Source name, last fetch, status, records fetched, error rate. If a source has an error, the row turns red and shows the error message. Refreshes every 2 min." },
        { name: "Model Registry", pos: "RIGHT MIDDLE · 50%", color: ACCENT, desc: "Table of deployed model versions. Columns: version tag, trained date, val log-loss, test log-loss, status (ACTIVE / SHADOW / RETIRED). Active model row highlighted. Button: 'Promote to Active' for shadow models. From GET /api/admin/model-registry." },
        { name: "Feature Store Freshness", pos: "BOTTOM · Full width", color: ROSE, desc: "Grid of all 26 features. Each tile: feature name, last computed date, null rate, mean value. Tiles go amber if last computed >24h ago, red if >48h. Clicking a tile shows a histogram of that feature's distribution across the last 500 matches." }
      ]
    },
    behaviour: [
      "Auto-refreshes entire page every 2 minutes. Countdown timer in top-right shows time to next refresh.",
      "Pipeline stages with ERROR status trigger a banner at the top of the screen: 'PIPELINE ERROR — Ingestion failed at 14:32 UTC. Predictions may be stale.'",
      "Model registry promote button triggers a confirmation modal before making the API call.",
      "Feature freshness tiles blink slowly when stale (CSS animation, amber colour, 2s cycle)."
    ]
  }
];

const dataFlowSteps = [
  { from: "User selects league", to: "GET /api/league/:id/*", result: "League table, fixtures, teams populated", color: CYAN },
  { from: "User selects team", to: "GET /api/team/:id + /stats/rolling", result: "Team profile, recent/upcoming matches rendered", color: ACCENT },
  { from: "User clicks PREDICT", to: "POST /api/predict (feature vector built server-side)", result: "Probabilities + SHAP values returned in ~300ms", color: "#e040fb" },
  { from: "Model returns prediction", to: "GET /api/match/:id/odds (parallel)", result: "Model vs betting odds comparison displayed", color: AMBER },
  { from: "Live ticker (every 30s)", to: "GET /api/live-scores", result: "In-play scores update without page reload", color: ROSE },
  { from: "Dashboard loads", to: "GET /api/predictions/history + model/performance", result: "Accuracy metrics and calibration curve rendered", color: CYAN },
];

export default function Blueprint() {
  const [activePage, setActivePage] = useState(0);
  const [activeSection, setActiveSection] = useState(null);
  const [activeTab, setActiveTab] = useState("layout");

  const page = pages[activePage];

  return (
    <div style={{
      background: "#070d14",
      minHeight: "100vh",
      color: "#b8ccd8",
      fontFamily: "'IBM Plex Mono', monospace",
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;600;700&family=Syne:wght@700;800;900&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-track { background: #070d14; }
        ::-webkit-scrollbar-thumb { background: #1e2e40; border-radius: 2px; }
        .page-btn { border: 1px solid #1e2e40; background: transparent; color: #3a5a7a; cursor: pointer; padding: 8px 10px; border-radius: 4px; font-family: 'IBM Plex Mono', monospace; font-size: 10px; font-weight: 600; transition: all 0.15s; text-align: left; display: flex; align-items: center; gap: 8px; width: 100%; }
        .page-btn:hover { border-color: #2a4a6a; color: #8aacc8; background: #0e1520; }
        .page-btn.active { border-color: ${ACCENT}; color: ${ACCENT}; background: ${ACCENT}10; }
        .sec-card { border: 1px solid #1e2e40; border-radius: 6px; background: #0e1520; padding: 12px 14px; cursor: pointer; transition: border-color 0.15s; margin-bottom: 8px; }
        .sec-card:hover { border-color: #2a4a6a; }
        .sec-card.open { border-color: var(--sc); background: #090f18; }
        .tab-btn { background: transparent; border: none; border-bottom: 2px solid transparent; padding: 8px 16px; font-family: 'IBM Plex Mono', monospace; font-size: 10px; font-weight: 700; letter-spacing: 0.1em; color: #3a5a7a; cursor: pointer; transition: all 0.15s; }
        .tab-btn.active { color: ${ACCENT}; border-bottom-color: ${ACCENT}; }
        .tab-btn:hover { color: #8aacc8; }
        .api-pill { display: inline-block; background: #0a1820; border: 1px solid #1e3848; border-radius: 3px; padding: 2px 8px; font-size: 10px; color: #4a8ab0; margin: 2px; }
        .beh-item { display: flex; gap: 10px; margin-bottom: 8px; align-items: flex-start; }
        .beh-dot { width: 6px; height: 6px; border-radius: 50%; background: ${ACCENT}; flex-shrink: 0; margin-top: 6px; }
        .flow-row { display: flex; align-items: center; gap: 0; margin-bottom: 6px; border: 1px solid #1e2e40; border-radius: 5px; overflow: hidden; }
        .flow-cell { padding: 8px 12px; font-size: 11px; }
        .grid-3 { display: grid; grid-template-columns: repeat(3,1fr); gap: 10px; }
      `}</style>

      {/* Top bar */}
      <div style={{ borderBottom: `1px solid ${BORDER}`, padding: "0 24px", display: "flex", alignItems: "center", height: 52, gap: 16 }}>
        <span style={{ fontFamily: "'Syne', sans-serif", fontSize: 18, fontWeight: 900, color: ACCENT, letterSpacing: "-0.03em" }}>PitchIQ</span>
        <span style={{ fontSize: 10, color: MUTED, borderLeft: `1px solid ${BORDER}`, paddingLeft: 16 }}>FRONTEND DESIGN BLUEPRINT</span>
        <div style={{ marginLeft: "auto", display: "flex", gap: 6 }}>
          {["6 PAGES","REAL-TIME DATA","ML-CONNECTED","FULL SPEC"].map(t => (
            <span key={t} style={{ fontSize: 9, padding: "2px 8px", border: `1px solid ${BORDER}`, borderRadius: 3, color: "#3a5a7a" }}>{t}</span>
          ))}
        </div>
      </div>

      <div style={{ display: "flex", height: "calc(100vh - 52px)", overflow: "hidden" }}>

        {/* LEFT NAV */}
        <div style={{ width: 220, borderRight: `1px solid ${BORDER}`, padding: "16px 12px", overflowY: "auto", flexShrink: 0 }}>
          <div style={{ fontSize: 9, color: MUTED, letterSpacing: "0.12em", marginBottom: 10 }}>PAGES</div>
          {pages.map((p, i) => (
            <button key={p.id} className={`page-btn ${activePage === i ? "active" : ""}`} onClick={() => { setActivePage(i); setActiveSection(null); setActiveTab("layout"); }}>
              <span style={{ fontSize: 14 }}>{p.icon}</span>
              <div>
                <div style={{ fontSize: 9, opacity: 0.5 }}>{p.number}</div>
                <div style={{ fontSize: 10, lineHeight: 1.3 }}>{p.name}</div>
              </div>
            </button>
          ))}
          <div style={{ borderTop: `1px solid ${BORDER}`, margin: "16px 0 10px" }} />
          <div style={{ fontSize: 9, color: MUTED, letterSpacing: "0.12em", marginBottom: 10 }}>DATA FLOW</div>
          <button className={`page-btn ${activePage === 99 ? "active" : ""}`} onClick={() => { setActivePage(99); setActiveSection(null); }}>
            <span style={{ fontSize: 14 }}>🔄</span>
            <div><div style={{ fontSize: 10 }}>API Data Flow</div></div>
          </button>
        </div>

        {/* MAIN CONTENT */}
        <div style={{ flex: 1, overflowY: "auto", padding: "24px 28px" }}>

          {/* Data flow page */}
          {activePage === 99 && (
            <>
              <div style={{ marginBottom: 24 }}>
                <div style={{ fontSize: 9, color: MUTED, letterSpacing: "0.14em", marginBottom: 6 }}>SYSTEM OVERVIEW</div>
                <h2 style={{ fontFamily: "'Syne', sans-serif", fontSize: 24, fontWeight: 800, color: "#e8f0fa", letterSpacing: "-0.02em" }}>
                  Frontend ↔ API ↔ ML Data Flow
                </h2>
                <p style={{ fontSize: 12, color: "#4a6a8a", marginTop: 6, lineHeight: 1.7 }}>
                  How every user action maps to an API call, how the ML model is invoked, and what data flows back to the UI.
                </p>
              </div>

              {dataFlowSteps.map((s, i) => (
                <div key={i} className="flow-row">
                  <div className="flow-cell" style={{ background: s.color + "12", borderRight: `1px solid ${BORDER}`, width: 220, color: s.color, fontSize: 11, fontWeight: 600 }}>
                    {s.from}
                  </div>
                  <div className="flow-cell" style={{ borderRight: `1px solid ${BORDER}`, flex: 1, color: "#4a8ab0", fontFamily: "monospace" }}>
                    {s.to}
                  </div>
                  <div className="flow-cell" style={{ flex: 1, color: "#6a8a9a" }}>
                    {s.result}
                  </div>
                </div>
              ))}

              <div style={{ marginTop: 28, marginBottom: 12 }}>
                <div style={{ fontSize: 9, color: MUTED, letterSpacing: "0.14em", marginBottom: 14 }}>STATE MANAGEMENT STRATEGY</div>
                <div className="grid-3">
                  {[
                    { label: "Global State (Zustand / Redux)", color: CYAN, items: ["Selected league ID", "Selected team ID", "Live scores cache", "User prediction history"] },
                    { label: "Server Cache (React Query / SWR)", color: ACCENT, items: ["League tables (5min TTL)", "Team stats (5min TTL)", "Fixtures (1min TTL for live)", "Predictions (no cache — always fresh)"] },
                    { label: "URL State (React Router)", color: AMBER, items: ["/league/:id", "/team/:id", "/predict/:matchId", "/dashboard?league=EPL"] },
                  ].map(g => (
                    <div key={g.label} style={{ background: CARD, border: `1px solid ${BORDER}`, borderRadius: 6, padding: 14, borderTop: `2px solid ${g.color}` }}>
                      <div style={{ fontSize: 10, color: g.color, fontWeight: 700, marginBottom: 10 }}>{g.label}</div>
                      {g.items.map(item => (
                        <div key={item} style={{ fontSize: 11, color: "#4a6a8a", marginBottom: 5, display: "flex", gap: 6 }}>
                          <span style={{ color: g.color }}>·</span>{item}
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              </div>

              <div style={{ marginTop: 24 }}>
                <div style={{ fontSize: 9, color: MUTED, letterSpacing: "0.14em", marginBottom: 14 }}>REAL-TIME UPDATE STRATEGY</div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                  {[
                    { trigger: "Live Scores Ticker", method: "Polling every 30s", reason: "WebSocket overkill for a university project; polling is simpler and sufficient." },
                    { trigger: "In-play match score", method: "Polling every 60s per match", reason: "Score updates per-match when fixture detail page is open." },
                    { trigger: "League table", method: "Polling every 5 min", reason: "Tables change only on match completion — infrequent enough for polling." },
                    { trigger: "Prediction result", method: "Single POST on user action", reason: "One-shot inference call. No streaming needed — model responds in <300ms." },
                  ].map(r => (
                    <div key={r.trigger} style={{ background: CARD, border: `1px solid ${BORDER}`, borderRadius: 6, padding: 12 }}>
                      <div style={{ fontSize: 11, fontWeight: 700, color: "#c0d8e8", marginBottom: 4 }}>{r.trigger}</div>
                      <div style={{ fontSize: 11, color: ACCENT, marginBottom: 4 }}>{r.method}</div>
                      <div style={{ fontSize: 10, color: "#3a5570", lineHeight: 1.5 }}>{r.reason}</div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* Page spec */}
          {activePage !== 99 && (
            <>
              {/* Page header */}
              <div style={{ marginBottom: 24 }}>
                <div style={{ fontSize: 9, color: MUTED, letterSpacing: "0.14em", marginBottom: 4 }}>PAGE {page.number} OF 06</div>
                <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 8 }}>
                  <span style={{ fontSize: 32 }}>{page.icon}</span>
                  <h2 style={{ fontFamily: "'Syne', sans-serif", fontSize: 26, fontWeight: 800, color: "#e8f0fa", letterSpacing: "-0.02em" }}>{page.name}</h2>
                </div>
                <p style={{ fontSize: 12, color: "#4a6a8a", lineHeight: 1.7, maxWidth: 600 }}>{page.role}</p>
                <div style={{ marginTop: 12, display: "flex", flexWrap: "wrap", gap: 4 }}>
                  {page.apiCalls.map(a => <span key={a} className="api-pill">{a}</span>)}
                </div>
              </div>

              {/* Tabs */}
              <div style={{ borderBottom: `1px solid ${BORDER}`, marginBottom: 20, display: "flex" }}>
                {["layout","behaviour"].map(t => (
                  <button key={t} className={`tab-btn ${activeTab === t ? "active" : ""}`} onClick={() => setActiveTab(t)}>
                    {t.toUpperCase()}
                  </button>
                ))}
              </div>

              {/* LAYOUT TAB */}
              {activeTab === "layout" && (
                <>
                  <div style={{ fontSize: 11, color: "#4a7a9a", lineHeight: 1.7, marginBottom: 20, background: CARD, border: `1px solid ${BORDER}`, borderRadius: 6, padding: "12px 16px" }}>
                    <span style={{ color: MUTED, fontSize: 10 }}>LAYOUT OVERVIEW  </span>{page.layout.description}
                  </div>

                  {/* Visual wireframe zone */}
                  <div style={{ marginBottom: 20, background: "#050b12", border: `1px solid ${BORDER}`, borderRadius: 8, padding: 16 }}>
                    <div style={{ fontSize: 9, color: MUTED, letterSpacing: "0.12em", marginBottom: 12 }}>WIREFRAME ZONES — CLICK A ZONE TO EXPAND</div>
                    <div style={{ display: "flex", flexDirection: "column", gap: 4, fontSize: 10 }}>
                      {page.layout.sections.map((s, i) => (
                        <div
                          key={i}
                          onClick={() => setActiveSection(activeSection === i ? null : i)}
                          style={{
                            border: `1px dashed ${activeSection === i ? s.color : BORDER}`,
                            borderRadius: 4,
                            padding: "8px 12px",
                            cursor: "pointer",
                            background: activeSection === i ? s.color + "0a" : "transparent",
                            transition: "all 0.15s",
                          }}
                        >
                          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                            <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                              <div style={{ width: 8, height: 8, borderRadius: 2, background: s.color, flexShrink: 0 }} />
                              <span style={{ fontWeight: 700, color: activeSection === i ? s.color : "#6a8a9a" }}>{s.name}</span>
                              <span style={{ fontSize: 9, color: "#2a4a6a", borderLeft: `1px solid ${BORDER}`, paddingLeft: 8 }}>{s.pos}</span>
                            </div>
                            <span style={{ color: MUTED, fontSize: 10 }}>{activeSection === i ? "▲" : "▼"}</span>
                          </div>
                          {activeSection === i && (
                            <div style={{ marginTop: 10, paddingTop: 10, borderTop: `1px solid ${BORDER}`, fontSize: 11, color: "#6a8aaa", lineHeight: 1.75 }}>
                              {s.desc}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}

              {/* BEHAVIOUR TAB */}
              {activeTab === "behaviour" && (
                <div>
                  <div style={{ fontSize: 9, color: MUTED, letterSpacing: "0.12em", marginBottom: 14 }}>INTERACTIVE BEHAVIOURS & RUNTIME LOGIC</div>
                  {page.behaviour.map((b, i) => (
                    <div key={i} className="beh-item">
                      <div className="beh-dot" style={{ background: i % 2 === 0 ? ACCENT : CYAN }} />
                      <span style={{ fontSize: 12, color: "#7a9ab8", lineHeight: 1.7 }}>{b}</span>
                    </div>
                  ))}
                  <div style={{ marginTop: 24, background: CARD, border: `1px solid ${BORDER}`, borderRadius: 6, padding: "14px 16px" }}>
                    <div style={{ fontSize: 9, color: MUTED, letterSpacing: "0.12em", marginBottom: 10 }}>LOADING & ERROR STATES</div>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
                      {[
                        { state: "Initial Load", treatment: "Skeleton loaders per section (pulsing grey blocks). Sections load independently — first ready, first shown." },
                        { state: "API Error", treatment: "Section-level error boundary. Shows: 'Unable to load [section name]. Retry?' button. Does not break other sections." },
                        { state: "Model Unavailable", treatment: "Prediction page shows degraded mode banner: 'ML model offline — statistical fallback only.' Probabilities shown with warning badge." },
                      ].map(s => (
                        <div key={s.state} style={{ border: `1px solid ${BORDER}`, borderRadius: 5, padding: "10px 12px" }}>
                          <div style={{ fontSize: 10, fontWeight: 700, color: AMBER, marginBottom: 6 }}>{s.state}</div>
                          <div style={{ fontSize: 10, color: "#4a6a8a", lineHeight: 1.6 }}>{s.treatment}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* RIGHT PANEL — summary */}
        {activePage !== 99 && (
          <div style={{ width: 210, borderLeft: `1px solid ${BORDER}`, padding: "16px 14px", overflowY: "auto", flexShrink: 0 }}>
            <div style={{ fontSize: 9, color: MUTED, letterSpacing: "0.12em", marginBottom: 12 }}>ALL PAGES</div>
            {pages.map((p, i) => (
              <div key={p.id} onClick={() => { setActivePage(i); setActiveSection(null); setActiveTab("layout"); }}
                style={{ marginBottom: 8, padding: "8px 10px", borderRadius: 5, border: `1px solid ${i === activePage ? ACCENT + "60" : BORDER}`, background: i === activePage ? ACCENT + "08" : "transparent", cursor: "pointer" }}>
                <div style={{ fontSize: 10, color: i === activePage ? ACCENT : "#3a5a7a", fontWeight: 600, marginBottom: 2 }}>{p.icon} {p.name}</div>
                <div style={{ fontSize: 9, color: "#2a3a4a", lineHeight: 1.4 }}>{p.apiCalls.length} API calls</div>
              </div>
            ))}
            <div style={{ borderTop: `1px solid ${BORDER}`, marginTop: 14, paddingTop: 14 }}>
              <div style={{ fontSize: 9, color: MUTED, letterSpacing: "0.12em", marginBottom: 10 }}>TECH STACK</div>
              {[["React 18", "SPA framework"],["React Router v6","Routing"],["React Query","Server state + cache"],["Zustand","Global client state"],["recharts","Charts"],["Tailwind CSS","Utility styling"],["Framer Motion","Animations"],["html2canvas","Share card generation"]].map(([t, d]) => (
                <div key={t} style={{ marginBottom: 6 }}>
                  <div style={{ fontSize: 10, color: "#6a8aaa" }}>{t}</div>
                  <div style={{ fontSize: 9, color: "#2a3a4a" }}>{d}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
