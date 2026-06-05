import json
import logging
import uuid
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List
from app.core.config import settings

# Configure a specialized audit logger with an env-driven path
LOG_DIR = Path(settings.audit_log_dir)
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "audit_trail.log"

audit_logger = logging.getLogger("signalhire.audit")
handler = logging.FileHandler(str(LOG_FILE))
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
audit_logger.addHandler(handler)
audit_logger.setLevel(logging.INFO)

class AuditAgent:
    """
    Multi-Agent Audit Trail system per research requirements (FCRA/Compliance).
    """
    
    @staticmethod
    async def log_decision(
        agent_name: str,
        action: str,
        candidate_id: str,
        job_id: str,
        metadata: Dict[str, Any],
        user_id: str = "system"
    ):
        """
        Logs a deterministic decision for the audit trail.
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_id": str(uuid.uuid4()),
            "agent": agent_name,
            "action": action,
            "candidate_id": candidate_id,
            "job_id": job_id,
            "user_id": user_id,
            "metadata": metadata
        }
        
        # Log to file for persistence and legal defensibility
        audit_logger.info(json.dumps(entry))
        
        # In production, we would also store this in a 'audit_logs' DB table
        print(f"[AUDIT][{agent_name}] {action} for candidate {candidate_id}")

    @staticmethod
    async def log_planning(job_id: str, policy: str):
        await AuditAgent.log_decision(
            "PlanningAgent",
            "policy_applied",
            "N/A",
            job_id,
            {"policy": policy}
        )

    @staticmethod
    async def log_provenance(candidate_id: str, source: str, data_points: List[str]):
        await AuditAgent.log_decision(
            "DataProvenanceAgent",
            "lineage_established",
            candidate_id,
            "N/A",
            {"source": source, "data_points": data_points}
        )

    @staticmethod
    async def log_compliance_check(candidate_id: str, job_id: str, status: str, findings: List[str]):
        await AuditAgent.log_decision(
            "ComplianceAgent",
            "algorithmic_audit",
            candidate_id,
            job_id,
            {"status": status, "findings": findings}
        )

    @staticmethod
    async def log_explanation(candidate_id: str, job_id: str, model: str):
        await AuditAgent.log_decision(
            "ExplainabilityAgent",
            "reasoning_generated",
            candidate_id,
            job_id,
            {"model": model}
        )
