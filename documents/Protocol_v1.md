# Protocol thực nghiệm v1 — dự báo outcome issue trong sprint

Ngày đăng ký: 2026-10-08. Chưa chạy mô hình hoặc xem metric test khi đăng ký. Config thực thi và checksum nằm trong `artifacts/protocol/config.json`, `lock.json`; manifest split là nguồn chính xác cho các phân vùng.

## Câu hỏi và phạm vi suy luận

RQ chính: tại 50% thời lượng sprint, lịch sử thực thi có cải thiện macro Recall@20% so với thông tin tại đầu sprint? Đơn vị là issue–sprint, lớp dương là chưa hoàn thành ở End_Date. H1 được ủng hộ khi chênh lệch ghép cặp dynamic CatBoost − static CatBoost dương và CI bootstrap 95% không chứa 0. RQ phụ: temporal transfer, held-out project transfer, calibration và độ sớm của cảnh báo.

Cohort là các issue có bằng chứng changelog membership trước/đúng Start_Date. Đây là phạm vi ghi nhận trong tracker, không chứng minh cam kết được ký/chấp thuận bởi con người. TAWOS v1.1 có 39 project, 458.232 issue. Không dùng liên kết snapshot để suy ngược membership. Chỉ nghiên cứu ngoại tuyến; không kết luận cảnh báo làm giảm trễ.

## Cohort và nhãn

- Sprint CLOSED, start/end hợp lệ, start từ năm 2000, thời lượng 1–60 ngày. Start_Date làm mốc; Activated_Date được audit riêng.
- Sprint changelog là tập ID Jira; map bằng `(project_id,jiraid)`, không bằng khóa database. Lấy `to_value` của event cuối trước/đúng start. Issue phải tồn tại trước start. Các sprint không có record được loại và ghi log.
- Không dựng trạng thái từ snapshot cuối hoặc `from_value` của event tương lai. Trước status event đầu tiên, trạng thái là unknown.
- Nhãn theo status event cuối trước/đúng end. Done whitelist: Done/Resolved/Closed/Complete, không phân biệt chữ hoa/thường. Mapping được xuất theo project và phân bố trạng thái.
- Accepted/Implemented/Deployed/Released/WAD mơ hồ được loại khỏi nhãn chính; không mặc định hoàn thành. Unknown không gán thành lớp âm/dương.
- Chuỗi trạng thái/membership không liên tục được đánh dấu unknown/loại theo chất lượng. Nếu start/end nằm trong khoảng thiếu event được xác nhận bởi hai record không khớp, loại tương ứng. Đây là audit hồi cứu chất lượng, không là feature.
- Giữ issue bị remove/reopen/cancel trong cohort chính; outcome theo status cuối sprint. Sensitivity loại cancel/remove, kiểm tra nhãn Closed-only và carried-over IDs.
- Tổng hợp tiến độ/cohort size trên toàn bộ cohort có bằng chứng, trước khi loại outcome NA. Ngân sách đánh giá dùng số instance có nhãn; báo cáo coverage để thấy chọn mẫu.

## Đặc trưng

Snapshot 0/25/50/75%. Baseline tĩnh được đóng băng tại start: tuổi issue, thời lượng sprint, trạng thái quan sát, số chuyển trạng thái, thời gian trong trạng thái, số hoạt động ở các field chọn, inactive time, số lần đổi assignee/priority/story-point, priority/type/estimate nếu có event, tiến độ cohort ban đầu. Thông tin lịch sử trước sprint được phép và làm baseline mạnh hơn.

Dynamic thêm cùng nhóm feature cập nhật đến landmark, tỷ lệ cohort done đến landmark. Event counts chỉ tính Sprint/status/resolution/priority/issuetype/assignee/Story Points. Không gọi đó là tổng mọi hoạt động. Không dùng text, người dùng, issue/project/sprint ID, trạng thái cuối, resolution cuối, thời gian tổng vòng đời. Field ID chỉ dùng join/group/audit. Timestamp provenance chỉ dùng kiểm tra, không đưa vào mô hình.

Static priority/type/estimate có thể missing nhiều vì không suy từ giá trị snapshot không có lịch sử. Báo cáo missingness; không diễn giải các field unknown như đặc trưng hoàn chỉnh của tracker.

## Chia dữ liệu

