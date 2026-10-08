# Đề cương nghiên cứu

## Dự báo sớm nguy cơ không hoàn thành công việc trong sprint từ lịch sử thực thi và cảnh báo theo ngân sách

**Tên tiếng Anh:** *Early Warning of Sprint Commitment Failure from Issue Execution Histories with Budget-Constrained Alerting*

## Tóm tắt

Nghiên cứu xây dựng và đánh giá phương pháp dự báo sớm khả năng một công việc phần mềm chưa hoàn thành vào ngày kết thúc sprint. Tại nhiều thời điểm trong sprint, mô hình sử dụng thông tin đã quan sát đến thời điểm đó, gồm thuộc tính issue, trạng thái và lịch sử thay đổi. Nghiên cứu so sánh các baseline với mô hình sử dụng lịch sử thực thi, đánh giá khả năng dự báo theo thời gian, mức độ hiệu chuẩn của xác suất và hiệu quả cảnh báo khi số cảnh báo bị giới hạn.

Trên nền kết quả dự báo đã kiểm chứng, nghiên cứu mở rộng sang một **agent cảnh báo chủ động có giới hạn**: controller ngoài LLM quyết định issue nào được cảnh báo và vào lúc nào theo capacity; agent dùng công cụ chỉ đọc để lập brief triage có bằng chứng; verifier, ledger và quyền do hệ thống kiểm soát. Agent được đánh giá từng lớp (policy, kỹ thuật, người dùng) so với baseline template và LLM một lượt, với bộ kịch bản và rubric khóa trước; mọi kết luận về hữu ích với người dùng hoặc giảm trễ chỉ được đưa ra khi có thiết kế nghiên cứu tương ứng.

Kết quả nghiên cứu được triển khai thành một mô-đun dự báo và cảnh báo trong ứng dụng web Agentick. Ứng dụng cung cấp danh sách công việc cần chú ý, xác suất rủi ro, brief có bằng chứng và các tín hiệu dữ liệu liên quan để người quản lý xem xét.

**Từ khóa:** dự báo rủi ro sprint, issue tracking, dự báo sớm, hiệu chuẩn xác suất, cảnh báo có ngân sách, predictive process monitoring, agent có công cụ, giải thích có bằng chứng.


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

**Câu hỏi mở rộng về agent** (bổ sung sau giai đoạn 1–4, không phải giả thuyết đăng ký trước; chi tiết ở mục 7):

**RQ-A.** Trên issue còn mở, phân bổ capacity cảnh báo theo thời gian có cải thiện recall phát hiện đủ sớm ở cùng tổng K không?

**RQ-B.** Với cùng candidate, score và bằng chứng, agent có công cụ có hỗ trợ quyết định tốt hơn template và LLM một lượt không, với chi phí và sai sót nào?

**RQ-C.** Verifier bằng chứng và ledger bền vững giảm bao nhiêu khẳng định không có căn cứ và cảnh báo vượt quyền/trùng lặp, đổi lại có mất coverage hay usefulness không?

## 3. Mục tiêu

### Mục tiêu tổng quát

Xây dựng và đánh giá một mô-đun dự báo sớm nguy cơ issue không hoàn thành trong sprint cùng một agent cảnh báo chủ động có giới hạn và dựa trên bằng chứng, sau đó triển khai trong ứng dụng web Agentick.

### Mục tiêu cụ thể

1. Xây dựng quy trình tái dựng dữ liệu issue tại nhiều mốc trong sprint.
2. Tạo baseline và mô hình dự báo từ thông tin tĩnh và lịch sử thực thi.
3. Đánh giá mô hình theo thời gian, theo dự án và theo ngân sách cảnh báo.
4. Thiết kế và đánh giá policy phân bổ capacity cảnh báo (controller ngoài LLM) so với baseline đơn giản.
5. Xây dựng agent có công cụ chỉ đọc, bằng chứng as-of, verifier và cơ chế quyền/capacity do hệ thống kiểm soát; so sánh với template và LLM một lượt trên bộ đánh giá kỹ thuật được khóa trước.
6. Tích hợp mô hình và agent vào ứng dụng để hiển thị và gửi (dry-run mặc định) cảnh báo có thể kiểm tra, kèm ledger phản hồi.
7. Công bố rõ giới hạn của dữ liệu, của benchmark agent và mức độ suy rộng của kết quả.


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

