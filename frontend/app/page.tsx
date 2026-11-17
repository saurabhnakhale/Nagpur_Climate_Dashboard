"use client";
import { useEffect, useMemo, useState, useCallback } from "react";
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell,
  ComposedChart, Legend, Line, LineChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import {
  Activity, AlertTriangle, CheckCircle, Cloud, CloudRain, CloudSun,
  Droplets, Gauge, HeartPulse, LayoutDashboard, MapPin,
  RefreshCw, ThermometerSun, Wind, Waves, Eye, TrendingUp,
} from "lucide-react";

// ── Types ────────────────────────────────────────────────────────────────────
type Weather = {
  location: string; description: string; observed_at: string;
  temperature_c: number; feels_like_c: number; humidity_pct: number;
  wind_kmh: number; pressure_hpa: number; rain_last_hour_mm: number;
};
type ForecastPoint = {
  datetime: string; temperature_c: number; feels_like_c: number;
  humidity_pct: number; rainfall_3h_mm: number;
};
type AirQuality = {
  aqi: number; category: string;
  components: Record<string, number>;
};
type DashboardData = {
  weather: Weather; forecast: ForecastPoint[]; air: AirQuality | null;
};

// ── Constants ────────────────────────────────────────────────────────────────
const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

const NAV_ITEMS = [
  { name: "Overview",     icon: LayoutDashboard },
  { name: "Weather",      icon: CloudSun },
  { name: "Heat Impact",  icon: ThermometerSun },
  { name: "Rainfall",     icon: CloudRain },
  { name: "Air Quality",  icon: Wind },
  { name: "Public Health",icon: HeartPulse },
  { name: "Map & Reports",icon: MapPin },
] as const;

const AQI_META: Record<number, { label: string; color: string; cls: string }> = {
  1: { label: "Good",      color: "#34d399", cls: "good"   },
  2: { label: "Fair",      color: "#fbbf24", cls: "warn"   },
  3: { label: "Moderate",  color: "#fb923c", cls: "warn"   },
  4: { label: "Poor",      color: "#f87171", cls: "danger" },
  5: { label: "Very Poor", color: "#f472b6", cls: "danger" },
};

const HEAT_THRESHOLDS = [
  { range: "< 27 °C",  label: "Comfortable",    color: "#34d399", bg: "rgba(52,211,153,.1)",  border: "rgba(52,211,153,.3)"  },
  { range: "27–32 °C", label: "Caution",         color: "#fbbf24", bg: "rgba(251,191,36,.1)",  border: "rgba(251,191,36,.3)"  },
  { range: "32–41 °C", label: "Extreme Caution", color: "#fb923c", bg: "rgba(251,146,60,.1)",  border: "rgba(251,146,60,.3)"  },
  { range: "41–54 °C", label: "Danger",          color: "#f87171", bg: "rgba(248,113,113,.1)", border: "rgba(248,113,113,.3)" },
  { range: "> 54 °C",  label: "Extreme Danger",  color: "#f472b6", bg: "rgba(244,114,182,.1)", border: "rgba(244,114,182,.3)" },
];

// ── Helpers ──────────────────────────────────────────────────────────────────
function fmtDT(iso: string) {
  return new Date(iso).toLocaleString("en-IN", {
    day: "2-digit", hour: "2-digit", minute: "2-digit", timeZone: "Asia/Kolkata",
  });
}
function fmtTime(iso: string) {
  return new Date(iso).toLocaleString("en-IN", {
    day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit", timeZone: "Asia/Kolkata",
  });
}
function heatLabel(feels: number): { text: string; cls: string; icon: string } {
  if (feels >= 54) return { text: "Extreme Danger",  cls: "danger", icon: "🔴" };
  if (feels >= 41) return { text: "Danger",           cls: "danger", icon: "🟠" };
  if (feels >= 32) return { text: "Extreme Caution",  cls: "warn",   icon: "🟡" };
  if (feels >= 27) return { text: "Caution",          cls: "warn",   icon: "🟢" };
  return { text: "Comfortable", cls: "good", icon: "✅" };
}
function csvDownload(rows: ForecastPoint[], fname = "nagpur-climate-forecast.csv") {
  const heads = ["datetime", "temperature_c", "feels_like_c", "humidity_pct", "rainfall_3h_mm"];
  const csv = [heads.join(","), ...rows.map(r =>
    heads.map(h => JSON.stringify(r[h as keyof ForecastPoint] ?? "")).join(",")
  )].join("\n");
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
  a.download = fname; a.click();
}

// ── Shared chart theme ───────────────────────────────────────────────────────
const GRID_COLOR = "#1a3450";
const TICK_STYLE = { fill: "#6a90b0", fontSize: 10 };

function ChartTip({ active, payload, label }: {
  active?: boolean; label?: string;
  payload?: Array<{ name: string; value: number; color: string }>;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: "#0a1929", border: "1px solid #1e3a52", padding: "10px 13px", borderRadius: 11, fontSize: 11, color: "#e0f0ff" }}>
      <div style={{ color: "#6a90b0", marginBottom: 5 }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color, marginBottom: 2 }}>
          <span style={{ opacity: .7 }}>{p.name}: </span>
          <strong>{typeof p.value === "number" ? p.value.toFixed(2) : p.value}</strong>
        </div>
      ))}
    </div>
  );
}

