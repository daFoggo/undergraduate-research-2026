# Protocol nghiên cứu — Pha 1: Chốt bài toán và thiết kế dữ liệu

> Tài liệu lịch sử v0.1. Protocol thực nghiệm đã khóa trước fit là [Protocol v1](Protocol_v1.md), kèm config/split/hash trong `artifacts/protocol/`. Kết quả và giới hạn dữ liệu đã ghi ở [báo cáo giai đoạn 4](Bao_cao_nghien_cuu_giai_doan_4.md).

**Dự án:** Dự báo sớm issue có nguy cơ không hoàn thành trong sprint  
**Thời lượng:** 2 tuần  
**Phiên bản:** 0.1 — protocol làm việc, cần khóa phiên bản trước khi chạy đánh giá mô hình  
**Liên kết đề cương tổng thể:** [Đề cương dự báo sớm rủi ro sprint](De_cuong_du_bao_som_rui_ro_sprint.md)

## 1. Mục đích và quyết định cuối pha

Pha này biến ý tưởng nghiên cứu thành một thiết kế có thể tái lập và có thể bị bác bỏ bằng dữ liệu. Hết tuần thứ hai, nhóm phải chốt được:

1. Câu hỏi nghiên cứu chính, estimand và giả thuyết kiểm chứng.
2. Quy tắc chọn dự án, sprint và issue; mọi lý do loại phải được ghi lại.
3. Định nghĩa nhãn, trạng thái không xác định và các phân tích độ nhạy.
4. Danh sách đặc trưng hợp lệ tại từng thời điểm dự báo và danh sách cấm do nguy cơ rò rỉ.
5. Protocol chia dữ liệu, chỉ số chính, cách tính bất định và điều kiện go/no-go.

Không dùng kết quả test để lựa chọn đặc trưng, mô hình, ngưỡng hay quy tắc làm sạch. Chỉ được xem thống kê chất lượng và khả năng tái dựng cohort trong pha này.

## 2. Câu hỏi nghiên cứu đã đề xuất

### RQ chính

**RQ1.** Trong các issue được ghi nhận là thuộc phạm vi sprint tại thời điểm cam kết, việc bổ sung lịch sử thực thi quan sát được đến giữa sprint có giúp xếp hạng các issue không hoàn thành tốt hơn thông tin có tại thời điểm bắt đầu sprint, trong điều kiện chỉ được cảnh báo tối đa 20% số issue của mỗi sprint hay không?

### RQ phụ

- **RQ2 — chuyển giao theo thời gian:** Hiệu quả cảnh báo có được duy trì khi kiểm tra trên các sprint xảy ra sau giai đoạn huấn luyện trong cùng dự án không?
- **RQ3 — chuyển giao dự án:** Hiệu quả có duy trì trên dự án không xuất hiện trong tập huấn luyện không?
- **RQ4 — chất lượng xác suất:** Xác suất dự báo có đủ hiệu chuẩn để diễn giải thành mức rủi ro không?

### Giả thuyết xác nhận

**H1.** Ở mốc 50% thời lượng sprint và cùng ngân sách cảnh báo 20%, mô hình động dùng lịch sử thực thi có `Recall@20%` trung bình theo sprint cao hơn mô hình tĩnh chỉ dùng thông tin tại đầu sprint.

Đây là giả thuyết về **giá trị dự báo trong replay ngoại tuyến**, không phải giả thuyết rằng cảnh báo sẽ làm giảm tỷ lệ trễ. Không diễn giải kết quả theo quan hệ nhân quả.

### Estimand

Đại lượng chính là chênh lệch ghép cặp giữa hai mô hình:

```text
Δ = macro-mean Recall@20% của mô hình động
  − macro-mean Recall@20% của mô hình tĩnh
```

Tính `Recall@20%` riêng cho từng sprint: xếp hạng issue theo xác suất rủi ro, lấy tối đa 20% issue (làm tròn lên, tối thiểu 1 nếu sprint có issue hợp lệ), rồi tính tỷ lệ issue dương tính được bắt trong danh sách đó. Macro-mean cho trọng số ngang nhau giữa các sprint; báo cáo thêm số liệu gộp theo issue để người đọc thấy ảnh hưởng của sprint lớn.