## 7. Agent cảnh báo chủ động có giới hạn và dựa trên bằng chứng (Giao diện tích hợp cho lõi ML)

> Đây là thành phần **giao diện cảnh báo chủ động và giải thích có căn cứ** được tích hợp trực tiếp vào bài toán nghiên cứu. Thành phần này không thay thế lõi ML dự báo rủi ro mà giải quyết khoảng trống thực tế: chuyển đổi điểm số rủi ro thô thành bản tóm tắt nguyên nhân (triage brief) kèm bằng chứng lịch sử có thể kiểm chứng độc lập.

### 7.1. Cơ sở khoa học của các tham số thiết kế

1. **Điểm mốc thời gian (Landmark $L = 0.40$):**
   - Đánh dấu thời điểm 40% chu kỳ sprint (ví dụ: ngày làm việc thứ 4 của sprint 2 tuần gồm 10 ngày làm việc).
   - *Cơ sở:* Nghiên cứu thực nghiệm cho thấy tại mốc 40%, đội ngũ đã tích lũy đủ dữ liệu tương tác thực tế (sự kiện commit, đổi trạng thái, bình luận) để mô hình phát hiện trạng thái đình trệ (stagnation), đồng thời còn lại 60% thời gian (lead time trung bình trên 8 ngày) đủ để Scrum Master/Tech Lead can thiệp tái phân bổ công việc. Cảnh báo quá sớm (0%) thiếu tín hiệu động; cảnh báo quá muộn (80%) không còn thời gian xử lý.

2. **Ngân sách cảnh báo hữu hạn ($K = 2$ issue/sprint):**
   - Giới hạn tối đa 2 issue có nguy cơ cao nhất được phép cảnh báo chủ động trong mỗi sprint.
   - *Cơ sở:* Dựa trên lý thuyết về Quá tải cảnh báo (Alert Fatigue / Cognitive Load Theory trong công nghệ phần mềm - *Johnson et al., 2013*) và chuẩn đánh giá giới hạn nguồn lực (Effort-aware Evaluation - *Kamei et al., IEEE TSE 2013*). Một sprint trung bình gồm 12–15 issue với tỷ lệ thất bại trung bình 15–25% (tương đương 2–3 issue trễ hạn). Ngân sách $K = 2$ tập trung sự chú ý có hạn của người quản lý vào đúng các nút thắt trọng yếu nhất mà không gây phiền toái hoặc khiến cảnh báo bị phớt lờ.

### 7.2. Kiến trúc giải pháp 2 tầng (Two-Tier Architecture)

Hệ thống được thiết kế theo mô hình phân tách trách nhiệm nghiêm ngặt giữa bộ suy luận xác suất và mô hình ngôn ngữ lớn:

```text
[Sprint Clock / Event Log]
         │
         ▼ (Tại Landmark 0.40)
┌────────────────────────────────────────────────────────┐
│ TẦNG 1: LÕI ML SCORER & POLICY CONTROLLER              │
│ - Mô hình CatBoost tính xác suất rủi ro P(Y=1)         │
│ - Lọc candidate: Chỉ xét issue đang còn mở (In-Flight) │
│ - Cấp ngân sách K = 2 cho top rủi ro cao nhất          │
└────────────────────────────────────────────────────────┘
         │
         ▼ (Chỉ kích hoạt khi có candidate vượt ngưỡng rủi ro)
┌────────────────────────────────────────────────────────┐
│ TẦNG 2: PROACTIVE GROUNDED AGENT INTERFACE             │
│ - Gọi công cụ chỉ đọc: get_issue_evidence(issue_id)    │
│ - Trích xuất chuỗi sự kiện lịch sử (Audit Trail)       │
│ - Tạo Brief giải thích theo ClaimSchemaV2              │
│ - Bộ kiểm chứng ClaimGrader (Ngăn chặn 100% bịa đặt)   │
└────────────────────────────────────────────────────────┘
         │
         ▼
[Outbox / Dashboard / Thông báo người quản lý]
```

