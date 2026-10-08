# Đánh giá lại nghiên cứu, benchmark và checklist chỉnh sửa

Ngày: 2026-10-08. Người review: agent thứ hai, độc lập với agent đã thực hiện các batch trước. Tài liệu này (1) ghi kết quả đánh giá, (2) liệt kê việc cần sửa, (3) là checklist bàn giao cho agent chuyên trách code. Agent đọc file này **không được** coi các nhận định ở đây là đã kiểm chứng hơn code: hãy tự chạy lại phần kiểm tra được ghi trong từng mục.

## 0. Phạm vi review và những gì chưa review

**Đã đọc và đối chiếu:** đề cương; `Protocol_v1`, `Protocol_agent_extension_v1`; báo cáo giai đoạn 4, thảo luận, completion audit, tiến độ nghiên cứu/agent, phân tích E1; deep research agent (đã mở thử 3 trang arXiv S04–S06 để xác nhận bài tồn tại, tiêu đề khớp); plan `docs/plans/2026-10-08-proactive-sprint-agent.md`; code `research/{build,replay,splits,train,metrics,evaluate,agent_policy,agent_policy_experiment,agent_scenarios,agent_evaluate}.py`, `app/services/{agent_context,agent_runner,evidence_verifier,gemini_client,risk_inference}.py`; test agent; artifact `agent_v1/*`, `policy_v1/contrasts.csv`, `posthoc_comparisons.csv`; abstract/conclusion bản LaTeX. Đã chạy `pytest tests -q`: **54 passed** (`Agent_research_progress.md` ghi 51 ở checklist nhưng 54 ở checkpoint — xem F-D3).

**Chưa review (không được coi là đã kiểm chứng bởi tài liệu này):** `research/{validate_data,validate_predictions,validate_agent_policy,validate_serving_parity,final_audit,report,analysis,posthoc}.py`, SQL migration PostgreSQL, 14 test còn lại của phase 4, các figure, bản LaTeX ngoài abstract/conclusion, tính đúng của các con số trong `summary.csv` (không tính lại). Không rebuild dataset, không retrain, không gọi LLM.

## 1. Kết luận

| Lớp | Đánh giá | Dùng được ở mức nào |
|---|---|---|
| Giai đoạn 1–4 (dữ liệu, protocol, split, mô hình, đánh giá) | **Nhìn chung vững**, caveat trung thực. Có vài vấn đề diễn giải/đặt tên (mục 2) cần nêu rõ hơn, không có dấu hiệu leakage thời gian trong phần code đã đọc | Giữ nguyên kết quả đóng băng; bổ sung caveat |
| E1 — policy replay | Thiết kế cẩn thận (selection không thấy `y`, cap/dedup được assert). Nhưng metric chính thiên lệch về cấu trúc và “audit độc lập” không độc lập | Exploratory, mô tả; không dùng để chọn policy |
| E2 — serving parity | Parity mẫu 18 bundle/180 snapshot hợp lý; còn thiếu rất nhiều | Chỉ chứng minh adapter tái hiện được suy luận nghiên cứu |
| **E3 — benchmark agent** | **Không hợp lệ.** Kết quả “100% mọi chỉ số, chi phí $0” là hệ quả của cách đo, không phải bằng chứng về agent. Tiến độ ghi `[x]` là sai | **Không dùng** cho bất kỳ kết luận nào, kể cả trong báo cáo/paper |
| Ledger/outbox, dashboard, delivery | Chưa làm | — |
| Nghiên cứu với người (E4) | Chưa làm | — |

Lý do chính khiến agent trước đó bị nghi ngờ là có cơ sở ở E3: benchmark tự chứng minh mình đúng. Phase 4 thì không rơi vào lỗi đó.

## 2. Phát hiện — giai đoạn 1–4 và E1/E2

Mức độ: **H** = ảnh hưởng kết luận/độ tin cậy; **M** = cần sửa để diễn giải đúng; **L** = nên làm.

