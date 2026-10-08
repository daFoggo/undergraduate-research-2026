# Protocol mở rộng cảnh báo chủ động v1

Ngày: 2026-10-08. Khóa specification trước khi tính metric mới. Không phải external preregistration; nghiên cứu phase 4 đã được xem. Mọi kết quả trên test cũ là post-hoc exploratory, không confirmatory. Không sửa protocol/model/predictions phase 4.

## Batch E1 chạy ngay

Mục tiêu: đánh giá sensitivity của timing/capacity trên scorer cũ, không tuyên bố đã đánh giá LLM agent hoặc tác động can thiệp.

Input: frozen predictions của temporal/cross_project, scorer business_rule/static_catboost/dynamic_catboost, landmark .25/.5/.75, dùng p_raw để không phụ thuộc cross-project calibrator. Không fit/tune mới.

Population đánh giá: issue của evaluation cohort còn mở tại .25, giữ denominator này tới cuối. Unknown/history-gap đã bị loại trong archival cohort, không suy rộng sang mọi issue live. Candidate mỗi mốc là subset còn mở, chưa initial alert; không lọc bằng y. Outcome y giữ nghĩa recorded non-completion. Không có feature removed-as-of trong prediction nên batch này không giả vờ lọc scope removal; có thể nghiên cứu riêng sau.

Capacity: K=1,2,3, cap=min(K,n0); thêm floor(.2*n0) cho strict rate. n0 là toàn evaluation cohort tại .25 trước lọc active, không phải toàn cohort raw chưa có nhãn. Đây là labeled replay denominator và phải ghi caveat sản phẩm. Budget không tăng khi Done giảm. Chặn duplicate issue/sprint. Quota cumulative ceil(cap*j/3) ở j=1,2,3; single-midpoint toàn cap tại .5; early toàn cap .25; late toàn cap .75. Tất cả deterministic raw-ranking/hash tie, không threshold tuning. Chỉ quota-vs-midpoint dynamic là primary exploratory contrast; các scorer/budget/early/late contrasts là phụ, không multiplicity-adjusted.

Primary metric: early_recall = số y=1 thuộc active-at-.25 được alert trước hoặc tại .5 / toàn y=1 active-at-.25. Secondary: recall cuối kỳ; precision; FP/sprint; cap used/allocated; realized issue fraction; conditional lead days cho true alerts. Metrics undefined khi denominator=0 giữ NA, không đổi thành 0. Sprints không có active issue giữ trong capacity/FP summary với zero alerts. Ghi n_positive_sprints và zero-cap.

Temporal CI paired bootstrap 2000 sprint trên early_recall; cross CI bootstrap 14 project, equal weight project mean early_recall. Seed 20261008. Báo macro sprint/project và micro, sample-size và paired units. Dependency/repeated issue caveat kế thừa phase 4.

Validation bắt buộc: input unique issue/sprint/landmark; đủ ba mốc; y và end nhất quán; prediction_at không sau end và theo thứ tự; số p hữu hạn thuộc [0,1]; dynamic_is_done thuộc 0/1; không chọn Done; alert identity unique/cap; invariance khi hoán vị rows hoặc đổi y (selection không được đổi). Hash mọi input, code/config và output trong run manifest; output vào namespace mới, từ chối ghi đè.

## Batch E2 chưa chạy

Development/validation scores mới và validation window đích để chọn threshold/calibration. Không chọn bằng E1. Serving registry không chọn fold theo test performance; landmark inference trước. Test/validation/data manifest riêng có exact hash.

## Batch E3 chưa chạy

Agent technical suite A0 template, A1 narrator, A2 bounded tool agent; same candidates/evidence/permissions; 3 repetitions. Hard safety guards bật trong mọi variant, ablation verifier/ledger chỉ sandbox. Rubric, scenario split, prompts, provider/model ID, decoding và call budget phải khóa trước LLM evaluation. Nghiên cứu SOTA-inspired theo [deep research](Deep_research_AI_agent_canh_bao_som.md), không lấy benchmark khác làm điểm số của sản phẩm mình.

## Batch E4 chưa chạy

Human decision study và opt-in pilot cần consent, participants và protocol/power-feasibility riêng. Không thay người thật bằng simulated LLM rồi kết luận giảm trễ. Không gửi thông báo external ở batch E1–E3.
