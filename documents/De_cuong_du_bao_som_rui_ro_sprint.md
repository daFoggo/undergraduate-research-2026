# Đề cương nghiên cứu

## Dự báo sớm nguy cơ không hoàn thành công việc trong sprint từ lịch sử thực thi và cảnh báo theo ngân sách

**Tên tiếng Anh:** *Early Warning of Sprint Commitment Failure from Issue Execution Histories with Budget-Constrained Alerting*

## Tóm tắt

Nghiên cứu xây dựng và đánh giá phương pháp dự báo sớm khả năng một công việc phần mềm chưa hoàn thành vào ngày kết thúc sprint. Tại nhiều thời điểm trong sprint, mô hình sử dụng thông tin đã quan sát đến thời điểm đó, gồm thuộc tính issue, trạng thái và lịch sử thay đổi. Nghiên cứu so sánh các baseline với mô hình sử dụng lịch sử thực thi, đánh giá khả năng dự báo theo thời gian, mức độ hiệu chuẩn của xác suất và hiệu quả cảnh báo khi số cảnh báo bị giới hạn.

Kết quả nghiên cứu được triển khai thành một mô-đun dự báo và cảnh báo trong ứng dụng web Agentick. Ứng dụng cung cấp danh sách công việc cần chú ý, xác suất rủi ro và các tín hiệu dữ liệu liên quan để người quản lý xem xét.

**Từ khóa:** dự báo rủi ro sprint, issue tracking, dự báo sớm, hiệu chuẩn xác suất, cảnh báo có ngân sách, predictive process monitoring.

## 1. Bối cảnh và lý do chọn đề tài

Các hệ thống quản lý issue lưu lại nhiều thông tin trong quá trình phát triển phần mềm, chẳng hạn trạng thái, thời điểm thay đổi, sprint, người phụ trách và mức độ ưu tiên. Những dữ liệu này có thể giúp nhận diện công việc đang có nguy cơ không hoàn thành theo kế hoạch.