| ID | Mức | Phát hiện | Bằng chứng | Hành động |
|---|---|---|---|---|
| P4-1 | M | Headline H1 (+8,90 pp) so dynamic với static **không thể thấy trạng thái Done tại landmark**. Phần lớn lợi ích đến từ nhận biết “đã xong”. Trên issue còn mở chỉ +2,59 pp (temporal), +2,03 pp (cross); dynamic vs rule +2,13 pp CI [−0,33; 4,60]; sequential vs static +1,30 pp CI [−0,46; 3,21]. Paper và `Thao_luan_ket_qua.md` đã nói rõ, nhưng `Bao_cao...giai_doan_4.md` mục “Kết quả chính” mở bằng con số 8,9 pp và chỉ trỏ sang thảo luận cho caveat | `Thao_luan_ket_qua.md` mục “Lợi ích trên công việc còn mở”; `posthoc_comparisons.csv`; `evaluate.py` dòng 107; `train.py` dòng 112 (rule dùng `dynamic_is_done`) | Không đổi kết quả đóng băng. Mọi tài liệu mới/tóm tắt phải đặt con số open-only và dynamic-vs-rule cạnh con số 8,9 pp (đã làm ở đề cương và tài liệu này; **không sửa** báo cáo giai đoạn 4 vì `final_audit.py` kiểm tra nó) |
| P4-2 | M | Nhãn “Recall@20%” gây hiểu nhầm: `ceil(0,2·n)` cho ngân sách thực **41,54%** (macro) / 25,81% (micro) ở temporal. Báo cáo đã ghi, nhưng tên metric vẫn là “Recall@20%” ở protocol/config | `splits.py` dòng 20, `Protocol_v1.md`; `Thao_luan_ket_qua.md` | Mọi sản phẩm mới dùng K nguyên + báo realized capacity; không dùng tên “@20%” khi nói về ceil |
| P4-3 | M | n dùng để tính ngân sách là số instance **đã có nhãn** (loại unknown/history gap dựa trên thông tin cuối sprint). Khi chạy thật, capacity phải dựa trên cohort as-of, không biết nhãn nào sẽ bị loại | `metrics.py` dòng 20–22; `Protocol_agent_extension_v1.md` (đã ghi caveat) | E2 và sản phẩm phải tính n từ cohort tại thời điểm dự báo; thêm sensitivity “n as-of” nếu dữ liệu cho phép |
| P4-4 | M | Bootstrap temporal lấy sprint làm đơn vị độc lập, bỏ qua tương quan trong project/issue lặp qua sprint; CI có thể hẹp. Đã có `project_weighted_exploratory` nhưng chỉ ở một điểm | `metrics.py` `paired_bootstrap`; `evaluate.py` dòng 117–140 | Thêm bootstrap hai tầng (project → sprint) làm sensitivity cho H1 và các contrast E1. Không thay H1 đã đăng ký |
| P4-5 | M | Baseline tĩnh là straw man cho câu hỏi “lịch sử có giúp không”: static đóng băng tại t₀ nhưng được chấm tại landmark. Baseline mạnh hơn (static + `is_done_at_landmark`, hoặc rule + logistic nhỏ) giúp cô lập giá trị của lịch sử. Sequential policy đã lọc Done cho cả static nên phần nào đã bù | `Thao_luan_ket_qua.md` dòng 47 | Thêm baseline “static + Done-at-landmark” làm phân tích post-hoc mới (namespace mới, ghi rõ không thay H1) |
| P4-6 | L | “Independent audit” của E1 (`independent_audit.json`) do cùng toolchain/agent tạo; chỉ chứng minh nhất quán nội bộ, không phải kiểm toán độc lập | `Phan_tich_policy_agent_E1.md` | Đổi cách gọi thành “automated secondary audit (same toolchain)” trong mọi tài liệu mới |
| P4-7 | L | Chọn project theo số lớp (≥30 mỗi lớp…) trước khi fit: dùng thông tin nhãn cho eligibility. Đã khai báo “feasibility only”, không dùng metric | `splits.py` dòng 46–60 | Giữ; đưa vào threats-to-validity của mọi extension |
| P4-8 | L | 14/39 project đủ điều kiện, 77% nhãn có coverage, một seed, một cấu hình, không điều chỉnh multiplicity; Done whitelist và ngày sprint từ snapshot; chỉ sprint CLOSED (survivorship) | Báo cáo giai đoạn 4, mục threats | Đã được khai báo; nhắc lại, không cần sửa code |
| E1-1 | M | Metric chính (`early_recall` ≤ 0,5) **ưu tiên cấu trúc** midpoint “dồn toàn cap tại 0,5” so với quota (`ceil(cap·2/3)` đến 0,5). Delta −12,7 pp ở K=3 phần lớn là cơ học, không phải so sánh công bằng giữa hai policy | `agent_policy.py` dòng 51–58; `contrasts.csv` (k3: −0,127 temporal, −0,134 cross) | Khi nhắc E1, chỉ trình bày như trade-off phân bổ. Với E1 v2, thêm frontier recall–earliness hoặc metric khớp lượng capacity |
| E1-2 | L | Hash protocol E1 được kiểm trong `validate_agent_policy.py` dòng 22 | `research/validate_agent_policy.py:22` | **Cấm sửa** `documents/Protocol_agent_extension_v1.md` (làm hỏng validator). Mọi amendment đi vào file mới |
| E2-1 | M | Parity chỉ trên 180 snapshot mẫu, một fold cố định (XD), không có validation scores mới → chưa có cơ sở chọn calibration/threshold cho triển khai | `artifacts/agent_extension/serving_parity.json` | Task E2 trong checklist |

