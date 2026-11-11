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
  state: 'resolved' | 'unsupported' | 'ambiguous' | 'not_applicable';
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
  confidence: number;
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
  gridCitation?: string;
  explanation: string;
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

export interface RunListItem {
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

export interface GridInfo {
  insurerId: string;
  insurerName: string;
  fileName: string;
  checksumSha256: string;
  effectiveFrom?: string;
  effectiveTo?: string;
  effectiveDateCaveat?: string;
  rulesCount: number;
  footnotesCount: number;
}

export interface BenchItem {
  insurer: string;
  policyType: string;
  fileName: string;
  tests: string;
  expectedStatus: string;
  expectedOd: string;
  expectedTp: string;
  citation: string;
}

export async function uploadPolicyPdf(file: File): Promise<{ id: string; status: string; fileName: string; isDuplicate: boolean }> {
  const formData = new FormData();
  formData.append('file', file);
  const resp = await fetch('/api/runs', {
    method: 'POST',
    body: formData
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(err.detail || 'Upload failed');
  }
  return resp.json();
}

export async function fetchRuns(status?: string, search?: string): Promise<RunListItem[]> {
  const params = new URLSearchParams();
  if (status && status !== 'all') params.append('status', status);
  if (search) params.append('search', search);
  const resp = await fetch(`/api/runs?${params.toString()}`);
  if (!resp.ok) throw new Error('Failed to fetch runs');
  return resp.json();
}

export async function fetchRun(id: string): Promise<RunDetail> {
  const resp = await fetch(`/api/runs/${id}`);
  if (!resp.ok) throw new Error('Failed to fetch run detail');
  return resp.json();
}

export async function rerunAnalysis(id: string): Promise<void> {
  const resp = await fetch(`/api/runs/${id}/rerun`, { method: 'POST' });
  if (!resp.ok) throw new Error('Failed to re-run analysis');
}

export async function fetchGrids(): Promise<GridInfo[]> {
  const resp = await fetch('/api/grids');
  if (!resp.ok) throw new Error('Failed to fetch grids');
  return resp.json();
}

export async function fetchBench(): Promise<BenchItem[]> {
  const resp = await fetch('/api/bench');
  if (!resp.ok) throw new Error('Failed to fetch bench');
  return resp.json();
}
