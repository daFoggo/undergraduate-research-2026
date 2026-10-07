# Tiến độ nghiên cứu đến giai đoạn 4

Cập nhật: 2026-10-08 (Asia/Saigon). Nhánh: `research/stage-4`.

## Cách đọc và cập nhật

Trạng thái: TODO → RUNNING → DONE; BLOCKED chỉ khi thiếu điều kiện thực sự. Một mục chỉ DONE khi artifact tồn tại và đã kiểm tra. Mọi kết quả mô hình phải đi kèm dataset/config/seed/split, phiên bản mã, metric và giới hạn. Không đánh dấu xong bằng dự kiến hoặc bằng việc chỉ viết code.

| ID | Công việc | Trạng thái | Tiêu chí hoàn thành / bằng chứng |
|---|---|---|---|
| P1.1 | Kiểm kê dữ liệu và nguồn học thuật | DONE | `Data_card_TAWOS.md`, `Literature_and_methods.md`, audit CSV; review có phạm vi, không tuyên bố SOTA |
| P1.2 | Xác minh Sprint ID, membership và workflow | DONE | `artifacts/dataset`, 765 SQL samples; giới hạn workflow nghiệp vụ trong Protocol_v1 |
| P1.3 | Khóa protocol và quyết định phương pháp | DONE | `Protocol_v1.md`, `artifacts/protocol/config.json`, `lock.json` trước fit |
| P2.1 | Dựng cohort, nhãn và exclusion log | DONE | 28.746 commitments, 22.147 labeled (77,04%), eligibility/exclusion/mapping CSV |
| P2.2 | Snapshot 0/25/50/75% | DONE | 88.588 snapshots; `feature_dictionary.csv`, provenance timestamps |
| P2.3 | Kiểm thử temporal integrity | DONE | 10 tests và `data_validation.json`; cohort aggregate tính trước label exclusion |
| P3.1 | Split temporal và cross-project | DONE | 14 projects, manifest temporal/cross; purge nhãn chưa khả dụng |
| P3.2 | Baseline tần suất/quy tắc/tĩnh | RUNNING | Model/config/validation/prediction artifacts đang bắt đầu |
| P3.3 | Mô hình động, ablation và calibration | RUNNING | Cấu hình khóa trước fit, sigmoid validation-only |
| P4.1 | Đánh giá temporal và cross-project | TODO | PR-AUC/Brier/calibration và per-project metrics |
| P4.2 | Alert budget, uncertainty và sensitivity | RUNNING | Evaluator đã viết, test total-budget/dedup; chưa đánh giá matrix chưa đủ |
| P4.3 | Phân tích và đóng gói kết quả | TODO | Báo cáo RQ/H1, biểu đồ, lệnh tái lập, giới hạn |

## Decision log

| ID / ngày | Quyết định | Căn cứ | Dữ liệu đã xem | Ảnh hưởng |
|---|---|---|---|---|
| D00 / 2026-10-08 | Tự quyết định nghiên cứu trong phạm vi giai đoạn 1–4; ghi tất cả thay đổi | Người dùng ủy quyền | Đề cương/protocol | Không cần duyệt từng bước |
| D01 / 2026-10-08 | Giữ nguyên nguồn PostgreSQL, xử lý ở module research và artifact riêng | TAWOS đã nhập và kiểm đếm | Schema, counts | Tái lập, bảo toàn nguồn |
| D02 / 2026-10-08 | Chưa chạy mô hình trước khi khóa cohort và nhãn | Điều kiện go/no-go của protocol | Chưa xem model/test metric | Tránh thay estimand theo kết quả |
| D03 / 2026-10-08 | Done exact whitelist, ambiguous/unknown/history gaps không gán nhãn; không suy từ snapshot cuối | Chuỗi event và SQL audit | Outcome feasibility, chưa model metric | Ground truth archival, không có human workflow confirmation |
| D04 / 2026-10-08 | ≥50 sprint/project, ≥10 test; purge nhãn ở ranh giới, fit temporal riêng project | Yêu cầu 10 test với tỷ lệ 20%, overlap | Cohort counts | 14 project eligible |
| D05 / 2026-10-08 | Giữ ceil budget theo protocol; thêm floor/active-only/scope-change/seen-ID sensitivity | Sprint nhỏ và nhận biết Done có thể thổi phồng kết quả | Chưa model metric | Báo cáo cả nominal/realized budget |
| D06 / 2026-10-08 | Cấu hình CatBoost cố định, sigmoid validation-only; static/dynamic matched model | So sánh thông tin, không thay thuật toán giữa hai vế | Chưa model metric | Không lựa chọn tham số theo test |