## 3. Phát hiện — E3 benchmark agent (nghiêm trọng)

Phần này là nội dung chính của review. Mỗi mục kèm vị trí code để kiểm chứng lại.

| ID | Mức | Phát hiện | Vị trí |
|---|---|---|---|
| E3-1 | **H** | **Metric được gán cứng.** `grounding_pass`, `numeric_pass`, `safety_pass` đặt `True` ngay khi run “completed”; chỉ đổi khi có exception. Vì `verify_claim` luôn `raise` thay vì trả `valid=False`, nên `valid` luôn `True` với run completed. Bảng “100% pass/grounding/numeric/safety” **đúng theo cấu trúc**, không phản ánh chất lượng | `research/agent_evaluate.py` dòng 56–66, 281–286; `evidence_verifier.py` dòng 63–98 |
| E3-2 | **H** | **Mẫu số bị lọc.** Mọi tỷ lệ chỉ tính trên `status=='completed'`; run bị verifier chặn hoặc lỗi provider bị loại khỏi mẫu số → survivorship. Pass rate không thể <100% theo cách tính | `agent_evaluate.py` dòng 272–286 |
| E3-3 | **H** | **Đầu ra mô hình bị sửa trước khi chấm.** `_extract_and_normalize_claim` điền số liệu từ ground truth khi JSON hỏng/sai kiểu (`risk_score`, `reported_inactive_days`), tự thêm **toàn bộ evidence_ids** nếu mô hình không trích dẫn, tự đặt `kind`, `cutoff`, `summary`. Lỗi của LLM bị che; verifier chỉ thấy bản đã sửa | `app/services/agent_runner.py` dòng 21–99 |
| E3-4 | **H** | **A2 hết bước vẫn “pass”.** Nếu vòng lặp tool hết `max_steps` mà mô hình chưa trả text cuối, claim được dựng từ `''` + evidence thật → claim hợp lệ do mã tạo ra, không phải do mô hình | `agent_runner.py` dòng 295–296 |
| E3-5 | **H** | **Dữ liệu kịch bản thoái hóa.** Mỗi scenario có **1 issue, 1 event** (status tại đúng `cutoff`), mô tả giả `Archival task X in project Y`. Không có timeline thật, không có issue khác trong sprint, không có event tương lai → test future-leak/cross-project/injection không bao giờ được kích hoạt. “Tool use” của A2 luôn là gọi duy nhất 1 tool có ý nghĩa (`tool_choice='required'` ở bước 1); A1 và A2 nhận cùng dữ kiện → không đo được giá trị của tool | `agent_scenarios.py` dòng 28–49; `agent_runner.py` dòng 244; `agent_context.py` dòng 48–55 |
| E3-6 | **H** | **Mẫu thiên lệch và quá nhỏ.** 10 kịch bản (kế hoạch: dev ~30, locked ~120), lấy ngẫu nhiên từ alert của policy midpoint/K=2/dynamic (toàn ca rủi ro cao). Không có ca no-action, dữ kiện thiếu/mâu thuẫn/lỗi thời, injection, tool lỗi. `ground_truth_y` được tải nhưng không dùng. Dùng tên dự án/issue ID thật (nguy cơ mô hình nhớ dữ liệu công khai) | `agent_scenarios.py` dòng 26, 64–88 |
| E3-7 | **H** | **Không có negative control.** Chưa có thử nghiệm nào chứng minh verifier/guard chặn được lỗi cố ý ở mức pipeline (chỉ 5 unit test đơn lẻ trên verifier). Câu “Mọi vi phạm đều bị phát hiện và ngăn chặn” trong `eval_report.md` không có bằng chứng | `agent_evaluate.py` dòng 313; `tests/test_evidence_verifier.py` |
| E3-8 | **H** | **Kiểm tra an toàn quá yếu.** “Causal safety” = 5 chuỗi con tiếng Anh (`definitely cause`, `guaranteed to`, …) trên `summary`+`suggested_checks`; dễ bị lách (“will cause”, “due to”, “because the assignee…”). Chỉ kiểm tra số `risk_score` (±0,05) và `inactive_days` (±0,1); không kiểm số/trạng thái/ngày xuất hiện **trong văn bản summary**, không kiểm `unknowns`. Semantic entailment không được đo (plan đã nói không được coi là solved) | `evidence_verifier.py` dòng 48–54, 77–96 |
| E3-9 | **H** | **Chi phí/độ trễ không thật.** `cost: 0.0` gán cứng trong client; bảng báo cáo in cố định `$0.00`; token có trong `usage` nhưng không đưa vào `results.csv`; A0 latency 0 là đo của hàm template. Không có p50/p95, không có số token | `gemini_client.py` dòng 157–161; `agent_evaluate.py` dòng 304–306; `agent_runner.py` dòng 140 |
| E3-10 | **H** | **Không khóa trước khi chạy (vi phạm protocol E3).** Không có rubric/prompt/provider/decoding/scenario lock hash, không có commit protocol trước run, không có 3 lần lặp, không có phương sai. Cache kết quả cũ (`cached_traces`) dùng lại bất kể prompt/model đổi → trộn kết quả từ cấu hình khác nhau; thư mục output bị ghi đè (E1 thì từ chối ghi đè) | `agent_evaluate.py` dòng 112–147; `Protocol_agent_extension_v1.md` mục E3 |
| E3-11 | **H** | **Tham số giải mã không được đặt.** `max_tokens` được truyền nhưng `GeminiClient.complete` bỏ qua; payload không có `generationConfig` (temperature, response MIME/schema, thinking budget). Nghĩa là “decoding tracked” trong protocol không đúng; kết quả không tái lập được. API key nằm trong query string URL | `gemini_client.py` dòng 48–49, 95–108 |
| E3-12 | M | **Provenance mô hình không kiểm chứng được trong repo.** Tên `gemini-3.5-flash-lite` và tuyên bố “Top 14 leaderboard τ²-Bench, 76,9%” chỉ xuất hiện trong `Agent_research_progress.md`, không có nguồn/ảnh chụp/URL; deep research cũng nói không lấy leaderboard làm bằng chứng. Review này không xác minh được | `gemini_client.py` dòng 7; `Agent_research_progress.md` dòng 23 |
| E3-13 | M | **Exception bị nuốt.** `validate_tool_call` bọc trong `try/except Exception: pass` rồi vẫn thực thi tool → lần gọi tool bị cấm không bị chặn/đếm; lỗi parse arguments được thay bằng issue mặc định | `agent_runner.py` dòng 258–268 |
| E3-14 | M | **Schema claim quá đơn giản.** Một `summary` tự do + danh sách evidence_ids chung; thiếu `claims[{text, evidence_ids, kind}]` như thiết kế. Không thể kiểm tra khẳng định nào được nguồn nào hỗ trợ | `evidence_verifier.py` dòng 28–37; deep research mục 6.2 |
| E3-15 | M | **Không có metric chất lượng/coverage/usefulness**, không có abstention, không so sánh A0 vs A1 vs A2 theo chất lượng nội dung (summary A0/A1 chỉ khác diễn đạt). Verifier-chặn-tất-cả sẽ đạt “an toàn” tuyệt đối | `agent_evaluate.py` |
| E3-16 | M | **Test phủ yếu.** `test_agent_evaluation.py` chỉ test A0 happy path. Không có test: tool timeout, tool injection, A2 hết bước, JSON hỏng, claim bị sửa, verifier trả invalid, cache stale. Plan Task 5 yêu cầu các test đó trước khi implement | `tests/test_agent_evaluation.py`; plan Task 5 |
| E3-17 | L | `max_steps=3` và `tool_choice='required'` ở bước đầu ép gọi tool; không đo “mô hình tự quyết định có cần tool không” | `agent_runner.py` dòng 239–246 |

