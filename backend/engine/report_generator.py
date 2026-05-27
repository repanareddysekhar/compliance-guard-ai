from datetime import datetime
from typing import List, Dict
from backend.db.models import Violation, AuditEvent

def generate_report(scan_run_id: str, violations: List[Violation], audit_events: List[AuditEvent]) -> Dict:
    severity_counts = {"HIGH": 0, "MED": 0, "LOW": 0}
    category_counts = {}
    
    for v in violations:
        severity_counts[v.severity] = severity_counts.get(v.severity, 0) + 1
        category_counts[v.category] = category_counts.get(v.category, 0) + 1
        
    total_violations = len(violations)
    # Simple compliance score calculation
    compliance_score = 100 - (severity_counts["HIGH"] * 10 + severity_counts["MED"] * 5 + severity_counts["LOW"] * 2)
    compliance_score = max(0, min(100, compliance_score))

    return {
        "scan_run_id": str(scan_run_id),
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_services": 1,  # MVP: one service per scan
            "total_violations": total_violations,
            "by_severity": severity_counts,
            "by_category": category_counts,
        },
        "violations": [
            {
                "id": str(v.id),
                "service": v.service,
                "severity": v.severity,
                "status": v.status,
                "category": v.category,
                "description": v.description,
                "file_path": v.file_path,
                "line_number": v.line_number,
                "remediation": v.remediation,
                "detected_at": v.detected_at.isoformat() if v.detected_at else None,
            } for v in violations
        ],
        "audit_events": [
            {
                "event_id": str(e.event_id),
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                "agent": e.agent,
                "tool_called": e.tool_called,
                "intent": e.intent,
                "policy_decision": e.policy_decision,
                "signature": e.signature,
            } for e in audit_events
        ],
        "compliance_score": compliance_score
    }