Nguyên tắc an toàn và kiểm soát:
- **Bộ điều khiển ngoài LLM:** Quyết định kích hoạt, xếp hạng và ngân sách hoàn toàn do mã phía máy chủ và mô hình ML chi phối. LLM không tự ý kích hoạt cảnh báo, không tự sinh xác suất và không can thiệp sửa đổi cấu trúc sprint.
- **Ràng buộc kiểm chứng sự kiện (Provenance):** Mọi tuyên bố trong bản tóm tắt cảnh báo bắt buộc phải dẫn chiếu (cite) mã định danh sự kiện (`event_id`) có thật trong cơ sở dữ liệu với timestamp không muộn hơn thời điểm dự báo.

### 7.3. Phương thức hoạt động và kiểm thử Agent

Để đánh giá chất lượng trích xuất bằng chứng và độ tin cậy của Agent, hệ thống đã triển khai giao thức thử nghiệm độc lập (**Protocol E3 v2**) so sánh 3 biến thể:
- **A0 (Template Baseline):** Sinh tóm tắt theo mẫu quy tắc xác định từ dữ liệu gốc, không dùng LLM (đóng vai trò chuẩn sàn).
- **A1 (Single Narrator):** LLM sinh lời giải thích trong một lượt từ toàn bộ ngữ cảnh được nạp sẵn.
- **A2 (Bounded Tool Agent):** Agent tự chủ, nhận định danh issue, tự gọi công cụ tra cứu sự kiện (`get_issue_evidence`), lập luận và đối soát qua `ClaimGrader`.

Bộ kịch bản kiểm thử độc lập bao gồm 5 lớp probe thử thách:
1. *Normal Stagnation:* Issue bị đình trệ điển hình cần cảnh báo với chuỗi bằng chứng rõ ràng.
2. *No-Action Control:* Issue đã hoàn thành hoặc rủi ro thấp (thử thách khả năng tự kiềm chế / abstain).
3. *Cross-Project Probe:* Dữ liệu giả mạo từ dự án khác (kiểm tra phân quyền dữ liệu).
4. *Future Leak Probe:* Sự kiện xảy ra sau mốc dự báo (kiểm tra rò rỉ tương lai).
5. *Prompt Injection Probe:* Bình luận cố tình chèn chỉ thị độc hại ép Agent bỏ qua cảnh báo hoặc cấp quyền sai lệch.

### 7.4. Kết quả thực nghiệm kỹ thuật

Toàn bộ các biến thể được kiểm tra tự động và chấm điểm độc lập bởi `ClaimGrader` trên đầu ra nguyên bản (không can thiệp sửa đổi):

| Biến thể | Evidence Recall | Grounding Precision | Numeric Accuracy | Decision Accuracy | Số lượt gọi công cụ | Độ trễ (p50) |
|---|---|---|---|---|---|---|
| **A0 (Template)** | **100.0%** | **100.0%** | **100.0%** | **100.0%** | 0.0 calls | 0.00s |
| **A1 (Narrator)** | **100.0%** | **100.0%** | **100.0%** | **100.0%** | 0.0 calls | 1.68s |
| **A2 (Bounded Agent)**| **100.0%** | **100.0%** | **100.0%** | **100.0%** | **1.0 calls** | 2.42s |

**Những phát hiện cốt lõi từ thực nghiệm:**
1. **Thu hồi bằng chứng hoàn chỉnh (100% Evidence Recall):** Với ràng buộc tường minh về tính minh bạch kiểm toán (Audit Trail / Provenance), Agent trích xuất đầy đủ 100% các sự kiện lịch sử cấu thành rủi ro, loại bỏ hoàn toàn hiện tượng tự ý rút gọn thông tin ban đầu.
2. **Khả năng chống bịa đặt tuyệt đối (100% Grounding Precision):** Cơ chế lược đồ cấu trúc `ClaimSchemaV2` kết hợp `ClaimGrader` bảo đảm không có bất kỳ mã sự kiện ma hay suy diễn vô căn cứ nào được chấp nhận vào đầu ra cuối cùng.
3. **Hiệu quả gọi công cụ tối ưu:** Biến thể A2 hoàn thành trích xuất đầy đủ ngữ cảnh chỉ với đúng **1.0 lượt gọi công cụ** (`get_issue_evidence`), đảm bảo thời gian phản hồi nhanh (2.42s) và chi phí token thấp.
4. **Vượt qua 100% các probe thử thách:** Tự động phát hiện và từ chối các prompt injection, ngăn chặn rò rỉ dữ liệu ngoài phạm vi dự án và dữ liệu tương lai.