## 3. Đơn vị phân tích, cohort và mốc thời gian

### Đơn vị phân tích

Một **issue–sprint instance**: một issue được đưa vào phạm vi một sprint cụ thể. Issue xuất hiện ở nhiều sprint tạo nhiều instance nếu dữ liệu chứng minh được các lần đưa vào sprint và mỗi lần có thể gắn với một outcome riêng.

Mỗi instance được quan sát ở các landmark chuẩn hóa `t = 0%, 25%, 50%, 75%` thời lượng sprint. RQ1/H1 dùng mốc `50%`; các mốc còn lại là phân tích phụ về độ sớm của cảnh báo.

### Timeline và điểm đóng cohort

```text
Cam kết/phạm vi đầu sprint (t0) → snapshot 25% → snapshot 50% → snapshot 75% → kết thúc sprint
       tạo cohort và baseline       đặc trưng chỉ từ sự kiện có timestamp ≤ landmark
```

Mốc sprint dùng `Start_Date` và `End_Date` hợp lệ sau khi chuẩn hóa UTC. Nếu `Activated_Date` khác đáng kể với `Start_Date`, ghi nhận và quyết định quy tắc theo từng project trước khi xem kết quả mô hình. Không tự động thay thế mốc theo cách làm tăng hiệu suất.

### Cohort chính: cam kết đầu sprint

Một issue thuộc cohort chính khi chứng minh được issue đã nằm trong sprint không muộn hơn thời điểm bắt đầu sprint (hoặc thời điểm chốt kế hoạch được xác định trước, nếu dữ liệu có trường/nhật ký phù hợp). Issue được thêm sau mốc này không thuộc cohort chính.

Đây là điều kiện quan trọng: README TAWOS mô tả bảng Sprint và quan hệ với Issue là các issue được giao trong sprint, nhưng thông tin công khai chưa xác nhận thời điểm lịch sử issue được thêm vào sprint. Vì vậy, cohort “đã cam kết đầu sprint” chỉ được dùng nếu kiểm tra schema và change log chứng minh được thời điểm đó. Không suy luận thời điểm thêm issue từ quan hệ liên kết hiện tại.

### Cohort dự phòng (không thay thế cohort chính)

Nếu không tái dựng được thời điểm cam kết, có thể mô tả riêng một cohort **issue–sprint theo liên kết snapshot**. Kết quả của cohort này chỉ được gọi là dự báo outcome của issue được gắn với sprint trong dữ liệu; không gọi là dự báo thất bại cam kết. Chỉ tiếp tục với cohort dự phòng nếu câu hỏi nghiên cứu được đổi tên và khóa lại trước phân tích kết quả.

## 4. Tiêu chí chọn dự án và sprint

### Tiêu chí bắt buộc cho project

Một project đủ điều kiện khi:

1. Có sprint với `Start_Date` và `End_Date` parse được, `End_Date > Start_Date`, timezone đã chuẩn hóa.
2. Có thể tái dựng lịch sử trạng thái đủ để xác định trạng thái issue tại các landmark và cuối sprint.
3. Có workflow mapping được xác định trước: trạng thái nào là hoàn thành, trạng thái nào là hủy/không còn áp dụng, trạng thái nào chưa kết luận.
4. Với cohort chính, có bằng chứng timestamp cho membership trước/đầu sprint; nếu không, project chỉ được xem xét ở cohort dự phòng.
5. Đạt ngưỡng dữ liệu tối thiểu đã định trước: đề xuất ban đầu là ít nhất **20 sprint hợp lệ**, **200 issue–sprint instance hợp lệ**, ít nhất **30 instance mỗi lớp** trên toàn bộ project, và có tối thiểu **10 sprint nằm trong giai đoạn test theo thời gian**. Các ngưỡng này là ngưỡng vận hành để tránh đánh giá trên mẫu quá nhỏ, không phải định luật thống kê; cần rà soát theo phân bố thực tế nhưng chỉ được sửa dựa trên feasibility, trước khi xem hiệu năng mô hình.

Nếu muốn làm leave-one-project-out, cần ít nhất 5 project đủ điều kiện để có một đánh giá liên dự án có ý nghĩa tối thiểu; số project ít hơn phải được báo cáo như case study/exploratory, không khẳng định khả năng tổng quát hóa.