## 4. Mâu thuẫn tài liệu cần dọn

| ID | Vấn đề | Trạng thái |
|---|---|---|
| F-D1 | `Agent_research_progress.md` đánh `[x]` E3 “với LLM thật … hoàn thiện, pilot benchmark hoàn tất” | **Đã sửa** thành `[ ]` kèm lý do (xem phần 6) |
| F-D2 | Quy ước E-number mâu thuẫn: `Protocol_agent_extension_v1.md` và plan: E3 = agent technical, E4 = human study. `Deep_research...` mục 9 dòng 239: E2 = policy/agent technical, E3 = human, E4 = causal | **Đã ghi chú** trong deep research; **quy ước chuẩn từ nay**: E1 policy replay; E2 serving/validation; E3 agent kỹ thuật; E4 nghiên cứu với người; E5 can thiệp. Đã dùng trong đề cương |
| F-D3 | Số test: một chỗ ghi 51, chỗ khác 54 | Hiện 54 passed (đã chạy). Khi sửa lại tiến độ chỉ ghi số đã chạy lại |
| F-D4 | `eval_report.md` (sinh tự động) chứa nhận xét tự khen không có bằng chứng và `$0.00` cố định | **Đã gắn banner “KHÔNG HỢP LỆ”**; sinh lại báo cáo mới trong namespace mới |
| F-D5 | `Deep_research...` dòng 3 vẫn ghi “chưa triển khai”; plan ghi “LLM provider chưa cấu hình” | Cập nhật khi có kết quả E3 v2; không sửa trước |

