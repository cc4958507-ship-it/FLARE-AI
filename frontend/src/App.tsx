import { t, useLanguage, setLanguage, getLanguage, msg } from "./i18n";
import { useEffect, useId, useRef, useState, type ReactNode } from "react";
import {
  Link,
  NavLink,
  Route,
  Routes,
  useLocation,
  useNavigate,
  useSearchParams,
} from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  BookOpen,
  ChartLine,
  ClockCounterClockwise,
  MagnifyingGlass,
  ArrowUpRight,
  ArrowRight,
  Plus,
  Check,
  X,
  Sun,
  Moon,
  Play,
  Pause,
  GitBranch,
  DownloadSimple,
  WarningCircle,
  SlidersHorizontal,
  Flask,
  Rows,
  ArrowLeft,
  FileText,
} from "@phosphor-icons/react";
import * as echarts from "echarts/core";
import { LineChart } from "echarts/charts";
import {
  GridComponent,
  LegendComponent,
  TooltipComponent,
  MarkLineComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
echarts.use([
  LineChart,
  GridComponent,
  LegendComponent,
  TooltipComponent,
  MarkLineComponent,
  CanvasRenderer,
]);
import { api } from "./api";
import Datasets from "./Datasets";
import Agents from "./Agents";
import ResearchLibrary from "./ResearchLibrary";
import type {
  Investigation,
  Run,
  Decision,
  Audit,
  Plan,
  Explanation,
  Frame,
} from "./types";

function Button({
  children,
  className = "",
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button className={"button " + className} {...props}>
      {t(children)}
    </button>
  );
}
function Status({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: string;
}) {
  return <span className={"status " + tone}>{t(children)}</span>;
}
function ErrorBox({ error, retry }: { error: unknown; retry?: () => void }) {
  return (
    <div className="error-box" role="alert">
      <WarningCircle size={20} />
      <div>
        {t(error instanceof Error ? error.message : "The request failed.")}
        {retry && <Button onClick={retry}>{t("Retry request")}</Button>}
      </div>
    </div>
  );
}
function Loading({
  children = "Loading research records…",
}: {
  children?: ReactNode;
}) {
  return (
    <div className="loading" role="status">
      {t(children)}
    </div>
  );
}
function Empty({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="empty">
      <Flask size={32} weight="duotone" />
      <h2>{t(title)}</h2>
      {t(children)}
    </div>
  );
}
function Modal({
  open,
  onClose,
  title,
  children,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  useEffect(() => {
    if (open && !ref.current?.open) ref.current?.showModal();
    else if (!open && ref.current?.open) ref.current?.close();
  }, [open]);
  return (
    <dialog
      ref={ref}
      onCancel={onClose}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      aria-labelledby={titleId}
    >
      <div className="dialog-head">
        <h2 id={titleId}>{t(title)}</h2>
        <Button
          className="icon-button"
          onClick={onClose}
          aria-label={t("Close dialog")}
        >
          <X size={20} />
        </Button>
      </div>
      {t(children)}
    </dialog>
  );
}
function PageTitle({
  kicker,
  title,
  description,
  action,
}: {
  kicker: string;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    heading.current?.focus();
  }, [title]);
  return (
    <div className="page-title">
      <div>
        <p className="eyebrow">{t(kicker)}</p>
        <h1 ref={heading} tabIndex={-1}>
          {t(title)}
        </h1>
        {description && <p className="description">{t(description)}</p>}
      </div>
      {t(action)}
    </div>
  );
}

export default function App() {
  const language = useLanguage();
  const firstRoute = useRef(true);
  const location = useLocation();
  const [dark, setDark] = useState(
    () => localStorage.getItem("flare-theme") === "dark",
  );
  useEffect(() => {
    document.documentElement.dataset.theme = dark ? "dark" : "light";
    localStorage.setItem("flare-theme", dark ? "dark" : "light");
  }, [dark]);
  useEffect(() => {
    document.title =
      "FLARE AI · " +
      t(location.pathname.includes("research-files") ? "Research files" : location.pathname.includes("agents") ? "Research agents" : location.pathname.includes("datasets") ? "Measurement imports" : location.pathname.includes("lab")
        ? "Simulation Lab"
        : location.pathname.includes("archive")
          ? "Run archive"
          : location.pathname.includes("scenario")
            ? "Scenario builder"
            : "Evidence library");
  }, [location.pathname, language]);
  useEffect(() => {
    if (firstRoute.current) {
      firstRoute.current = false;
      return;
    }
    requestAnimationFrame(() =>
      (
        document.querySelector<HTMLElement>("h1") ||
        document.querySelector<HTMLElement>("#main")
      )?.focus(),
    );
  }, [location.pathname]);
  const runs = useQuery({
    queryKey: ["runs"],
    queryFn: () => api<{ items: Run[] }>("/runs"),
    refetchInterval: 5000,
  });
  const health = useQuery({queryKey:['health'], queryFn:() => api<{model_mode:string}>("/health"), refetchInterval:30000});
  return (
    <>
      <a className="skip-link" href="#main">{t("Skip to content")}</a>
      <div className="app-shell">
        <aside className="sidebar">
          <Link to="/" className="wordmark" aria-label={t("FLARE AI home")}>{t("FLARE")}<span>{t("AI")}</span>
          </Link>
          <p className="brand-sub">{t("Combustion research")}<br />{t(" & observation")}</p>
          <div className="nav-caption">{t("Workbench")}</div>
          <nav aria-label={t("Main navigation")}>
            <NavLink to="/research-files"><FileText size={20}/>{t('Research files')}</NavLink>
            <NavLink to="/agents"><Flask size={20} />{language === 'ar' ? 'إيجنتس البحث' : 'Research agents'}</NavLink>
            <NavLink to="/datasets"><FileText size={20} />{t("Measurement imports")}</NavLink>
            <NavLink to="/" end>
              <BookOpen size={20} />{t("Evidence library")}</NavLink>
            <NavLink to="/lab">
              <ChartLine size={20} />{t("Simulation lab")}</NavLink>
            <NavLink to="/archive">
              <ClockCounterClockwise size={20} />{t("Run archive")}{runs.data && (
                <span className="nav-count">{t(runs.data.items.length)}</span>
              )}
            </NavLink>
          </nav>
          <div className="sidebar-bottom">
            <div className="workspace-label">
              <span className="workspace-avatar">{t("F")}</span>
              <div>{t("Research workspace")}<small>{t("Local prototype · v0.2")}</small>
              </div>
            </div>
            <div className="theme-row">
              <span>{t("Appearance")}</span>
              <Button
                className="icon-button"
                onClick={() => setDark(!dark)}
                aria-label={
                  t(dark ? "Switch to light theme" : "Switch to dark theme")
                }
              >
                {dark ? <Sun size={19} /> : <Moon size={19} />}
              </Button>
            </div>
          </div>
        </aside>
        <div className="workspace">
          <header className="topbar">
            <div className="breadcrumb">{t("Workspace ")}<span>/</span>{t(" ")}
              <strong>
                {t(location.pathname.includes("research-files") ? "Research files" : location.pathname.includes("agents") ? (language === 'ar' ? 'إيجنتس البحث' : 'Research agents') : location.pathname.includes("datasets") ? "Measurement imports" : location.pathname.includes("lab")
                  ? "Simulation lab"
                  : location.pathname.includes("archive")
                    ? "Run archive"
                    : location.pathname.includes("scenario")
                      ? "Scenario builder"
                      : location.pathname.includes("compare")
                        ? "Compare evidence"
                        : "Evidence library")}
              </strong>
            </div>
            <div className="topbar-tools">
              <span className="top-note" title={t(health.data?.model_mode === 'live' ? 'Live Kie evidence explanations are configured. Simulation decisions remain deterministic.' : 'Live Kie model is not configured. Evidence explanations use reviewed source summaries.')}>
                <Flask size={16} />{t(health.data?.model_mode === 'live' ? 'AI explanations: live' : 'AI explanations: offline')}
              </span>
              <label className="language-switch"><span className="sr-only">Language / اللغة</span>
                <select value={language} onChange={e => setLanguage(e.target.value as 'ar' | 'en')} aria-label="Language / اللغة">
                  <option value="en" lang="en">English</option><option value="ar" lang="ar">العربية</option>
                </select>
              </label>
            </div>
          </header>
          <main id="main" tabIndex={-1}>
            <Routes>
              <Route path="/research-files" element={<ResearchLibrary/>}/>
              <Route path="/agents" element={<Agents />} />
              <Route path="/datasets" element={<Datasets />} />
              <Route path="/" element={<Library />} />
              <Route path="/investigations/:id" element={<Library />} />
              <Route path="/compare" element={<Compare />} />
              <Route path="/scenario" element={<Scenario />} />
              <Route path="/lab" element={<Lab />} />
              <Route path="/lab/:id" element={<Lab />} />
              <Route path="/archive" element={<Archive />} />
              <Route
                path="*"
                element={
                  <Empty title={t("This page does not exist")}>
                    <Link className="button" to="/">{t("Return to evidence library")}</Link>
                  </Empty>
                }
              />
            </Routes>
          </main>
          <footer className="workspace-footer">
            <span>{t("FLARE AI / Research workbench")}</span>
            <span>{t("Synthetic simulations are not safety assessments.")}</span>
          </footer>
        </div>
      </div>
    </>
  );
}

function Library() {
  const [params, setParams] = useSearchParams();
  const q = params.get("q") || "";
  const family = params.get("family") || "";
  const [selected, setSelected] = useState<string[]>([]);
  const [detail, setDetail] = useState<Investigation | null>(null);
  const [notice, setNotice] = useState("");
  const query = useQuery({
    queryKey: ["investigations", q, family],
    queryFn: () =>
      api<{ items: Investigation[] }>(
        "/investigations?" +
          new URLSearchParams({ q, ...(family ? { family } : {}) }),
      ),
  });
  const toggle = (id: string) => {
    if (!selected.includes(id) && selected.length === 3) {
      setNotice(
        "Compare up to three records. Remove one before adding another.",
      );
      return;
    }
    setNotice("");
    setSelected((s) =>
      s.includes(id) ? s.filter((i) => i !== id) : [...s, id],
    );
  };
  const filter = (key: string, value: string) =>
    setParams(
      (p) => {
        if (value) p.set(key, value);
        else p.delete(key);
        return p;
      },
      { replace: true },
    );
  const all = query.data?.items || [];
  return (
    <>
      <section className="library-intro">
        <div>
          <p className="eyebrow">{t("The evidence comes first.")}</p>
          <h1 tabIndex={-1}>{t("Look beyond")}<br />{t("the visible flame")}<span className="copper">.</span>
          </h1>
          <p>{t("Explore combustion research, understand its limits,")}<br className="desktop-break" />{t(" and test your questions in a transparent simulation.")}</p>
          <Link className="text-link" to="/scenario">{t("Build a research scenario ")}<ArrowRight size={18} />
          </Link>
        </div>
        <div className="specimen">
          <div className="specimen-meta">
            <span>{t("Observation study")}</span>
            <span>{t("01 / FLEX")}</span>
          </div>
          <div className="droplet-study" aria-hidden="true">
            <div className="orbit orbit-one" />
            <div className="orbit orbit-two" />
            <div className="droplet-core" />
            <div className="annotation annotation-a">{t("Visible boundary")}</div>
            <div className="annotation annotation-b">{t("Unobserved source?")}</div>
            <div className="specimen-axis" />
          </div>
          <div className="specimen-caption">
            <span>{t("Absence of a visible flame ≠ proof of extinction")}</span>
            <small>{t("Conceptual schematic · not an experimental image")}</small>
          </div>
        </div>
      </section>
      <section className="library-section">
        <div className="section-heading">
          <div>
            <h2>{t("Evidence library ")}<span className="count">{t(all.length)}</span>
            </h2>
            <p>{t("Source-linked context. Unknowns stay visible.")}</p>
          </div>
          <Link className="button" to="/scenario">
            <Plus size={18} />{t("New scenario")}</Link>
        </div>
        <div className="filterbar">
          <label className="search">
            <MagnifyingGlass size={20} />
            <input
              aria-label={t("Search the evidence library")}
              placeholder={t("Search droplets, monitoring, extinction…")}
              value={q}
              onChange={(e) => filter("q", e.target.value)}
            />
            {q && (
              <button onClick={() => filter("q", "")} aria-label={t("Clear search")}>
                <X size={16} />
              </button>
            )}
          </label>
          <label className="family-select">
            <SlidersHorizontal size={18} />
            <span className="sr-only">{t("Research family")}</span>
            <select
              aria-label={t("Filter by research family")}
              value={family}
              onChange={(e) => filter("family", e.target.value)}
            >
              <option value="">{t("All research families")}</option>
              {[
                "Liquid droplets",
                "Suppression research",
                "Gas monitoring",
                "Atmosphere research",
              ].map((f) => (
                <option key={f}>{t(f)}</option>
              ))}
            </select>
          </label>
        </div>
        <div className="library-table-heading">
          <span>{t("Research record")}</span>
          <span>{t("Context & availability")}</span>
          <span>{t("Actions")}</span>
        </div>
        {query.isPending ? (
          <Loading />
        ) : query.isError ? (
          <ErrorBox error={query.error} retry={() => query.refetch()} />
        ) : all.length === 0 ? (
          <Empty title={t("No records match these filters")}>
            <p>{t("Try “droplet” or clear your filters to see the research index.")}</p>
            <Button onClick={() => setParams({})}>{t("Clear filters")}</Button>
          </Empty>
        ) : (
          <div className="evidence-list">
            {all.map((row, index) => (
              <article className="evidence-row" key={row.id}>
                <div className="record-number">
                  {t(String(index + 1).padStart(2, "0"))}
                </div>
                <div className="evidence-main">
                  <div className="record-class">
                    <span>{t(row.family)}</span>
                    <span
                      className={
                        "source-type " +
                        (row.type === "Synthetic" ? "synthetic" : "")
                      }
                    >
                      {t(row.type)}
                    </span>
                  </div>
                  <button
                    className="record-title"
                    onClick={() => setDetail(row)}
                  >
                    {t(row.title)}
                  </button>
                  <p>{t(row.summary)}</p>
                  <span className="record-ref">{t(row.reference)}</span>
                  {q && <small className="ranking">{t(row.ranking_reason)}</small>}
                </div>
                <div className="evidence-context">
                  <span>{t(row.gravity)}</span>
                  <small>
                    {row.id === 'flex' ? <Link to="/datasets">{t("FLEX-007 measurements available")}</Link> : row.raw_available
                      ? "Generated series available"
                      : "No raw series imported"}
                  </small>
                  <span className="unknown-count">
                    {t(row.unknowns.length)}{t(" known gaps")}</span>
                </div>
                <div className="evidence-actions">
                  <label className="compare-check">
                    <input
                      type="checkbox"
                      checked={selected.includes(row.id)}
                      onChange={() => toggle(row.id)}
                    />
                    <span>{t("Compare")}</span>
                  </label>
                  <Button
                    className="icon-button"
                    onClick={() => setDetail(row)}
                    aria-label={t("Open " + row.title)}
                  >
                    <ArrowUpRight size={20} />
                  </Button>
                </div>
              </article>
            ))}
          </div>
        )}
        <div className="library-note">
          <FileText size={18} />
          <p>{t("NASA records and literature provide context. Only the clearly labeled synthetic model powers the lab.")}</p>
        </div>
        <div role="status" className="notice">
          {t(notice)}
        </div>
      </section>
      {selected.length > 0 && (
        <div className="compare-tray">
          <span>{t(selected.length)}{t(" of 3 selected")}</span>
          <Button onClick={() => setSelected([])}>{t("Clear selection")}</Button>
          {selected.length >= 2 ? (
            <Link
              className="button primary"
              to={"/compare?ids=" + selected.join(",")}
            >{t("Compare records ")}<ArrowRight size={16} />
            </Link>
          ) : (
            <span className="muted">{t("Select one more record")}</span>
          )}
        </div>
      )}
      <Modal
        open={!!detail}
        title={t(detail?.short || "Investigation")}
        onClose={() => setDetail(null)}
      >
        {detail && <InvestigationDetail row={detail} />}
      </Modal>
    </>
  );
}
function InvestigationDetail({ row }: { row: Investigation }) {
  return (
    <>
      <div className="detail-intro">
        <Status tone={row.type === "Synthetic" ? "copper" : ""}>
          {t(row.type)}
        </Status>
        <h3>{t(row.title)}</h3>
        <p>{t(row.summary)}</p>
      </div>
      <dl className="definition-grid">
        <div>
          <dt>{t("Fuel")}</dt>
          <dd>{t(row.fuel)}</dd>
        </div>
        <div>
          <dt>{t("Geometry")}</dt>
          <dd>{t(row.geometry)}</dd>
        </div>
        <div>
          <dt>{t("Gravity")}</dt>
          <dd>{t(row.gravity)}</dd>
        </div>
        <div>
          <dt>{t("Evidence class")}</dt>
          <dd>{t(row.classification)}</dd>
        </div>
      </dl>
      <h3>{t("What the source supports")}</h3>
      <p>{t(row.finding)}</p>
      <h3>{t("What we still need")}</h3>
      <ul className="gap-list">
        {row.unknowns.map((g) => (
          <li key={g}>{t(g)}</li>
        ))}
      </ul>
      <div className="source-box">
        <strong>{t(row.reference)}</strong>
        <p>{t(row.note)}</p>
        {row.url && (
          <a href={row.url} target="_blank" rel="noreferrer">{t("Open source record ")}<ArrowUpRight size={16} />
          </a>
        )}
      </div>
      <Link
        className="button primary full-width"
        to={"/scenario?ids=" + row.id}
      >{t("Create scenario from this record")}</Link>
    </>
  );
}
function Compare() {
  const [params] = useSearchParams();
  const ids = (params.get("ids") || "flex,cool-flames").split(",");
  const query = useQuery({
    queryKey: ["compare", ids.join(",")],
    queryFn: () =>
      api<{ items: Investigation[]; limitations: string[] }>("/comparisons", {
        investigation_ids: ids,
      }),
  });
  return (
    <>
      <PageTitle
        kicker={t("Evidence / Side by side")}
        title={t("Compare the conditions")}
        description={t("Shared terminology does not imply interchangeable experiments.")}
        action={
          <Link className="button" to="/">
            <ArrowLeft size={16} />{t("Library")}</Link>
        }
      />
      {query.isPending ? (
        <Loading />
      ) : query.isError ? (
        <ErrorBox error={query.error} />
      ) : (
        <>
          <div className="callout">
            <WarningCircle size={22} />
            <div>
              <strong>{t("Context comparison only")}</strong>
              <p>{query.data.limitations.map(t).join(" ")}</p>
            </div>
          </div>
          <div className="table-scroll">
            <table className="comparison-table">
              <caption className="sr-only">{t("Research context comparison")}</caption>
              <thead>
                <tr>
                  <th scope="col">{t("Research context")}</th>
                  {query.data.items.map((i) => (
                    <th scope="col" key={i.id}>
                      {t(i.short)}
                      <small>{t(i.type)}</small>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(
                  [
                    "title",
                    "family",
                    "gravity",
                    "fuel",
                    "geometry",
                    "channels",
                    "unknowns",
                    "reference",
                  ] as const
                ).map((key) => (
                  <tr key={key}>
                    <th scope="row">
                      {t(key === "unknowns"
                        ? "Information gaps"
                        : key[0].toUpperCase() + key.slice(1))}
                    </th>
                    {query.data.items.map((i) => (
                      <td key={i.id}>
                        {t(Array.isArray(i[key])
                          ? (i[key] as string[]).join(" · ") || "Unknown"
                          : i[key])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="section-end">
            <p>{t("Simulation uses the single synthetic profile, regardless of selected literature.")}</p>
            <Link
              className="button primary"
              to={"/scenario?ids=" + ids.join(",")}
            >{t("Build scenario with these sources")}</Link>
          </div>
        </>
      )}
    </>
  );
}

function Scenario() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const cache = useQueryClient();
  const ids = (params.get("ids") || "flex,cool-flames").split(",");
  const [name, setName] = useState(() => t("Droplet extinction study"));
  const [question, setQuestion] = useState(
    () => t("Does the absence of a visible flame establish extinction in this synthetic droplet model?"),
  );
  const [seed, setSeed] = useState(42);
  const [preset, setPreset] = useState("manual");
  const [plan, setPlan] = useState<Plan | null>(null);
  const [pack, setPack] = useState<{
    items: Investigation[];
    explanation: Explanation;
  } | null>(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState<unknown>(null);
  const [accepted, setAccepted] = useState(false);
  const review = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy("Retrieving source context and creating a versioned plan…");
    setError(null);
    try {
      const scenario = await api<{ id: string }>("/scenarios", {
        name,
        question,
        investigation_ids: ids,
      });
      const evidence = await api<{
        items: Investigation[];
        explanation: Explanation;
      }>("/scenarios/" + scenario.id + "/evidence", { version: 1, language:getLanguage() });
      setPack(evidence);
      setPlan(
        await api<Plan>("/scenarios/" + scenario.id + "/plans", { version: 1 }),
      );
    } catch (e) {
      setError(e);
    } finally {
      setBusy("");
    }
  };
  const launch = async () => {
    if (!plan) return;
    setBusy("Approving plan and preparing the run…");
    setError(null);
    try {
      await api("/plans/" + plan.id + "/approve", {
        plan_version: 1,
        profile_ref: "synthetic-v1",
      });
      const run = await api<Run>("/runs", {
        plan_ref: plan.id,
        seed,
        name,
        preset,
      });
      await cache.invalidateQueries({ queryKey: ["runs"] });
      navigate("/lab/" + run.id);
    } catch (e) {
      setError(e);
    } finally {
      setBusy("");
    }
  };
  return (
    <>
      <PageTitle
        kicker={t("Research / Scenario builder")}
        title={t(plan ? "Review your observation plan" : "Start with a question")}
        description={t("Evidence informs the plan. Deterministic rules determine the result.")}
      />
      <div className="scenario-layout">
        <div className="scenario-main">
          {!plan ? (
            <form onSubmit={review} className="panel scenario-form">
              <div className="panel-heading">
                <span className="step-label">01</span>
                <h2>{t("Define the investigation")}</h2>
              </div>
              <label>{t("Scenario name")}<input
                  required
                  maxLength={120}
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </label>
              <label>{t("Research question")}<textarea
                  required
                  minLength={5}
                  maxLength={2000}
                  rows={4}
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                />
              </label>
              <div className="two-fields">
                <label>{t("Fuel context")}<input readOnly value="Abstract liquid droplet" />
                </label>
                <label>{t("Geometry")}<input readOnly value="Single droplet" />
                </label>
              </div>
              <div className="two-fields">
                <label>{t("Reproducibility seed")}<input
                    type="number"
                    required
                    min={0}
                    max={2147483647}
                    value={seed}
                    onChange={(e) => setSeed(Number(e.target.value))}
                  />
                </label>
                <label>{t("Initial event schedule")}<select
                    value={preset}
                    onChange={(e) => setPreset(e.target.value)}
                  >
                    <option value="manual">{t("Manual interventions")}</option>
                    <option value="reduce">{t("Reduce source at 20s")}</option>
                    <option value="stop">{t("Stop source at 20s")}</option>
                    <option value="data-loss">{t("Stop at 0s + missing CO channel")}</option>
                  </select>
                </label>
              </div>
              <p className="field-hint">{t("The schedule changes generator events, never selects a result. You can also apply interventions in the lab.")}</p>
              <Button type="submit" className="primary" disabled={!!busy}>{t("Retrieve evidence & review plan ")}<ArrowRight size={18} />
              </Button>
            </form>
          ) : (
            <>
              <section className="panel">
                <div className="panel-heading">
                  <span className="step-label">02</span>
                  <h2>{t("Evidence context")}</h2>
                  <Status>
                    {t(pack?.explanation.mode === "live"
                      ? "Live explanation"
                      : "Reviewed summaries")}
                  </Status>
                </div>
                <p className="muted">{t(pack?.explanation.message)}</p>
                {pack?.explanation.claims.map((c, i) => (
                  <div className="claim" key={i}>
                    <p>{t(c.text)}</p>
                    <span>
                      {t(c.classification)} · {t(c.evidence_ids.join(", "))}
                    </span>
                  </div>
                ))}
              </section>
              <section className="panel">
                <div className="panel-heading">
                  <span className="step-label">03</span>
                  <h2>{t("Approve the monitoring plan")}</h2>
                </div>
                <dl className="definition-grid">
                  <div>
                    <dt>{t("Profile")}</dt>
                    <dd>{t("synthetic-v1 · version 1")}</dd>
                  </div>
                  <div>
                    <dt>{t("Continuous hold")}</dt>
                    <dd>{t("30 seconds")}</dd>
                  </div>
                  <div>
                    <dt>{t("Danger clearance")}</dt>
                    <dd>{t("10 seconds before hold")}</dd>
                  </div>
                  <div>
                    <dt>{t("Required channels")}</dt>
                    <dd>{t("Flame, thermal, CO, ventilation")}</dd>
                  </div>
                </dl>
                <label className="approval-check">
                  <input
                    type="checkbox"
                    checked={accepted}
                    onChange={(e) => setAccepted(e.target.checked)}
                  />
                  <span>{t("I reviewed the source limitations and approve this plan for the synthetic simulation only.")}</span>
                </label>
                <div className="button-row">
                  <Button
                    className="primary"
                    onClick={launch}
                    disabled={!accepted || !!busy}
                  >{t("Approve plan & open lab ")}<ArrowRight size={18} />
                  </Button>
                  <Button
                    onClick={() => {
                      setPlan(null);
                      setAccepted(false);
                    }}
                    disabled={!!busy}
                  >{t("Edit scenario")}</Button>
                </div>
              </section>
            </>
          )}
          {busy && <Loading>{t(busy)}</Loading>}
          {error != null && <ErrorBox error={error} />}
        </div>
        <aside className="scenario-aside">
          <p className="eyebrow">{t("Observation protocol")}</p>
          <h2>{t("Measure what")}<br />{t("you cannot see.")}</h2>
          <div className="protocol-rule">
            <span>01</span>
            <div>
              <strong>{t("Keep evidence in scope")}</strong>
              <p>{t("Sources provide context, not interchangeable calibration.")}</p>
            </div>
          </div>
          <div className="protocol-rule">
            <span>02</span>
            <div>
              <strong>{t("Observe independent signals")}</strong>
              <p>{t("A missing channel resets the continuous verification hold.")}</p>
            </div>
          </div>
          <div className="protocol-rule">
            <span>03</span>
            <div>
              <strong>{t("Separate the conclusions")}</strong>
              <p>{t("Combustion, contaminants and data quality remain independent.")}</p>
            </div>
          </div>
          <div className="source-footnote">
            {msg("A reference to {0} sources is selected", [ids.length])}<br />{t("Synthetic model · sim_unit only")}</div>
        </aside>
      </div>
    </>
  );
}

function SignalChart({
  frames,
  run,
  resetKey,
}: {
  frames: Frame[];
  run: Run;
  resetKey: number;
}) {
  const language = useLanguage();
  const host = useRef<HTMLDivElement>(null);
  const chart = useRef<echarts.ECharts | null>(null);
  const [theme, setTheme] = useState(document.documentElement.dataset.theme);
  useEffect(() => {
    const observer = new MutationObserver(() =>
      setTheme(document.documentElement.dataset.theme),
    );
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-theme"],
    });
    return () => observer.disconnect();
  }, []);
  useEffect(() => {
    if (!host.current) return;
    chart.current = echarts.init(host.current);
    const observer = new ResizeObserver(() => chart.current?.resize());
    observer.observe(host.current);
    return () => {
      observer.disconnect();
      chart.current?.dispose();
    };
  }, []);
  useEffect(() => {
    const dark = document.documentElement.dataset.theme === "dark";
    const ink = dark ? "#aaa9a3" : "#64645e";
    chart.current?.setOption(
      {
        animation: false,
        textStyle: { fontFamily: "IBM Plex Sans, sans-serif" },
        tooltip: { trigger: "axis", confine: true },
        legend: {
          selectedMode: false,
          top: 0,
          left: 0,
          textStyle: { color: ink },
          itemWidth: 18,
          itemHeight: 3,
        },
        grid: {
          top: (host.current?.clientWidth || 600) < 500 ? 80 : 56,
          left: 42,
          right: 20,
          bottom: 48,
        },
        xAxis: {
          type: "value",
          name: t("Virtual time (s)"),
          nameLocation: "middle",
          nameGap: 30,
          min: 0,
          max: Math.max(60, Math.ceil(run.t / 30) * 30),
          axisLabel: { color: ink },
          axisLine: { lineStyle: { color: ink } },
          splitLine: { show: false },
        },
        yAxis: {
          type: "value",
          min: 0,
          max: 1,
          name: "sim_unit",
          nameTextStyle: { color: ink, align: "left" },
          splitLine: { lineStyle: { color: dark ? "#353734" : "#e9e9e3" } },
          axisLabel: { color: ink },
        },
        series: [
          {
            key: "thermal_excess",
            name: "Thermal excess",
            color: dark ? "#f2ad80" : "#a34b20",
            type: "solid",
          },
          {
            key: "co_proxy",
            name: "CO proxy",
            color: dark ? "#8bcbb8" : "#2b7766",
            type: "solid",
          },
          {
            key: "co2_proxy",
            name: "CO₂ proxy",
            color: dark ? "#c7b989" : "#83713c",
            type: "dashed",
          },
          {
            key: "flame_presence",
            name: "Visible flame",
            color: dark ? "#b4b6b2" : "#777970",
            type: "dotted",
          },
        ].map((s, i) => ({
          name: t(s.name),
          type: "line",
          symbol: "none",
          connectNulls: false,
          step: s.key === "flame_presence" ? "end" : undefined,
          data: frames.map((f) => [
            f.sample.t,
            f.sample[s.key as keyof typeof f.sample],
          ]),
          lineStyle: {
            width: i === 3 ? 1.5 : 2.5,
            color: s.color,
            type: s.type,
          },
          itemStyle: { color: s.color },
          ...(i === 0
            ? {
                markLine: {
                  symbol: "none",
                  silent: true,
                  label: {
                    formatter: t("Intervention"),
                    color: ink,
                    fontSize: 10,
                  },
                  lineStyle: { color: ink, type: "dashed" },
                  data: run.interventions
                    .filter((e) => e.t <= run.t)
                    .map((e) => ({ xAxis: e.t })),
                },
              }
            : {}),
        })),
      },
      true,
    );
  }, [frames, run, resetKey, theme, language]);
  return (
    <div
      ref={host}
      className="signal-chart"
      role="img"
      aria-label={t("Observed synthetic channel values over virtual time. Exact readings are available in the channel table below.")}
    />
  );
}
function Lab() {
  const location = useLocation();
  const navigate = useNavigate();
  const cache = useQueryClient();
  const all = useQuery({
    queryKey: ["runs"],
    queryFn: () => api<{ items: Run[] }>("/runs"),
  });
  const id = location.pathname.split("/")[2] || all.data?.items[0]?.id;
  const runQuery = useQuery({
    queryKey: ["run", id],
    queryFn: () => api<Run>("/runs/" + id),
    enabled: !!id,
    refetchInterval: 1000,
  });
  const framesQuery = useQuery({
    queryKey: ["frames", id],
    queryFn: () => api<{ items: Frame[] }>("/runs/" + id + "/samples"),
    enabled: !!id,
    refetchInterval: 1000,
  });
  const events = useQuery({
    queryKey: ["events", id],
    queryFn: () => api<{ items: Audit[] }>("/runs/" + id + "/events"),
    enabled: !!id,
    refetchInterval: 1500,
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [branch, setBranch] = useState(false);
  const [branchTime, setBranchTime] = useState(0);
  const [branchName, setBranchName] = useState(() => t("Alternative intervention"));
  const [confirm, setConfirm] = useState<string | null>(null);
  const [faultKind, setFaultKind] = useState("drop");
  const [inspect, setInspect] = useState<Decision | null>(null);
  const [resetKey, setResetKey] = useState(0);
  const run = runQuery.data;
  const frames = framesQuery.data?.items || [];
  const decision = run?.decision;
  const mutate = async (path: string, body: unknown) => {
    setBusy(true);
    setError(null);
    try {
      await api("/runs/" + id + path, body);
      await Promise.all([
        cache.invalidateQueries({ queryKey: ["run", id] }),
        cache.invalidateQueries({ queryKey: ["events", id] }),
      ]);
      setConfirm(null);
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };
  const doBranch = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const child = await api<Run>("/runs/" + id + "/branches", {
        parent_t_ms: branchTime * 1000,
        name: branchName,
      });
      setBranch(false);
      await cache.invalidateQueries({ queryKey: ["runs"] });
      navigate("/lab/" + child.id);
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };
  if (all.isPending) return <Loading>{t("Loading saved runs…")}</Loading>;
  if (all.isError)
    return <ErrorBox error={all.error} retry={() => all.refetch()} />;
  if (!id)
    return (
      <>
        <PageTitle
          kicker={t("Research / Simulation lab")}
          title={t("A question needs an observation")}
        />
        <Empty title={t("Your lab is ready")}>
          <p>{t("Create a scenario and review its plan before starting the synthetic observation.")}</p>
          <Link className="button primary" to="/scenario">{t("Create a research scenario")}</Link>
        </Empty>
      </>
    );
  if (runQuery.isError)
    return <ErrorBox error={runQuery.error} retry={() => runQuery.refetch()} />;
  if (!run)
    return <Loading>{t("Restoring measurements and decision state…")}</Loading>;
  if (!decision)
    return (
      <Empty title={t("This run has no valid saved snapshot")}>
        <p>{t("Create a new scenario to begin a complete observation history.")}</p>
        <Link className="button primary" to="/scenario">{t("Create scenario")}</Link>
      </Empty>
    );
  return (
    <>
      <PageTitle
        kicker={t("Workbench / Simulation lab")}
        title={t(run.name)}
        description={t("Single-droplet model · " + run.id)}
        action={
          <div className="button-row">
            <Button
              onClick={() => {
                setBranchTime(Math.max(0, run.t - 1));
                setBranch(true);
              }}
            >
              <GitBranch size={18} />{t("New branch")}</Button>
            <a
              className="button"
              href={"/api/v1/runs/" + id + "/report?format=json"}
            >
              <DownloadSimple size={18} />{t("Export run")}</a>
          </div>
        }
      />
      <div className="lab-banner">
        <Status tone="copper">{t("Synthetic demo")}</Status>
        <span>{t("Educational model · sim_unit · no physical calibration")}</span>
        <span className="mono">{t("Seed ")}{t(run.seed)}{t(" / synthetic-v1")}</span>
      </div>
      {error != null && <ErrorBox error={error} />}
      <div className="lab-layout">
        <div className="lab-main">
          <section className="panel signals-panel">
            <div className="panel-heading">
              <div>
                <h2>{t("What do the signals show?")}</h2>
                <p>{t("Observed channels, not the hidden model source.")}</p>
              </div>
              <Button
                className="subtle"
                onClick={() => setResetKey((k) => k + 1)}
              >{t("Reset view")}</Button>
            </div>
            {framesQuery.isError ? (
              <ErrorBox error={framesQuery.error} />
            ) : (
              <SignalChart frames={frames} run={run} resetKey={resetKey} />
            )}
            <div className="transport">
              <div className="play-controls">
                <Button
                  className={run.status === "running" ? "" : "primary"}
                  disabled={busy || run.status === "completed"}
                  onClick={() =>
                    mutate("/commands", {
                      command:
                        run.status === "running"
                          ? "pause"
                          : run.status === "ready"
                            ? "start"
                            : "resume",
                      command_id: crypto.randomUUID(),
                    })
                  }
                >
                  {run.status === "running" ? (
                    <Pause size={18} weight="fill" />
                  ) : (
                    <Play size={18} weight="fill" />
                  )}
                  {t(run.status === "running"
                    ? "Pause"
                    : run.status === "completed"
                      ? "Completed"
                      : run.status === "ready"
                        ? "Start run"
                        : "Resume")}
                </Button>
                <span className="run-clock">
                  {t(String(Math.floor(run.t / 60)).padStart(2, "0"))}:
                  {t(String(run.t % 60).padStart(2, "0"))}
                  <small> / 04:00</small>
                </span>
              </div>
              <div className="speed-controls" aria-label={t("Playback speed")}>
                {([1, 4, 16] as const).map((s) => (
                  <button
                    key={s}
                    disabled={busy || run.status === "completed"}
                    aria-pressed={run.speed === s}
                    onClick={() =>
                      mutate("/commands", {
                        command: "speed",
                        speed: s,
                        command_id: crypto.randomUUID(),
                      })
                    }
                  >
                    {t(s)}×
                  </button>
                ))}
              </div>
              <Status>{t(run.status)}</Status>
            </div>
          </section>
          <section className="panel decision-panel">
            <div className="decision-state">
              <span className="eyebrow">{t("Combustion status")}</span>
              <div
                className={
                  "decision-value " + decision.combustion_status.toLowerCase()
                }
              >
                {decision.combustion_status === "Verified" ? (
                  <Check size={30} />
                ) : (
                  <WarningCircle size={30} />
                )}
                <h2>{t(decision.combustion_status)}</h2>
              </div>
              <p>
                {t(decision.combustion_status === "Verified"
                  ? "Verified within simulated conditions"
                  : decision.combustion_status === "Danger"
                    ? "Observed danger or latched evidence remains."
                    : "Evidence is incomplete or the continuous hold is still in progress.")}
              </p>
              <Button
                className="text-link"
                onClick={() => setInspect(decision)}
              >{t("Inspect decision ")}<ArrowRight size={16} />
              </Button>
            </div>
            <div className="independent-states">
              <div>
                <span>{t("Atmosphere")}</span>
                <strong>{t(decision.atmosphere_status)}</strong>
                <small>{t("Separate from combustion")}</small>
              </div>
              <div>
                <span>{t("Required data")}</span>
                <strong>{t(decision.required_quality)}</strong>
                <small>
                  {t(run.fault_at !== null
                    ? "CO channel loss scheduled or active"
                    : "Four required channels")}
                </small>
              </div>
            </div>
          </section>
          <section className="panel hold-panel">
            <div className="panel-heading">
              <h2>{t("Continuous verification window")}</h2>
              <span className="mono">{t(Math.min(30, decision.hold_elapsed_s))}{t(" / 30 s")}</span>
            </div>
            <div
              className="hold-ruler"
              aria-label={
                msg("Verification hold {0} of 30 seconds", [Math.min(30, decision.hold_elapsed_s)])
              }
            >
              <div
                style={{
                  width:
                    Math.min(100, (decision.hold_elapsed_s / 30) * 100) + "%",
                }}
              />
              {[0, 5, 10, 15, 20, 25, 30].map((n) => (
                <span style={{ left: (n / 30) * 100 + "%" }} key={n}>
                  <i />
                  {t(n)}{t("s")}</span>
              ))}
            </div>
            <p className="muted">{t("A complete 10-second danger clearance precedes this hold. Data gaps or context changes reset it.")}</p>
          </section>
          <details className="panel channel-details">
            <summary>
              <Rows size={18} />{t("Channel readings ")}<span>{t("Accessible table")}</span>
            </summary>
            <div className="table-scroll">
              <table>
                <caption>{t("All observed synthetic samples · sim_unit")}</caption>
                <thead>
                  <tr>
                    <th scope="col">{t("Time (s)")}</th>
                    <th scope="col">{t("Flame")}</th>
                    <th scope="col">{t("Thermal")}</th>
                    <th scope="col">{t("CO")}</th>
                    <th scope="col">{t("Ventilation")}</th>
                    <th scope="col">{t("CO₂")}</th>
                  </tr>
                </thead>
                <tbody>
                  {frames.map((f) => (
                    <tr key={f.sample.t}>
                      <th scope="row">{t(f.sample.t)}</th>
                      {(
                        [
                          "flame_presence",
                          "thermal_excess",
                          "co_proxy",
                          "ventilation_proxy",
                          "co2_proxy",
                        ] as const
                      ).map((k) => (
                        <td key={k}>
                          {t(f.sample[k] === null
                            ? "Missing"
                            : f.sample[k]?.toFixed(3))}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        </div>
        <aside className="lab-aside">
          <section className="panel interventions-panel">
            <div className="panel-heading">
              <h2>{t("Intervention controls")}</h2>
            </div>
            <p>{t("Actions change future observations. Review before applying.")}</p>
            <button
              className="intervention-option"
              disabled={busy || run.status === "completed"}
              onClick={() => setConfirm("SIM_REDUCE_SOURCE")}
            >
              <span className="option-index">{t("A")}</span>
              <div>
                <strong>{t("Reduce source")}</strong>
                <small>{t("One-time reduction to 45%")}</small>
              </div>
              <Plus size={18} />
            </button>
            <button
              className="intervention-option"
              disabled={busy || run.status === "completed"}
              onClick={() => setConfirm("SIM_STOP_SOURCE")}
            >
              <span className="option-index">{t("B")}</span>
              <div>
                <strong>{t("Stop source")}</strong>
                <small>{t("Residual channels decay over time")}</small>
              </div>
              <Plus size={18} />
            </button>
            <div className="fault-section">
              <label>{t("CO sensor fault")}<select value={faultKind} onChange={e => setFaultKind(e.target.value)}>
                  <option value="drop">{t("Missing channel")}</option>
                  <option value="freeze">{t("Frozen reading / failed heartbeat")}</option>
                  <option value="replay">{t("Replayed reading")}</option>
                  <option value="skew">{t("Clock skew outside tolerance")}</option>
                  <option value="saturation">{t("Sensor saturation")}</option>
                </select>
              </label>
              <Button
                disabled={
                  busy || run.status === "completed" || run.fault_at !== null || !!run.faults?.some(f => f.channel === "co_proxy")
                }
                onClick={() => setConfirm("fault")}
              >
                <WarningCircle size={18} />{t("Inject sensor fault")}</Button>
              <small>{t("Missing data cannot clear a danger latch.")}</small>
            </div>
          </section>
          <section className="panel ledger-panel">
            <div className="panel-heading">
              <h2>{t("Decision ledger")}</h2>
              <span className="count">{t(events.data?.items.length || 0)}</span>
            </div>
            {events.isError ? (
              <ErrorBox error={events.error} />
            ) : (
              <ol className="ledger">
                {events.data?.items
                  .filter((e) => e.type !== "measurements_committed")
                  .slice()
                  .reverse()
                  .slice(0, 10)
                  .map((event) => (
                    <li key={event.seq}>
                      <span className="mono">
                        {t(String(Math.max(0, event.t)).padStart(3, "0"))}{t("s")}</span>
                      <div>
                        {event.decision ? (
                          <button onClick={() => setInspect(event.decision!)}>
                            {t(event.decision.combustion_status)}
                            <ArrowUpRight size={14} />
                          </button>
                        ) : (
                          <strong>{t(event.type.replaceAll("_", " "))}</strong>
                        )}
                        <small>
                          {t(event.action?.replaceAll("_", " ") ||
                            event.decision?.reason_codes[0]
                              .replaceAll("_", " ")
                              .toLowerCase() ||
                            "Recorded in run history")}
                        </small>
                      </div>
                    </li>
                  ))}
              </ol>
            )}
            <a
              className="text-link"
              href={"/api/v1/runs/" + id + "/report?format=html&language=" + getLanguage()}
              target="_blank"
              rel="noreferrer"
            >{t("Open printable report ")}<ArrowUpRight size={16} />
            </a>
          </section>
        </aside>
      </div>
      <div role="status" className="sr-only">{t("Combustion status: ")}{t(decision.combustion_status)}
      </div>
      <Modal
        open={!!confirm}
        title={
          t(confirm === "fault"
            ? "Confirm synthetic sensor fault"
            : "Confirm synthetic intervention")
        }
        onClose={() => setConfirm(null)}
      >
        <p>
          {t(confirm === "fault"
            ? msg("Apply {0} to the CO channel from the next virtual sample. Invalid observations block verification.", [faultKind])
            : confirm === "SIM_STOP_SOURCE"
              ? "Set the synthetic source to zero from the next virtual sample. Residual heat and gases remain."
              : "Reduce the synthetic source once to 45% from the next virtual sample. A nonzero source remains.")}
        </p>
        <p className="muted">{t("This affects only this run. No physical equipment is connected.")}</p>
        {error != null && <ErrorBox error={error} />}
        <Button
          className="primary full-width"
          disabled={busy}
          onClick={() =>
            mutate(
              confirm === "fault" ? "/faults" : "/interventions",
              confirm === "fault"
                ? { channel: "co_proxy", fault: faultKind }
                : { option_id: confirm },
            )
          }
        >
          {t(busy ? "Applying…" : "Apply to next sample")}
        </Button>
      </Modal>
      <Modal
        open={branch}
        title={t("Create an independent branch")}
        onClose={() => setBranch(false)}
      >
        <form onSubmit={doBranch}>
          <label>{t("Branch name")}<input
              required
              value={branchName}
              onChange={(e) => setBranchName(e.target.value)}
              maxLength={120}
            />
          </label>
          <label>{t("Branch at virtual second")}<input
              type="number"
              required
              min={0}
              max={run.t}
              value={branchTime}
              onChange={(e) => setBranchTime(Number(e.target.value))}
            />
          </label>
          <p className="muted">{t("Rebuild from the same seed and past events. Future interventions will belong only to the new branch.")}</p>
          {error != null && <ErrorBox error={error} />}
          <Button type="submit" className="primary" disabled={busy}>{t("Create branch")}</Button>
        </form>
      </Modal>
      <Modal
        open={!!inspect}
        title={t("Decision trace")}
        onClose={() => setInspect(null)}
      >
        {inspect && (
          <>
            <Status tone={inspect.combustion_status.toLowerCase()}>
              {t(inspect.label)}
            </Status>
            <dl className="definition-grid">
              <div>
                <dt>{t("Observation window")}</dt>
                <dd>
                  {t(inspect.window_start)}–{t(inspect.window_end)}{t("s")}</dd>
              </div>
              <div>
                <dt>{t("Profile")}</dt>
                <dd>{t(inspect.profile)}</dd>
              </div>
              <div>
                <dt>{t("Required data")}</dt>
                <dd>{t(inspect.required_quality)}</dd>
              </div>
              <div>
                <dt>{t("Hold elapsed")}</dt>
                <dd>{t(inspect.hold_elapsed_s)}{t("s")}</dd>
              </div>
            </dl>
            <h3>{t("Reason codes")}</h3>
            {inspect.reason_codes.map((r) => (
              <p className="code-block" key={r}>
                {t(r)}
              </p>
            ))}
            <h3>{t("Observed features")}</h3>
            {Object.entries(inspect.features).map(([k, v]) => (
              <p key={k} className="feature-row">
                <span>{t(k)}{t(" slope")}</span>
                <strong>{t(v.toFixed(5))}{t(" sim_unit/s")}</strong>
              </p>
            ))}
            <p className="muted">{t("Engine 0.1.0 · Source: synthetic observations only. No language model calculated this state.")}</p>
          </>
        )}
      </Modal>
    </>
  );
}
function Archive() {
  const query = useQuery({
    queryKey: ["runs"],
    queryFn: () => api<{ items: Run[] }>("/runs"),
    refetchInterval: 5000,
  });
  return (
    <>
      <PageTitle
        kicker={t("Workbench / Run archive")}
        title={t("Every decision leaves a trace")}
        description={t("Saved runs, independent branches, and reproducible observation histories.")}
        action={
          <Link className="button primary" to="/scenario">
            <Plus size={18} />{t("New scenario")}</Link>
        }
      />
      {query.isPending ? (
        <Loading>{t("Loading saved run history…")}</Loading>
      ) : query.isError ? (
        <ErrorBox error={query.error} retry={() => query.refetch()} />
      ) : !query.data.items.length ? (
        <Empty title={t("No runs yet")}>
          <p>{t("Approve an observation plan to create your first saved run.")}</p>
          <Link className="button primary" to="/scenario">{t("Create scenario")}</Link>
        </Empty>
      ) : (
        <div className="archive-list">
          {query.data.items.map((run) => (
            <article className="archive-row" key={run.id}>
              <div className="archive-mark">
                {run.parent_id ? (
                  <GitBranch size={24} />
                ) : (
                  <ChartLine size={24} />
                )}
              </div>
              <div>
                <Link to={"/lab/" + run.id} className="archive-title">
                  {run.name}
                </Link>
                <p>
                  {t(run.parent_id ? "Branch · " : "Original run · ")}{t("Seed")}{t(" ")}
                  {t(run.seed)} · {t(run.t)}{t("s observed")}</p>
                <small className="mono">{t(run.id)}</small>
              </div>
              <Status
                tone={(
                  run.decision?.combustion_status || "Uncertain"
                ).toLowerCase()}
              >
                {t(run.decision?.combustion_status || "Uncertain")}
              </Status>
              <span className="muted">{t(run.status)}</span>
              <Link className="button" to={"/lab/" + run.id}>{t("Open lab ")}<ArrowRight size={16} />
              </Link>
            </article>
          ))}
        </div>
      )}
    </>
  );
}
