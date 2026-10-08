# Tiến độ nghiên cứu agent cảnh báo chủ động

Ngày 2026-10-08. Tiếp nối phase 4 nhưng không sửa study frozen. Người dùng yêu cầu deep research theo SOTA nhất có thể, tạo lộ trình và thực hiện đánh giá theo quy trình trước.

Format mỗi batch: mục tiêu; protocol/version/hash; trạng thái; commands; evidence/metrics; limitations; quyết định; next step. DONE chỉ khi có verification.

- [x] Research nhiều vòng và tổng hợp 15 nguồn chính, đánh dấu mức đọc và giới hạn.
- [x] Thiết kế ba lớp model/controller/tool agent, baselines/ablation và human study.
- [x] Protocol E1 và lộ trình triển khai được viết trước metric mới.
- [x] E1 policy replay, CI, audit và báo cáo (post-hoc exploratory).
- [ ] E2 validation/serving parity và chọn calibration cho deployment.
- [ ] E3 technical agent benchmark với LLM thật.
- [ ] E4 human decision study / opt-in pilot.
- [ ] Manuscript extension bằng kết quả mới.

## Checkpoint hiện tại

E1 đã kết thúc exit 0 bằng `.venv/Scripts/python.exe -m research.agent_policy_experiment`. 252 input files, 96 cells, 24 CI contrasts, 113.232 sprint metric rows và 180.638 alert rows. Đã đọc kết quả sau run và viết `Phan_tich_policy_agent_E1.md`. Không tìm thấy tên env API-key LLM phù hợp ở session; `.env` không tồn tại. Không in secret và chưa gọi provider trả phí. E1 offline không cần provider. Không sửa `papers/sprint-risk/main.pdf` đang dirty từ trước. Skill writing-plans/TDD/verification áp dụng để task nhỏ có bằng chứng; không dùng Obsidian workflow vì output trong repo.

Trong lúc E1 chạy, đã làm một phần E2: `app/services/risk_inference.py` tái dùng prepare/logit từ research code, không sửa trainer. `.venv/Scripts/python.exe -m research.validate_serving_parity` pass 18 trusted local bundles / 180 snapshots ở fold XD cố định, ba main scorers, hai experiment và ba landmark, raw/calibrated parity atol=1e-12. Artifact: `artifacts/agent_extension/serving_parity.json`. Không có production champion, serving registry, inference endpoint, live feature parity hay calibration đích. Docker API base chưa được bổ sung research runtime cho serving.

Verification: 29 tests pass trước output audit; sau đó thêm một regression test timestamp. Audit lần đầu lỗi parsing fractional seconds, đã isolate parser bằng systematic-debugging, sửa `format='ISO8601'` ở audit-only, regression test pass. Independent audit pass trên toàn alert output, hashes/prefix eligibility/counts đều đúng. Không sửa policy/evaluator source sau run. Có một warning Starlette/httpx deprecation từ suite cũ.

Final checkpoint verification: full suite **30 passed**, independent policy audit PASS, serving parity audit PASS, compileall và `git diff --check` pass. Giữ thay đổi PDF có sẵn ngoài commit batch này.

Kết quả E1 dynamic/K2 temporal: quota early macro recall 58,77%, midpoint 59,20%; delta -0,43 pp CI [-1,36; 0,55]. Quota lead days conditional 8,18 vs 6,29, precision micro 77,31% vs 79,70%. Không kết luận superior/causal; cohort/cap khác H1 cũ. Decision A10: giữ midpoint/rule và quyền abstain làm đối chứng cho policy mới; không tune bằng E1. CSV lớn giữ local, manifest SHA và summary/CI/audit tracking Git.

Next safe step: serving registry/as-of context và template/verifier sandbox theo plan, cùng validation scores mới. E3 LLM thực cần provider/model configuration, E4 cần người tham gia/consent; chưa thực hiện và không được báo DONE. Không có job E1 đang chạy cần resume.

Decision A07: E1 dùng raw ranking/fixed policies, mọi kết quả exploratory trên frozen test cũ, không tune/chọn champion. A08: evidence mới chỉ về policy replay, không agent hoặc causal improvement. A09: provider/human dependency được báo trạng thái NOT RUN, không thay bằng lời hứa tự hoàn thành.
