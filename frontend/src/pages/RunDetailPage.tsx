import React, { useState } from 'react';
import { 
  ArrowLeft, Download, RotateCcw, CheckCircle2, 
  AlertTriangle, XCircle 
} from 'lucide-react';
import { RunDetail, api } from '../api/client';

interface RunDetailPageProps {
  run: RunDetail;
  onBack: () => void;
  onRerun: () => void;
}

export const RunDetailPage: React.FC<RunDetailPageProps> = ({ run, onBack, onRerun }) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'pdf' | 'json'>('overview');
  const [isRerunning, setIsRerunning] = useState(false);

  const handleRerunClick = async () => {
    setIsRerunning(true);
    try {
      await api.rerunAnalysis(run.id);
      onRerun();
    } catch (e) {
      console.error(e);
    } finally {
      setIsRerunning(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'resolved':
      case 'saved':
        return <span className="status-badge status-badge-resolved"><CheckCircle2 size={14} /> Resolved</span>;
      case 'unsupported':
        return <span className="status-badge status-badge-unsupported"><XCircle size={14} /> Unsupported</span>;
      case 'ambiguous':
        return <span className="status-badge status-badge-ambiguous"><AlertTriangle size={14} /> Ambiguous</span>;
      default:
        return <span className="status-badge status-badge-queued">{status}</span>;
    }
  };

  const odRate = run.rates?.od;
  const tpRate = run.rates?.tp;

  return (
    <div className="run-detail-container animate-fade-in">
      <div className="detail-top-nav">
        <button className="btn-back" onClick={onBack}>
          <ArrowLeft size={16} /> Back to Dashboard
        </button>

        <div className="detail-actions">
          <a 
            href={api.getExportUrl(run.id)} 
            download={`run_${run.id}.json`}
            className="btn btn-secondary"
          >
            <Download size={14} /> Export JSON
          </a>
          <button 
            className="btn btn-primary"
            onClick={handleRerunClick}
            disabled={isRerunning}
          >
            <RotateCcw size={14} className={isRerunning ? "animate-spin" : ""} /> Re-run
          </button>
        </div>
      </div>

      <div className="run-header-card">
        <div className="run-header-main">
          <div className="run-header-title-row">
            <h2 className="run-file-title">{run.fileName}</h2>
            {getStatusBadge(run.status)}
            {run.isDuplicate && <span className="duplicate-tag">Duplicate (Retrieved)</span>}
          </div>
          <div className="run-meta-row">
            <span className="meta-item"><strong>Run ID:</strong> {run.id.slice(0, 8)}...</span>
            <span className="meta-item"><strong>Date:</strong> {new Date(run.createdAt).toLocaleString()}</span>
            {run.modelId && <span className="meta-item"><strong>Model:</strong> {run.modelId}</span>}
            {run.resolverVersion && <span className="meta-item"><strong>Resolver:</strong> v{run.resolverVersion}</span>}
          </div>
        </div>

        <div className="detail-tabs-bar">
          <button 
            className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            Analysis Overview
          </button>
          <button 
            className={`tab-btn ${activeTab === 'pdf' ? 'active' : ''}`}
            onClick={() => setActiveTab('pdf')}
          >
            Source Policy PDF
          </button>
          <button 
            className={`tab-btn ${activeTab === 'json' ? 'active' : ''}`}
            onClick={() => setActiveTab('json')}
          >
            Raw Decision JSON
          </button>
        </div>
      </div>

      {activeTab === 'overview' && (
        <div className="detail-tab-content">
          {/* Rates Cards Grid */}
          <div className="rate-cards-grid">
            {/* Own Damage Card */}
            <div className={`rate-card ${odRate?.state === 'resolved' ? 'rate-card-success' : 'rate-card-neutral'}`}>
              <div className="rate-card-header">
                <span className="rate-card-label">Own Damage (OD) Commission</span>
                <span className={`rate-state-pill state-${odRate?.state || 'none'}`}>
                  {odRate?.state === 'not_applicable' ? 'Not Applicable' : odRate?.state || 'Unknown'}
                </span>
              </div>
              <div className="rate-card-body">
                {odRate?.ratePercent !== null && odRate?.ratePercent !== undefined ? (
                  <div className="rate-value-display">
                    <span className="rate-num">{odRate.ratePercent.toFixed(1)}%</span>
                  </div>
                ) : (
                  <div className="rate-value-empty">
                    <span>{odRate?.state === 'not_applicable' ? 'N/A' : 'Not Published / Unsupported'}</span>
                  </div>
                )}
                <p className="rate-reason-text">{odRate?.reason || 'No Own Damage coverage specified.'}</p>
                {odRate?.citations && odRate.citations.length > 0 && (
                  <div className="citation-pill-box">
                    <span className="citation-title">Citations:</span>
                    {odRate.citations.map((c, idx) => (
                      <span key={idx} className="citation-pill font-mono">
                        {c.sheet ? `${c.sheet}!` : ''}{c.coordinate || `p.${c.page}`}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Third Party Card */}
            <div className={`rate-card ${tpRate?.state === 'resolved' ? 'rate-card-success' : 'rate-card-neutral'}`}>
              <div className="rate-card-header">
                <span className="rate-card-label">Third Party (TP) Commission</span>
                <span className={`rate-state-pill state-${tpRate?.state || 'none'}`}>
                  {tpRate?.state === 'not_applicable' ? 'Not Applicable' : tpRate?.state === 'not_published' ? 'Not Published' : tpRate?.state || 'Unknown'}
                </span>
              </div>
              <div className="rate-card-body">
                {tpRate?.ratePercent !== null && tpRate?.ratePercent !== undefined ? (
                  <div className="rate-value-display">
                    <span className="rate-num">{tpRate.ratePercent.toFixed(1)}%</span>
                  </div>
                ) : (
                  <div className="rate-value-empty">
                    <span>{tpRate?.state === 'not_applicable' ? 'N/A' : tpRate?.state === 'not_published' ? 'Not Published' : 'Unsupported'}</span>
                  </div>
                )}
                <p className="rate-reason-text">{tpRate?.reason || 'No Third Party coverage specified.'}</p>
                {tpRate?.citations && tpRate.citations.length > 0 && (
                  <div className="citation-pill-box">
                    <span className="citation-title">Citations:</span>
                    {tpRate.citations.map((c, idx) => (
                      <span key={idx} className="citation-pill font-mono">
                        {c.sheet ? `${c.sheet}!` : ''}{c.coordinate || `p.${c.page}`}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Extracted Facts & Premiums */}
          <div className="facts-and-premiums-grid">
            <div className="facts-section-card">
              <h3 className="card-section-heading">Extracted Policy Facts</h3>
              <table className="facts-table">
                <tbody>
                  <tr>
                    <td className="fact-label">Insurer</td>
                    <td className="fact-val">
                      {run.facts?.insurer?.value || '—'}
                      {run.facts?.insurer?.page && <span className="page-badge">p.{run.facts.insurer.page}</span>}
                    </td>
                  </tr>
                  <tr>
                    <td className="fact-label">Previous Insurer</td>
                    <td className="fact-val">
                      {run.facts?.previousInsurer?.value || <span className="text-muted">Not stated</span>}
                      {run.facts?.previousInsurer?.page && <span className="page-badge">p.{run.facts.previousInsurer.page}</span>}
                      {run.facts?.previousInsurer?.lowConfidence && <span className="badge-uncertain">Uncertain</span>}
                    </td>
                  </tr>
                  <tr>
                    <td className="fact-label">Policy / Business Type</td>
                    <td className="fact-val">
                      <span className="badge-type">{run.facts?.policyType?.value || '—'}</span> / 
                      <span className="badge-type">{run.facts?.businessType?.value || '—'}</span>
                    </td>
                  </tr>
                  <tr>
                    <td className="fact-label">Vehicle Make & Model</td>
                    <td className="fact-val">
                      {run.facts?.make?.value} {run.facts?.model?.value}
                      {run.facts?.model?.page && <span className="page-badge">p.{run.facts.model.page}</span>}
                    </td>
                  </tr>
                  <tr>
                    <td className="fact-label">Fuel Type</td>
                    <td className="fact-val">
                      {run.facts?.fuel?.value || '—'}
                      {run.facts?.fuel?.lowConfidence && (
                        <span className="badge-uncertain" title={run.facts?.fuel?.uncertainty}>Inferred</span>
                      )}
                    </td>
                  </tr>
                  <tr>
                    <td className="fact-label">Engine CC</td>
                    <td className="fact-val">{run.facts?.engineCc?.value ? `${run.facts.engineCc.value} cc` : '—'}</td>
                  </tr>
                  <tr>
                    <td className="fact-label">Registration / Age</td>
                    <td className="fact-val">
                      {run.facts?.registrationYear?.value || '—'} 
                      {run.facts?.vehicleAgeYears?.value !== undefined && run.facts?.vehicleAgeYears?.value !== null 
                        ? ` (${run.facts.vehicleAgeYears.value} yrs)` 
                        : ''}
                      {run.facts?.vehicleAgeYears?.uncertainty && (
                        <span className="page-badge" title={run.facts.vehicleAgeYears.uncertainty}>
                          {run.facts.vehicleAgeYears.uncertainty}
                        </span>
                      )}
                    </td>
                  </tr>
                  <tr>
                    <td className="fact-label">RTO & Location</td>
                    <td className="fact-val">
                      <strong>{run.facts?.rto?.value || '—'}</strong> • {run.facts?.printedLocation?.value || '—'}
                    </td>
                  </tr>
                  <tr>
                    <td className="fact-label">Policy Start Date</td>
                    <td className="fact-val">{run.facts?.policyStartDate?.value || '—'}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="premiums-section-card">
              <h3 className="card-section-heading">Financial Premium Breakup</h3>
              {run.facts?.premiums ? (
                <table className="premiums-table">
                  <tbody>
                    <tr>
                      <td className="prem-label">Basic Own Damage (OD)</td>
                      <td className="prem-val font-mono">
                        {odRate?.applicable === false ? '—' : run.facts.premiums.basicOd != null ? `₹${run.facts.premiums.basicOd.toLocaleString('en-IN')}` : '—'}
                      </td>
                    </tr>
                    <tr>
                      <td className="prem-label">NCB Discount ({run.facts.premiums.ncbPercent ?? 0}%)</td>
                      <td className="prem-val font-mono text-success">
                        {odRate?.applicable === false ? '—' : run.facts.premiums.ncbDiscount ? `-₹${run.facts.premiums.ncbDiscount.toLocaleString('en-IN')}` : '—'}
                      </td>
                    </tr>
                    <tr className="prem-row-net">
                      <td className="prem-label">Net OD Premium</td>
                      <td className="prem-val font-mono font-bold">
                        {odRate?.applicable === false ? '—' : run.facts.premiums.netOd != null ? `₹${run.facts.premiums.netOd.toLocaleString('en-IN')}` : '—'}
                      </td>
                    </tr>
                    <tr>
                      <td className="prem-label">Basic Third Party (TP)</td>
                      <td className="prem-val font-mono">
                        {tpRate?.applicable === false ? '—' : run.facts.premiums.basicTp != null ? `₹${run.facts.premiums.basicTp.toLocaleString('en-IN')}` : '—'}
                      </td>
                    </tr>
                    <tr>
                      <td className="prem-label">Net TP Premium</td>
                      <td className="prem-val font-mono">
                        {tpRate?.applicable === false ? '—' : run.facts.premiums.netTp != null ? `₹${run.facts.premiums.netTp.toLocaleString('en-IN')}` : '—'}
                      </td>
                    </tr>
                    <tr>
                      <td className="prem-label">GST / Taxes</td>
                      <td className="prem-val font-mono">₹{run.facts.premiums.taxes?.toLocaleString('en-IN') ?? '—'}</td>
                    </tr>
                    <tr className="prem-row-total">
                      <td className="prem-label">Total Payable GWP</td>
                      <td className="prem-val font-mono font-bold">₹{run.facts.premiums.total?.toLocaleString('en-IN') ?? '—'}</td>
                    </tr>
                  </tbody>
                </table>
              ) : (
                <div className="empty-notice">No premium figures parsed.</div>
              )}
            </div>
          </div>

          {/* Decision Trace Timeline */}
          <div className="trace-section-card">
            <h3 className="card-section-heading">Deterministic Resolution Decision Trace</h3>
            <div className="trace-timeline">
              {run.trace && run.trace.map((step, idx) => (
                <div key={idx} className="trace-step-item">
                  <div className="trace-step-marker">{step.step || idx + 1}</div>
                  <div className="trace-step-content">
                    <div className="trace-step-header">
                      <span className="trace-step-name">Step {step.step || idx + 1}</span>
                    </div>
                    <p className="trace-decision-text">{step.decision}</p>
                    {step.gridCitation && (
                      <div className="trace-citation-tag font-mono">
                        Citation: {typeof step.gridCitation === 'object' ? `${step.gridCitation.file || ''} ${step.gridCitation.sheet ? `[${step.gridCitation.sheet}]` : ''} (${step.gridCitation.coordinate || `p.${step.gridCitation.page || ''}`})` : String(step.gridCitation)}
                      </div>
                    )}
                    {step.caveats && step.caveats.length > 0 && (
                      <div className="trace-caveats-box">
                        {step.caveats.map((cav, cidx) => (
                          <div key={cidx} className="caveat-line">• {cav}</div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'pdf' && (
        <div className="pdf-viewer-tab-content">
          <iframe 
            src={api.getPdfUrl(run.id)} 
            className="pdf-iframe-viewer" 
            title="Source Policy PDF"
          />
        </div>
      )}

      {activeTab === 'json' && (
        <div className="json-viewer-tab-content">
          <pre className="json-pre-block">
            {JSON.stringify(run, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};
