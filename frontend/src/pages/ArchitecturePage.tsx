import React from 'react';
import { Database, Server, HardDrive, Cpu, ShieldCheck } from 'lucide-react';

export const ArchitecturePage: React.FC = () => {
  return (
    <div className="page-container animate-fade-in">
      <div className="page-header-row">
        <div>
          <h1 className="page-title">System Architecture & Durability</h1>
          <p className="page-subtitle">Production-grade specification for motor policy commission resolution</p>
        </div>
      </div>

      <div className="architecture-grid">
        <div className="arch-card">
          <div className="arch-card-icon">
            <Database size={24} className="text-primary" />
          </div>
          <h3>Relational Persistence (PostgreSQL)</h3>
          <p>
            Every policy run, extraction payload, commission output, and audit trace is persisted in PostgreSQL with async transactions via SQLAlchemy & asyncpg. SQLite is strictly relegated to local development/testing.
          </p>
        </div>

        <div className="arch-card">
          <div className="arch-card-icon">
            <HardDrive size={24} className="text-primary" />
          </div>
          <h3>Durable Object Storage (S3 / Supabase)</h3>
          <p>
            Source policy PDFs are streamed directly into an S3-compatible bucket, identified by their SHA-256 content hashes. Ephemeral container disk storage is never used in production.
          </p>
        </div>

        <div className="arch-card">
          <div className="arch-card-icon">
            <Cpu size={24} className="text-primary" />
          </div>
          <h3>AI Extraction via Google Gemini</h3>
          <p>
            Runs on <code>gemini-3.5-flash</code> via the official <code>google-genai</code> Python SDK. Extracts structured JSON schemas with page coordinates, confidence levels, and uncertainty notes at temperature 0.0.
          </p>
        </div>

        <div className="arch-card">
          <div className="arch-card-icon">
            <ShieldCheck size={24} className="text-primary" />
          </div>
          <h3>Deterministic Commission Engine</h3>
          <p>
            Zero LLM hallucination in rate calculation. Implements strict geography key doctrines, explicit slab boundary handling, percentage-point vs multiplicative footnote evaluations, and grounded portfolio GWP refusal rules.
          </p>
        </div>
      </div>
    </div>
  );
};
