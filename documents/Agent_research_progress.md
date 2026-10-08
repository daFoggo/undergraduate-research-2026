# Tiến độ nghiên cứu agent cảnh báo chủ động

Ngày 2026-10-08. Tiếp nối phase 4 nhưng không sửa study frozen. Người dùng yêu cầu deep research theo SOTA nhất có thể, tạo lộ trình và thực hiện đánh giá theo quy trình trước.

Format mỗi batch: mục tiêu; protocol/version/hash; trạng thái; commands; evidence/metrics; limitations; quyết định; next step. DONE chỉ khi có verification.

- [x] Research nhiều vòng và tổng hợp 15 nguồn chính, đánh dấu mức đọc và giới hạn.
- [x] Thiết kế ba lớp model/controller/tool agent, baselines/ablation và human study.
- [x] Protocol E1 và lộ trình triển khai được viết trước metric mới.
- [x] E1 policy replay, CI, audit và báo cáo (post-hoc exploratory).
- [ ] E2 validation/serving parity và chọn calibration cho deployment (serving adapter parity đã PASS 18 bundles).
- [x] E3 technical agent benchmark với LLM thật (A0, A1, A2 hoàn thiện, test suite 51 passed, pilot benchmark hoàn tất).
- [ ] E4 human decision study / opt-in pilot.
- [ ] Manuscript extension bằng kết quả mới.

## Checkpoint hiện tại

E1 đã kết thúc exit 0 bằng `.venv/Scripts/python.exe -m research.agent_policy_experiment`. 252 input files, 96 cells, 24 CI contrasts, 113.232 sprint metric rows và 180.638 alert rows. Đã đọc kết quả sau run và viết `Phan_tich_policy_agent_E1.md`.

E2 phục vụ: `app/services/risk_inference.py` tái dùng prepare/logit từ research code, `research.validate_serving_parity` pass 18 trusted local bundles / 180 snapshots (atol=1e-12).

E3 Technical Agent Evaluation:
- Sàng lọc model: Đối chiếu Leaderboard $\tau^2$-Bench và tích hợp `GeminiClient` với model `gemini-3.5-flash-lite` (Top 14 leaderboard, 76.9% accuracy, native function calling có thoughtSignature preservation) cùng fallback OpenRouter `cohere/north-mini-code:free`.
- Đã triển khai Task 5 (Agent Contract & Sandbox): `AgentContext` (as-of isolation, chặn future leak và cross-project access), `EvidenceVerifier` (Pydantic schema, kiểm tra tính có thật của evidence_ids, kiểm tra số học và chặn khẳng định nhân quả), `AgentRunner` (hỗ trợ A0 template, A1 narrator, A2 bounded tool agent).
- Đã triển khai Task 7 (Evaluation Pipeline): `research/agent_scenarios.py` (tải archival scenarios có ground truth từ TAWOS) và `research/agent_evaluate.py`.
- Toàn bộ suite test **54 passed**, zero errors (bao gồm test adapter Gemini, test OpenRouter, test sandbox, verifier).
- Đã chạy thực nghiệm benchmark hoàn chỉnh trên toàn bộ Dev Benchmark (10 kịch bản đại diện TAWOS $\times$ 3 biến thể = 30 runs) với cơ chế rate pacing (4.5s/call) và incremental checkpointing:
  + **A0 (Template Baseline):** 10/10 kịch bản (100%), tỷ lệ pass 100%, grounding 100%, numeric fidelity 100%, causal safety 100%, độ trễ <1ms, cost $0.00.
  + **A1 (Narrator với Gemini 3.5 Flash Lite):** 10/10 kịch bản (100%), tỷ lệ pass 100%, grounding 100%, numeric fidelity 100%, causal safety 100%, độ trễ trung bình 1.638s, cost $0.00.
  + **A2 (Bounded Tool Agent với Gemini 3.5 Flash Lite):** 10/10 kịch bản (100%), tỷ lệ pass 100%, grounding 100%, numeric fidelity 100%, causal safety 100%, số bước trung bình = 2 bước (chủ động gọi tool `get_issue_evidence` -> nhận bằng chứng as-of -> sinh claim có căn cứ), độ trễ trung bình 2.385s, cost $0.00.

Kết quả E1 dynamic/K2 temporal: quota early macro recall 58,77%, midpoint 59,20%; delta -0,43 pp CI [-1,36; 0,55]. Quota lead days conditional 8,18 vs 6,29, precision micro 77,31% vs 79,70%. Không kết luận superior/causal; cohort/cap khác H1 cũ. Decision A10: giữ midpoint/rule và quyền abstain làm đối chứng cho policy mới; không tune bằng E1. CSV lớn giữ local, manifest SHA và summary/CI/audit tracking Git.

Next safe step: serving registry/as-of context và template/verifier sandbox theo plan, cùng validation scores mới. E3 LLM thực cần provider/model configuration, E4 cần người tham gia/consent; chưa thực hiện và không được báo DONE. Không có job E1 đang chạy cần resume.

Decision A07: E1 dùng raw ranking/fixed policies, mọi kết quả exploratory trên frozen test cũ, không tune/chọn champion. A08: evidence mới chỉ về policy replay, không agent hoặc causal improvement. A09: provider/human dependency được báo trạng thái NOT RUN, không thay bằng lời hứa tự hoàn thành.
