# Data card — TAWOS v1.1 và cohort nghiên cứu

Đóng băng dữ liệu thực nghiệm ngày 2026-10-08. Dữ liệu nguồn PostgreSQL schema `tawos_raw`; metadata nhập khẩu trong `research.dataset_imports`. [Nguồn chính thức](https://github.com/SOLAR-group/TAWOS), [dataset DOI](https://doi.org/10.5522/04/21308124), [bài giới thiệu](https://arxiv.org/abs/2202.00979).

## Nguồn và quyền sử dụng

TAWOS v1.1 là snapshot Jira của các dự án Agile mã nguồn mở. Repository nêu Apache 2.0 và terms dành cho nghiên cứu, tránh gây hại/tái nhận diện người đóng góp. Bản nghiên cứu này dùng ID chỉ để liên kết/audit; không dùng danh tính người dùng làm feature. Không phân phối lại dump SQL trong Git.

Checksum SQL gốc: `278984F788008C58D338E1F4AA195EAE8E5B15B4153E51C247659EF8465917F7`. Manifest nguồn: `artifacts/audit/source_manifest.csv`. Timestamp nguồn UTC theo mô tả TAWOS; cột PostgreSQL dùng timestamptz. Dữ liệu thời gian chủ yếu từ các năm trước 2021; ngày tải/chạy năm 2026 không biến dữ liệu thành quan sát hiện tại.

## Flow dữ liệu thực tế

| Bước | Số lượng |
|---|---:|
| Project nguồn | 39 |
| Sprint nguồn | 4.594 |
| Sprint CLOSED nguồn | 4.507 |
| Issue nguồn | 458.232 |
| Changelog nguồn | 9.253.419 |
| Commitments có membership trước đầu sprint sau audit ngày/membership | 28.746 |
| Commitments gán nhãn được | 22.147 |
| Outcome unknown/ambiguous/history gap | 6.599 |
| Coverage nhãn trong cohort | 77,04% |
| Sprint có instance gán nhãn | 2.555 |
| Snapshot 0/25/50/75% | 88.588 |
| Project đánh giá chính | 14 |
| Instance trong 14 project | 18.322 |
| Sprint trong 14 project | 1.962 |
| Sprint train / validation / test / purge | 1.165 / 383 / 397 / 17 |

Tỷ lệ không hoàn thành trong 14 project là 47,21%; 6,48% instance đã Done tại đầu sprint nhưng vẫn giữ theo cohort để ghi nhận cả trường hợp reopen. Có 926 instance mang dấu cancel/duplicate/invalid resolution và 1.592 instance đã bị remove khỏi sprint ở cuối sprint; các nhóm có thể giao nhau.

`project_eligibility.csv`, `exclusion_log.csv`, `label_mapping.csv` là bằng chứng từng bước, không chỉ số tổng. Cohort có thể nhỏ hơn số issue được gắn sprint ở snapshot: cần timestamp membership và đủ trạng thái lịch sử, không suy ngược từ final fields. Những issue không có Sprint changelog không vào cohort chính.

## Các lựa chọn dữ liệu

Map Sprint bằng `(project_id,jiraid)`. `sprint.id` khác `jiraid` ở mọi record; không có duplicate `(project_id,jiraid)` trong snapshot. Sprint references không có record được ghi log. Sprint duration 1–60 ngày, start từ 2000, CLOSED; các ngày bất thường không sửa tự động.

Nhãn dựa last observed status tại End_Date với exact terminal whitelist Done/Resolved/Closed/Complete. Giá trị mơ hồ và chuỗi thiếu transition không gán nhãn. Feature chỉ lấy prefix đến prediction time; không dùng final status/type/priority/estimate để điền ngược. Do đó mức missing/unknown của một số field cao: xem `artifacts/validation/feature_dictionary.csv`.

Phần tử cohort không biết outcome vẫn góp vào tiến độ/cohort size nếu membership đã biết. Việc loại nhãn không thay đổi aggregate feature. Đánh giá được thực hiện trên population có nhãn, nên vẫn có selection bias cần báo cáo.

## Kiểm tra và giới hạn

Đối chiếu SQL độc lập 765 instance từ 14 project, gồm hai lớp và scope changes; kiểm tra membership, nhãn và corroboration bằng FROM của event tiếp theo. Các check đều pass. SQL audit kiểm chứng cách đọc log, không xác nhận Jira workflow nghiệp vụ. Không có inter-rater agreement; status-category gốc không có trong schema.

Kiểm tra toàn bộ snapshot: unique issue–sprint–landmark, bốn landmark/instance, label nhất quán, provenance ≤ landmark, không còn history gap trong tập labeled, nhãn train/validation khả dụng trước partition sau. Unit tests kiểm tra multi-sprint, removal, reopen, unknown và bất biến với event tương lai.

Không phải mẫu đại diện cho mọi dự án Agile hoặc doanh nghiệp. Jira logs có thể thiếu record mà không để lại dấu chuỗi không khớp. Start/End là kế hoạch lưu trong snapshot; dataset không có lịch sử đổi chính ngày sprint, nên chưa chứng minh deadline lịch sử luôn đúng như người dùng nhìn thấy tại t0. Kết quả phụ thuộc giả định ngày sprint không bị chỉnh hồi cứu theo cách đáng kể; đây là threat to validity cần xác minh bằng dữ liệu live về sau.

Không dùng tác giả/assignee identity, không phân tích hiệu suất cá nhân. Kết quả ngoại tuyến đo khả năng xếp hạng và xác suất; không đo tác động cải thiện tiến độ do cảnh báo.