## 5. Đặc tả E3 v2 (để agent code thực hiện)

Mọi mục dưới đây là **yêu cầu**, không phải gợi ý. Tạo `documents/Protocol_agent_E3_v2.md` **trước** khi chạy bất kỳ LLM nào, commit, rồi ghi hash vào manifest của run. Không sửa `Protocol_agent_extension_v1.md`.

1. **Namespace mới** `artifacts/agent_extension/agent_v2/`, từ chối ghi đè (như E1). Kết quả `agent_v1/` giữ nguyên làm hiện vật “đã bị vô hiệu”, không xóa.
2. **Scenario có cấu trúc thật** (schema Pydantic, lưu JSONL, hash từng file):
   - Context nhiều issue trong sprint, timeline nhiều event có timestamp, bao gồm event **sau cutoff**, issue project khác, mô tả/comment có prompt injection, dữ kiện thiếu/mâu thuẫn/lỗi thời, ca no-action (issue đã Done/đủ tiến độ), ca tool lỗi/timeout.
   - Nguồn: (a) **archival** dựng từ timeline thật của TAWOS (cần truy vấn PostgreSQL, ẩn danh ID/tên project) và (b) **synthetic stress** do mã sinh có seed. Báo cáo hai nguồn riêng.
   - Dev ≈30, locked ≈120; chia **trước** khi chạy; locked không được xem khi chỉnh prompt. `y` không đi vào công cụ và không dùng để chấm tính đúng của giải thích.
   - Oracle cho từng scenario: tập facts đúng, tập evidence_ids hợp lệ, hành động bị cấm, expected-abstain.
