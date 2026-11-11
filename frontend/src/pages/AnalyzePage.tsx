import React, { useState } from 'react';
import { UploadCloud, FileText, Play, CheckCircle2, AlertCircle } from 'lucide-react';
import { api, RunSummary } from '../api/client';

interface AnalyzePageProps {
  onRunSelected: (runId: string) => void;
}

export const AnalyzePage: React.FC<AnalyzePageProps> = ({ onRunSelected }) => {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeUploadId, setActiveUploadId] = useState<string | null>(null);
  const [activeUploadStatus, setActiveUploadStatus] = useState<string>('idle');

  const handleFileUpload = async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('Please upload a valid PDF policy document.');
      return;
    }
    setError(null);
    setIsUploading(true);
    setActiveUploadStatus('Uploading PDF document...');

    try {
      const res = await api.uploadPolicy(file);
      setActiveUploadId(res.id);
      setActiveUploadStatus('Queued for AI extraction...');

      // Poll until analysis completes or fails
      const pollInterval = setInterval(async () => {
        try {
          const detail = await api.getRun(res.id);
          if (detail.status === 'extracting') {
            setActiveUploadStatus('Extracting policy facts via Gemini...');
          } else if (detail.status === 'resolving') {
            setActiveUploadStatus('Matching insurer rater grid & resolving commissions...');
          } else if (detail.status === 'saved' || detail.status === 'unsupported' || detail.status === 'ambiguous') {
            clearInterval(pollInterval);
            setIsUploading(false);
            onRunSelected(res.id);
          } else if (detail.status === 'failed') {
            clearInterval(pollInterval);
            setIsUploading(false);
            setError(detail.errorMessage || 'Analysis failed.');
          }
        } catch (err: any) {
          clearInterval(pollInterval);
          setIsUploading(false);
          setError(err.message || 'Error polling run status.');
        }
      }, 1500);
    } catch (err: any) {
      setIsUploading(false);
      setError(err.message || 'Upload failed.');
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="page-container animate-fade-in">
      <div className="hero-section">
        <h1 className="hero-title">Motor Policy Commission Resolver</h1>
        <p className="hero-subtitle">
          Upload any Indian private car policy schedule (Comprehensive or Standalone TP). The engine extracts policy parameters, executes deterministic grid resolution, and presents full cell/page citations.
        </p>
      </div>

      <div
        className="upload-dropzone"
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        onClick={() => document.getElementById('policy-file-input')?.click()}
      >
        <input
          id="policy-file-input"
          type="file"
          accept=".pdf,application/pdf"
          style={{ display: 'none' }}
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              handleFileUpload(e.target.files[0]);
            }
          }}
        />

        <div className="upload-icon-wrapper">
          <UploadCloud size={40} className="text-primary" />
        </div>
        <h3 className="upload-heading">Click to upload or drag & drop policy PDF</h3>
        <p className="upload-subtext">Supports Comprehensive, Stand-Alone OD, and Stand-Alone TP motor policy schedules (up to 50 MB)</p>

        {isUploading && (
          <div className="upload-progress-box">
            <div className="spinner-border animate-spin" />
            <span className="font-mono text-sm">{activeUploadStatus}</span>
          </div>
        )}

        {error && (
          <div className="error-alert">
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}
      </div>

      <div className="samples-grid-section">
        <h2 className="section-title">Pre-Verified Benchmark Policies</h2>
        <p className="section-subtitle">Inspect the 4 challenge test policies pre-resolved through the deterministic rater engine:</p>

        <div className="benchmark-cards-grid">
          <div className="benchmark-card" onClick={() => onRunSelected('hdfc-ergo')}>
            <div className="benchmark-card-header">
              <span className="insurer-tag tag-hdfc">HDFC ERGO</span>
              <span className="status-pill status-resolved">OD: 15.0%</span>
            </div>
            <h4 className="benchmark-card-title">Mahindra Bolero Neo (Comprehensive)</h4>
            <p className="benchmark-card-meta">Zone 2 (Haryana) • Net OD ₹8,053 (&lt;10k slab) • TP not published</p>
          </div>

          <div className="benchmark-card" onClick={() => onRunSelected('reliance')}>
            <div className="benchmark-card-header">
              <span className="insurer-tag tag-reliance">Reliance General</span>
              <span className="status-pill status-resolved">OD: 17.5%</span>
            </div>
            <h4 className="benchmark-card-title">Renault Kwid 1.0 (Comprehensive)</h4>
            <p className="benchmark-card-meta">North Zone • Base 22.5% - 5.0% (&lt;1000cc footnote H3) • TP not published (H2)</p>
          </div>

          <div className="benchmark-card" onClick={() => onRunSelected('godigit')}>
            <div className="benchmark-card-header">
              <span className="insurer-tag tag-godigit">Go Digit</span>
              <span className="status-pill status-resolved">TP: 29.5%</span>
            </div>
            <h4 className="benchmark-card-title">Hyundai Santro (Stand-Alone TP)</h4>
            <p className="benchmark-card-meta">Cluster UP_Bad (Kanpur Nagar) • Age 7 yrs • OD Not Applicable</p>
          </div>

          <div className="benchmark-card" onClick={() => onRunSelected('tata-aig')}>
            <div className="benchmark-card-header">
              <span className="insurer-tag tag-tata">Tata AIG</span>
              <span className="status-pill status-unsupported">Unsupported</span>
            </div>
            <h4 className="benchmark-card-title">Maruti Zen Estilo CNG (Stand-Alone TP)</h4>
            <p className="benchmark-card-meta">GWP incremental COA doctrine (Pvtcar!F3) • Uncertified base 38.0% logged</p>
          </div>
        </div>
      </div>
    </div>
  );
};
