import React, { useState, useEffect } from 'react';
import { Search, Filter, RotateCw, ExternalLink, Calendar, FileText } from 'lucide-react';
import { api, RunSummary } from '../api/client';

interface HistoryPageProps {
  onSelectRun: (runId: string) => void;
}

export const HistoryPage: React.FC<HistoryPageProps> = ({ onSelectRun }) => {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);

  const fetchRuns = async () => {
    setLoading(true);
    try {
      const data = await api.listRuns({
        search: search || undefined,
        status: statusFilter !== 'all' ? statusFilter : undefined,
        page,
        limit: 20
      });
      setRuns(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, [search, statusFilter, page]);

  return (
    <div className="page-container animate-fade-in">
      <div className="page-header-row">
        <div>
          <h1 className="page-title">Analysis History</h1>
          <p className="page-subtitle">Durable audit trail of all motor policies processed by the resolver</p>
        </div>
        <button className="btn btn-secondary" onClick={fetchRuns}>
          <RotateCw size={14} className={loading ? "animate-spin" : ""} /> Refresh
        </button>
      </div>

      <div className="filter-toolbar">
        <div className="search-input-box">
          <Search size={16} className="search-icon" />
          <input
            type="text"
            placeholder="Search by policy filename..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
          />
        </div>

        <div className="filter-select-box">
          <Filter size={16} />
          <select 
            value={statusFilter} 
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
          >
            <option value="all">All Statuses</option>
            <option value="saved">Resolved / Saved</option>
            <option value="unsupported">Unsupported</option>
            <option value="ambiguous">Ambiguous</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="loading-state-box">
          <div className="spinner-border animate-spin" />
          <p>Loading runs from database...</p>
        </div>
      ) : runs.length === 0 ? (
        <div className="empty-state-box">
          <FileText size={48} className="text-muted" />
          <h3>No policy runs found</h3>
          <p>Try adjusting your search criteria or upload a new policy schedule to analyze.</p>
        </div>
      ) : (
        <div className="runs-table-wrapper">
          <table className="runs-table">
            <thead>
              <tr>
                <th>File Name</th>
                <th>Status</th>
                <th>OD Rate</th>
                <th>TP Rate</th>
                <th>Created At</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((r) => {
                const od = r.rates?.od;
                const tp = r.rates?.tp;
                return (
                  <tr key={r.id} onClick={() => onSelectRun(r.id)} className="clickable-row">
                    <td className="font-semibold">{r.fileName}</td>
                    <td>
                      <span className={`status-pill status-${r.status}`}>{r.status}</span>
                    </td>
                    <td className="font-mono">
                      {od?.ratePercent !== null && od?.ratePercent !== undefined ? `${od.ratePercent.toFixed(1)}%` : (od?.state === 'not_applicable' ? 'N/A' : '—')}
                    </td>
                    <td className="font-mono">
                      {tp?.ratePercent !== null && tp?.ratePercent !== undefined ? `${tp.ratePercent.toFixed(1)}%` : (tp?.state === 'not_applicable' ? 'N/A' : '—')}
                    </td>
                    <td className="text-muted text-sm">{new Date(r.createdAt).toLocaleString()}</td>
                    <td>
                      <button className="btn-icon">
                        <ExternalLink size={16} />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