## Nhật ký và checkpoint tiếp tục

- Đã đọc toàn bộ đề cương và protocol v0.1. PostgreSQL/API đang hoạt động; Git sạch trước khi tạo nhánh.
- Phát hiện cần xác minh: `sprint.id` khác `sprint.jiraid`; giá trị Sprint trong changelog không được mặc định là khóa database. Sprint ID cũng có thể trùng giữa repository.
- Protocol có điểm cần khóa: ≥20 sprint nhưng yêu cầu ≥10 sprint test với split 20%; cách làm tròn ngân sách và giới hạn 20%; xử lý sprint overlap và ngày nhãn train khả dụng.
- Data build hoàn tất: `python -m research.build`; protocol/split: `python -m research.splits`; full data verification: `python -m research.validate_data`. Các lượt build trước train đã cải thiện audit gaps, chưa xem test model metric.
- SQL sample audit 765 instance đối chiếu forward và reverse consistency đều pass. Không có inter-rater agreement hoặc Jira status-category metadata; giới hạn đã đăng ký rõ.
- Bước kế tiếp: `python -m research.train --experiment temporal`, sau đó cross_project; viết evaluator/plots/alert replay và báo cáo. Kiểm tra run hash khi resume; không ghi đè artifact khác hash.
- Huấn luyện đang chạy đồng thời bằng hai process: terminal session `4431` (temporal) và `10455` (cross_project), xác nhận live bằng polling; không khởi chạy bản thứ hai cùng experiment. Checkpoint mới nhất: temporal đã sang CONFSERVER, cross_project đang CONFCLOUD.
- Evaluator yêu cầu đủ 672 prediction files trước khi tính test metrics. Code ở `research/evaluate.py`; test sequential budget giữ tổng cap toàn sprint, deduplicate issue.
- Protocol/data checkpoint đã commit `2f3a73f`. Code evaluator, environment và các doc mới đang tiếp tục hoàn thiện. Còn thiếu kết quả thực nghiệm đầy đủ, plot/analysis report và completion audit; goal chưa hoàn thành.
- Verification mới nhất: 11 tests pass, `git diff --check` pass. Runtime thực tế Python 3.12.10 và 88 installed distributions ghi ở `artifacts/environment/runtime.json`. Script split có guard chống ghi đè lock khi prediction đã tồn tại.

## Quy tắc tiếp tục khi đổi context

Đọc file này, protocol đã khóa, decision log và Git diff trước khi tiếp tục. Kiểm tra tiến trình đang chạy, không khởi chạy lại thí nghiệm đã có artifact hợp lệ. Cập nhật checkpoint trước thao tác dài hoặc khi context gần đầy. Lưu tiến độ trong repo thay vì chỉ dựa vào lịch sử chat.

## Nguồn đã kiểm tra

| ID | Nguồn | Phạm vi sử dụng | Đã đọc |
|---|---|---|---|
| C01 | [TAWOS repository](https://github.com/SOLAR-group/TAWOS) | v1.1, schema, UTC, changelog, terms/license | 2026-10-08 |
| C02 | [Tawosi et al., MSR 2022](https://arxiv.org/abs/2202.00979) | Nguồn dataset; snapshot bài báo khác v1.1 | Abstract/metadata, 2026-10-08 |
| C03 | [scikit-learn calibration](https://scikit-learn.org/stable/modules/calibration.html) | Calibration phải fit trên dữ liệu ngoài train/test | Documentation, 2026-10-08 |

TAWOS dùng cho nghiên cứu theo terms nguồn; không tái nhận diện người đóng góp. Sản phẩm giai đoạn 4 là mô-đun/đánh giá nghiên cứu, chưa phải kiểm chứng tác động can thiệp trong doanh nghiệp.