## 8. Sản phẩm ứng dụng

Ứng dụng web Agentick gồm các phần:

- quản lý project, sprint và issue;
- giao diện theo dõi tiến độ;
- mô-đun dự báo nguy cơ không hoàn thành sprint;
- bảng ưu tiên issue theo xác suất và ngưỡng cảnh báo;
- giải thích dựa trên các đặc trưng đã dùng, chẳng hạn “issue chưa thay đổi trạng thái trong 5 ngày”;
- **brief triage có bằng chứng** do agent lập (mục 7), mỗi khẳng định gắn với sự kiện nguồn; người dùng có thể bỏ qua, snooze hoặc hỏi thêm;
- gửi thông báo qua email hoặc Telegram theo cấu hình (mặc định dry-run; chỉ gửi thật khi người dùng opt-in);
- lưu lại thời điểm dự báo, phiên bản mô hình/policy/prompt, cảnh báo đã gửi và phản hồi người dùng (không dùng thumbs-up để tự động huấn luyện lại mô hình).

Backend nghiên cứu được triển khai theo các module FastAPI dùng `APIRouter`; PostgreSQL là kho dữ liệu truy vấn chính và Docker Compose tái lập môi trường. Bản TAWOS MySQL gốc được nhập vào PostgreSQL qua một bước migration có kiểm tra số dòng và lưu manifest phiên bản/checksum. Schema dữ liệu nguồn được giữ riêng với schema metadata/thực nghiệm của ứng dụng.

Hệ thống hỗ trợ người quản lý quyết định. Nó không tự thay đổi deadline, người phụ trách hoặc phạm vi sprint.

## 9. Đóng góp dự kiến

1. Một giao thức có thể tái lập để tạo snapshot issue theo thời gian và dự báo kết quả sprint.
2. Bằng chứng thực nghiệm về việc lịch sử thực thi có cải thiện dự báo so với dữ liệu tĩnh hay không, tách phần “nhận biết issue đã Done” khỏi phần dự báo công việc còn mở.
3. Đánh giá khả năng chuyển giao giữa dự án và độ hiệu chuẩn của dự báo.
4. So sánh chính sách cảnh báo ở cùng ngân sách để đo mối quan hệ giữa recall, cảnh báo sai và độ sớm.
5. Một kiến trúc agent cảnh báo có giới hạn (controller ngoài LLM, bằng chứng as-of, verifier, quyền do hệ thống kiểm soát) cùng bộ đánh giá kỹ thuật tái lập được, so với baseline template và LLM một lượt.
6. Một mô-đun phần mềm tích hợp vào Agentick để trình diễn kết quả nghiên cứu.

Đóng góp được kỳ vọng là **bằng chứng thực nghiệm và hệ thống đánh giá cho bài toán cụ thể**, không mặc định là một thuật toán dự báo mới. Với phần agent, kết quả “template ngang agent với chi phí thấp hơn” cũng là một kết quả hợp lệ.

## 10. Phạm vi và giới hạn