### Tiêu chí sprint/instance

- Sprint đã kết thúc, có thời lượng dương và outcome quan sát được.
- Issue thuộc cohort theo quy tắc đã chọn; loại duplicate liên kết trùng lặp của cùng issue–sprint.
- Có thể tái dựng nhãn tại `End_Date` bằng lịch sử timestamp hoặc trường resolution đã xác minh tương thích.
- Bỏ khỏi phân tích chính các sprint bị hủy, thiếu ngày kết thúc, có thời lượng bất thường chưa giải thích được, hoặc outcome không xác định.
- Không loại sprint chỉ vì tỷ lệ hoàn thành thấp/cao hoặc vì kết quả làm mô hình kém.

### Đăng ký sổ loại trừ

Tạo bảng `exclusion_log.csv` với tối thiểu các trường: project, sprint, issue (ID đã giả danh), cấp loại trừ, mã lý do, nguồn trường/timestamp, người quyết định, ngày quyết định. Báo cáo flow: số project/sprint/instance ban đầu → số loại theo từng lý do → số còn lại.

## 5. Định nghĩa outcome và nhãn

### Nhãn chính ở cấp issue–sprint

- `Y=1` (**không hoàn thành**): issue thuộc cohort đầu sprint và không ở trạng thái hoàn thành tại `End_Date`.
- `Y=0` (**hoàn thành**): issue thuộc cohort đầu sprint và đã chuyển sang trạng thái hoàn thành không muộn hơn `End_Date`.
- `Y=NA` (**không xác định**): không đủ lịch sử/trường để xác định trạng thái tại `End_Date`, mapping mơ hồ, hoặc dữ liệu mâu thuẫn. Không ép `NA` thành 0.

Trạng thái hoàn thành phải được map theo project vào nhóm trạng thái Jira tương đương `Done/Resolved/Closed` sau khi kiểm tra workflow. Không dùng một chuỗi trạng thái toàn cục nếu cùng tên mang nghĩa khác giữa project.

### Trường hợp đặc biệt

- **Reopen trước cuối sprint:** nhãn theo trạng thái tại `End_Date`; nếu còn mở thì `Y=1`.
- **Resolved rồi reopen sau cuối sprint:** không làm thay đổi nhãn của sprint đã kết thúc.
- **Cancelled/duplicate/withdrawn:** quy tắc chính đề xuất giữ trong mẫu cam kết và gán `Y=1` nếu chưa hoàn thành, vì đây vẫn là công việc đã cam kết nhưng không hoàn thành. Phân tích độ nhạy loại các trường hợp này để tách scope change khỏi execution risk. Không xóa âm thầm.
- **Bị chuyển khỏi sprint sau khi bắt đầu:** giữ trong cohort chính theo nguyên tắc intention-to-treat; đánh dấu scope change và chạy phân tích độ nhạy loại instance này.
- **Issue carried over sang sprint sau:** instance ở sprint trước vẫn giữ outcome riêng; instance sprint sau chỉ thêm nếu có bằng chứng được cam kết riêng cho sprint sau.

### Kiểm tra nhãn thủ công

Lấy mẫu ngẫu nhiên tối thiểu 50 instance/project (hoặc toàn bộ nếu ít hơn), ưu tiên cả hai lớp và ca reopen/cancel/remove. Hai người rà độc lập trạng thái cuối sprint và cohort membership; bất đồng được phân xử, ghi quy tắc sửa vào sổ quyết định. Báo cáo agreement và tỷ lệ nhãn không xác định. Nếu không có người thứ hai, thực hiện rà lặp mù theo sample và ghi rõ giới hạn.

## 6. Đặc trưng và quy tắc thời gian

### Baseline tĩnh tại đầu sprint

Chỉ dùng thông tin đã có tại `t0`: loại issue, priority tại `t0`, story point/estimate đã tồn tại tại `t0`, tuổi issue, độ dài title/description tại `t0`, và lịch sử dự án chỉ tính từ trước sprint. Không dùng giá trị snapshot cuối cùng thay thế giá trị đầu sprint.

### Đặc trưng động đến landmark `t`

Chỉ thêm tín hiệu có thể quan sát đến đúng mốc `t`:

- trạng thái hiện tại tại `t`, thời gian từ khi vào trạng thái, số lần chuyển trạng thái trước hoặc tại `t`;
- thời gian kể từ hoạt động/change log gần nhất;
- số lần đổi assignee/priority/estimate đã xảy ra đến `t` (không đưa danh tính cá nhân vào mô hình chính);
- tỷ lệ thời gian sprint đã trôi qua và còn lại;
- trạng thái tiến độ tổng hợp của cohort đầu sprint đến `t` (ví dụ số/tỷ lệ issue hoàn thành), được tính chỉ trên các issue đã thuộc cohort tại `t0`;
- đặc trưng lịch sử project/sprint chỉ từ sprint đã kết thúc trước đó.

Text từ title/description có thể là nhánh mở rộng. Phiên bản chính ưu tiên đặc trưng cấu trúc để giảm rủi ro sao chép template, nhận diện dự án và khó giải thích; nếu dùng text, phải snapshot văn bản tại `t0`/`t`, tách riêng kết quả và không đưa comment tương lai vào.

### Danh sách cấm trong đánh giá tại mốc `t`

- resolution/final status hiện tại nếu không tái dựng được giá trị tại `t`;
- ngày resolved/closed cuối cùng, tổng resolution time, effort/time spent cuối cùng;
- số lần thay đổi, comment, assignee hoặc estimate tính trên toàn bộ vòng đời;
- comment/change log sau `t`, nội dung description được cập nhật sau `t`;
- dữ liệu của sprint tương lai, trường phản ánh outcome hoặc ID làm khóa ghi nhớ;
- phép chuẩn hóa/imputation/feature selection được fit trên validation/test.

### Unit test chống leakage

Với mỗi feature dynamic, kiểm tra `max(event_timestamp) <= prediction_timestamp`. Thêm test tự động: khi xóa/đẩy các event sau landmark, vector đặc trưng tại landmark không được thay đổi. Các đặc trưng cohort-level phải dùng membership được biết tại `t0`, không dùng danh sách sprint hoàn chỉnh được dựng sau này.

## 7. Chia dữ liệu và đánh giá

### A. Temporal within-project — đánh giá chính

Trong từng project đủ dữ liệu, sắp sprint theo `Start_Date` (sprint trùng/đè thời gian được xử lý theo quy tắc overlap khóa trước). Chia theo thời gian thành 60% train sớm nhất, 20% validation kế tiếp, 20% test mới nhất. Chia theo **sprint**, không theo snapshot; mọi landmark của cùng issue–sprint nằm cùng partition. Không shuffle ngẫu nhiên.

Nếu project có quá ít sprint để giữ riêng validation và test, không ép chia 60/20/20; ghi project đó vào phần mô tả hoặc exploratory. Hyperparameter, threshold/calibrator chọn bằng train/validation; test chỉ chạy một lần sau khi khóa pipeline.

### B. Cross-project — đánh giá tổng quát hóa

Dùng GroupKFold/leave-one-project-out: toàn bộ dữ liệu của project test bị giữ ngoài huấn luyện. Mọi chọn mô hình và hiệu chuẩn diễn ra bằng các project train/validation; không dùng project test để chọn quyết định. Báo cáo macro-mean theo project và phân bố từng project; không chỉ gộp toàn bộ issue.

### Lặp issue qua nhiều sprint

Issue ID không là feature. Với temporal evaluation, sự xuất hiện của cùng issue ở sprint sau chỉ được giữ nếu lịch sử đến dự báo thực sự có thể biết tại thời điểm đó; các instance/snapshot của cùng issue–sprint không được tách partition. Báo cáo thêm sensitivity loại các issue ID xuất hiện ở cả train và test để kiểm tra mức phụ thuộc vào lặp issue, nếu cỡ mẫu cho phép.

### Tuning, imbalance và bất định

- Huấn luyện/hiệu chuẩn chỉ trên train/validation.
- Không oversample trước khi chia split; nếu dùng class weighting, fit trong train.
- Tính khoảng tin cậy 95% cho `Δ` bằng bootstrap ghép cặp theo sprint trong temporal test; với cross-project bootstrap theo project (và trình bày hạn chế khi ít project).
- So sánh các mô hình trên cùng tập sprint và cùng quy tắc ngân sách.
- Không coi snapshot ở nhiều landmark của cùng instance là các mẫu độc lập.

