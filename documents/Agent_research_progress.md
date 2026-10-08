# Tiến độ nghiên cứu agent cảnh báo chủ động

Ngày 2026-10-08. Tiếp nối phase 4 nhưng không sửa study frozen. Người dùng yêu cầu deep research theo SOTA nhất có thể, tạo lộ trình và thực hiện đánh giá theo quy trình trước.

Format mỗi batch: mục tiêu; protocol/version/hash; trạng thái; commands; evidence/metrics; limitations; quyết định; next step. DONE chỉ khi có verification.

- [x] Research nhiều vòng và tổng hợp 15 nguồn chính, đánh dấu mức đọc và giới hạn.
- [x] Thiết kế ba lớp model/controller/tool agent, baselines/ablation và human study.
- [x] Protocol E1 và lộ trình triển khai được viết trước metric mới.
- [x] E1 policy replay, CI, audit và báo cáo (post-hoc exploratory).
- [ ] E2 validation/serving parity và chọn calibration cho deployment (serving adapter parity đã PASS 18 bundles).
- [x] E3 technical agent benchmark — **ĐÃ HOÀN THÀNH (Protocol E3 v2 trên bộ dữ liệu Full 50 kịch bản)**: Đã thiết kế lại độc lập theo Protocol E3 v2, loại bỏ hoàn toàn việc gán cứng và sửa đầu ra bằng ground-truth. Triển khai `ClaimGrader` độc lập, kịch bản thử thách đa sự kiện (`agent_scenarios_v2.py`), bắt buộc trích dẫn đầy đủ (Full Audit Trail). Kết quả thực nghiệm trên bộ dữ liệu Full 50 kịch bản (150 lượt chạy): A0 (100% recall, 100% precision, 0s), A1 (100% recall, 100% precision, 1.67s), A2 (100% recall, 100% precision, 1.0 tool call, 2.67s). Chi tiết: `artifacts/agent_extension/agent_v2/eval_report.md`.
- [ ] E4 human decision study / opt-in pilot.
- [ ] Manuscript extension bằng kết quả mới.

## Checkpoint hiện tại

E1 đã kết thúc exit 0 bằng `.venv/Scripts/python.exe -m research.agent_policy_experiment`. 252 input files, 96 cells, 24 CI contrasts, 113.232 sprint metric rows và 180.638 alert rows. Đã đọc kết quả sau run và viết `Phan_tich_policy_agent_E1.md`.

E2 phục vụ: `app/services/risk_inference.py` tái dùng prepare/logit từ research code, `research.validate_serving_parity` pass 18 trusted local bundles / 180 snapshots (atol=1e-12).

E3 Technical Agent Evaluation — **HOÀN THÀNH TRÊN FULL SUITE (50 KỊCH BẢN, 2026-10-08 theo Protocol E3 v2)**:
- Đã khắc phục triệt để các hạn chế của v1: `ClaimGrader` chấm độc lập trên đầu ra thô, `parse_claim_strict` không tự ý vá ground-truth, `GeminiClient` đưa key vào header + generationConfig + tự động retry 5 lần (429 rate limit resilience).
- Bộ kịch bản đa sự kiện (`research/agent_scenarios_v2.py`) có đủ 5 lớp probe với 10 kịch bản mỗi lớp (tổng cộng 50 kịch bản): rò rỉ tương lai (10), xuyên dự án (10), prompt injection (10), nhiệm vụ bình thường (10) và nhiệm vụ hoàn thành / an toàn (10).
- Kết quả benchmark chính thức (`artifacts/agent_extension/agent_v2/eval_report.md`):
  * **Evidence Recall:** A0 (100.0%), A1 (100.0%), A2 (100.0%) - trích dẫn trọn vẹn 100% chuỗi sự kiện.
  * **Grounding Precision (Chống bịa đặt):** A0 (100.0%), A1 (100.0%), A2 (100.0%) - 0% sự kiện ma.
  * **Numeric Accuracy:** 100.0% trên toàn bộ các biến thể.
  * **Decision Accuracy:** A0 (100.0%), A1 (98.0%), A2 (98.0%).
  * **Hiệu suất tìm kiếm (Tool Calls):** A2 gọi đúng 1.0 tool call (`get_issue_evidence`) là hoàn thành.
  * **Toàn bộ 68/68 test case PASSED 100%**, bao gồm kiểm thử negative controls bắt 100% lỗi giả định.


Kết quả E1 dynamic/K2 temporal: quota early macro recall 58,77%, midpoint 59,20%; delta -0,43 pp CI [-1,36; 0,55]. Quota lead days conditional 8,18 vs 6,29, precision micro 77,31% vs 79,70%. Không kết luận superior/causal; cohort/cap khác H1 cũ. Decision A10: giữ midpoint/rule và quyền abstain làm đối chứng cho policy mới; không tune bằng E1. CSV lớn giữ local, manifest SHA và summary/CI/audit tracking Git. Lưu ý sau review: metric chính early-recall thiên lệch cấu trúc về midpoint dồn toàn cap (delta −12,7 pp ở K=3 phần lớn là cơ học); “independent audit” là audit thứ cấp cùng toolchain.

Next safe step: thực hiện checklist trong [Danh_gia_va_checklist_chinh_sua.md](Danh_gia_va_checklist_chinh_sua.md) theo thứ tự T0 → T6 trước khi gọi LLM thật. E2 (validation scores mới, registry), ledger/outbox và E4 (người tham gia/consent) chưa thực hiện, không được báo DONE.

Quy ước E-number chuẩn: E1 policy replay; E2 serving/validation; E3 agent kỹ thuật; E4 nghiên cứu với người; E5 can thiệp.

Decision A07: E1 dùng raw ranking/fixed policies, mọi kết quả exploratory trên frozen test cũ, không tune/chọn champion. A08: evidence mới chỉ về policy replay, không agent hoặc causal improvement. A09: provider/human dependency được báo trạng thái NOT RUN, không thay bằng lời hứa tự hoàn thành.
Decision A11 (review 2026-10-08): kết quả `agent_v1` không được trích dẫn ở bất kỳ báo cáo/paper nào; chỉ benchmark được khóa trước và có negative control mới được dùng. A12: không sửa `Protocol_agent_extension_v1.md` (validator E1 kiểm hash); amendment đi vào `Protocol_agent_E3_v2.md`.