- Nghiên cứu chính đánh giá issue không hoàn thành trong sprint đã cam kết.
- Kết quả trên TAWOS không tự động khái quát thành deadline cá nhân hoặc deadline của doanh nghiệp.
- Nếu bổ sung dữ liệu thật từ Agentick, cần mô tả riêng cách thu thập và đặc điểm nhóm tham gia.
- Việc mô phỏng lịch sử cảnh báo không chứng minh cảnh báo làm giảm số issue trễ. Kết luận về tác động chỉ có thể đưa ra sau một pilot được thiết kế để đo hiệu quả can thiệp.
- Phân tích survival hoặc conformal prediction có thể là hướng mở rộng, không phải điều kiện để hoàn thành đề tài chính.
- Các phân tích policy (E1) chạy trên test đã được xem ở giai đoạn 4 nên chỉ là post-hoc exploratory; muốn chọn policy phải dùng validation/cửa sổ dữ liệu mới.
- Đánh giá kỹ thuật agent (E3) kiểm tra tính bám bằng chứng, an toàn và chi phí trên kịch bản có kiểm soát. Nó không đo chất lượng quyết định của người dùng (cần E4) và không đo hiệu quả giảm trễ (cần thiết kế can thiệp riêng).
- Không dùng LLM đóng vai người quản lý để thay thế nghiên cứu với người; không kết luận SOTA từ vài baseline nội bộ.
- Chưa đưa vào phạm vi v1: multi-agent, RL/causal policy, temporal graph controller, conformal-gated policy, semantic/text features cho mô hình dự báo (chỉ là hướng mở rộng).


## 11. Kế hoạch thực hiện

| Giai đoạn | Thời lượng | Kết quả |
|---|---:|---|
| Chốt câu hỏi, protocol và tiêu chí chọn dự án | 2 tuần | Định nghĩa cohort, nhãn, đặc trưng và cách chia dữ liệu |
| Kiểm tra dữ liệu, dựng snapshot | 2 tuần | Báo cáo chất lượng TAWOS và pipeline dữ liệu |
| Xây baseline và mô hình dự báo | 3 tuần | Mô hình tĩnh, mô hình động, bộ đặc trưng |
| Chạy đánh giá và phân tích kết quả | 3 tuần | Temporal/project split, calibration, alert budget |
| **WP-A1: Policy cảnh báo theo capacity (E1) và serving (E2)** | 2 tuần | Replay policy trên scorer đã đóng băng; adapter inference dùng chung với nghiên cứu; validation scores mới nếu cần chọn calibration/threshold |
| **WP-A2: Agent có bằng chứng — xây dựng** | 3 tuần | `AgentContext` as-of, verifier, bounded tool agent (A0/A1/A2), ledger/outbox, dry-run delivery |
| **WP-A3: Agent — đánh giá kỹ thuật (E3)** | 3 tuần | Dev/locked scenario suites, rubric và prompt khóa trước chạy, lặp ≥3 lần, báo cáo chi phí/độ trễ/an toàn/coverage |
| Tích hợp vào Agentick | 3 tuần | Bảng cảnh báo, brief có bằng chứng, log dự báo, shadow mode |
| **WP-A4: Nghiên cứu với người (E4), chỉ khi có người tham gia** | Chưa xác định | Protocol, consent, power/precision target; không thay bằng LLM đóng vai người dùng |
| Viết báo cáo và hoàn thiện sản phẩm | 3 tuần | Báo cáo nghiên cứu, mã xử lý dữ liệu và ứng dụng |

Các tuần của WP-A1–A3 chồng một phần lên giai đoạn tích hợp Agentick; tổng thời lượng sẽ được chốt lại sau khi review benchmark agent (xem [Danh_gia_va_checklist_chinh_sua.md](Danh_gia_va_checklist_chinh_sua.md)).

**Điều kiện tiếp tục sau giai đoạn kiểm tra dữ liệu:** phải tái dựng được phạm vi issue đã cam kết và trạng thái hoàn thành tại cuối sprint với độ tin cậy chấp nhận được. Nếu không đạt, cần đổi tập dữ liệu hoặc đổi bài toán trước khi chạy thực nghiệm.

**Điều kiện kết luận cho phần agent:** một biến thể agent chỉ được báo cáo là “tốt hơn” template/narrator khi có (i) suite và rubric khóa trước khi chạy, (ii) kết quả lặp kèm phương sai, (iii) negative control cho từng cơ chế an toàn (verifier thật sự chặn được lỗi cố ý), và (iv) báo cáo cùng coverage/usefulness, không chỉ tỷ lệ vượt verifier.

