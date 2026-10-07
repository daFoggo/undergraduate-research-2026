# Thảo luận kết quả thực nghiệm giai đoạn 4

Ngày phân tích: 2026-10-08. Nguồn số liệu là `artifacts/results/`; không có model nào được sửa hoặc chọn lại tham số sau khi đọc test. Các so sánh ngoài H1 được đánh dấu sensitivity hoặc post-hoc exploratory.

## Kết luận có thể bảo vệ

Execution history có giá trị dự báo thêm so với thông tin ở đầu sprint trong population tái dựng được của TAWOS. Tại 50%, temporal macro Recall tăng từ 44,46% lên 53,36%, tức +8,90 điểm phần trăm, CI [6,38; 11,70]. Cross-project macro theo project tăng từ 43,56% lên 53,52%, tức +9,96 điểm, CI [7,53; 12,82]. Cả 14 project có chênh lệch trung bình dương ở hai thiết lập; không suy từ đó rằng từng project đều có khác biệt có ý nghĩa thống kê.

Temporal có 397 sprint test nhưng chỉ 336 có lớp dương để tính macro recall. Mô hình động phát hiện 682/1.883 issue không hoàn thành trong 850 cảnh báo, so với static phát hiện 605 issue ở cùng số cảnh báo. Precision gộp tăng từ 71,18% lên 80,24%; false alerts giảm từ 245 xuống 168. Đây là ưu tiên issue trong replay, không phải bằng chứng giảm trễ sau can thiệp.

Ở landmark 0%, Δ chỉ +0,66 điểm ở temporal và +0,67 ở cross-project, với CI đều chứa 0. Mốc này không thêm execution information so với baseline; khác biệt nhỏ có thể đến từ encoding/dimensionality và fitting. Không coi nó là bằng chứng history tương lai có tác dụng từ đầu sprint.

## “Ngân sách 20%” cần được hiểu chính xác

Quy tắc chính ceil(0,2×n) cho tối thiểu một cảnh báo ngay cả khi n<5. Temporal có 207/397 sprint ít hơn 5 instance đánh giá được. Vì vậy budget thực tế là 41,54% khi mỗi sprint có trọng số ngang nhau, hoặc 25,81% khi gộp theo issue. Cross-project tương ứng 38,55% và 24,93%, với 827/1.962 sprint nhỏ.

Không được viết “phát hiện 53% rủi ro chỉ cảnh báo 20% issue” mà bỏ qua cách làm tròn và mẫu số. Với giới hạn nghiêm ngặt floor(0,2×n), macro recall động còn 18,20% temporal và 22,31% macro project cross-project. Chênh lệch với static vẫn dương: +3,82 điểm temporal, CI [2,20; 5,67]; +6,09 điểm cross-project, CI [4,34; 8,09]. Tuy nhiên budget macro được sử dụng chỉ 8,45%/9,85% vì sprint nhỏ không được cấp cảnh báo. Bài toán sản phẩm phải chốt K nguyên hoặc quy tắc phân bổ capacity, thay vì chỉ nêu tỷ lệ danh nghĩa.

## Lợi ích trên công việc còn mở nhỏ hơn kết quả toàn cohort

Active-only là kiểm tra quan trọng nhất để phân biệt dự báo tương lai với nhận biết issue đã Done. Khi loại issue Done tại 50%, Δ giảm còn +2,59 điểm temporal, CI [0,68; 4,69]; và +2,03 điểm cross-project, CI [0,73; 3,58]. Các tập con dùng ngân sách tính trên số issue còn mở, nên không cùng estimand với H1 toàn cohort.

Feature importance CatBoost cũng cho thấy trạng thái chi phối: `dynamic_is_done` chiếm trung bình 27,41% importance temporal và 56,44% cross-project; `dynamic_status` thêm 15,58%/13,90%. Importance không chứng minh quan hệ nhân quả và các feature tương quan có thể chia sẻ attribution. Kết quả ủng hộ tín hiệu lịch sử nhưng không ủng hộ câu chuyện rằng mô hình đã học được toàn bộ nguyên nhân trễ phức tạp.

Sensitivity loại cancel/remove vẫn cho Δ dương, và loại issue ID xuất hiện trong train gần như giữ nguyên Δ. Do đó kết quả chính không chỉ đến từ scope change hoặc ghi nhớ trực tiếp issue lặp. Chỉ số Closed-only thay đổi target mà không retrain; không dùng stress test này như kết luận về một model được tối ưu riêng cho Closed-only.

## Baseline nghiệp vụ là đối thủ thực sự

Rule dựa Done/inactivity đạt temporal macro recall 51,23%, gần 53,36% của dynamic CatBoost. So sánh bổ sung sau test cho Δ dynamic − rule = +2,13 điểm, CI [−0,33; 4,60]: chưa đủ bằng chứng mô hình học máy vượt rule về metric cảnh báo temporal này. Đây không phải kết luận tương đương.