// ── Sub-components ───────────────────────────────────────────────────────────
function MetricCard({ label, value, note, icon: Icon, delta, deltaDir }: {
  label: string; value: string; note: string;
  icon: React.ElementType; delta?: string; deltaDir?: "up" | "down" | "neu";
}) {
  return (
    <div className="card">
      <div className="card-top">
        <span className="metric-label">{label}</span>
        <Icon size={16} color="#2dd4bf" />
      </div>
      <div className="metric-value">{value}</div>
      <div className="metric-note">{note}</div>
      {delta && <div className={`metric-delta ${deltaDir ?? "neu"}`}>{delta}</div>}
    </div>
  );
}

function SectionHead({ kicker, title, sub }: { kicker: string; title: string; sub?: string }) {
  return (
    <div className="section-head">
      <div className="section-head-left">
        <div className="section-kicker">{kicker}</div>
        <div className="section-title">{title}</div>
        {sub && <div className="section-sub">{sub}</div>}
      </div>
    </div>
  );
}

function GaugeBlock({ label, value, unit, color }: { label: string; value: string; unit: string; color: string }) {
  return (
    <div className="gauge-block">
      <div className="gauge-label">{label}</div>
      <div className="gauge-value" style={{ color }}>{value}</div>
      <div className="gauge-unit">{unit}</div>
    </div>
  );
}