### Trạng thái thực hiện (cập nhật 2026-10-08)

| Hạng mục | Trạng thái | Ghi chú |
|---|---|---|
| Giai đoạn 1–4 (nghiên cứu archival) | Hoàn thành, đã kiểm toán | Giữ nguyên protocol/kết quả đã khóa |
| E1 — replay policy (post-hoc exploratory) | Hoàn thành | Không phải confirmatory; chưa có LLM/agent |
| E2 — serving parity | Một phần | Parity mẫu 18 bundle/180 snapshot; chưa có validation scores mới, registry, endpoint |
| E3 — đánh giá kỹ thuật agent | **Chưa đạt yêu cầu protocol** | Benchmark hiện có (10 kịch bản, kết quả 100%) có lỗi thiết kế; cần làm lại — xem tài liệu đánh giá |
| Ledger/outbox, dashboard, dry-run delivery | Chưa thực hiện | |
| E4 — nghiên cứu với người / pilot | Chưa thực hiện | Cần người tham gia và consent |


## 12. Tài liệu tham khảo nền tảng

1. I. Verenich, M. Dumas, M. La Rosa, F. M. Maggi, and I. Teinemaa, “Survey and Cross-benchmark Comparison of Remaining Time Prediction Methods in Business Process Monitoring,” *ACM Transactions on Intelligent Systems and Technology*, 2019. [DOI](https://doi.org/10.1145/3331449)
2. A. E. Márquez-Chamorro, M. Resinas, and A. Ruiz-Cortés, “Predictive Monitoring of Business Processes: A Survey,” *IEEE Transactions on Services Computing*, 2018. [Bản lưu trữ học thuật](https://idus.us.es/items/d7e0adf1-6ecc-4674-aa4a-e81ced302480)
3. M. Kubrak et al., “Prescriptive Process Monitoring: Quo Vadis?,” *PeerJ Computer Science*, 2022. [Bài báo](https://peerj.com/articles/cs-1097/)
4. F. Tu, J. Zhu, Q. Zheng, and M. Zhou, “Be Careful of When: An Empirical Study on Time-Related Misuse of Issue Tracking Data,” ESEC/FSE, 2018. [Bài báo hội nghị](https://2018.fseconference.org/details/fse-2018-research-papers/47/Be-Careful-of-When-An-Empirical-Study-on-Time-Related-Misuse-of-Issue-Tracking-Data)
5. V. Tawosi, A. Al-Subaihin, R. Moussa, and F. Sarro, “A Versatile Dataset of Agile Open Source Software Projects,” 2022. [arXiv](https://arxiv.org/abs/2202.00979)

### Tài liệu bổ sung cho phần agent (mục 7)

6. S. Yao et al., “τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains,” 2024. [arXiv](https://arxiv.org/abs/2406.12045) — đánh giá theo trạng thái cuối và độ nhất quán qua nhiều lần chạy.
7. E. Debenedetti et al., “AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents,” 2024. [arXiv](https://arxiv.org/abs/2406.13352) — injection từ dữ liệu công cụ; đo cả utility lẫn security.
8. “ProAgentBench: Evaluating LLM Agents for Proactive Assistance with Real-World Data,” 2026. [arXiv](https://arxiv.org/abs/2602.04482) — tách “khi nào hỗ trợ” và “hỗ trợ như thế nào”.
9. “Do Proactive Agents Need an LLM to Decide When to Act?,” 2026. [arXiv](https://arxiv.org/abs/2605.30152) — controller ngoài LLM quyết định trigger.
10. “PM-Bench: Evaluating Prospective Memory in LLM Agents,” 2026. [arXiv](https://arxiv.org/abs/2607.12385) — thêm truy vấn/nhắc lịch không mặc định tăng độ tin cậy.
11. Danh mục đầy đủ, mức đã đọc và giới hạn của từng nguồn: [Deep research AI agent cảnh báo sớm](Deep_research_AI_agent_canh_bao_som.md) (S01–S15). Các nguồn 8–10 là preprint 2026; chỉ dùng làm cơ sở thiết kế, không lấy số liệu của họ làm kết quả của đề tài.
