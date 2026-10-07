# Căn cứ học thuật và lựa chọn phương pháp

Rà soát mục tiêu ngày 2026-10-08 bằng nguồn nghiên cứu gốc, trang hội nghị/tạp chí và tài liệu chính thức. Đây là targeted review phục vụ protocol, chưa phải systematic literature review đầy đủ. Không khẳng định đã xác định một thuật toán SOTA duy nhất cho cùng cohort/nhãn/budget.

| Nguồn | Bài toán / bằng chứng đã đọc | Vai trò trong nghiên cứu |
|---|---|---|
| [Tawosi et al., MSR 2022](https://arxiv.org/abs/2202.00979), [TAWOS](https://github.com/SOLAR-group/TAWOS) | Dataset issue/changelog Agile; phiên bản bài báo và v1.1 khác nhau | Pin snapshot, xác minh schema và khả năng dựng thời gian |
| [Tu et al., FSE 2018](https://2018.fseconference.org/details/fse-2018-research-papers/47/Be-Careful-of-When-An-Empirical-Study-on-Time-Related-Misuse-of-Issue-Tracking-Data) | Time-related misuse trong issue tracking | Prefix features, tách nhãn/feature, kiểm thử future invariance |
| [Teinemaa et al., TKDD 2019](https://doi.org/10.1145/3301300), [author manuscript](https://lepo.it.da.ut.ee/~dumas/pubs/TKDDSurveyPredictive.pdf) | Outcome prediction từ partial traces; benchmark nhiều encoding/method | Landmark/prefix encoding, baseline và đánh giá nhất quán |
| [Prokhorenkova et al., NeurIPS 2018](https://proceedings.neurips.cc/paper_files/paper/2018/hash/14491b756b3a51daac41c24863285549-Abstract.html) | CatBoost với dữ liệu categorical/tabular | Learner tĩnh/động cùng thuật toán, kiểm tra giá trị lịch sử |
| [Tawosi et al., replication effort estimation](https://solar.cs.ucl.ac.uk/pdf/tawosi2022tse.pdf) | Replication/extension Deep-SE; kết quả không nhất quán với tuyên bố ưu thế ban đầu | Baseline mạnh, chronological validation, không mặc định deep learning tốt hơn |
| [Bui et al., 2025](https://arxiv.org/abs/2509.14483) | Multi-agent LLM cho agile effort/story-point estimation; abstract/metadata | Related work khác target, không baseline trực tiếp cho binary sprint outcome |
| [scikit-learn probability calibration](https://scikit-learn.org/stable/modules/calibration.html) | Calibration/reliability và dữ liệu riêng để fit calibrator | Validation-only sigmoid; raw/calibrated metrics |

## Lập luận nghiên cứu

Cách đặt bài toán gần outcome-oriented predictive process monitoring: một prefix issue history tại thời điểm đang chạy dự báo outcome cuối sprint. Nhưng sprint là deadline chung, cohort đóng ở đầu sprint, và alert capacity được định nghĩa ở cấp sprint. Nghiên cứu phải xử lý membership hồi cứu, issue bị remove và reopen; chỉ huấn luyện một classifier trên bảng issue cuối cùng không trả lời được câu hỏi này.

Story-point/effort estimation dự báo một đại lượng khác. MAE của effort model không thể so với Recall@budget hoặc calibration của risk model. Vì vậy các phương pháp LLM effort estimation được thảo luận như bối cảnh, không coi là SOTA trực tiếp rồi tuyên bố đã vượt qua bằng một metric khác.

CatBoost được chọn cho dữ liệu tabular nhỏ/vừa, nhiều trạng thái categorical và missing values; đây là lựa chọn vận hành, không tuyên bố CatBoost SOTA cho sprint risk. Hai vế H1 dùng cùng learner/cấu hình để chênh lệch phản ánh thông tin lịch sử. Logistic Regression, frequency và business rule giúp kiểm tra mô hình phức tạp có đem thêm giá trị không.

Đóng góp có thể bảo vệ bằng thực nghiệm là protocol/data pipeline có provenance, đo incremental value của execution history, phân tích transfer/calibration và cảnh báo trong giới hạn nguồn lực. Giá trị khoa học nằm ở câu hỏi có thể bác bỏ, dữ liệu đáng kiểm tra và kết quả có bất định; không phụ thuộc vào việc H1 được ủng hộ.

## Search log và mức độ chứng minh

Các truy vấn mục tiêu: `sprint completion prediction TAWOS`, `sprint risk prediction machine learning issue 2024 2025`, `deadline issue prediction calibration software`, `predictive process monitoring temporal leakage benchmark`. Kết quả tìm kiếm có nhiều bài về effort estimation, software defect prediction hoặc risk ở cấp toàn sprint; không tự động tương đương issue–sprint commitment outcome.

Một kết quả gần tên bài toán là [Explainable AI-Based Early Sprint Risk Prediction](https://journal-of-social-education.org/index.php/Jorunal/article/view/1472). Chỉ đọc abstract/trang xuất bản; chưa xác minh dữ liệu, split, mã nguồn và khả năng replay cùng protocol, nên không dùng số accuracy hoặc tuyên bố ưu thế để chọn mô hình/so sánh kết quả.

Không tìm thấy baseline có thể chạy trực tiếp không chứng minh bài toán chưa từng được nghiên cứu. Khi viết bài nộp hội nghị cần snowballing và tìm thêm trên ACM/IEEE/Scopus theo tiêu chí rõ ràng; tránh câu “nghiên cứu đầu tiên” hoặc “đạt SOTA” khi chưa có evidence tương ứng.
