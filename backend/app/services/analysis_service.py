import hashlib
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.storage.models import RunModel
from backend.app.storage.object_store import object_store
from backend.app.extraction.gemini_extractor import GeminiFactExtractor
from backend.app.grids.registry import registry
from backend.app.resolver.resolver import resolve_policy
from backend.app.resolver.states import PolicyFacts

logger = logging.getLogger(__name__)

class AnalysisService:
    def __init__(self, extractor=None):
        self.extractor = extractor or GeminiFactExtractor()
        
    async def create_run(self, session: AsyncSession, file_name: str, pdf_bytes: bytes) -> RunModel:
        pdf_sha256 = hashlib.sha256(pdf_bytes).hexdigest()
        
        # Check for duplicate upload (any existing run with this sha256)
        stmt = select(RunModel).where(RunModel.pdf_sha256 == pdf_sha256).order_by(desc(RunModel.created_at)).limit(1)
        res = await session.execute(stmt)
        existing = res.scalar_one_or_none()
        
        if existing:
            # Check if grid checksum or resolver version has changed since existing run
            current_resolver_version = "1.0.0"
            needs_re_resolution = False
            
            # Identify insurer grid
            facts_dict = existing.facts or {}
            ins_val = (facts_dict.get("insurer", {}).get("value") or "").lower()
            target_grid_id = None
            if "hdfc" in ins_val:
                target_grid_id = "hdfc_ergo"
            elif "digit" in ins_val:
                target_grid_id = "godigit"
            elif "reliance" in ins_val:
                target_grid_id = "reliance"
            elif "tata" in ins_val:
                target_grid_id = "tata_aig"
                
            grid = registry.get_grid(target_grid_id) if target_grid_id else None
            current_checksum = grid.checksumSha256 if grid else None
            
            if (
                existing.resolver_version != current_resolver_version
                or (current_checksum and existing.grid_checksum_sha256 != current_checksum)
            ):
                needs_re_resolution = True

            if needs_re_resolution and grid and existing.facts:
                try:
                    facts_obj = PolicyFacts(**existing.facts)
                    resolution = resolve_policy(facts_obj, grid)
                    dup_run = RunModel(
                        file_name=file_name,
                        file_size_bytes=len(pdf_bytes),
                        pdf_sha256=pdf_sha256,
                        pdf_storage_path=existing.pdf_storage_path,
                        status=resolution.status.value,
                        completed_at=datetime.utcnow(),
                        grid_checksum_sha256=resolution.appliedGridChecksum,
                        resolver_version=resolution.resolverVersion,
                        model_id=existing.model_id,
                        raw_extraction_json=existing.raw_extraction_json,
                        facts=existing.facts,
                        rates={k: v.model_dump() for k, v in resolution.rates.items()},
                        confidence=resolution.confidence,
                        trace=[t.model_dump() for t in resolution.trace],
                        is_duplicate=True
                    )
                    session.add(dup_run)
                    await session.commit()
                    await session.refresh(dup_run)
                    return dup_run
                except Exception as ex:
                    logger.warning(f"Re-resolution failed for duplicate {file_name}: {ex}")

            dup_run = RunModel(
                file_name=file_name,
                file_size_bytes=len(pdf_bytes),
                pdf_sha256=pdf_sha256,
                pdf_storage_path=existing.pdf_storage_path,
                status=existing.status,
                completed_at=existing.completed_at,
                grid_checksum_sha256=existing.grid_checksum_sha256,
                resolver_version=existing.resolver_version,
                model_id=existing.model_id,
                raw_extraction_json=existing.raw_extraction_json,
                facts=existing.facts,
                rates=existing.rates,
                confidence=existing.confidence,
                trace=existing.trace,
                is_duplicate=True
            )
            session.add(dup_run)
            await session.commit()
            await session.refresh(dup_run)
            return dup_run
            
        storage_key = f"policies/{pdf_sha256}/{file_name}"
        storage_path = object_store.upload_pdf(storage_key, pdf_bytes)
        
        run = RunModel(
            file_name=file_name,
            file_size_bytes=len(pdf_bytes),
            pdf_sha256=pdf_sha256,
            pdf_storage_path=storage_key,
            status="queued"
        )
        session.add(run)
        await session.commit()
        await session.refresh(run)
        return run

    async def create_run_from_storage(self, session: AsyncSession, file_name: str, object_key: str) -> RunModel:
        # Download PDF from object storage to inspect magic bytes, page count, and sha256
        pdf_bytes = object_store.get_pdf(object_key)
        if not pdf_bytes.startswith(b"%PDF"):
            raise ValueError("Invalid file format: must be a valid PDF document (magic bytes %PDF required).")
        
        # Verify page count <= 30
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        if len(doc) > 30:
            raise ValueError(f"Document exceeds 30-page limit ({len(doc)} pages found). PDFs over 30 pages are rejected.")

        pdf_sha256 = hashlib.sha256(pdf_bytes).hexdigest()
        
        # Check duplicate
        stmt = select(RunModel).where(RunModel.pdf_sha256 == pdf_sha256).order_by(desc(RunModel.created_at)).limit(1)
        res = await session.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing and existing.status in ("resolved", "saved", "ambiguous", "unsupported"):
            dup_run = RunModel(
                file_name=file_name,
                file_size_bytes=len(pdf_bytes),
                pdf_sha256=pdf_sha256,
                pdf_storage_path=existing.pdf_storage_path,
                status=existing.status,
                completed_at=datetime.utcnow(),
                grid_checksum_sha256=existing.grid_checksum_sha256,
                resolver_version=existing.resolver_version,
                model_id=existing.model_id,
                raw_extraction_json=existing.raw_extraction_json,
                facts=existing.facts,
                rates=existing.rates,
                confidence=existing.confidence,
                trace=existing.trace,
                is_duplicate=True
            )
            session.add(dup_run)
            await session.commit()
            await session.refresh(dup_run)
            return dup_run

        run = RunModel(
            file_name=file_name,
            file_size_bytes=len(pdf_bytes),
            pdf_sha256=pdf_sha256,
            pdf_storage_path=object_key,
            status="queued"
        )
        session.add(run)
        await session.commit()
        await session.refresh(run)
        return run

    async def process_run(self, session: AsyncSession, run_id: str):
        stmt = select(RunModel).where(RunModel.id == run_id)
        res = await session.execute(stmt)
        run = res.scalar_one_or_none()
        if not run:
            return
            
        try:
            # 1. Update status to extracting
            run.status = "extracting"
            await session.commit()
            
            pdf_bytes = object_store.get_pdf(run.pdf_storage_path)
            
            # 2. Extract facts via Gemini
            extraction_result = await self.extractor.extract_facts(pdf_bytes, run.file_name)
            facts: PolicyFacts = extraction_result["facts"]
            
            run.raw_extraction_json = extraction_result["raw_json"]
            run.model_id = extraction_result["model_id"]
            run.facts = facts.model_dump()
            run.status = "resolving"
            await session.commit()
            
            # 3. Match Insurer Grid
            ins_val = (facts.insurer.value or "").lower()
            target_grid_id = None
            if "hdfc" in ins_val:
                target_grid_id = "hdfc_ergo"
            elif "digit" in ins_val:
                target_grid_id = "godigit"
            elif "reliance" in ins_val:
                target_grid_id = "reliance"
            elif "tata" in ins_val:
                target_grid_id = "tata_aig"
                
            if not target_grid_id or not registry.get_grid(target_grid_id):
                run.status = "unsupported"
                run.error_message = f"No matching rater grid found for insurer '{facts.insurer.value}'"
                run.completed_at = datetime.utcnow()
                await session.commit()
                return
                
            grid = registry.get_grid(target_grid_id)
            
            # 4. Deterministic Resolution
            resolution = resolve_policy(facts, grid)
            
            # Store the resolved run status: one of resolved, unsupported, ambiguous
            run.status = resolution.status.value
            run.grid_checksum_sha256 = resolution.appliedGridChecksum
            run.resolver_version = resolution.resolverVersion
            run.rates = {k: v.model_dump() for k, v in resolution.rates.items()}
            run.confidence = resolution.confidence
            run.trace = [t.model_dump() for t in resolution.trace]
            run.completed_at = datetime.utcnow()
            await session.commit()
            
        except Exception as e:
            logger.exception(f"Error processing run {run_id}: {e}")
            run.status = "failed"
            run.error_message = str(e)
            run.completed_at = datetime.utcnow()
            await session.commit()

analysis_service = AnalysisService()