3. **Schema claim mới:** `claims: list[{text, kind, evidence_ids, numeric_values}]`, `suggested_checks`, `unknowns`, `abstain: bool + reason`. Không có trường xác suất do LLM sinh.
4. **Parse nghiêm ngặt:** JSON schema/response schema của provider; nếu parse/validate lỗi → ghi `schema_violation`, **không sửa**, không điền từ ground truth. Hết bước tool → `incomplete`, tính là thất bại.
5. **Chấm điểm tách khỏi verifier runtime:** viết `grader` độc lập, chạy trên đầu ra thô, trả `valid=False` + danh sách lỗi (không raise). Kiểm tra: ID tồn tại và thuộc đúng issue/project/cutoff; **mọi số/trạng thái/ngày trong `claims[].text`** khớp oracle (trích bằng parser số/ngày, không chỉ so trường số); claim nhân quả/quyết định (danh sách mở rộng + kiểm tra mẫu “vì/do/because/due to/will cause” khi không có evidence); claim phủ định vô căn cứ (“không có blocker” vs “chưa có bằng chứng blocker”). Entailment ngữ nghĩa: chấm tay tối thiểu 2 người trên mẫu (hoặc ghi rõ “không đo”).
6. **Negative controls bắt buộc:** bộ lỗi cố ý (ID bịa, ID thuộc issue khác, số sai, ngày tương lai, claim nhân quả, tool bị cấm, injection thành công) chèn qua một “mô hình giả” để đo **recall của verifier/guard**; báo riêng với tỷ lệ lỗi trên đầu ra tự nhiên.
7. **Biến thể:** A0 (template), A1 (LLM một lượt), A2 (tool agent), A2-no-verifier và A2-no-ledger (sandbox). Cùng candidate/evidence/ngân sách tool/giới hạn token. `tool_choice='auto'` (không ép gọi tool); đo tỷ lệ gọi tool đúng/thừa/thiếu.
8. **Lặp ≥3 lần** mỗi (scenario × biến thể), seed/decoding cố định; báo trung bình, phương sai và kết quả theo scenario; tính “pass^k” hoặc độ nhất quán.
9. **Số đo thật:** token vào/ra, chi phí tính từ bảng giá đã ghi (hoặc “không áp dụng free tier” + ghi quota), p50/p95 latency, số lượt gọi tool, số retry/429. Không in chi phí cố định.
10. **Mẫu số đầy đủ:** mọi run (kể cả lỗi provider, schema_violation, incomplete, bị chặn) nằm trong mẫu số; báo `coverage = brief hợp lệ/tổng`, `abstain rate`, `blocked rate`.
11. **Chất lượng nội dung:** rubric có điều kiện (đủ facts quan trọng, unknowns đúng, bước kiểm tra phù hợp, không gây hại), chấm bởi người (≥2, kappa) trên mẫu; nếu chưa có người thì gọi kết quả là “deterministic technical audit”, không gọi là chất lượng.
12. **Khóa và ghi vào manifest:** hash protocol, scenario files, rubric, prompt (A1/A2), schema, provider + **model ID/version trả về từ API**, `generationConfig` (temperature, top_p, thinking budget, max output tokens, response schema), ngân sách tool, hash mã (`agent_runner`, `agent_context`, grader), phiên bản thư viện. Cache chỉ dùng khi hash khớp toàn bộ; khác → run mới.
13. **Provider:** chưa xác minh `gemini-3.5-flash-lite` — gọi API liệt kê model (`models.list`) và ghi kết quả vào manifest; dùng header `x-goog-api-key` thay vì query string; nếu model không có, báo `NOT RUN`/đổi model có ghi nhận, không suy diễn.
14. **Diễn giải:** nếu A0 ≈ A1/A2 về chất lượng và rẻ hơn → báo đúng như vậy. Không tuyên bố SOTA. Phân biệt “technical audit” (E3) với “hữu ích cho người dùng” (E4) và “giảm trễ” (E5).

## 6. Thay đổi tài liệu đã thực hiện trong lượt review này

| Tài liệu | Thay đổi |
|---|---|
| `documents/De_cuong_du_bao_som_rui_ro_sprint.md` | Thêm phần agent: tóm tắt, từ khóa, RQ-A/B/C, mục tiêu 4–7, mục 7 mới (agent, kiến trúc, đánh giá E1–E5, yêu cầu hợp lệ E3), mở rộng sản phẩm, đóng góp, phạm vi, kế hoạch (WP-A1–A4) và bảng trạng thái; thêm tài liệu tham khảo 6–11; đánh số lại 8–12 |
| `documents/Agent_research_progress.md` | Sửa E3 thành chưa đạt; ghi phát hiện và liên kết tài liệu này; loại bỏ khẳng định không có căn cứ; bổ sung quyết định A10–A12 |
| `artifacts/agent_extension/agent_v1/eval_report.md` | Gắn banner vô hiệu, không sửa dữ liệu |
| `documents/Deep_research_AI_agent_canh_bao_som.md` | Ghi chú quy ước E-number (mục 9) |
| `README.md` | Thêm liên kết tài liệu mới |

**Cố ý không sửa:** `Protocol_v1.md`, `Protocol_agent_extension_v1.md`, `Bao_cao_nghien_cuu_giai_doan_4.md`, `Thao_luan_ket_qua.md`, `Completion_audit.md`, `artifacts/protocol/*`, `artifacts/agent_extension/policy_v1/*`, bản paper — các file này được hash/kiểm toán bởi `validate_agent_policy.py` hoặc `final_audit.py`, hoặc là kết quả đóng băng. Paper hiện đã nêu đúng các caveat chính (open-only, rule cạnh tranh, ceil budget); chỉ cần cập nhật nếu thêm phân tích mới (P4-4, P4-5).

## 7. Checklist cho agent chuyên trách code

