export interface Citation {
  sourceType: string;
  file: string;
  sheet?: string;
  page?: number;
  coordinate?: string;
  description: string;
}

export interface RateComponent {
  applicable: boolean;
  ratePercent: number | null;
  state: 'resolved' | 'unsupported' | 'ambiguous' | 'not_applicable' | 'not_published';
  reason: string;
  citations: Citation[];
}

export interface FactField<T = any> {
  value: T;
  page?: number;
  confidence: number;
  uncertainty?: string;
  lowConfidence?: boolean;
}

export interface PremiumBreakup {
  basicOd?: number;
  ncbDiscount?: number;
  netOd?: number;
  basicTp?: number;
  netTp?: number;
  taxes?: number;
  total?: number;
  page?: number;
  confidence?: number;
  ncbPercent?: number;
  ncbUnclearNote?: string;
}

export interface PolicyFacts {
  insurer: FactField<string>;
  previousInsurer: FactField<string | null>;
  businessType: FactField<string>;
  policyType: FactField<string>;
  make: FactField<string>;
  model: FactField<string>;
  fuel: FactField<string>;
  rto: FactField<string>;
  printedLocation?: FactField<string>;
  engineCc?: FactField<number>;
  registrationYear?: FactField<number>;
  manufactureYear?: FactField<number | null>;
  vehicleAgeYears?: FactField<number>;
  policyStartDate?: FactField<string>;
  premiums: PremiumBreakup;
}

export interface TraceStep {
  step: number;
  decision: string;
  policyCitation?: string;
  gridCitation?: any;
  explanation?: string;
  caveats?: string[];
}

export interface RunDetail {
  id: string;
  fileName: string;
  fileSizeBytes: number;
  pdfSha256: string;
  status: 'queued' | 'extracting' | 'resolving' | 'saved' | 'failed' | 'resolved' | 'unsupported' | 'ambiguous';
  createdAt: string;
  completedAt?: string;
  gridChecksum?: string;
  resolverVersion?: string;
  modelId?: string;
  facts?: PolicyFacts;
  rates?: {
    od: RateComponent;
    tp: RateComponent;
  };
  confidence?: {
    level: number;
    reason: string;
  };
  trace?: TraceStep[];
  rawExtractionJson?: string;
  errorMessage?: string;
  isDuplicate?: boolean;
}

export interface RunSummary {
  id: string;
  fileName: string;
  fileSizeBytes: number;
  status: string;
  createdAt: string;
  completedAt?: string;
  isDuplicate: boolean;
  rates?: {
    od: RateComponent;
    tp: RateComponent;
  };
  confidence?: {
    level: number;
    reason: string;
  };
}

export const api = {
  uploadPolicy: async (file: File): Promise<{ id: string; status: string; fileName: string; isDuplicate: boolean }> => {
    const formData = new FormData();
    formData.append('file', file);
    const resp = await fetch('/api/runs', { method: 'POST', body: formData });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail || 'Upload failed');
    }
    return resp.json();
  },

  listRuns: async (params?: { status?: string; search?: string; page?: number; limit?: number }): Promise<RunSummary[]> => {
    const qs = new URLSearchParams();
    if (params?.status && params.status !== 'all') qs.append('status', params.status);
    if (params?.search) qs.append('search', params.search);
    if (params?.page) qs.append('page', params.page.toString());
    if (params?.limit) qs.append('limit', params.limit.toString());
    const resp = await fetch(`/api/runs?${qs.toString()}`);
    if (!resp.ok) throw new Error('Failed to fetch runs');
    return resp.json();
  },

  getRun: async (id: string): Promise<RunDetail> => {
    // Check if benchmark shortcut
    if (['hdfc-ergo', 'reliance', 'godigit', 'tata-aig'].includes(id)) {
      const resp = await fetch(`/api/bench/${id}`);
      if (!resp.ok) throw new Error('Failed to load benchmark output');
      return resp.json();
    }
    const resp = await fetch(`/api/runs/${id}`);
    if (!resp.ok) throw new Error('Failed to fetch run detail');
    return resp.json();
  },

  getPdfUrl: (id: string) => `/api/runs/${id}/pdf`,
  getExportUrl: (id: string) => `/api/runs/${id}/export`,

  rerunAnalysis: async (id: string): Promise<void> => {
    const resp = await fetch(`/api/runs/${id}/rerun`, { method: 'POST' });
    if (!resp.ok) throw new Error('Failed to re-run analysis');
  },

  getGrids: async (): Promise<{ count: number; grids: any[] }> => {
    const resp = await fetch('/api/grids');
    if (!resp.ok) throw new Error('Failed to fetch grids');
    return resp.json();
  }
};
