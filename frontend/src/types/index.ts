// frontend/src/types/index.ts

export type Severity = "HIGH" | "MED" | "LOW";
export type ViolationStatus = "BLOCKED" | "FLAGGED" | "REPORTED" | "AUTO_FIXED";
export type PolicyDecision = "ALLOW" | "BLOCK";
export type ScanStatus = "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";

export interface ScanRun {
  id: string;                    // UUID
  service_name: string;
  repo_path: string;
  status: ScanStatus;
  started_at: string;            // ISO8601
  completed_at?: string;
  services_scanned: number;
  violations_found: number;
  auto_fixed: number;
}

export interface Violation {
  id: string;
  scan_run_id: string;
  service: string;
  severity: Severity;
  status: ViolationStatus;
  category: "CRYPTOGRAPHIC" | "DEPENDENCY" | "CONTAINER" | "ACCESS_CONTROL" | "HEADER";
  description: string;
  file_path?: string;
  line_number?: number;
  remediation: string;           // Step-by-step fix recommendation
  opa_policy_ref: string;        // e.g. "compliance/cryptographic"
  detected_at: string;
}

export interface AuditEvent {
  event_id: string;
  scan_run_id: string;
  timestamp: string;
  agent: string;
  tool_called: string;
  intent: string;
  policy_decision: PolicyDecision;
  input_hash: string;
  output_hash: string;
  signature: string;             // ArmorIQ cryptographic signature
}

export interface Report {
  scan_run_id: string;
  generated_at: string;
  summary: {
    total_services: number;
    total_violations: number;
    by_severity: Record<Severity, number>;
    by_category: Record<string, number>;
  };
  violations: Violation[];
  audit_events: AuditEvent[];
  compliance_score: number;      // 0–100
}

export interface WsEvent {
  type: "SCAN_STARTED" | "TOOL_CALLED" | "VIOLATION_FOUND" | "SCAN_COMPLETED" | "SCAN_FAILED";
  scan_id: string;
  service?: string;
  tool?: string;
  intent?: string;
  decision?: PolicyDecision;
  violation?: Violation;
  summary?: any;
  error?: string;
}