## 8. Chỉ số và quy tắc kết luận

### Chỉ số chính

`Recall@20%` ở landmark 50%, macro-mean theo sprint, và chênh lệch ghép cặp `Δ` giữa mô hình động với baseline tĩnh.

### Chỉ số phụ

- `PR-AUC` (gộp và macro theo sprint/project) cho chất lượng xếp hạng trên lớp mất cân bằng;
- `Brier score`, reliability/calibration plot và calibration slope/intercept cho xác suất;
- `Precision@20%`, số cảnh báo sai trung bình mỗi sprint;
- ở landmark 25% và 75%: các chỉ số cảnh báo tương tự, và lead time đến cuối sprint;
- ROC-AUC chỉ báo cáo phụ, không dùng làm chỉ số kết luận duy nhất.

Sprint không có issue dương tính có `Recall@20%` không xác định; sprint đó không góp vào mẫu số macro-Recall, nhưng vẫn được giữ khi báo cáo precision/false alerts và flow dữ liệu. Báo cáo số sprint bị loại khỏi mẫu số metric này. Không chọn ngưỡng cảnh báo theo test. `Recall@20%` đo khả năng ưu tiên dưới một giới hạn xử lý, không chứng minh tác động của can thiệp.

### Quy tắc diễn giải H1

- Bằng chứng ủng hộ H1 nếu `Δ > 0` và khoảng tin cậy 95% không chứa 0 trên temporal test chính.
- Nếu khoảng tin cậy chứa 0: kết luận chưa đủ bằng chứng cho cải thiện, không diễn giải là hai phương pháp tương đương.
- Nếu kết quả dương ở temporal nhưng không ở cross-project: chỉ kết luận khả năng dùng trong dự án đã có lịch sử, không tuyên bố tổng quát hóa.
- Nếu nhãn/cohort không thể tái dựng đáng tin cậy: dừng kiểm định H1 trên TAWOS và sửa câu hỏi hoặc tìm nguồn dữ liệu khác.

## 9. Tiêu chí go/no-go dữ liệu

### Go cho nghiên cứu “cam kết đầu sprint” khi

1. Có cách xác định cohort tại `t0` bằng dữ liệu có timestamp, không phải snapshot cuối.
2. Có nhãn hoàn thành ở cuối sprint cho phần lớn cohort; tỷ lệ `NA` và lý do được báo cáo.
3. Mapping workflow được kiểm tra thủ công trên các project được chọn.
4. Có đủ số sprint/project theo ngưỡng đăng ký, gồm temporal test có cả hai lớp.
5. Unit test xác nhận không feature nào dùng event sau landmark.

### No-go hoặc đổi estimand khi

- chỉ có liên kết Issue–Sprint ở snapshot và không có lịch sử thời điểm thêm issue;
- timestamp hoặc trạng thái cuối sprint thiếu/không thể đối chiếu;
- các project hợp lệ quá ít hoặc chỉ có một lớp outcome ở test;
- chất lượng dữ liệu phụ thuộc vào một cách xử lý tùy ý không thể xác minh.

Nếu chuyển sang cohort snapshot, đổi thuật ngữ từ “không hoàn thành cam kết sprint” sang “không hoàn thành issue thuộc sprint trong dữ liệu”, cập nhật RQ/nhãn và ghi phiên bản protocol mới trước khi huấn luyện.

## 10. Kế hoạch công việc 2 tuần

| Thời gian | Công việc | Đầu ra kiểm chứng được |
|---|---|---|
| Ngày 1–2 | Tải/pin TAWOS snapshot; kiểm kê schema, license/terms, bảng Sprint–Issue–Change_Log; ghi checksum và phiên bản | Data card v0, manifest dữ liệu |
| Ngày 3–4 | Kiểm tra timestamp sprint, membership và khả năng dựng trạng thái tại thời điểm; lập sơ đồ event timeline | Báo cáo feasibility cohort/label, ví dụ truy vết thủ công |
| Ngày 5 | Chốt RQ, cohort chính/dự phòng, nhãn và quy tắc ca đặc biệt | Protocol v1 được khóa |
| Ngày 6–8 | Thống kê counts chỉ phục vụ feasibility; chạy quy tắc inclusion/exclusion; rà mẫu nhãn | Bảng flow, workflow mapping, exclusion log |
| Ngày 9–10 | Chốt feature whitelist/blacklist, test temporal integrity, split và metric | Đặc tả feature, split manifest, test leakage |
| Ngày 11–12 | Rà lại quyết định độc lập; sửa mâu thuẫn protocol; đóng băng config | Decision log và protocol v1.0 |
| Ngày 13–14 | Review go/no-go, đóng gói artifact, quyết định tiếp tục/đổi estimand/đổi dataset | Biên bản kết thúc pha và backlog pha 2 |

