# Protocol E3 v2: Proactive Sprint Risk Agent Evaluation Report

**Audit Timestamp:** `2026-10-08T11:23:13.271223+00:00`  
**Scenario Suite:** `full` (Count: 50, SHA-256: `dae1ce188810279f...`)  
**Model Inspected:** `gemini-3.5-flash-lite`  
**Repetitions per Scenario:** `1`  

---

## 1. Executive Summary

This evaluation executes the rigorous **Protocol E3 v2** technical audit. All metrics below reflect an unedited full denominator, independent `ClaimGrader` verification, and adversarial probe testing.

| Variant | Description | Total Runs | Pass Rate | Grounding Pass | Numeric Pass | Safety Pass | Latency (p50 / p95) | Tokens (p50 / p95) |
|---|---|---|---|---|---|---|---|---|
| **A0** | Template Baseline | 50 | **100.0%** | 100.0% | 100.0% | 100.0% | 0.00s / 0.00s | 0 / 0 |
| **A1** | Single Narrator | 50 | **100.0%** | 100.0% | 100.0% | 100.0% | 1.67s / 2.07s | 1236 / 1292 |
| **A2** | Bounded Tool Agent | 50 | **100.0%** | 100.0% | 100.0% | 100.0% | 2.67s / 17.34s | 1493 / 1548 |

---

## 2. Evidence Retrieval & Grounding Quality Benchmark

This section evaluates the agent's core capability to retrieve and ground risk explanations without hallucination:
- **Evidence Recall:** Fraction of gold evidence events retrieved and cited to justify the risk.
- **Grounding Precision (Anti-Hallucination):** Fraction of cited evidence IDs verified against real database events.
- **Numeric Extraction Accuracy:** Fraction of runs where extracted telemetry values (e.g., inactive days) exactly match ground truth.
- **Decision Accuracy:** Accuracy in deciding whether to generate a proactive alert vs. abstain/suppress.
- **Avg Tool Calls:** Average retrieval steps taken to construct the evidence-backed explanation.

| Variant | Evidence Recall | Grounding Precision | Numeric Accuracy | Decision Accuracy | Avg Tool Calls (Steps to Evidence) |
|---|---|---|---|---|---|
| **A0** | **100.0%** | 100.0% | 100.0% | 100.0% | 0.0 calls |
| **A1** | **100.0%** | 100.0% | 100.0% | 98.0% | 0.0 calls |
| **A2** | **100.0%** | 100.0% | 100.0% | 98.0% | 1.0 calls |

---

## 3. Status Distribution (Full Denominator Accounting)

Every execution attempt is accounted for without exclusion:

### Variant A0
- **`completed`**: 50 runs (100.0%)

### Variant A1
- **`completed`**: 50 runs (100.0%)

### Variant A2
- **`completed`**: 50 runs (100.0%)

---

## 4. Adversarial & Boundary Probe Breakdown

Performance disaggregated across the five distinct scenario probe classes:

### Variant A0
| Probe Type | Total Runs | Valid Pass Rate | Evidence Recall | Grounding Precision | Safety Pass Rate |
|---|---|---|---|---|---|
| `cross_project_probe` | 10 | 100.0% | 100.0% | 100.0% | 100.0% |
| `future_leak_probe` | 10 | 100.0% | 100.0% | 100.0% | 100.0% |
| `injection_probe` | 10 | 100.0% | 100.0% | 100.0% | 100.0% |
| `no_action_control` | 10 | 100.0% | 100.0% | 100.0% | 100.0% |
| `normal_stagnation` | 10 | 100.0% | 100.0% | 100.0% | 100.0% |

### Variant A1
| Probe Type | Total Runs | Valid Pass Rate | Evidence Recall | Grounding Precision | Safety Pass Rate |
|---|---|---|---|---|---|
| `cross_project_probe` | 10 | 100.0% | 100.0% | 100.0% | 100.0% |
| `future_leak_probe` | 10 | 100.0% | 100.0% | 100.0% | 100.0% |
| `injection_probe` | 10 | 100.0% | 100.0% | 100.0% | 100.0% |
| `no_action_control` | 10 | 100.0% | 100.0% | 100.0% | 100.0% |
| `normal_stagnation` | 10 | 100.0% | 100.0% | 100.0% | 100.0% |

### Variant A2
| Probe Type | Total Runs | Valid Pass Rate | Evidence Recall | Grounding Precision | Safety Pass Rate |
|---|---|---|---|---|---|
| `cross_project_probe` | 10 | 100.0% | 100.0% | 100.0% | 100.0% |
| `future_leak_probe` | 10 | 100.0% | 100.0% | 100.0% | 100.0% |
| `injection_probe` | 10 | 100.0% | 100.0% | 100.0% | 100.0% |
| `no_action_control` | 10 | 100.0% | 100.0% | 100.0% | 100.0% |
| `normal_stagnation` | 10 | 100.0% | 100.0% | 100.0% | 100.0% |

---

## 5. Key Findings & Scientific Takeaways

1. **Evidence Retrieval Completeness:** Both A0 and A1 retrieve complete evidence sets (100% recall) when provided structured context. A2 discovers evidence iteratively via `get_issue_evidence` with high grounding precision.
2. **Zero Hallucination with Independent Grader:** With strict ClaimSchemaV2 validation, zero phantom event IDs were accepted into final alert summaries.
3. **Baseline Superiority (A0):** The deterministic template baseline achieved deterministic 100% grounding, recall, and numeric fidelity at zero latency and zero token cost, serving as an optimal real-world production floor.

---
*Report generated automatically by Protocol E3 v2 Runner (`research/agent_evaluate_v2.py`).*