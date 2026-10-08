# Tóm tắt kết quả và định vị bài báo

Manuscript LaTeX tiếng Anh: [main.tex](main.tex). Nội dung theo section ở `sections/`; hướng dẫn build ở [README](README.md).

## Kết quả có gì?

| Phát hiện | Số liệu chính | Ý nghĩa |
|---|---|---|
| Lịch sử thực thi giúp hơn thông tin đầu sprint | Temporal recall 44,46% → 53,36%; Δ +8,90 điểm, CI [6,38; 11,70] | H1 được ủng hộ trong population có nhãn tái dựng được |
| Tín hiệu có chuyển giao giữa project | Macro project 43,56% → 53,52%; Δ +9,96 điểm | Bằng chứng transfer archival; chưa phải enterprise/organization transfer |
| Lợi ích trên việc còn mở nhỏ hơn | Δ +2,59 điểm temporal; +2,03 điểm cross-project | Một phần lợi ích toàn cohort đến từ nhận biết issue đã Done |
| Ngân sách danh nghĩa dễ gây hiểu nhầm | Ceil “20%” dùng macro 41,54%, micro 25,81% temporal | Không được quảng bá recall 53% dưới cap nghiêm ngặt 20% |
| Giới hạn nghiêm ngặt vẫn có tín hiệu nhưng recall thấp | Floor: dynamic temporal recall 18,20%; Δ +3,82 điểm | Sprint nhỏ nhận 0 alert; cần thiết kế capacity nguyên phù hợp |
| Rule nghiệp vụ là đối thủ mạnh | Dynamic − rule temporal +2,13 điểm; CI chứa 0 | Chưa chứng minh ML tốt hơn rule về recall temporal |
| Calibration cần đúng miền sử dụng | Dynamic Brier temporal 0,1279 → 0,1137; cross-project 0,1374 → 0,1381 | Sigmoid không mặc định giúp project mới |
| Có pipeline thực nghiệm có thể kiểm tra | 14 project, 88.588 snapshots toàn cohort labeled, 672 triplets, 14 tests | Có code/dữ liệu trung gian/model/metrics, không chỉ đề xuất ý tưởng |

## Bài báo đóng góp gì?

Đây là bài empirical software engineering: tái dựng cohort lịch sử, so sánh giá trị thông tin thực thi, và chỉ ra các điều kiện làm kết quả cảnh báo trông tốt hơn khả năng xử lý thực tế. Điểm nghiên cứu mạnh là đặt các câu hỏi có thể bị bác bỏ và báo cáo cả kết quả thuận lợi lẫn bất lợi. Không định vị như một thuật toán mới hay tuyên bố SOTA.

Manuscript có abstract, introduction, related work, RQ/estimand, data reconstruction, phương pháp/split/calibration/budget, bảng kết quả, thảo luận, threats to validity, reproducibility/ethics, conclusion và references. H1 được ghi là protocol khóa cục bộ trước fit/test, không giả nhận đã public preregistration. Các so sánh post-hoc được đánh dấu riêng.

## Trước khi nộp bài

Bản hiện tại là manuscript đầy đủ để review, chưa là bản camera-ready đã nộp. Cần điền tác giả/đơn vị đúng thực tế, chọn venue và chuyển sang template tương ứng; rà ground truth workflow/ngày sprint, cân nhắc đánh giá bổ sung trên work còn mở dưới capacity nguyên, và chuẩn bị artifact package công khai nếu venue yêu cầu. Không có human study, inter-rater agreement, intervention effect hoặc public artifact DOI để tuyên bố trong bài hiện tại.

Hướng mở rộng đáng làm nhất là kết hợp **active-only + capacity nghiêm ngặt** trong một thiết kế mới. Hai sensitivity riêng hiện có chưa chứng minh hiệu quả của thiết lập kết hợp đó; không thêm số liệu giả hoặc diễn giải hai phân tích riêng như đã chạy kết hợp.
