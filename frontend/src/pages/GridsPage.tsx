import React, { useState, useEffect } from 'react';
import { Database, FileSpreadsheet, ShieldCheck, MapPin } from 'lucide-react';
import { api } from '../api/client';

export const GridsPage: React.FC = () => {
  const [grids, setGrids] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getGrids()
      .then((data) => setGrids(data.grids))
      .catch((e) => console.error(e))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="page-container animate-fade-in">
      <div className="page-header-row">
        <div>
          <h1 className="page-title">Authoritative Rater Grids</h1>
          <p className="page-subtitle">Indexed and parsed commission rate cards for Indian General Insurers</p>
        </div>
      </div>

      {loading ? (
        <div className="loading-state-box">
          <div className="spinner-border animate-spin" />
          <p>Loading rater grids metadata...</p>
        </div>
      ) : (
        <div className="grids-cards-layout">
          {grids.map((grid) => (
            <div key={grid.insurer_slug} className="grid-summary-card">
              <div className="grid-card-top">
                <span className="insurer-tag">{grid.insurer_slug.toUpperCase()}</span>
                <span className="font-mono text-sm text-muted">{grid.rule_count} Rules</span>
              </div>
              <h3 className="grid-insurer-name">{grid.insurer_name}</h3>
              <p className="grid-file-name font-mono text-xs">{grid.version_name}</p>

              <div className="grid-details-list">
                <div className="grid-detail-item">
                  <Database size={14} />
                  <span><strong>Rules Indexed:</strong> {grid.rule_count.toLocaleString()}</span>
                </div>
                <div className="grid-detail-item">
                  <MapPin size={14} />
                  <span><strong>RTO / Geo Mappings:</strong> {grid.mapping_count.toLocaleString()}</span>
                </div>
                {grid.effective_from && (
                  <div className="grid-detail-item">
                    <ShieldCheck size={14} />
                    <span><strong>Effective From:</strong> {grid.effective_from}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