### Artifact phải có khi kết thúc

- `protocol_v1.0.md` (tài liệu này sau khi điền các quyết định thực tế);
- `data_manifest` (phiên bản/URL tải, ngày tải, checksum, license/terms đã đọc);
- `project_eligibility.csv` và `exclusion_log.csv`;
- `label_mapping.csv` theo project và kiểm tra nhãn;
- `feature_dictionary.csv` gồm định nghĩa, nguồn, thời điểm khả dụng, phép biến đổi, trạng thái allow/deny;
- `split_manifest.csv` liệt kê sprint/project thuộc train/validation/test;
- kiểm thử tự động cho leakage và báo cáo feasibility.

## 11. Các quyết định cần ghi vào decision log

| Mã | Quyết định | Trạng thái ban đầu | Bằng chứng cần có |
|---|---|---|---|
| D1 | Cohort là cam kết đầu sprint hay liên kết snapshot | Chưa khóa — phụ thuộc khả năng dựng membership timestamp | Schema, changelog, truy vết issue mẫu |
| D2 | Mốc bắt đầu sprint dùng `Start_Date` hay `Activated_Date` | Mặc định `Start_Date`; xác minh độ lệch | Phân bố và ngữ nghĩa trường |
| D3 | Mapping trạng thái hoàn thành | Theo project, chưa khóa | Workflow/status values và sample audit |
| D4 | Cancel/remove có tính là không hoàn thành không | Chính: giữ là `Y=1`; sensitivity: loại | Nhãn, lý do thay đổi phạm vi |
| D5 | Ngưỡng project tối thiểu | Đề xuất ở mục 4, chỉ chỉnh theo feasibility | Phân bố số sprint/instance/lớp |
| D6 | Feature whitelist và split manifest | Chưa khóa | Data dictionary, unit test leakage |

Mỗi thay đổi sau protocol v1.0 cần có ngày, người sửa, lý do, phần dữ liệu/kết quả đã xem trước thay đổi và đánh dấu là phân tích xác nhận hay exploratory.

## 12. Nguồn và căn cứ thiết kế

1. Tawosi et al. (2022), *A Versatile Dataset of Agile Open Source Software Projects*, MSR. [Bản arXiv](https://arxiv.org/abs/2202.00979), [DOI](https://doi.org/10.1145/3524842.3528029).
2. TAWOS v1.1, [repository và mô tả schema](https://github.com/SOLAR-group/TAWOS). README hiện nêu 458,232 issue thuộc 39 project; bài báo mô tả snapshot ban đầu 508,963 issue thuộc 44 project. Do đó phải pin đúng bản dataset dùng trong nghiên cứu và báo cáo khác biệt phiên bản.
3. Tu et al. (2018), *Be Careful of When: An Empirical Study on Time-Related Misuse of Issue Tracking Data*, ESEC/FSE. [DOI](https://doi.org/10.1145/3236024.3236054). Căn cứ cho việc tái dựng feature theo thời điểm dự báo thay vì dùng snapshot cuối.
4. TAWOS README mô tả Sprint fields gồm `State`, `Start_Date`, `End_Date`, `Activated_Date`, `Completion_Date`; changelog chứa các thay đổi theo thời gian. Tuy vậy, cần xác minh bằng schema và dữ liệu thực tế rằng có thể dựng membership issue–sprint tại thời điểm cam kết; mô tả dataset hiện có không tự chứng minh điều này.

---

**Trạng thái:** Bản protocol đề xuất. Các trường D1–D6 phải được điền bằng kết quả feasibility trước khi chạy mô hình hoặc xem metric trên test.