Project chính có ≥50 sprint với cohort gán nhãn, ≥200 instance, ≥30 mỗi lớp. Ngưỡng 50 giải quyết yêu cầu ≥10 sprint test ở tỷ lệ 20%; không thay đổi ngưỡng theo model metric. Train/validation/test theo 60/20/20 sprint Start_Date trong từng project; cùng timestamp phải cùng partition. Purge train có End_Date ≥ validation start, purge validation có End_Date ≥ test start để nhãn sẵn có khi fit/calibrate. Train ≥10 mỗi lớp; validation/test ≥5 mỗi lớp, test ≥10 sprint. Các project khác mô tả trong eligibility.

Temporal fit riêng từng project, không pool dự án có ngày train tương lai so với test của dự án khác. Mọi landmark cùng issue–sprint có cùng partition.

Cross-project leave-one-project-out trên các project đủ điều kiện; 20% project còn lại (tối thiểu 2) làm validation bằng seed cố định; toàn bộ project test không tham gia fit/calibrate. Đây là đánh giá chuyển miền với lịch sử archival, không phải mô phỏng lịch triển khai toàn cầu. Nếu cần kết luận chuyển miền theo thời gian thực, cần thêm thiết kế cutoff toàn cục.

## Mô hình và hiệu chuẩn

Frequency train-only; business rule dựa trạng thái/inactivity; Logistic Regression tĩnh; CatBoost tĩnh và động với cùng cấu hình; ablation động không có aggregate cohort. CatBoost 400 trees, depth 5, learning rate .05, L2 5, seed 20261008, CPU 4 threads. Cấu hình cố định trước test, không tuning theo test. LR chuẩn hóa/one-hot/imputation fit train-only. Không class-weight mặc định để giữ xác suất phản ánh prevalence.

Sigmoid calibration fit trên validation bằng logit xác suất; mô hình base chỉ fit train. Báo cáo raw và calibrated. Nếu validation không đủ hai lớp, identity fallback và ghi rõ. Không chọn calibration bằng test.

## Metric, ngân sách và độ bất định

Primary Recall@20% macro theo sprint tại 50%; budget `ceil(q*n)` như protocol đề xuất, báo cáo budget thực tế vì sprint nhỏ có thể vượt tỷ lệ danh nghĩa. Sensitivity `floor(q*n)` đo giới hạn tỷ lệ nghiêm ngặt. Tie-break bằng hash issue–sprint độc lập nhãn, giống nhau giữa mô hình.

Budget q=10/20/30%; PR-AUC dùng average precision (không trapezoidal PR-AUC), Brier, ROC-AUC phụ, calibration intercept/slope và reliability plot. Precision, false alerts/sprint, lead time. Sprint không dương: recall NA nhưng giữ precision/false alerts. Lead time chỉ ở true alerts và báo cáo coverage; không diễn giải thời gian của toàn bộ rủi ro.

Paired bootstrap 2.000 lần theo sprint temporal và project cross-project. Báo cáo per-project để tránh dự án lớn chi phối. Sensitivity active-only loại issue đã Done tại landmark: giúp phân biệt dự báo rủi ro thực sự với nhận biết công việc đã hoàn thành. Mô phỏng cảnh báo tích lũy phải deduplicate và giữ tổng ngân sách mỗi sprint, không cộng ngân sách mỗi landmark.

## Giới hạn audit

Kiểm tra tự động trên toàn bộ timestamp, split và chuỗi event; lấy tối thiểu 50 instance/project để đối chiếu bằng truy vấn SQL độc lập. Đây là kiểm tra nhất quán dữ liệu/code, không thay thế hai người xác minh nghiệp vụ workflow. Không có người thứ hai: phải ghi rõ chưa có inter-rater agreement và chưa có Jira status-category metadata gốc. Kết quả mang tính nghiên cứu archival với terminal whitelist, không tuyên bố đã xác thực ground truth nghiệp vụ hoàn toàn.

## Tài liệu căn cứ

- [TAWOS repository/terms/schema](https://github.com/SOLAR-group/TAWOS), đọc 2026-10-08.
- [Tawosi et al., MSR 2022](https://arxiv.org/abs/2202.00979), nguồn dataset.
- [Tu et al., FSE 2018](https://doi.org/10.1145/3236024.3236054), rủi ro sử dụng issue tracker sai thời điểm.
- [Teinemaa et al., outcome-oriented PPM benchmark](https://arxiv.org/abs/1707.06766), nền tảng prefix/outcome evaluation.
- [Prokhorenkova et al., NeurIPS 2018](https://proceedings.neurips.cc/paper_files/paper/2018/hash/14491b756b3a51daac41c24863285549-Abstract.html), CatBoost.
- [scikit-learn calibration](https://scikit-learn.org/stable/modules/calibration.html), calibration tách khỏi dữ liệu fit mô hình/test.
