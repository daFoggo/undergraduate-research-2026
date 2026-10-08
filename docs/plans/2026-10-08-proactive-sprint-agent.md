# Proactive Sprint Agent Implementation Plan

> Thực hiện trong session hiện tại theo checkpoint; không tạo chat hoặc subagent tự động. Dùng @test-driven-development và @verification-before-completion. Workspace hiện tại chứa artifact đã kiểm chứng nên tiếp tục tại đây, bảo toàn thay đổi PDF có sẵn; không copy dataset lớn sang worktree.

**Goal:** mở rộng nghiên cứu bằng controller cảnh báo dưới capacity và agent dùng công cụ có bằng chứng, đánh giá từng lớp.

**Architecture:** cùng lõi prediction cho replay/serving, policy ngoài LLM, bounded agent sau trigger, verifier/ledger/permission guard và outbox. Raw model scores không là calibrated probability cho Agentick.

**Tech stack:** Python hiện có, pandas/NumPy/pytest, FastAPI modular, PostgreSQL/Docker ở bước integration; LLM provider chưa cấu hình.

Root tuyệt đối: `C:/Users/Foggo/Documents/Dev projects/nkch-sv-2026/`. Các đường dẫn dưới đây ghép với root này. Required reading: `documents/Deep_research_AI_agent_canh_bao_som.md`, `documents/Protocol_agent_extension_v1.md`, `research/train.py`, `research/evaluate.py`, `research/metrics.py`. Không sửa source protocol/train phase 4.

## Task 1 protocol và checklist

Files: `documents/Protocol_agent_extension_v1.md`, `documents/Agent_research_progress.md`. Khóa E1 trước replay, ghi test đã xem/metrics mới chưa xem, hashes và scope. Kiểm tra `git diff --check`; kỳ vọng exit 0. Checkpoint local Git chỉ stage file của batch, không stage `papers/sprint-risk/main.pdf` đã thay đổi từ trước.

## Task 2 policy core theo TDD

Create `research/agent_policy.py`, `tests/test_agent_policy.py`. Test cap whole sprint, skip Done, fixed active-at-.25 denominator, zero-cap, label/permutation invariance và malformed input. Run `.venv/Scripts/python.exe -m pytest tests/test_agent_policy.py -q` trước implement (ModuleNotFoundError), sau implement phải pass. Interface:

```python
metrics, alerts = replay_policy(frame, policy='quota', capacity='k2')
assert (metrics.alerts <= metrics.cap).all()
assert not alerts.duplicated(['sprint_id', 'issue_id']).any()
```

Selection function không nhận outcome; evaluator join y sau selection. Capacity choices k1/k2/k3/floor20; policies quota/midpoint/early/late. Validate keys/landmarks/timestamps/scores trước chạy. Không ghi dữ liệu network/database.

## Task 3 replay runner và evidence audit

Create `research/agent_policy_experiment.py`; output `artifacts/agent_extension/policy_v1/`. Hash protocol/source/input, refuse existing directory. Run `.venv/Scripts/python.exe -m research.agent_policy_experiment`; kỳ vọng terminal success và manifest, per-sprint/alert/summary/CI CSV, báo cáo Markdown. So sánh quota-midpoint theo protocol, không chọn best scorer từ test làm champion. Run all tests, compileall, diff-check trước commit.

## Task 4 serving adapter và parity

Create `app/services/risk_inference.py`, `tests/test_risk_inference.py`. Đọc feature order/bundle/hash, từ chối unsupported landmark/schema và unsafe model source. Reuse prepare/logit behavior; parity trên frozen sample trước refactor shared code. Run `.venv/Scripts/python.exe -m pytest tests/test_risk_inference.py -q`; phải khớp within numerical tolerance, not after-current event access. Chưa đưa endpoint public nếu chưa auth/project scoping.

## Task 5 agent contract và sandbox

Create `app/services/agent_context.py`, `app/services/agent_runner.py`, `app/services/evidence_verifier.py`, `tests/test_agent_context.py`, `tests/test_agent_runner.py`, `tests/test_evidence_verifier.py`. Pydantic claim schema với evidence IDs, cutoff, kind, suggested_checks và unknowns. First fail test future/cross-project evidence, forged numeric values, unsupported causal claims, forbidden tool calls, tool timeout. Implement template A0 trước; tiếp A1/A2 sau provider config. Exact prompt/provider/decoding tracked, secrets never tracked. Run từng module pytest và toàn suite; expected zero failures. Test dữ liệu công cụ có injection mà recipient/scope vẫn server-controlled. Semantic entailment không được gọi là solved bởi chỉ check IDs.

## Task 6 durable ledger/outbox

Create migrations và service/tests sau khi đọc @postgres và @supabase-postgres-best-practices. Atomic reserve/cap, unique initial alert, durable snooze và delivery reconciliation. First integration test concurrent reservation, restart, ambiguous send timeout. Chạy migration trên test DB riêng, không source `tawos_raw`. Chỉ gọi gửi thật sau opt-in; default dry-run. Schema/SQL exact được viết khi scope/auth và transaction interface đã rõ, không phỏng đoán trong research plan.

## Task 7 locked agent evaluation

Create `research/agent_scenarios.py`, `research/agent_evaluate.py`, `tests/test_agent_evaluation.py`, `artifacts/agent_extension/agent_v1/`. Dev 30/locked ~120 scenarios là target kỹ thuật, không power claim. Lock suite/rubric trước outputs, 3 repetitions A0/A1/A2, same context/tool budget. End-state assertions, claim-grounding, safety+coverage, cost/latency. Synthetic vs archival báo tách; thiếu provider -> NOT RUN, không synthetic result giả làm LLM actual.

## Task 8 human study và publication

Write `documents/Agent_human_study_protocol.md` khi recruitment khả thi. Counterbalanced matched scenarios/context; độc lập outcome/actionability; power/precision target trước tuyển. Shadow calibration rồi opt-in pilot; không tự tạo participants/consent. Update paper chỉ bằng evidence đã chạy, giữ frozen empirical findings. Mỗi checkpoint ghi command, actual result, limitations, artifacts/hash và next safe step.

## Điều kiện kết thúc

Research synthesis + E1 không phải hoàn tất phase 5. Hoàn tất phase 5 kỹ thuật khi parity, policy, bounded agent, verifier/ledger, dashboard/dry-run delivery có tests/audit và report. Kết luận decision quality cần E3 với nhãn người/E4 phù hợp; causal effect cần study riêng. Không kết luận SOTA từ vài baseline nội bộ.