// ── Health Upload ────────────────────────────────────────────────────────────
type HealthRow = { date: string; zone: string; disease: string; cases: number };
function HealthUpload() {
  const [rows, setRows]       = useState<HealthRow[]>([]);
  const [msg, setMsg]         = useState("Select a CSV file with columns: date, zone, disease, cases.");
  const [disease, setDisease] = useState("");
  const [zone, setZone]       = useState("All zones");

  function readFile(file?: File) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const lines = String(reader.result ?? "").trim().split(/\r?\n/);
      const heads = lines[0].split(",").map(x => x.trim().toLowerCase());
      const ix    = ["date","zone","disease","cases"].map(x => heads.indexOf(x));
      if (ix.some(x => x < 0)) { setMsg("CSV must include columns: date, zone, disease, cases."); return; }
      const parsed = lines.slice(1).map(line => {
        const c = line.split(",");
        return { date: c[ix[0]]?.trim() ?? "", zone: c[ix[1]]?.trim() ?? "",
                 disease: c[ix[2]]?.trim() ?? "", cases: Number(c[ix[3]]) };
      }).filter(x => x.date && x.zone && x.disease && Number.isFinite(x.cases) && x.cases >= 0);
      setRows(parsed);
      setDisease(parsed[0]?.disease ?? "");
      setZone("All zones");
      setMsg(`✅ ${parsed.length} valid rows loaded in browser memory.`);
    };
    reader.readAsText(file);
  }

  const diseases = [...new Set(rows.map(x => x.disease))].sort();
  const zones    = [...new Set(rows.map(x => x.zone))].sort();
  const selected = rows.filter(x =>
    (!disease || x.disease === disease) && (zone === "All zones" || x.zone === zone)
  );
  const monthly = Object.values(
    selected.reduce((a, x) => {
      const m = x.date.slice(0, 7);
      a[m] ??= { month: m, cases: 0 };
      a[m].cases += x.cases;
      return a;
    }, {} as Record<string, { month: string; cases: number }>)
  ).sort((a, b) => a.month.localeCompare(b.month));

  const totalCases = selected.reduce((s, x) => s + x.cases, 0);

  return (
    <div className="panel">
      <div style={{ marginBottom: 14 }}>
        <input type="file" accept=".csv,text/csv" className="file-input"
               onChange={e => readFile(e.target.files?.[0])} />
        <p style={{ fontSize: 11, color: "#6a90b0", marginTop: 8 }}>{msg}</p>
      </div>

      {rows.length > 0 && (
        <>
          <div className="four-col" style={{ gridTemplateColumns: "repeat(3,1fr)", marginBottom: 14 }}>
            <MetricCard label="Total Cases" value={String(totalCases)} note="Selected filter" icon={Activity} />
            <MetricCard label="Diseases" value={String(diseases.length)} note="In dataset" icon={HeartPulse} />
            <MetricCard label="Zones" value={String(zones.length)} note="In dataset" icon={MapPin} />
          </div>

          <div className="form-row">
            <select className="select-input" value={disease} onChange={e => setDisease(e.target.value)}>
              {diseases.map(x => <option key={x}>{x}</option>)}
            </select>
            <select className="select-input" value={zone} onChange={e => setZone(e.target.value)}>
              <option>All zones</option>
              {zones.map(x => <option key={x}>{x}</option>)}
            </select>
            <span className="pill" style={{ display:"inline-block",padding:"6px 12px" }}>
              {totalCases} cases selected
            </span>
          </div>

          <div className="chart-wrap tall">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={monthly}>
                <defs>
                  <linearGradient id="healthFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%"   stopColor="#2dd4bf" stopOpacity={0.3}/>
                    <stop offset="100%" stopColor="#2dd4bf" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid stroke={GRID_COLOR} strokeDasharray="3 3"/>
                <XAxis dataKey="month" tick={TICK_STYLE}/>
                <YAxis tick={TICK_STYLE}/>
                <Tooltip content={<ChartTip/>}/>
                <Area dataKey="cases" name="Reported Cases" stroke="#2dd4bf"
                      strokeWidth={2.5} fill="url(#healthFill)"/>
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="table-wrap" style={{ marginTop: 16 }}>
            <table className="data-table">
              <thead><tr>
                <th>Date</th><th>Zone</th><th>Disease</th><th>Cases</th>
              </tr></thead>
              <tbody>
                {selected.slice(0, 100).map((x, i) => (
                  <tr key={i}>
                    <td>{x.date}</td><td>{x.zone}</td><td>{x.disease}</td>
                    <td><strong style={{ color: "#f0f8ff" }}>{x.cases}</strong></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      <div className="notice warn" style={{ marginTop: 14 }}>
        ⚠️ Upload only <strong>authorized, aggregated, de-identified</strong> records.
        This tool shows reported trends — not outbreak predictions or climate causation.
        All processing is local in your browser.
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ═══════════════════════════════════════════════════════════════════════════════
export default function Home() {
  const [data,    setData]    = useState<DashboardData | null>(null);
  const [page,    setPage]    = useState<string>("Overview");
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState("");
  const [updated, setUpdated] = useState("");
  const [activeTab, setActiveTab] = useState(0);

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const r = await fetch("/api/dashboard", {
  method: "GET",
  cache: "no-store"
});
      if (!r.ok) throw new Error(`API returned ${r.status}: ${await r.text()}`);
      setData(await r.json());
      setUpdated(new Date().toLocaleString("en-IN", { timeZone: "Asia/Kolkata" }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to load dashboard data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  // Chart data with formatted time labels
  const chartData = useMemo(() =>
    data?.forecast.map(x => ({
      ...x,
      time:  fmtDT(x.datetime),
      label: fmtTime(x.datetime),
      wind_kmh: 0, // placeholder — not in forecast payload
    })) ?? [], [data]);

  const w = data?.weather;
  const rainTotal   = data?.forecast.reduce((s, p) => s + p.rainfall_3h_mm, 0) ?? 0;
  const rainyPeriods = data?.forecast.filter(x => x.rainfall_3h_mm > 0).length ?? 0;
  const peakTemp    = data ? Math.max(...data.forecast.map(x => x.temperature_c)) : null;
  const minTemp     = data ? Math.min(...data.forecast.map(x => x.temperature_c)) : null;
  const avgHumidity = data ? data.forecast.reduce((s, x) => s + x.humidity_pct, 0) / data.forecast.length : null;

  // Cumulative rainfall
  const cumRain = useMemo(() => {
    let acc = 0;
    return chartData.map(x => ({ ...x, cumulative: (acc += x.rainfall_3h_mm) }));
  }, [chartData]);

  const heatStatus = w ? heatLabel(w.feels_like_c) : null;
  const aqiMeta    = data?.air ? (AQI_META[data.air.aqi] ?? { label: "N/A", color: "#7a9ab8", cls: "info" }) : null;
  const now = new Date().toLocaleString("en-IN", { timeZone: "Asia/Kolkata", day:"2-digit", month:"short", year:"numeric", hour:"2-digit", minute:"2-digit" });

  return (
    <div className="shell">
      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div className="brand">
          🌦️ NAGPUR
          <small>CLIMATE INTELLIGENCE</small>
          <span className="build">SMART CITY MONITORING · v2.0</span>
        </div>
        <div className="sidebar-divider"/>
        <div className="navtitle">WORKSPACE</div>
        <nav className="nav">
          {NAV_ITEMS.map(({ name, icon: Icon }) => (
            <button key={name} className={page === name ? "active" : ""}
                    onClick={() => { setPage(name); setActiveTab(0); }}>
              <span className="nav-icon"><Icon size={14}/></span>
              {name}
            </button>
          ))}
        </nav>
        <div className="sidefoot">
          <strong>📍 MONITORING AREA</strong>
          Nagpur, Maharashtra, India<br/>
          21.1458° N · 79.0882° E<br/>
          Altitude ≈ 310 m · Vidarbha<br/><br/>
          🌐 Data: OpenWeatherMap<br/>
          ⏱️ Cache: 10-minute cycle<br/>
          📦 Build: v2.0 Pro Edition
        </div>
      </aside>

      {/* ── Main ── */}
      <main className="main">
        {/* Hero */}
        <header className="hero">
          <div className="kicker">🏙️ NAGPUR MUNICIPAL CORPORATION · ENVIRONMENT & PUBLIC HEALTH DIVISION</div>
          <h1>Climate Impact <span>Intelligence</span></h1>
          <p>Real-time atmospheric monitoring, thermal-stress analytics, precipitation forecasting,
             air-quality surveillance and public-health trend analysis — all in one unified command view.</p>
          <div className="pills">
            <span className="pill">📍 Nagpur, 21.14°N 79.08°E</span>
            <span className="pill">🌐 Live OpenWeather Feed</span>
            <span className="pill">📊 5-Day Forecast</span>
            <span className="pill amber">🕐 {now} IST</span>
            <span className="pill violet">🔬 Research &amp; Planning Tool</span>
          </div>
        </header>

        {/* Status bar */}
        <div className="statusbar">
          <span className={`dot ${error ? "red" : loading ? "amber" : "green"}`}/>
          <strong style={{ color: error ? "#f87171" : loading ? "#fbbf24" : "#34d399", fontWeight: 700 }}>
            {error ? "FEED UNAVAILABLE" : loading ? "CONNECTING…" : "LIVE FEED CONNECTED"}
          </strong>
          {w && <><span className="sep">·</span><span>{w.description}</span></>}
          {updated && <><span className="sep">·</span><span>Updated {updated} IST</span></>}
          {data && <><span className="sep">·</span><span>{data.forecast.length} forecast points</span></>}
          <button className="refresh-btn" onClick={() => void load()}>
            <RefreshCw size={12}/> Refresh
          </button>
        </div>

        {error && <div className="notice danger" style={{ marginBottom: 16 }}>
          ⚠️ {error} — Check backend URL and NEXT_PUBLIC_API_BASE_URL.</div>}
        {loading && !data && (
          <div className="loading-state"><span className="spinner"/><span>Loading Nagpur live data…</span></div>
        )}

        {/* KPI strip */}
        {w && (
          <div className="metrics-grid">
            <MetricCard label="Temperature"  value={`${w.temperature_c.toFixed(1)} °C`}
              note="Current air temp" icon={ThermometerSun}
              delta={`Feels ${w.feels_like_c.toFixed(1)}°C`}
              deltaDir={w.feels_like_c > w.temperature_c ? "up" : "down"}/>
            <MetricCard label="Humidity"     value={`${w.humidity_pct}%`}
              note="Relative humidity" icon={Droplets}/>
            <MetricCard label="Wind Speed"   value={`${w.wind_kmh.toFixed(1)} km/h`}
              note="Current surface wind" icon={Wind}/>
            <MetricCard label="Pressure"     value={`${w.pressure_hpa}`}
              note="hPa atmospheric" icon={Gauge}/>
            <MetricCard label="Rain · 1 h"  value={`${w.rain_last_hour_mm.toFixed(1)} mm`}
              note="Last hour reported" icon={CloudRain}/>
            <MetricCard label="Forecast Rain" value={`${rainTotal.toFixed(1)} mm`}
              note="5-day total forecast" icon={Waves}/>
          </div>
        )}

        {/* ── PAGE: OVERVIEW ── */}
        {data && page === "Overview" && (
          <>
            <SectionHead kicker="EXECUTIVE OVERVIEW" title="City Climate Command Center"
              sub="Integrated snapshot of current conditions and 5-day outlook"/>

            <div className="content-grid">
              {/* Left: charts */}
              <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                <div className="panel">
                  <div className="tab-bar">
                    {["Temperature Outlook","Humidity & Wind"].map((t,i) => (
                      <button key={t} className={`tab-btn ${activeTab===i?"active":""}`}
                              onClick={()=>setActiveTab(i)}>{t}</button>
                    ))}
                  </div>

                  {activeTab === 0 && (
                    <div className="chart-wrap tall">
                      <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={chartData}>
                          <defs>
                            <linearGradient id="tempFill" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="0%"   stopColor="#2dd4bf" stopOpacity={0.15}/>
                              <stop offset="100%" stopColor="#2dd4bf" stopOpacity={0}/>
                            </linearGradient>
                          </defs>
                          <CartesianGrid stroke={GRID_COLOR} strokeDasharray="3 3"/>
                          <XAxis dataKey="time" tick={TICK_STYLE} minTickGap={30}/>
                          <YAxis tick={TICK_STYLE}/>
                          <Tooltip content={<ChartTip/>}/>
                          <Legend wrapperStyle={{ fontSize: 11, color: "#7a9ab8" }}/>
                          <Area dataKey="temperature_c" name="Temperature °C"
                                stroke="#2dd4bf" strokeWidth={2.5} fill="url(#tempFill)"/>
                          <Line dataKey="feels_like_c"  name="Feels Like °C"
                                stroke="#fbbf24" strokeWidth={2} strokeDasharray="5 3" dot={false}/>
                        </ComposedChart>
                      </ResponsiveContainer>
                    </div>
                  )}
                  {activeTab === 1 && (
                    <div className="chart-wrap tall">
                      <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={chartData}>
                          <CartesianGrid stroke={GRID_COLOR} strokeDasharray="3 3"/>
                          <XAxis dataKey="time" tick={TICK_STYLE} minTickGap={30}/>
                          <YAxis yAxisId="left"  tick={TICK_STYLE}/>
                          <YAxis yAxisId="right" orientation="right" tick={TICK_STYLE}/>
                          <Tooltip content={<ChartTip/>}/>
                          <Legend wrapperStyle={{ fontSize: 11, color: "#7a9ab8" }}/>
                          <Bar yAxisId="left" dataKey="humidity_pct" name="Humidity %" fill="#4f96ff" opacity={0.75} radius={[3,3,0,0]}/>
                          <Line yAxisId="right" dataKey="rainfall_3h_mm" name="Rainfall mm/3h"
                                stroke="#2dd4bf" strokeWidth={2} dot={false}/>
                        </ComposedChart>
                      </ResponsiveContainer>
                    </div>
                  )}
                </div>

                {/* Rainfall mini-bar */}
                <div className="panel">
                  <h3>🌧️ Precipitation Forecast · mm per 3-hour interval</h3>
                  <div className="chart-wrap med">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={chartData}>
                        <CartesianGrid stroke={GRID_COLOR} strokeDasharray="3 3"/>
                        <XAxis dataKey="time" tick={TICK_STYLE} minTickGap={30}/>
                        <YAxis tick={TICK_STYLE}/>
                        <Tooltip content={<ChartTip/>}/>
                        <Bar dataKey="rainfall_3h_mm" name="Rainfall mm" radius={[4,4,0,0]}>
                          {chartData.map((_, i) => (
                            <Cell key={i} fill={`rgba(45,212,191,${0.3 + (chartData[i]?.rainfall_3h_mm ?? 0) * 0.07})`}/>
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>

              {/* Right: snapshot */}
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                <div className="panel">
                  <h3>🌤️ Current Conditions</h3>
                  <div style={{ fontSize: 22, fontWeight: 800, color: "#f0f8ff",
                                fontFamily: "Manrope,sans-serif", margin: "8px 0 4px" }}>
                    {w?.description}
                  </div>
                  <div style={{ fontSize: 11, color: "#4e7a9a" }}>📍 Nagpur city-centre reference point</div>

                  {heatStatus && (
                    <div className={`notice ${heatStatus.cls}`} style={{ marginTop: 14, fontSize: 12 }}>
                      {heatStatus.icon} Heat status: <strong>{heatStatus.text}</strong>
                      <br/><span style={{ opacity: .8 }}>Apparent temperature: {w?.feels_like_c.toFixed(1)}°C</span>
                    </div>
                  )}
                </div>

                <div className="panel">
                  <h3>📊 Forecast Summary</h3>
                  <div className="forecast-list">
                    {[
                      ["Forecast rainfall", `${rainTotal.toFixed(1)} mm`],
                      ["Rainy periods (3h)", `${rainyPeriods} / ${data.forecast.length}`],
                      ["Peak temperature",   peakTemp ? `${peakTemp.toFixed(1)} °C` : "—"],
                      ["Min temperature",    minTemp  ? `${minTemp.toFixed(1)} °C`  : "—"],
                      ["Avg humidity",       avgHumidity ? `${avgHumidity.toFixed(1)}%` : "—"],
                      ["Air quality",        data.air ? `${data.air.category} (AQI ${data.air.aqi})` : "Unavailable"],
                      ["Pressure",          w ? `${w.pressure_hpa} hPa` : "—"],
                    ].map(([k, v]) => (
                      <div className="forecast-row" key={k}>
                        <span>{k}</span>
                        <strong>{v}</strong>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="notice info">
                  ℹ️ Heat indicators are illustrative screening signals only. Always refer to official
                  <strong> IMD</strong> advisories for heatwave classification.
                </div>
              </div>
            </div>

            {/* Operational notices */}
            <SectionHead kicker="OPERATIONAL CONTEXT" title="Important Interpretation Notes"/>
            <div className="three-col">
              <div className="notice info">🌡️ <strong>Heat indicators</strong> are screening signals. Refer to official IMD advisories for heatwave classification and public-action triggers.</div>
              <div className="notice warn">🌧️ <strong>Rainfall values</strong> are forecast intervals from a city-centre coordinate — not measured ward-level rainfall or flood-risk assessments.</div>
              <div className="notice info">📡 A <strong>single coordinate</strong> cannot represent the full range of microclimates across all Nagpur municipal zones.</div>
            </div>
          </>
        )}

        {/* ── PAGE: WEATHER ── */}
        {data && page === "Weather" && (
          <>
            <SectionHead kicker="ATMOSPHERIC CONDITIONS" title="Weather Intelligence Suite"
              sub="Multi-variable atmospheric analysis and 5-day forecast"/>

            <div className="tab-bar">
              {["Temperature & Humidity","Wind Analysis","Pressure & Clouds"].map((t,i)=>(
                <button key={t} className={`tab-btn ${activeTab===i?"active":""}`} onClick={()=>setActiveTab(i)}>{t}</button>
              ))}
            </div>

            {activeTab === 0 && (
              <div className="panel">
                <h3>Temperature & Humidity Forecast · 5 Days</h3>
                <div className="chart-wrap tall">
                  <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={chartData}>
                      <CartesianGrid stroke={GRID_COLOR} strokeDasharray="3 3"/>
                      <XAxis dataKey="time" tick={TICK_STYLE} minTickGap={28}/>
                      <YAxis yAxisId="temp" tick={TICK_STYLE}/>
                      <YAxis yAxisId="hum" orientation="right" tick={TICK_STYLE}/>
                      <Tooltip content={<ChartTip/>}/>
                      <Legend wrapperStyle={{ fontSize: 11, color: "#7a9ab8" }}/>
                      <Line yAxisId="temp" dataKey="temperature_c" name="Temperature °C"
                            stroke="#2dd4bf" strokeWidth={2.5} dot={{ r: 3, fill: "#2dd4bf" }}/>
                      <Line yAxisId="temp" dataKey="feels_like_c" name="Feels Like °C"
                            stroke="#fbbf24" strokeWidth={2} strokeDasharray="5 3" dot={false}/>
                      <Bar  yAxisId="hum"  dataKey="humidity_pct" name="Humidity %"
                            fill="#4f96ff" opacity={0.35} radius={[3,3,0,0]}/>
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}
            {activeTab === 1 && (
              <>
                <div className="gauge-row" style={{ marginBottom: 14 }}>
                  <GaugeBlock label="Current Wind Speed" value={`${w!.wind_kmh.toFixed(1)}`} unit="km/h" color="#4f96ff"/>
                  <GaugeBlock label="Atmospheric Pressure" value={`${w!.pressure_hpa}`} unit="hPa" color="#8b5cf6"/>
                  <GaugeBlock label="Relative Humidity" value={`${w!.humidity_pct}`} unit="%" color="#2dd4bf"/>
                </div>
                <div className="panel">
                  <h3>Humidity Forecast over 5 Days</h3>
                  <div className="chart-wrap tall">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={chartData}>
                        <defs>
                          <linearGradient id="humFill" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%"   stopColor="#4f96ff" stopOpacity={0.3}/>
                            <stop offset="100%" stopColor="#4f96ff" stopOpacity={0}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid stroke={GRID_COLOR} strokeDasharray="3 3"/>
                        <XAxis dataKey="time" tick={TICK_STYLE} minTickGap={28}/>
                        <YAxis domain={[0, 100]} tick={TICK_STYLE}/>
                        <Tooltip content={<ChartTip/>}/>
                        <Area dataKey="humidity_pct" name="Humidity %" stroke="#4f96ff"
                              strokeWidth={2.5} fill="url(#humFill)"/>
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </>
            )}
            {activeTab === 2 && (
              <div className="panel">
                <h3>Forecast Data Table</h3>
                <div className="table-wrap">
                  <table className="data-table">
                    <thead><tr>
                      <th>Date & Time</th><th>Temp (°C)</th><th>Feels Like (°C)</th>
                      <th>Humidity (%)</th><th>Rainfall (mm/3h)</th>
                    </tr></thead>
                    <tbody>
                      {data.forecast.map((r, i) => (
                        <tr key={i}>
                          <td>{fmtDT(r.datetime)}</td>
                          <td><strong style={{ color: "#2dd4bf" }}>{r.temperature_c.toFixed(1)}</strong></td>
                          <td>{r.feels_like_c.toFixed(1)}</td>
                          <td>{r.humidity_pct}</td>
                          <td style={{ color: r.rainfall_3h_mm > 0 ? "#4f96ff" : "#4e7a9a" }}>
                            {r.rainfall_3h_mm.toFixed(2)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div style={{ marginTop: 14 }}>
                  <button className="btn" onClick={() => csvDownload(data.forecast)}>
                    <TrendingUp size={13}/> Download Forecast CSV
                  </button>
                </div>
              </div>
            )}
          </>
        )}

        {/* ── PAGE: HEAT IMPACT ── */}
        {data && page === "Heat Impact" && (
          <>
            <SectionHead kicker="THERMAL STRESS MONITORING" title="Heat Risk & Exposure Analytics"
              sub="Apparent-temperature based screening indicators for Nagpur"/>

            <div className="gauge-row" style={{ marginBottom: 16 }}>
              <GaugeBlock label="Air Temperature" value={`${w!.temperature_c.toFixed(1)}`} unit="°C" color="#f87171"/>
              <GaugeBlock label="Apparent Temperature" value={`${w!.feels_like_c.toFixed(1)}`} unit="°C" color="#fb923c"/>
              <GaugeBlock label="Relative Humidity" value={`${w!.humidity_pct}`} unit="%" color="#4f96ff"/>
            </div>

            {heatStatus && (
              <div className={`notice ${heatStatus.cls}`} style={{ marginBottom: 16, fontSize: 13 }}>
                {heatStatus.icon} <strong>Current heat status: {heatStatus.text}</strong>
                {" — "}Feels-like temperature: {w!.feels_like_c.toFixed(1)}°C.
                {w!.feels_like_c >= 35
                  ? " Elevated apparent-temperature flag. Review official IMD advisories."
                  : " No elevated flag under illustrative screening thresholds."}
                {" "}Not an official IMD heatwave classification or medical heat-index assessment.
              </div>
            )}

            <div className="panel" style={{ marginBottom: 14 }}>
              <h3>Feels-Like Temperature Forecast · 5 Days</h3>
              <div className="chart-wrap tall">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={chartData}>
                    <defs>
                      <linearGradient id="heatFill" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%"   stopColor="#f87171" stopOpacity={0.3}/>
                        <stop offset="100%" stopColor="#f87171" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    {/* Heat risk zones */}
                    <CartesianGrid stroke={GRID_COLOR} strokeDasharray="3 3"/>
                    <XAxis dataKey="time" tick={TICK_STYLE} minTickGap={28}/>
                    <YAxis tick={TICK_STYLE}/>
                    <Tooltip content={<ChartTip/>}/>
                    <Legend wrapperStyle={{ fontSize: 11, color: "#7a9ab8" }}/>
                    <Area dataKey="feels_like_c" name="Feels Like °C" stroke="#f87171"
                          strokeWidth={2.5} fill="url(#heatFill)"/>
                    <Line dataKey="temperature_c" name="Temperature °C"
                          stroke="#fbbf24" strokeWidth={2} strokeDasharray="5 3" dot={false}/>
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </div>

            <SectionHead kicker="REFERENCE TABLE" title="Screening Thresholds"/>
            <div className="panel">
              {HEAT_THRESHOLDS.map(t => (
                <div key={t.label} className="heat-row"
                     style={{ background: t.bg, borderColor: t.border, color: t.color }}>
                  <span style={{ fontSize: 20 }}>
                    {t.label === "Comfortable" ? "✅" : t.label === "Caution" ? "🟢" :
                     t.label === "Extreme Caution" ? "🟡" : t.label === "Danger" ? "🟠" : "🔴"}
                  </span>
                  <strong style={{ minWidth: 100 }}>{t.range}</strong>
                  <span style={{ color: "#c8d8e8" }}>{t.label}</span>
                </div>
              ))}
              <p style={{ marginTop: 12, fontSize: 11, color: "#4e7a9a" }}>
                ⚠️ Illustrative screening reference only. Not official IMD heatwave classification or medical advice.
              </p>
            </div>
          </>
        )}

        {/* ── PAGE: RAINFALL ── */}
        {data && page === "Rainfall" && (
          <>
            <SectionHead kicker="PRECIPITATION MONITORING" title="Rainfall Outlook & Accumulation"
              sub="5-day forecast precipitation analysis for Nagpur"/>

            <div className="four-col" style={{ marginBottom: 16 }}>
              <MetricCard label="Forecast Total"   value={`${rainTotal.toFixed(1)} mm`}  note="5-day total" icon={CloudRain}/>
              <MetricCard label="Peak 3-h Intensity" value={`${Math.max(...data.forecast.map(x=>x.rainfall_3h_mm)).toFixed(1)} mm`} note="Highest single period" icon={AlertTriangle}/>
              <MetricCard label="Rainy Periods"    value={`${rainyPeriods}`}               note={`of ${data.forecast.length} intervals`} icon={Cloud}/>
              <MetricCard label="Days with Rain"   value={`${[...new Set(data.forecast.filter(x=>x.rainfall_3h_mm>0).map(x=>x.datetime.slice(0,10)))].length}`} note="Distinct calendar days" icon={Waves}/>
            </div>

            <div className="tab-bar">
              {["Bar Chart","Cumulative"].map((t,i)=>(
                <button key={t} className={`tab-btn ${activeTab===i?"active":""}`} onClick={()=>setActiveTab(i)}>{t}</button>
              ))}
            </div>

            <div className="panel">
              {activeTab === 0 ? (
                <>
                  <h3>Forecast Precipitation · mm per 3-hour interval</h3>
                  <div className="chart-wrap tall">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={chartData}>
                        <CartesianGrid stroke={GRID_COLOR} strokeDasharray="3 3"/>
                        <XAxis dataKey="time" tick={TICK_STYLE} minTickGap={28}/>
                        <YAxis tick={TICK_STYLE}/>
                        <Tooltip content={<ChartTip/>}/>
                        <Bar dataKey="rainfall_3h_mm" name="Rainfall mm/3h" radius={[5,5,0,0]}>
                          {chartData.map((entry, i) => (
                            <Cell key={i}
                              fill={entry.rainfall_3h_mm > 5 ? "#2dd4bf" :
                                    entry.rainfall_3h_mm > 1 ? "#4f96ff" : "#1a3a5a"}/>
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </>
              ) : (
                <>
                  <h3>Cumulative Forecast Rainfall · mm</h3>
                  <div className="chart-wrap tall">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={cumRain}>
                        <defs>
                          <linearGradient id="cumFill" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%"   stopColor="#2dd4bf" stopOpacity={0.3}/>
                            <stop offset="100%" stopColor="#2dd4bf" stopOpacity={0}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid stroke={GRID_COLOR} strokeDasharray="3 3"/>
                        <XAxis dataKey="time" tick={TICK_STYLE} minTickGap={28}/>
                        <YAxis tick={TICK_STYLE}/>
                        <Tooltip content={<ChartTip/>}/>
                        <Area dataKey="cumulative" name="Cumulative mm" stroke="#2dd4bf"
                              strokeWidth={2.5} fill="url(#cumFill)"/>
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </>
              )}
            </div>
            <div className="notice warn" style={{ marginTop: 14 }}>
              ⚠️ Forecast rainfall represents model output from a single city-centre coordinate.
              Not observed or ward-level rainfall. Do not use for flood-risk assessment.
            </div>
          </>
        )}

        {/* ── PAGE: AIR QUALITY ── */}
        {data && page === "Air Quality" && (
          <>
            <SectionHead kicker="ATMOSPHERIC POLLUTION" title="Air Quality Intelligence"
              sub="Real-time pollutant concentrations and AQI monitoring"/>

            {data.air ? (
              <>
                <div className="gauge-row" style={{ marginBottom: 16 }}>
                  <div className="gauge-block">
                    <div className="gauge-label">OpenWeather AQI</div>
                    <div className="gauge-value" style={{ color: aqiMeta!.color, fontSize: 44 }}>
                      {data.air.aqi}
                    </div>
                    <div className="gauge-unit">out of 5</div>
                    <span className={`pill ${aqiMeta!.cls === "good" ? "" : aqiMeta!.cls}`}
                          style={{ marginTop: 8, background: `${aqiMeta!.color}20`, borderColor: `${aqiMeta!.color}50`, color: aqiMeta!.color }}>
                      {aqiMeta!.label}
                    </span>
                  </div>
                  <GaugeBlock label="PM2.5" value={(data.air.components.pm2_5 ?? 0).toFixed(2)} unit="µg/m³" color="#fb923c"/>
                  <GaugeBlock label="PM10"  value={(data.air.components.pm10  ?? 0).toFixed(2)} unit="µg/m³" color="#fbbf24"/>
                </div>

                <div className="panel" style={{ marginBottom: 14 }}>
                  <h3>Pollutant Concentrations · µg/m³</h3>
                  <div className="chart-wrap">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={Object.entries(data.air.components).map(([name, value]) => ({
                        name: name.toUpperCase(), value
                      }))}>
                        <CartesianGrid stroke={GRID_COLOR} strokeDasharray="3 3"/>
                        <XAxis dataKey="name" tick={TICK_STYLE}/>
                        <YAxis tick={TICK_STYLE}/>
                        <Tooltip content={<ChartTip/>}/>
                        <Bar dataKey="value" name="Concentration µg/m³" radius={[6,6,0,0]}>
                          {Object.keys(data.air.components).map((_, i) => (
                            <Cell key={i} fill={["#34d399","#4f96ff","#2dd4bf","#fbbf24","#fb923c","#f87171","#f472b6","#8b5cf6"][i%8]}/>
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                <div className="panel">
                  <h3>Pollutant Details</h3>
                  <div className="table-wrap">
                    <table className="data-table">
                      <thead><tr><th>Pollutant</th><th>Concentration (µg/m³)</th></tr></thead>
                      <tbody>
                        {Object.entries(data.air.components).map(([k, v]) => (
                          <tr key={k}>
                            <td><strong style={{ color: "#b0cce6" }}>{k.toUpperCase()}</strong></td>
                            <td>{v.toFixed(4)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </>
            ) : (
              <div className="notice warn">⚠️ Air quality feed unavailable from OpenWeather.</div>
            )}
            <div className="notice info" style={{ marginTop: 14 }}>
              ℹ️ OpenWeather AQI uses a 1–5 scale (1=Good, 5=Very Poor).
              This is <strong>NOT</strong> India&apos;s CPCB National AQI scale (0–500).
              For regulatory purposes use the official CPCB data portal.
            </div>
          </>
        )}

        {/* ── PAGE: PUBLIC HEALTH ── */}
        {page === "Public Health" && (
          <>
            <SectionHead kicker="EPIDEMIOLOGY & ENVIRONMENT" title="Public Health Surveillance"
              sub="Upload authorized, aggregated, de-identified records for browser-local trend analysis"/>
            <div className="notice info" style={{ marginBottom: 14 }}>
              📋 Required CSV columns: <code>date</code>, <code>zone</code>, <code>disease</code>, <code>cases</code>.
              All data processing happens locally in your browser — nothing is uploaded to any server.
            </div>
            <HealthUpload/>
          </>
        )}

        {/* ── PAGE: MAP & REPORTS ── */}
        {data && page === "Map & Reports" && (
          <>
            <SectionHead kicker="GEOSPATIAL VIEW" title="Nagpur Monitoring Location"
              sub="Reference coordinate used for all API calls"/>

            <div className="panel" style={{ marginBottom: 14 }}>
              <h3>📍 Nagpur, Maharashtra · 21.1458° N, 79.0882° E</h3>
              <div className="map-wrap">
                <iframe
                  title="Nagpur map"
                  src="https://www.openstreetmap.org/export/embed.html?bbox=78.95%2C21.07%2C79.22%2C21.22&layer=mapnik&marker=21.1458%2C79.0882"
                  loading="lazy"
                />
              </div>
              <p style={{ marginTop: 10, fontSize: 11, color: "#4e7a9a" }}>
                📡 This pin represents the city-centre API reference coordinate, not zone-wise weather coverage.
              </p>
            </div>

            <div className="two-col" style={{ marginBottom: 14 }}>
              <div className="panel">
                <h3>📥 Download Datasets</h3>
                <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 8 }}>
                  <button className="btn" onClick={() => csvDownload(data.forecast)}>
                    <TrendingUp size={13}/> Full Forecast CSV
                  </button>
                  <button className="btn" onClick={() => csvDownload(
                    data.forecast.filter(x => x.rainfall_3h_mm > 0), "nagpur-rainfall-periods.csv"
                  )}>
                    <CloudRain size={13}/> Rainy Periods CSV
                  </button>
                </div>
              </div>
              <div className="panel">
                <h3>📋 Location Metadata</h3>
                <div className="forecast-list">
                  {[
                    ["City",         "Nagpur"],
                    ["State",        "Maharashtra, India"],
                    ["Latitude",     "21.1458° N"],
                    ["Longitude",    "79.0882° E"],
                    ["Altitude",     "≈ 310 m above MSL"],
                    ["Climate Zone", "Tropical Wet & Dry (Aw)"],
                    ["Data Source",  "OpenWeatherMap API v2.5"],
                  ].map(([k, v]) => (
                    <div className="forecast-row" key={k}>
                      <span>{k}</span><strong>{v}</strong>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="notice info">
              ℹ️ This dashboard uses a single API coordinate. It is a <strong>research and planning prototype</strong> —
              not for emergency response, regulatory reporting or official forecasting.
            </div>
          </>
        )}

        {/* Footer */}
        <div className="footer">
          <span>NAGPUR CLIMATE INTELLIGENCE · PROFESSIONAL EDITION v2.0</span>
          <span>DATA: OPENWEATHERMAP · CACHE: 10 MIN · 21.1458°N 79.0882°E</span>
          <span>⚠️ ILLUSTRATIVE TOOL — NOT FOR EMERGENCY OR REGULATORY USE</span>
        </div>
      </main>
    </div>
  );
}
