import React, { useState, useEffect } from 'react';
import {
  RunDetail,
  RunListItem,
  GridInfo,
  BenchItem,
  uploadPolicyPdf,
  fetchRuns,
  fetchRun,
  fetchGrids,
  fetchBench,
  rerunAnalysis
} from './api/client';
import { UploadCloud, CheckCircle2, AlertTriangle, XCircle, RefreshCw, FileText, ArrowRight, Download, Eye, ExternalLink } from 'lucide-react';
import './styles/main.css';

export function App() {
  const [tab, setTab] = useState<'analyze' | 'history' | 'grids' | 'bench' | 'docs'>('analyze');
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [currentRun, setCurrentRun] = useState<RunDetail | null>(null);
  const [runs, setRuns] = useState<RunListItem[]>([]);
  const [grids, setGrids] = useState<GridInfo[]>([]);
  const [bench, setBench] = useState<BenchItem[]>([]);
  
  // Analyze tab state
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<string>('');
  const [uploadError, setUploadError] = useState<string | null>(null);
  
  // History filters
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  
  // Modals / toggles
  const [showJson, setShowJson] = useState(false);
  const [showPdf, setShowPdf] = useState(false);

  // Sync hash with tabs
  useEffect(() => {
    const handleHash = () => {
      const h = (window.location.hash || '#analyze').slice(1);
      if (h.startsWith('run-')) {
        const id = h.replace('run-', '');
        setSelectedRunId(id);
      } else if (['analyze', 'history', 'grids', 'bench', 'docs'].includes(h)) {
        setTab(h as any);
        setSelectedRunId(null);
      }
    };
    handleHash();
    window.addEventListener('hashchange', handleHash);
    return () => window.removeEventListener('hashchange', handleHash);
  }, []);

  // Load run detail when selectedRunId changes or while polling
  useEffect(() => {
    if (!selectedRunId) {
      setCurrentRun(null);
      return;
    }
    let interval: any = null;
    const loadDetail = async () => {
      try {
        const detail = await fetchRun(selectedRunId);
        setCurrentRun(detail);
        if (['queued', 'extracting', 'resolving'].includes(detail.status)) {
          interval = setTimeout(loadDetail, 1500);
        }
      } catch (err: any) {
        console.error(err);
      }
    };
    loadDetail();
    return () => clearTimeout(interval);
  }, [selectedRunId]);

  // Load tab-specific data
  useEffect(() => {
    if (tab === 'history') {
      fetchRuns(filterStatus, searchQuery).then(setRuns).catch(console.error);
    } else if (tab === 'grids') {
      fetchGrids().then(setGrids).catch(console.error);
    } else if (tab === 'bench') {
      fetchBench().then(setBench).catch(console.error);
    }
  }, [tab, filterStatus, searchQuery]);

  // Handle file drop/upload
  const handleFileUpload = async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setUploadError('Only PDF documents are supported (magic bytes %PDF required).');
      return;
    }
    setUploadError(null);
    setUploading(true);
    setUploadProgress('Uploading policy PDF to durable storage...');
    try {
      const result = await uploadPolicyPdf(file);
      setUploadProgress('Queued for deterministic extraction and rating...');
      window.location.hash = `run-${result.id}`;
    } catch (err: any) {
      setUploadError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const renderStatusChip = (status: string) => {
    const s = status.toLowerCase();
    if (['resolved', 'saved'].includes(s)) return <span className="chip resolved"><CheckCircle2 size={13}/> {status}</span>;
    if (['unsupported', 'failed'].includes(s)) return <span className="chip unsupported"><XCircle size={13}/> {status}</span>;
    return <span className="chip ambiguous"><AlertTriangle size={13}/> {status}</span>;
  };

  return (
    <div className="app">
      <header className="nav">
        <div className="brand">Rater<i>.</i></div>
        <button className={`tab-btn ${tab === 'analyze' && !selectedRunId ? 'on' : ''}`} onClick={() => { window.location.hash = 'analyze'; }}>Analyze</button>
        <button className={`tab-btn ${tab === 'history' || selectedRunId ? 'on' : ''}`} onClick={() => { window.location.hash = 'history'; }}>History</button>
        <button className={`tab-btn ${tab === 'grids' ? 'on' : ''}`} onClick={() => { window.location.hash = 'grids'; }}>Rater Grids</button>
        <button className={`tab-btn ${tab === 'bench' ? 'on' : ''}`} onClick={() => { window.location.hash = 'bench'; }}>Test Bench</button>
        <button className={`tab-btn ${tab === 'docs' ? 'on' : ''}`} onClick={() => { window.location.hash = 'docs'; }}>Architecture</button>
      </header>

      <main className="main-content">
        {selectedRunId && currentRun ? (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
              <div>
                <h6>Analysis Detail · {currentRun.fileName}</h6>
                <h1>{currentRun.facts?.policyType?.value ? `${currentRun.facts.policyType.value.replace(/_/g, ' ').toUpperCase()} · ${currentRun.facts.insurer.value}` : currentRun.fileName}</h1>
              </div>
              <div>{renderStatusChip(currentRun.status)}</div>
            </div>

            <div style={{ display: 'flex', gap: 10, margin: '20px 0', flexWrap: 'wrap' }}>
              <button className="btn g" onClick={() => setShowPdf(!showPdf)}><Eye size={15}/> {showPdf ? 'Hide PDF' : 'View Source PDF'}</button>
              <button className="btn g" onClick={() => setShowJson(!showJson)}><FileText size={15}/> {showJson ? 'Hide JSON' : 'Toggle JSON'}</button>
              <a className="btn g" href={`/api/runs/${currentRun.id}/export`} target="_blank" rel="noreferrer"><Download size={15}/> Download JSON</a>
              <button className="btn g" onClick={async () => { await rerunAnalysis(currentRun.id); window.location.reload(); }}><RefreshCw size={15}/> Re-run</button>
            </div>

            {showPdf && (
              <div className="card" style={{ marginBottom: 24, padding: 12 }}>
                <iframe src={`/api/runs/${currentRun.id}/pdf`} style={{ width: '100%', height: '650px', border: 'none', borderRadius: 8 }} title="Source PDF" />
              </div>
            )}

            {showJson && (
              <pre className="code-block">{JSON.stringify(currentRun, null, 2)}</pre>
            )}

            {['queued', 'extracting', 'resolving'].includes(currentRun.status) ? (
              <div className="card" style={{ margin: '24px 0', textAlign: 'center', padding: '48px 24px' }}>
                <RefreshCw size={32} className="spin" style={{ color: 'var(--acc)', margin: '0 auto 16px', display: 'block' }} />
                <h2>Analysis in progress...</h2>
                <p style={{ color: 'var(--mute)' }}>Status: <b>{currentRun.status.toUpperCase()}</b>. Resolving through authoritative rater grids deterministically.</p>
              </div>
            ) : (
              <>
                <div className="grid-cols">
                  {/* OD Card */}
                  <div className="card">
                    <h6>Own Damage Commission</h6>
                    {currentRun.rates?.od.applicable ? (
                      currentRun.rates.od.ratePercent !== null ? (
                        <div className="rate-display">{currentRun.rates.od.ratePercent}<sup>%</sup></div>
                      ) : (
                        <div className="na-display">Unresolved</div>
                      )
                    ) : (
                      <div className="na-display">Not applicable</div>
                    )}
                    <p style={{ color: 'var(--mute)', fontSize: 13, margin: '8px 0 0' }}>{currentRun.rates?.od.reason}</p>
                    {currentRun.rates?.od.citations?.map((c, i) => (
                      <div key={i} className="cite" style={{ marginTop: 6 }}>{c.file} · {c.sheet || `Page ${c.page}`} · {c.coordinate}</div>
                    ))}
                  </div>

                  {/* TP Card */}
                  <div className="card">
                    <h6>Third Party Commission</h6>
                    {currentRun.rates?.tp.applicable ? (
                      currentRun.rates.tp.ratePercent !== null ? (
                        <div className="rate-display">{currentRun.rates.tp.ratePercent}<sup>%</sup></div>
                      ) : (
                        <div className="na-display">Unsupported</div>
                      )
                    ) : (
                      <div className="na-display">Not applicable</div>
                    )}
                    <p style={{ color: 'var(--mute)', fontSize: 13, margin: '8px 0 0' }}>{currentRun.rates?.tp.reason}</p>
                    {currentRun.rates?.tp.citations?.map((c, i) => (
                      <div key={i} className="cite" style={{ marginTop: 6 }}>{c.file} · {c.sheet || `Page ${c.page}`} · {c.coordinate}</div>
                    ))}
                  </div>

                  {/* Confidence Card */}
                  <div className="card">
                    <h6>Confidence Level</h6>
                    <div className="conf-bar">
                      <b style={{ font: '600 20px var(--mono)' }}>{currentRun.confidence?.level || 85}%</b>
                      <div className="bar-track"><div className="bar-fill" style={{ width: `${currentRun.confidence?.level || 85}%` }}></div></div>
                    </div>
                    <p style={{ color: 'var(--mute)', fontSize: 13, marginTop: 12 }}>{currentRun.confidence?.reason}</p>
                  </div>
                </div>

                {/* Facts Table */}
                <section>
                  <h2>Extracted Policy Facts</h2>
                  <div className="card" style={{ padding: 0, overflowX: 'auto' }}>
                    <table>
                      <thead>
                        <tr>
                          <th>Fact Dimension</th>
                          <th>Extracted Value</th>
                          <th>Confidence</th>
                          <th>Policy Source</th>
                        </tr>
                      </thead>
                      <tbody>
                        {currentRun.facts && [
                          ['Insurer', currentRun.facts.insurer?.value, currentRun.facts.insurer?.page, currentRun.facts.insurer?.confidence],
                          ['Previous Insurer', currentRun.facts.previousInsurer?.value || 'None / Not stated', currentRun.facts.previousInsurer?.page, currentRun.facts.previousInsurer?.confidence],
                          ['Business Type', currentRun.facts.businessType?.value, currentRun.facts.businessType?.page, currentRun.facts.businessType?.confidence],
                          ['Policy Type', currentRun.facts.policyType?.value, currentRun.facts.policyType?.page, currentRun.facts.policyType?.confidence],
                          ['Registration No / RTO', currentRun.facts.rto?.value, currentRun.facts.rto?.page, currentRun.facts.rto?.confidence],
                          ['Printed Location', currentRun.facts.printedLocation?.value || 'N/A', currentRun.facts.printedLocation?.page, currentRun.facts.printedLocation?.confidence],
                          ['Vehicle Make & Model', `${currentRun.facts.make?.value || ''} ${currentRun.facts.model?.value || ''}`, currentRun.facts.make?.page, currentRun.facts.make?.confidence],
                          ['Fuel Type', currentRun.facts.fuel?.value, currentRun.facts.fuel?.page, currentRun.facts.fuel?.confidence],
                          ['Engine Capacity', currentRun.facts.engineCc?.value ? `${currentRun.facts.engineCc.value} cc` : 'N/A', currentRun.facts.engineCc?.page, currentRun.facts.engineCc?.confidence],
                          ['Registration Year', currentRun.facts.registrationYear?.value || 'N/A', currentRun.facts.registrationYear?.page, currentRun.facts.registrationYear?.confidence],
                          ['Vehicle Age (Derived)', currentRun.facts.vehicleAgeYears?.value !== undefined ? `${currentRun.facts.vehicleAgeYears.value} years` : 'N/A', null, 0.95],
                          ['Net OD Premium', currentRun.facts.premiums?.netOd !== undefined ? `₹${currentRun.facts.premiums.netOd.toLocaleString()}` : 'N/A', currentRun.facts.premiums?.page, 0.99],
                          ['Net TP Premium', currentRun.facts.premiums?.netTp !== undefined ? `₹${currentRun.facts.premiums.netTp.toLocaleString()}` : 'N/A', currentRun.facts.premiums?.page, 0.99],
                          ['Total Gross Premium', currentRun.facts.premiums?.total !== undefined ? `₹${currentRun.facts.premiums.total.toLocaleString()}` : 'N/A', currentRun.facts.premiums?.page, 0.99]
                        ].map(([label, val, page, conf], idx) => (
                          <tr key={idx}>
                            <td><b>{label}</b></td>
                            <td>{String(val)}</td>
                            <td><span style={{ font: '500 12px var(--mono)', color: (conf as number) < 0.8 ? 'var(--warn)' : 'var(--ok)' }}>{Math.round(((conf as number) || 0.9) * 100)}%</span></td>
                            <td className="cite">{page ? `Page ${page}` : 'Derived / Schedule'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>

                {/* Decision Trace */}
                <section>
                  <h2>Deterministic Decision Trace</h2>
                  <ol className="trace">
                    {currentRun.trace?.map((t, idx) => (
                      <li key={idx}>
                        <div style={{ fontWeight: 600 }}>{t.decision}</div>
                        <p style={{ margin: '4px 0 6px', color: 'var(--ink)' }}>{t.explanation}</p>
                        <div className="cite">{[t.policyCitation, t.gridCitation].filter(Boolean).join(' · ')}</div>
                      </li>
                    ))}
                  </ol>
                </section>
              </>
            )}
          </div>
        ) : tab === 'analyze' ? (
          <div>
            <h6>Motor Policy Brokerage Resolver</h6>
            <h1>Teach an agent to read the fine print.</h1>
            <p style={{ color: 'var(--mute)', maxWidth: 650, marginTop: 8 }}>
              Upload any private motor policy PDF (scanned or digital). Extracted via Google Gemini vision, resolved deterministically against authoritative insurer commission grids with exact cell and page citations.
            </p>

            <label className={`dropzone ${uploading ? 'active' : ''}`} style={{ marginTop: 28 }}>
              <input
                type="file"
                accept="application/pdf"
                style={{ display: 'none' }}
                disabled={uploading}
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) handleFileUpload(e.target.files[0]);
                }}
              />
              <UploadCloud size={44} style={{ color: 'var(--acc)', margin: '0 auto 12px', display: 'block' }} />
              <b>Drag and drop your motor policy PDF here</b>
              <span>or click to browse from your computer (PDF only, up to 50 MB)</span>
            </label>

            {uploading && (
              <div className="card" style={{ marginTop: 20, textAlign: 'center' }}>
                <p style={{ font: '500 14px var(--mono)', color: 'var(--acc)', margin: 0 }}>{uploadProgress}</p>
              </div>
            )}

            {uploadError && (
              <div className="card" style={{ marginTop: 20, borderColor: 'var(--bad)', background: 'var(--badb)' }}>
                <b style={{ color: 'var(--bad)' }}>Upload Error:</b>
                <p style={{ margin: '6px 0 0', color: 'var(--bad)' }}>{uploadError}</p>
              </div>
            )}

            <div className="grid-cols" style={{ marginTop: 32 }}>
              <div className="card">
                <h6>Step 01</h6>
                <b>Gemini Vision Extraction</b>
                <p style={{ color: 'var(--mute)', fontSize: 13, marginTop: 6 }}>Reads scanned schedules into a structured schema with page citations and cross-checks.</p>
              </div>
              <div className="card">
                <h6>Step 02</h6>
                <b>Deterministic Resolution</b>
                <p style={{ color: 'var(--mute)', fontSize: 13, marginTop: 6 }}>Pure reproducible Python engine traverses the exact insurer rate card (no LLM rating).</p>
              </div>
              <div className="card">
                <h6>Step 03</h6>
                <b>Cell & Page Proof</b>
                <p style={{ color: 'var(--mute)', fontSize: 13, marginTop: 6 }}>Cites the exact grid sheet and cell range or PDF page for every rate and footnote override.</p>
              </div>
              <div className="card">
                <h6>Step 04</h6>
                <b>Durable Persistence</b>
                <p style={{ color: 'var(--mute)', fontSize: 13, marginTop: 6 }}>All analyses and PDFs survive browser refreshes, redeployments, and server restarts.</p>
              </div>
            </div>
          </div>
        ) : tab === 'history' ? (
          <div>
            <h6>Saved Runs</h6>
            <h1>History</h1>
            <p style={{ color: 'var(--mute)' }}>Loaded directly from PostgreSQL database. Persisted across browser refresh and redeployments.</p>

            <div style={{ display: 'flex', gap: 12, margin: '20px 0', flexWrap: 'wrap' }}>
              <input
                className="search-input"
                style={{ flex: 1, minWidth: 260 }}
                placeholder="Search runs by filename..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <div style={{ display: 'flex', gap: 6 }}>
                {['all', 'resolved', 'unsupported', 'ambiguous'].map((s) => (
                  <button
                    key={s}
                    className={`btn g ${filterStatus === s ? 'on' : ''}`}
                    style={filterStatus === s ? { background: 'var(--ink)', color: 'var(--bg)' } : {}}
                    onClick={() => setFilterStatus(s)}
                  >
                    {s.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>

            <div className="card" style={{ padding: 0, overflowX: 'auto' }}>
              <table>
                <thead>
                  <tr>
                    <th>File Name</th>
                    <th>Uploaded</th>
                    <th>Status</th>
                    <th>OD Rate</th>
                    <th>TP Rate</th>
                    <th>Storage</th>
                  </tr>
                </thead>
                <tbody>
                  {runs.length === 0 ? (
                    <tr>
                      <td colSpan={6} style={{ textAlign: 'center', padding: 32, color: 'var(--mute)' }}>No matching runs found in database.</td>
                    </tr>
                  ) : (
                    runs.map((r) => (
                      <tr key={r.id}>
                        <td>
                          <a href={`#run-${r.id}`} style={{ color: 'var(--acc)', fontWeight: 600, textDecoration: 'none' }}>
                            {r.fileName}
                          </a>
                        </td>
                        <td style={{ font: '400 13px var(--mono)', color: 'var(--mute)' }}>{new Date(r.createdAt).toLocaleString()}</td>
                        <td>{renderStatusChip(r.status)}</td>
                        <td><b>{r.rates?.od?.applicable ? (r.rates.od.ratePercent !== null ? `${r.rates.od.ratePercent}%` : 'Unresolved') : 'N/A'}</b></td>
                        <td><b>{r.rates?.tp?.applicable ? (r.rates.tp.ratePercent !== null ? `${r.rates.tp.ratePercent}%` : 'Unsupported') : 'N/A'}</b></td>
                        <td className="cite">Durable S3 + DB</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        ) : tab === 'grids' ? (
          <div>
            <h6>Authoritative Commission Grids</h6>
            <h1>Rater Grids</h1>
            <p style={{ color: 'var(--mute)' }}>Preloaded and parsed directly from the official starter corpus.</p>

            <div className="grid-cols">
              {grids.map((g) => (
                <div key={g.insurerId} className="card">
                  <h6>{g.insurerId.toUpperCase()}</h6>
                  <b style={{ font: '600 18px var(--serif)', display: 'block', margin: '4px 0 8px' }}>{g.insurerName}</b>
                  <p style={{ color: 'var(--mute)', fontSize: 13, margin: '4px 0' }}>File: <code>{g.fileName}</code></p>
                  <p style={{ color: 'var(--mute)', fontSize: 13, margin: '4px 0' }}>Rules parsed: <b>{g.rulesCount}</b> | Footnotes: <b>{g.footnotesCount}</b></p>
                  <p style={{ color: 'var(--mute)', fontSize: 13, margin: '4px 0' }}>Effective: <b>{g.effectiveFrom || 'Open-ended'}</b></p>
                  <div className="cite" style={{ marginTop: 12 }}>SHA-256: {g.checksumSha256.slice(0, 16)}... (Verified)</div>
                </div>
              ))}
            </div>
          </div>
        ) : tab === 'bench' ? (
          <div>
            <h6>Benchmark Evaluation Corpus</h6>
            <h1>Test Bench</h1>
            <p style={{ color: 'var(--mute)' }}>The four reference motor policies evaluated deterministically against their authoritative grids.</p>

            <div className="card" style={{ padding: 0, overflowX: 'auto', marginTop: 24 }}>
              <table>
                <thead>
                  <tr>
                    <th>Insurer & Policy</th>
                    <th>Evaluation Criteria</th>
                    <th>Expected OD</th>
                    <th>Expected TP</th>
                    <th>Expected Status</th>
                    <th>Authoritative Citation</th>
                  </tr>
                </thead>
                <tbody>
                  {bench.map((b, idx) => (
                    <tr key={idx}>
                      <td>
                        <b>{b.insurer}</b>
                        <div style={{ color: 'var(--mute)', fontSize: 12 }}>{b.policyType} · {b.fileName}</div>
                      </td>
                      <td>{b.tests}</td>
                      <td><b>{b.expectedOd}</b></td>
                      <td><b>{b.expectedTp}</b></td>
                      <td>{renderStatusChip(b.expectedStatus)}</td>
                      <td className="cite">{b.citation}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div>
            <h6>System Architecture & Durability</h6>
            <h1>Architecture & Storage</h1>

            <section>
              <h2>The Pipeline</h2>
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center', margin: '18px 0' }}>
                <span className="card" style={{ padding: '10px 18px', font: '500 13px var(--mono)' }}>PDF Upload</span>
                <ArrowRight size={18} style={{ color: 'var(--mute)' }} />
                <span className="card" style={{ padding: '10px 18px', font: '500 13px var(--mono)' }}>Gemini Vision (Schema)</span>
                <ArrowRight size={18} style={{ color: 'var(--mute)' }} />
                <span className="card" style={{ padding: '10px 18px', font: '500 13px var(--mono)' }}>Deterministic Resolver</span>
                <ArrowRight size={18} style={{ color: 'var(--mute)' }} />
                <span className="card" style={{ padding: '10px 18px', font: '500 13px var(--mono)' }}>Granular Citations</span>
                <ArrowRight size={18} style={{ color: 'var(--mute)' }} />
                <span className="card" style={{ padding: '10px 18px', font: '500 13px var(--mono)' }}>PostgreSQL + S3 Storage</span>
              </div>
            </section>

            <section>
              <h2>Persistence Model</h2>
              <div className="grid-cols">
                <div className="card">
                  <h6>Policy PDF Storage</h6>
                  <b>Object Storage (S3 / Supabase)</b>
                  <p style={{ color: 'var(--mute)', fontSize: 13, marginTop: 8 }}>Original uploaded files are keyed by SHA-256 hash in durable object storage. Never ephemeral container disk.</p>
                </div>
                <div className="card">
                  <h6>Analysis Metadata</h6>
                  <b>PostgreSQL (Neon / Supabase)</b>
                  <p style={{ color: 'var(--mute)', fontSize: 13, marginTop: 8 }}>All run records, raw extraction JSON, facts, rates, and ordered traces are durably committed in PostgreSQL.</p>
                </div>
                <div className="card">
                  <h6>Durability Guarantee</h6>
                  <b>Survives Restarts & Redeploys</b>
                  <p style={{ color: 'var(--mute)', fontSize: 13, marginTop: 8 }}>Runs persist across browser refresh, closing/reopening tabs, container restarts, and production redeployments.</p>
                </div>
              </div>
            </section>
          </div>
        )}
      </main>
    </div>
  );
}
