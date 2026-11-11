import React, { useState, useEffect } from 'react';
import { 
  FileText, History as HistoryIcon, Layers, Server, 
  Sun, Moon, ShieldCheck 
} from 'lucide-react';
import { AnalyzePage } from './pages/AnalyzePage';
import { RunDetailPage } from './pages/RunDetailPage';
import { HistoryPage } from './pages/HistoryPage';
import { GridsPage } from './pages/GridsPage';
import { ArchitecturePage } from './pages/ArchitecturePage';
import { api, RunDetail } from './api/client';

export const App: React.FC = () => {
  const [activeNav, setActiveNav] = useState<'analyze' | 'history' | 'grids' | 'architecture'>('analyze');
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [activeRunDetail, setActiveRunDetail] = useState<RunDetail | null>(null);
  const [loadingRun, setLoadingRun] = useState(false);
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const loadRunDetail = async (runId: string) => {
    setActiveRunId(runId);
    setLoadingRun(true);
    try {
      const data = await api.getRun(runId);
      setActiveRunDetail(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingRun(false);
    }
  };

  const handleBackToAnalyze = () => {
    setActiveRunId(null);
    setActiveRunDetail(null);
  };

  return (
    <div className="app-layout">
      {/* Top Navbar */}
      <header className="navbar">
        <div className="navbar-brand">
          <div className="brand-logo">
            <ShieldCheck size={22} className="text-primary" />
          </div>
          <div className="brand-text">
            <span className="brand-name">VAATUN</span>
            <span className="brand-app">RATER AGENT</span>
          </div>
        </div>

        <nav className="nav-links">
          <button 
            className={`nav-link ${activeNav === 'analyze' && !activeRunId ? 'active' : ''}`}
            onClick={() => { setActiveNav('analyze'); setActiveRunId(null); }}
          >
            <FileText size={16} /> Analyze Policy
          </button>
          <button 
            className={`nav-link ${activeNav === 'history' && !activeRunId ? 'active' : ''}`}
            onClick={() => { setActiveNav('history'); setActiveRunId(null); }}
          >
            <HistoryIcon size={16} /> Run History
          </button>
          <button 
            className={`nav-link ${activeNav === 'grids' ? 'active' : ''}`}
            onClick={() => { setActiveNav('grids'); setActiveRunId(null); }}
          >
            <Layers size={16} /> Rater Grids
          </button>
          <button 
            className={`nav-link ${activeNav === 'architecture' ? 'active' : ''}`}
            onClick={() => { setActiveNav('architecture'); setActiveRunId(null); }}
          >
            <Server size={16} /> Architecture & Durability
          </button>
        </nav>

        <div className="navbar-controls">
          <button 
            className="theme-toggle-btn"
            onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
            title="Toggle theme"
          >
            {theme === 'light' ? <Moon size={16} /> : <Sun size={16} />}
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="main-content">
        {activeRunId && activeRunDetail ? (
          <RunDetailPage 
            run={activeRunDetail} 
            onBack={handleBackToAnalyze}
            onRerun={() => loadRunDetail(activeRunId)}
          />
        ) : loadingRun ? (
          <div className="loading-state-box">
            <div className="spinner-border animate-spin" />
            <p>Loading run details...</p>
          </div>
        ) : activeNav === 'analyze' ? (
          <AnalyzePage onRunSelected={loadRunDetail} />
        ) : activeNav === 'history' ? (
          <HistoryPage onSelectRun={loadRunDetail} />
        ) : activeNav === 'grids' ? (
          <GridsPage />
        ) : (
          <ArchitecturePage />
        )}
      </main>
    </div>
  );
};

export default App;