Quy tắc chung: đọc file này trước; làm theo thứ tự phụ thuộc; mỗi task có kiểm chứng riêng; không báo DONE nếu chưa chạy lệnh kiểm chứng và dán kết quả thực. Trước task nào chạm LLM thật, phải xong T0–T3. **Không** chạm `artifacts/protocol/*`, `artifacts/predictions/*`, `artifacts/models/*`, `artifacts/agent_extension/policy_v1/*`, `documents/Protocol_agent_extension_v1.md`. Mọi output mới vào namespace mới, từ chối ghi đè. Không commit secret (`.env` đã ignore). Lệnh test: `.venv/Scripts/python.exe -m pytest tests -q` (hiện 54 passed — không được giảm).

### Giai đoạn A — sửa nền tảng agent (không cần gọi LLM thật)

- [ ] **T0 — Khóa protocol E3 v2.** Tạo `documents/Protocol_agent_E3_v2.md` theo mục 5 (rubric, schema, chỉ số, mẫu số, quy tắc không-sửa-đầu-ra, ngân sách). Commit trước mọi run. *Kiểm chứng:* file tồn tại, hash ghi được vào manifest bởi runner.
- [ ] **T1 — Sửa `agent_runner` / bỏ normalizer che lỗi (E3-3, E3-4, E3-13, E3-17).** Parse nghiêm ngặt, không điền số từ ground truth, hết bước = `incomplete`, đếm tool bị cấm/arguments lỗi, `tool_choice='auto'`. *Test trước (phải fail trước khi sửa):* JSON hỏng → `schema_violation`; mô hình bịa số → không bị sửa; hết bước → `incomplete`; tool bị cấm → bị chặn **và** đếm; arguments lỗi → bị ghi nhận.
- [ ] **T2 — Schema claim mới + grader độc lập (E3-1, E3-2, E3-7, E3-8, E3-14, E3-15).** `claims[...]`, `abstain`; grader trả `valid=False`+lỗi (không raise); kiểm tra số/ngày/trạng thái trong text; mở rộng pattern nhân quả; không còn gán cứng `*_pass=True`; mẫu số gồm mọi run. *Test:* mỗi loại lỗi trong mục 5.5 có test đỏ→xanh; test “verifier chặn hết” đạt safety nhưng coverage thấp được báo đúng.
- [ ] **T3 — Sửa `GeminiClient` (E3-9, E3-11, E3-12).** Áp `generationConfig` (temperature, top_p, max output tokens, thinking budget, response schema/MIME), trả về token thật và model version, đưa key vào header, thêm `list_models()`; không gán `cost=0.0` — trả `None` + bảng giá cấu hình. *Test:* mock xác nhận payload chứa `generationConfig`; `max_tokens` được tôn trọng; repr/exception không lộ key.
- [ ] **T4 — Scenario archival + synthetic (E3-5, E3-6).** Thư viện sinh scenario nhiều issue/nhiều event/event tương lai/cross-project/injection/no-action/tool lỗi; archival dựng từ timeline thật qua PostgreSQL (ẩn danh); chia dev/locked **trước**, lưu JSONL + hash; oracle cho từng scenario; `y` không vào context. *Kiểm chứng:* test future-leak, cross-project, injection thực sự được kích hoạt (assert số lần kích hoạt >0); đếm phân bố loại scenario.
- [ ] **T5 — Runner đánh giá v2 (E3-10).** Namespace `agent_v2`, từ chối ghi đè, manifest hash đầy đủ (mục 5.12), cache chỉ khi hash khớp, 3 lần lặp, ghi token/latency/retry/429, mẫu số đầy đủ, báo cáo theo scenario + phương sai, **không in chi phí cố định**, báo `NOT RUN` khi thiếu provider.
- [ ] **T6 — Negative-control harness (E3-7).** “Mô hình giả” chèn lỗi cố ý; báo recall của verifier/guard theo loại lỗi; chạy trong CI không cần mạng. *Kiểm chứng:* recall từng loại lỗi được báo cáo; lỗi nào lọt phải được ghi, không ẩn.

### Giai đoạn B — chạy đánh giá (cần provider)