Cross-project có Δ +3,83 điểm, CI [2,10; 5,73], nhưng là so sánh exploratory theo project. CatBoost còn có AP macro project tốt hơn rule (temporal 0,8128 so với 0,7517; cross-project 0,8035 so với 0,6537). Những lợi ích này cần cân cùng độ phức tạp, calibration và chi phí vận hành; không chỉ chọn model có tên thuật toán phức tạp hơn.

Ablation không có cohort aggregates hơi tốt hơn ở temporal recall (54,23% so với 53,36%); Δ model đầy đủ − ablation = −0,87 điểm, CI [−2,26; 0,29]. Ở cross-project model đầy đủ hơn +0,72 điểm, CI [0,05; 1,42], vẫn là exploratory. Chưa có bằng chứng aggregate cohort giúp ổn định ở mọi thiết lập. Không chọn ablation bằng kết quả test rồi dùng cùng test để quảng bá một model mới.

## Calibration không chuyển giao tự động

Sigmoid fit trên validation cải thiện Brier temporal của model động từ 0,1279 xuống 0,1137. Pooled calibration intercept/slope từ 0,5736/0,8654 thành 0,0902/1,0260, gần lý tưởng hơn. Nhưng cross-project Brier gộp tăng nhẹ từ 0,1374 lên 0,1381; macro project tăng từ 0,1295 lên 0,1339. Calibration từ các project khác không bảo đảm xác suất tốt hơn ở project mới.

Temporal pooled AP tăng 0,8764 → 0,9000 sau sigmoid, nhưng AP macro project giữ nguyên 0,8128. Với sigmoid đơn điệu trong từng project, thay đổi pooled AP có thể đến từ sắp lại score giữa project; không phải tự nhiên có khả năng phân biệt tốt hơn trong mỗi project. Raw-ranking của H1 cho Δ và CI giống calibrated-ranking ở 50%, nên kết quả H1 chính không đến từ đảo rank bởi calibrator.

Không chọn raw hay sigmoid theo test trong lượt này. Giai đoạn sản phẩm nên thu thập một validation window mới để quyết định calibration policy, theo dõi drift, và hiển thị giới hạn dữ liệu; không đưa một ngưỡng xác suất chung cho mọi project thành bảo đảm rủi ro.

## Cảnh báo sớm và tổng capacity

Replay tuần tự giữ tổng cap cả sprint, không phát lại issue. Dynamic đạt temporal macro recall 51,56%, precision 77,67%, mean lead time trong các sprint có true alerts khoảng 8,30 ngày. So với static trong cùng sequential policy, Δ chỉ +1,30 điểm, CI [−0,46; 3,21], chưa đủ bằng chứng cải thiện temporal. Cross-project có Δ +1,88 điểm, CI [0,60; 3,14], exploratory.

Sequential policy cho lead time sớm hơn cảnh báo riêng ở 50% (khoảng 6,30 ngày temporal), nhưng sử dụng capacity ở thời điểm thông tin ít hơn; không bảo đảm recall cao hơn. Static sequential baseline cũng được lọc issue đang Done bằng quan sát tại landmark, nên đây là baseline mạnh hơn “chỉ nhìn dữ liệu đầu sprint” thuần túy. Các con số lead time chỉ mô tả issue được phát hiện, không phải mọi rủi ro.

## Định hướng phù hợp cho nghiên cứu và sản phẩm tiếp theo

Đóng góp hiện có là benchmark/replay có temporal provenance, bằng chứng incremental value của lịch sử, và phân tích các yếu tố có thể làm kết quả lạc quan: Done recognition, rounding budget, calibration transfer và baseline mạnh. Không tuyên bố thuật toán mới hoặc SOTA.

Đối với sản phẩm, giữ rule đơn giản và model động làm hai phương án pilot; định nghĩa rõ danh sách công việc còn mở và capacity nguyên, thu thập status-category/metadata lịch sử ngày sprint và phản hồi cảnh báo. Chọn/hiệu chuẩn model bằng validation mới trước đánh giá pilot. Hướng nghiên cứu đáng theo đuổi là dự báo trên công việc còn mở và chính sách phân bổ capacity qua thời gian, với dữ liệu có deadline/membership lịch sử đáng tin cậy hơn. Đây là hướng tiếp theo được đề xuất từ kết quả, chưa được kiểm định trong lượt nghiên cứu này.

Các giới hạn chưa được giải quyết: nhãn chỉ có coverage 77,04%, chưa có human workflow ground truth hoặc inter-rater agreement, ngày sprint lấy từ snapshot, project holdout chưa là organization holdout, một seed/cấu hình cố định và nhiều phân tích phụ. Hoàn thành giai đoạn 4 nghĩa là đã có thí nghiệm/báo cáo tái lập và phạm vi kết luận rõ ràng; không nghĩa là đã đủ để triển khai tự động hoặc nộp bài mà không rà soát học thuật.