Các nghiên cứu về predictive process monitoring đã xem xét việc dự báo kết quả và thời gian còn lại của một quy trình đang diễn ra. Các nghiên cứu về prescriptive process monitoring còn xem xét cách sử dụng dự báo để đề xuất hành động. Đề tài này tập trung vào một thiết lập cụ thể: dự báo issue có hoàn thành trong sprint đã cam kết hay không, và kiểm tra xem hệ thống có đưa ra cảnh báo đủ sớm trong điều kiện số cảnh báo bị giới hạn không. ([Verenich et al., 2019](https://doi.org/10.1145/3331449); [Kubrak et al., 2022](https://peerj.com/articles/cs-1097/))

## 2. Bài toán nghiên cứu

### 2.1. Đơn vị dự báo

Đơn vị phân tích là **một issue thuộc một sprint** (*issue-sprint instance*).

Tại thời điểm `t` trong sprint, hệ thống dự báo:

```text
P(issue chưa hoàn thành tại ngày kết thúc sprint
  | thông tin quan sát đến thời điểm t)
```

Mô hình chỉ được sử dụng dữ liệu đã phát sinh trước hoặc tại thời điểm dự báo.

### 2.2. Định nghĩa kết quả cần dự báo

Một issue được gán nhãn **không hoàn thành trong sprint** nếu issue thuộc phạm vi sprint tại thời điểm chốt cam kết nhưng chưa đạt trạng thái hoàn thành vào ngày kết thúc sprint.

Trước khi xây dựng dữ liệu, cần thống nhất:

- thời điểm được xem là thời điểm chốt danh sách issue của sprint;
- trạng thái nào được xem là hoàn thành;
- cách xử lý issue bị hủy, mở lại hoặc chuyển khỏi sprint;
- cách xác định ngày bắt đầu và kết thúc sprint.

Nếu dữ liệu không đủ để tái dựng các thông tin này, phạm vi dữ liệu phải được điều chỉnh trước khi kết luận mô hình dự báo được kết quả sprint.

### 2.3. Câu hỏi nghiên cứu

**RQ1.** Lịch sử trạng thái và thay đổi của issue có cải thiện dự báo so với thông tin chỉ có tại thời điểm bắt đầu sprint không?

**RQ2.** Chất lượng dự báo thay đổi thế nào khi mô hình được kiểm tra trên các sprint tương lai và các dự án chưa xuất hiện trong dữ liệu huấn luyện?

**RQ3.** Khi số lượng cảnh báo mỗi sprint bị giới hạn, mô hình nào phát hiện được nhiều issue không hoàn thành hơn và cảnh báo sớm hơn?

## 3. Mục tiêu

### Mục tiêu tổng quát

Xây dựng và đánh giá một mô-đun dự báo sớm nguy cơ issue không hoàn thành trong sprint, sau đó triển khai mô-đun này trong ứng dụng web Agentick.

### Mục tiêu cụ thể

1. Xây dựng quy trình tái dựng dữ liệu issue tại nhiều mốc trong sprint.
2. Tạo baseline và mô hình dự báo từ thông tin tĩnh và lịch sử thực thi.
3. Đánh giá mô hình theo thời gian, theo dự án và theo ngân sách cảnh báo.
4. Tích hợp mô hình vào ứng dụng để hiển thị và gửi cảnh báo có thể kiểm tra.
5. Công bố rõ giới hạn của dữ liệu và mức độ suy rộng của kết quả.

## 4. Dữ liệu nghiên cứu

### 4.1. Nguồn dữ liệu chính

Có thể sử dụng TAWOS, bộ dữ liệu từ các dự án Agile mã nguồn mở lưu trên Jira. Repository hiện tại mô tả 458.232 issue từ 39 dự án thuộc 12 repository Jira công khai; bài giới thiệu ban đầu mô tả hơn 500.000 issue từ 44 dự án. Do khác biệt phiên bản, nghiên cứu cần ghi rõ snapshot được tải, ngày tải và tập con được chọn. ([TAWOS repository](https://github.com/SOLAR-group/TAWOS); [Tawosi et al., 2022](https://arxiv.org/abs/2202.00979))

### 4.2. Giai đoạn kiểm tra tính khả thi

Trước khi huấn luyện mô hình, kiểm tra xem dữ liệu có đủ thông tin để:

- xác định sprint và thời gian bắt đầu, kết thúc;
- xác định issue thuộc sprint ở thời điểm cam kết;
- tái dựng trạng thái và các thay đổi của issue theo thời gian;
- ánh xạ trạng thái theo từng dự án về một quy tắc hoàn thành thống nhất.

Chỉ chọn những dự án đạt tiêu chí dữ liệu đã đặt trước. Báo cáo số lượng issue và sprint bị loại cùng lý do loại.

### 4.3. Tạo snapshot

Với mỗi issue đã cam kết trong sprint, tạo bản ghi tại các mốc chuẩn hóa, chẳng hạn khi sprint đã trôi qua 25%, 50% và 75% thời lượng. Mỗi bản ghi bao gồm những gì hệ thống có thể biết tại mốc tương ứng.

Các nhóm đặc trưng dự kiến:

- **Thông tin ban đầu:** loại issue, mức ưu tiên, estimate nếu có, thời điểm tạo, độ dài mô tả.
- **Thông tin sprint:** thời gian đã trôi qua, thời gian còn lại, số issue đã hoàn thành tính đến thời điểm `t`.
- **Lịch sử thực thi:** trạng thái hiện tại, thời gian ở trạng thái hiện tại, số lần chuyển trạng thái, khoảng thời gian từ thay đổi gần nhất, thay đổi mức ưu tiên hoặc estimate nếu có.
- **Thông tin văn bản:** title và description tại thời điểm dự báo. Có thể dùng TF-IDF như một biến thể bổ sung; nghiên cứu chính không phụ thuộc vào LLM.

Không đưa thông tin chỉ xuất hiện sau thời điểm dự báo vào đặc trưng. Ví dụ: ngày đóng cuối cùng, trạng thái cuối cùng, tổng số lần thay đổi trong cả vòng đời hoặc bình luận được tạo sau mốc dự báo. Sai lệch thời gian trong issue tracker có thể tạo ra kết quả đánh giá lạc quan giả tạo. ([Tu et al., 2018](https://2018.fseconference.org/details/fse-2018-research-papers/47/Be-Careful-of-When-An-Empirical-Study-on-Time-Related-Misuse-of-Issue-Tracking-Data))

## 5. Phương pháp nghiên cứu

### 5.1. Các mô hình so sánh

1. **Baseline theo tần suất:** xác suất không hoàn thành dựa trên tỷ lệ lịch sử của dự án hoặc sprint.
2. **Quy tắc nghiệp vụ:** ví dụ, cảnh báo khi sprint đã qua một tỷ lệ thời gian nhất định nhưng issue chưa bắt đầu hoặc chưa thay đổi trạng thái.
3. **Mô hình thông tin tĩnh:** Logistic Regression hoặc mô hình cây với dữ liệu tại thời điểm cam kết.
4. **Mô hình lịch sử thực thi:** CatBoost hoặc XGBoost với đặc trưng động đến thời điểm `t`.
5. **Mô hình kết hợp:** thông tin ban đầu, lịch sử thực thi và đặc trưng văn bản nếu dữ liệu cho phép.

So sánh mô hình tĩnh với mô hình động sẽ cho biết lịch sử thực thi đóng góp thêm bao nhiêu giá trị.

### 5.2. Hiệu chuẩn xác suất

Đầu ra cần là xác suất rủi ro, không chỉ là nhãn “rủi ro/không rủi ro”. Nếu cần hiệu chuẩn, thực hiện trên tập validation theo thời gian, không điều chỉnh bằng tập test.

Có thể đánh giá hiệu chuẩn bằng Brier score, calibration plot và hệ số calibration slope/intercept. Không dùng duy nhất một ngưỡng xác suất để kết luận mô hình tốt, vì cùng một ngưỡng có thể tạo ra lượng cảnh báo khác nhau giữa các dự án.

### 5.3. Thiết kế chia dữ liệu

- **Đánh giá theo thời gian:** huấn luyện trên các sprint cũ, kiểm tra trên các sprint diễn ra sau đó.
- **Đánh giá dự án chưa thấy:** giữ một số dự án ngoài dữ liệu huấn luyện để đo khả năng chuyển giao.
- Các snapshot của cùng issue-sprint phải thuộc cùng một phân vùng đánh giá.
- Kết quả within-project và cross-project được báo cáo riêng.

## 6. Chỉ số đánh giá

### Chất lượng dự báo

- PR-AUC để đánh giá khả năng tìm issue không hoàn thành khi lớp này mất cân bằng.
- Brier score để đánh giá chất lượng xác suất.
- Calibration plot và calibration slope/intercept để xem xác suất dự báo có khớp với tỷ lệ xảy ra thực tế không.

### Chất lượng cảnh báo

Thiết lập một ngân sách cố định, ví dụ tối đa `K` cảnh báo mỗi sprint hoặc tối đa một tỷ lệ `q` issue được cảnh báo. Tại ngân sách đó, đo:

- recall của issue không hoàn thành;
- số cảnh báo sai trên mỗi sprint;
- thời gian cảnh báo trung bình trước khi sprint kết thúc;
- tỷ lệ issue rủi ro được phát hiện trước một mốc thời gian cụ thể.

Khoảng tin cậy có thể tính bằng bootstrap theo sprint hoặc dự án. Khi so sánh giữa các mô hình, không coi mọi snapshot của cùng issue là các quan sát độc lập.

## 7. Sản phẩm ứng dụng

Ứng dụng web Agentick gồm các phần:

- quản lý project, sprint và issue;
- giao diện theo dõi tiến độ;
- mô-đun dự báo nguy cơ không hoàn thành sprint;
- bảng ưu tiên issue theo xác suất và ngưỡng cảnh báo;
- giải thích dựa trên các đặc trưng đã dùng, chẳng hạn “issue chưa thay đổi trạng thái trong 5 ngày”;
- gửi thông báo qua email hoặc Telegram theo cấu hình;
- lưu lại thời điểm dự báo, phiên bản mô hình, cảnh báo đã gửi và phản hồi người dùng.

Backend nghiên cứu được triển khai theo các module FastAPI dùng `APIRouter`; PostgreSQL là kho dữ liệu truy vấn chính và Docker Compose tái lập môi trường. Bản TAWOS MySQL gốc được nhập vào PostgreSQL qua một bước migration có kiểm tra số dòng và lưu manifest phiên bản/checksum. Schema dữ liệu nguồn được giữ riêng với schema metadata/thực nghiệm của ứng dụng.

Hệ thống hỗ trợ người quản lý quyết định. Nó không tự thay đổi deadline, người phụ trách hoặc phạm vi sprint.

## 8. Đóng góp dự kiến

1. Một giao thức có thể tái lập để tạo snapshot issue theo thời gian và dự báo kết quả sprint.
2. Bằng chứng thực nghiệm về việc lịch sử thực thi có cải thiện dự báo so với dữ liệu tĩnh hay không.
3. Đánh giá khả năng chuyển giao giữa dự án và độ hiệu chuẩn của dự báo.
4. So sánh chính sách cảnh báo ở cùng ngân sách để đo mối quan hệ giữa recall, cảnh báo sai và độ sớm.
5. Một mô-đun phần mềm tích hợp vào Agentick để trình diễn kết quả nghiên cứu.

Đóng góp được kỳ vọng là **bằng chứng thực nghiệm và hệ thống đánh giá cho bài toán cụ thể**, không mặc định là một thuật toán dự báo mới.

## 9. Phạm vi và giới hạn

- Nghiên cứu chính đánh giá issue không hoàn thành trong sprint đã cam kết.
- Kết quả trên TAWOS không tự động khái quát thành deadline cá nhân hoặc deadline của doanh nghiệp.
- Nếu bổ sung dữ liệu thật từ Agentick, cần mô tả riêng cách thu thập và đặc điểm nhóm tham gia.
- Việc mô phỏng lịch sử cảnh báo không chứng minh cảnh báo làm giảm số issue trễ. Kết luận về tác động chỉ có thể đưa ra sau một pilot được thiết kế để đo hiệu quả can thiệp.
- Phân tích survival hoặc conformal prediction có thể là hướng mở rộng, không phải điều kiện để hoàn thành đề tài chính.

## 10. Kế hoạch thực hiện

| Giai đoạn | Thời lượng | Kết quả |
|---|---:|---|
| Chốt câu hỏi, protocol và tiêu chí chọn dự án | 2 tuần | Định nghĩa cohort, nhãn, đặc trưng và cách chia dữ liệu |
| Kiểm tra dữ liệu, dựng snapshot | 2 tuần | Báo cáo chất lượng TAWOS và pipeline dữ liệu |
| Xây baseline và mô hình dự báo | 3 tuần | Mô hình tĩnh, mô hình động, bộ đặc trưng |
| Chạy đánh giá và phân tích kết quả | 3 tuần | Temporal/project split, calibration, alert budget |
| Tích hợp mô hình vào Agentick | 3 tuần | Bảng cảnh báo, giải thích, log dự báo |
| Viết báo cáo và hoàn thiện sản phẩm | 3 tuần | Báo cáo nghiên cứu, mã xử lý dữ liệu và ứng dụng |

**Điều kiện tiếp tục sau giai đoạn kiểm tra dữ liệu:** phải tái dựng được phạm vi issue đã cam kết và trạng thái hoàn thành tại cuối sprint với độ tin cậy chấp nhận được. Nếu không đạt, cần đổi tập dữ liệu hoặc đổi bài toán trước khi chạy thực nghiệm.

## 11. Tài liệu tham khảo nền tảng

1. I. Verenich, M. Dumas, M. La Rosa, F. M. Maggi, and I. Teinemaa, “Survey and Cross-benchmark Comparison of Remaining Time Prediction Methods in Business Process Monitoring,” *ACM Transactions on Intelligent Systems and Technology*, 2019. [DOI](https://doi.org/10.1145/3331449)
2. A. E. Márquez-Chamorro, M. Resinas, and A. Ruiz-Cortés, “Predictive Monitoring of Business Processes: A Survey,” *IEEE Transactions on Services Computing*, 2018. [Bản lưu trữ học thuật](https://idus.us.es/items/d7e0adf1-6ecc-4674-aa4a-e81ced302480)
3. M. Kubrak et al., “Prescriptive Process Monitoring: Quo Vadis?,” *PeerJ Computer Science*, 2022. [Bài báo](https://peerj.com/articles/cs-1097/)
4. F. Tu, J. Zhu, Q. Zheng, and M. Zhou, “Be Careful of When: An Empirical Study on Time-Related Misuse of Issue Tracking Data,” ESEC/FSE, 2018. [Bài báo hội nghị](https://2018.fseconference.org/details/fse-2018-research-papers/47/Be-Careful-of-When-An-Empirical-Study-on-Time-Related-Misuse-of-Issue-Tracking-Data)
5. V. Tawosi, A. Al-Subaihin, R. Moussa, and F. Sarro, “A Versatile Dataset of Agile Open Source Software Projects,” 2022. [arXiv](https://arxiv.org/abs/2202.00979)