- [ ] **T7 — Xác minh provider/model.** `models.list`, ghi model ID/version thật vào manifest; nếu `gemini-3.5-flash-lite` không tồn tại hoặc khác, ghi nhận và chọn model thay thế **trước** khi khóa. Xóa tuyên bố leaderboard không có nguồn khỏi tiến độ.
- [ ] **T8 — Dev run.** Chỉ dùng dev suite để chỉnh prompt; sau đó **khóa** prompt/rubric/hash. Ghi mọi lần chỉnh vào decision log.
- [ ] **T9 — Locked run.** A0/A1/A2 (+ ablation sandbox) × locked ≈120 × ≥3 lần. Không chỉnh gì giữa chừng; nếu lỗi hạ tầng → resume theo hash hoặc run mới, không trộn.
- [ ] **T10 — Báo cáo kỹ thuật.** Bảng theo biến thể: hallucination/claim, độ chính xác số, violation (cố gắng/thành công), end-state, coverage/abstain/blocked, nhất quán, token/chi phí/latency p50-p95, tỷ lệ gọi tool đúng/thừa/thiếu; phân loại lỗi; archival tách synthetic; chấm tay mẫu (nếu có người) kèm kappa. Kết luận chỉ trong phạm vi “technical audit”.

### Giai đoạn C — nền tảng sản phẩm/nghiên cứu còn thiếu

- [ ] **T11 — E2 validation scores.** Sinh validation/OOF scores mới (run mới, không sửa artifact cũ), chọn calibration/threshold **chỉ** trên validation; registry không chọn fold theo hiệu năng test; capacity dựa trên cohort as-of (P4-3).
- [ ] **T12 — E1 v2 (tùy chọn).** Policy có threshold+abstain được khóa trên validation; contrast công bằng về capacity (E1-1) hoặc frontier recall–earliness–false alerts; bootstrap hai tầng (P4-4).
- [ ] **T13 — Phân tích bổ sung phase 4 (post-hoc, namespace mới).** Baseline “static + Done-at-landmark” (P4-5) và bootstrap hai tầng cho H1/sensitivity (P4-4); không đổi H1, không đổi model/calibrator; không sửa file bị audit.
- [ ] **T14 — Ledger/outbox.** Migration trên DB test riêng (không `tawos_raw`): atomic reserve cap, unique initial alert, snooze bền vững, reconciliation gửi mơ hồ, dry-run mặc định. Test: đồng thời, restart, timeout sau gửi. Đọc skill `postgres` trước khi viết SQL.
- [ ] **T15 — Agent endpoint/dashboard.** Chỉ sau khi có auth/project scoping; chưa public endpoint trước đó.
- [ ] **T16 — Human study protocol** (`documents/Agent_human_study_protocol.md`) chỉ khi có khả năng tuyển người; không tạo participant/consent giả.

### Giai đoạn D — dọn tài liệu sau khi có kết quả thật

- [ ] **T17 — Cập nhật `Agent_research_progress.md`, `Research_progress.md` (mục agent), `Reproduce_research.md`** bằng lệnh/số liệu/hash của run thật; ghi E-number theo quy ước chuẩn.
- [ ] **T18 — Cập nhật paper chỉ bằng evidence đã chạy** (nếu thêm P4-4/P4-5 hoặc E3 v2); không tuyên bố SOTA/causal.
- [ ] **T19 — Chạy lại `final_audit.py`, `validate_agent_policy.py`, `validate_serving_parity.py`** để chắc không phá artifact cũ; `git diff --check`.

### Điều kiện hoàn thành tối thiểu (không được báo hoàn tất nếu thiếu)

1. T0–T6 xong với test đỏ→xanh được ghi lại. 2. Negative-control cho từng cơ chế an toàn có số thật. 3. Locked run có ≥3 lần lặp, mẫu số đầy đủ, manifest hash đầy đủ. 4. Báo cáo nêu rõ phạm vi: kỹ thuật, chưa đo hữu ích với người dùng, chưa đo can thiệp. 5. Không còn số liệu hardcode (`cost`, `*_pass`) trong runner/báo cáo.

## 8. Câu hỏi cần chủ dự án quyết định

1. Provider/model dùng cho E3 v2 (giữ Gemini free tier và chấp nhận rate limit/nguy cơ đổi model, hay chọn model có version cố định và chi phí đo được)?
2. Có người chấm tay độc lập (≥2) cho mẫu E3/E4 không? Nếu không, báo cáo chỉ gọi là “deterministic technical audit”.
3. Có chấp nhận ẩn danh hóa dự án/ID TAWOS trong scenario archival để giảm rò rỉ pretrain không? (khuyến nghị: có.)
4. Có kênh tuyển người cho E4 trong thời gian đề tài? Nếu không, bỏ E4 khỏi phạm vi và ghi vào giới hạn.
