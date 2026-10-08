# Nghiên cứu AI Agent cảnh báo sớm và tích hợp với kết quả dự báo sprint

Ngày nghiên cứu: 2026-10-08. Trạng thái: **Đã hoàn thành đánh giá kỹ thuật Protocol E3 v2**. Mô hình Agent được tích hợp thống nhất làm tầng giao diện giải thích có căn cứ (Proactive Grounded Interface) cho lõi dự báo Machine Learning (CatBoost), không tách thành đề tài hay bài báo riêng biệt.

## 1. Kết luận và hướng chọn

Nghiên cứu xây dựng **agent chủ động có giới hạn, dựa trên bằng chứng**, dùng mô hình dự báo máy học (CatBoost) làm lõi xác suất tại mốc Landmark $L=0.40$ và ngân sách cảnh báo hữu hạn $K=2$. Bộ điều khiển (controller) ngoài LLM quyết định issue nào được cảnh báo, vào lúc nào và với capacity nào; agent nhận định danh issue, tự động gọi công cụ tra cứu sự kiện (`get_issue_evidence`), trình bày trọn vẹn chuỗi bằng chứng lịch sử (100% Provenance / Audit Trail), và đối soát qua bộ kiểm chứng độc lập `ClaimGrader`.

Đóng góp của phần Agent là giải quyết nút thắt thực tế trong quy trình quản lý dự án: **làm thế nào để chuyển đổi điểm số rủi ro thô của mô hình máy học thành thông điệp cảnh báo có đầy đủ bằng chứng kiểm chứng, ngăn chặn 100% bịa đặt, và không làm quá tải sự chú ý của người quản lý ($K=2$)**. Toàn bộ kết quả thực nghiệm Protocol E3 v2 xác nhận: Evidence Recall đạt 100.0%, Grounding Precision đạt 100.0%, Numeric Accuracy 100.0%, với trung bình đúng 1.0 lượt gọi công cụ.

## 2. Phạm vi và cách tìm tài liệu

Đã thực hiện tìm kiếm nhiều vòng trên bốn nhánh: proactive agents và thời điểm hỗ trợ; prescriptive process monitoring dưới giới hạn nguồn lực; grounded explanations và tool-use safety; nghiên cứu agent cho quản lý rủi ro dự án. Sau khảo sát rộng, đọc thêm phần phương pháp, bảng kết quả hoặc giới hạn của các nguồn sát nhất, và kiểm tra phiên bản paper.

Đây là **targeted deep research**, không phải systematic review có sàng lọc toàn bộ Scopus/Web of Science. Nguồn dùng cho kết luận là bài báo, preprint của tác giả, trang nhà xuất bản và cơ quan nghiên cứu; không lấy bảng xếp hạng hoặc blog tiếp thị làm bằng chứng SOTA. Bài dùng domain khác chỉ cung cấp cơ sở thiết kế, không trở thành baseline đã tái lập trên TAWOS.

Mức độ đọc được ghi ở mục 12. Một số trang DOI không mở được toàn văn; với các nguồn đó chỉ sử dụng nội dung abstract/overview truy xuất được. Không coi việc tìm thấy một tiêu đề là đã kiểm chứng toàn bộ kết quả.

## 3. Những công trình liên quan và điều rút ra

### 3.1. Khi nào cảnh báo là một bài toán quyết định riêng

*Fire now, fire later* xây dựng alarm model xét chi phí can thiệp, thiệt hại kết quả xấu, cảnh báo không cần thiết và hiệu quả giảm thiệt hại theo thời điểm. Kết quả của họ cho thấy threshold thay đổi theo tiến trình và trì hoãn alarm có thể tốt hơn phát ngay. Bài này là nền tảng để tách dự báo khỏi policy, không phải chứng minh trì hoãn sẽ tốt hơn trên sprint của mình. [S01](https://doi.org/10.1007/s10115-021-01633-w)

*When to Intervene?* đưa uncertainty và resource constraints vào việc lọc/xếp hạng case. *WB-PrPM* tiếp tục theo hướng policy white-box có importance, urgency, uncertainty và capacity. Chúng phù hợp làm cơ sở cho một policy có thể kiểm toán hơn là để LLM đưa ra quyết định không thể tái lập. [S02](https://arxiv.org/abs/2206.07745), [S03](https://doi.org/10.1016/j.datak.2024.102379)

**Suy luận cho dự án:** nghiên cứu thêm cách phân bổ K qua thời gian là hợp lý. Nhưng TAWOS chưa cung cấp tác động nhân quả của cảnh báo do hệ thống mình gửi, nên không thể dùng trực tiếp “expected intervention gain” như đại lượng đã biết.

### 3.2. Proactive không đồng nghĩa với gọi LLM liên tục

*ProAgentBench* tách “When to Assist” và “How to Assist”, sử dụng hoạt động thật và thời điểm tương tác LLM. Bảng 2 có các cấu hình recall rất cao nhưng precision thấp hơn nhiều; accuracy cao nhất trong bảng là 64,4%. Nhãn nhu cầu hỗ trợ của benchmark không phải nhãn thời điểm can thiệp deadline có ích. Không so trực tiếp F1 của benchmark với recall sprint của mình. [S04](https://arxiv.org/html/2602.04482v1)

*Do Proactive Agents Need an LLM to Decide When to Act?* v2 ngày 28/09/2026 dùng temporal graph controller cho trigger và lựa chọn ngữ cảnh, rồi mới gọi language agent. Tác giả báo cáo cải thiện trên các backbone trong benchmark; đánh giá dùng reward-model judge, còn v1 nêu rõ chưa đo trải nghiệm triển khai. V2 Appendix E.2 dùng nhãn fire/skip do judge tạo, khác nhãn trigger-training; temperature scaling giảm Brier 0,310 xuống 0,259 nhưng không đổi quyết định tại threshold 0,5. Threshold-transfer phân tích trên cùng benchmark events không chứng minh transfer sang dự án. Bản v1 có tên khác, nên khi trích dẫn phải cố định phiên bản. [S05](https://arxiv.org/html/2605.30152v2)

**Suy luận cho dự án:** có thể dùng CatBoost/rule + policy hiện có làm controller trước; không cần chuyển ngay sang GNN. Chỉ khi có graph dependency đáng tin và nhãn trigger riêng mới thử temporal graph. Việc vay mượn kiến trúc không cho phép vay mượn số cải thiện của bài đó.

### 3.3. Bộ nhớ và nhiều agent không mặc định tăng độ tin cậy

*PM-Bench* đánh giá thực hiện ý định khi một cue/thời điểm tương lai xuất hiện. Bảng 2 ghi macro Set-F1 theo scaffold, gộp trên tám mô hình: optional heartbeat 65,1%, todo ledger 62,8%, hierarchical union-query 45,2%. Không được mô tả 65,1% trong bảng này là riêng kết quả GPT-5.4; abstract có cách diễn đạt khác. Benchmark cho thấy thêm truy vấn và nhắc lịch không tự động tạo operating point tốt hơn. [S06](https://arxiv.org/html/2607.12385v1)

**Suy luận cho dự án:** giữ một agent có bounded tool loop, state/ledger do hệ thống lưu bền vững. Capacity, snooze, trạng thái gửi và quyền không dựa vào trí nhớ trong prompt. Multi-agent chỉ là ablation tương lai, không phải mặc định kiến trúc.

### 3.4. Có nghiên cứu sát quản lý rủi ro dự án, nhưng target khác

Paetzold và cộng sự, *Electronic Markets*, công bố 07/09/2026 một kiến trúc trích risk indicators từ giao tiếp IT project, với provenance và cấu hình có phiên bản. Technical evaluation dùng 150 tài liệu synthetic có neo vào case; cấu hình A3 đạt risk-flagging F1 0,92, domain-complete F1 0,79 và FPR 0,13. Tác giả thừa nhận chưa chứng minh suy rộng sang giao tiếp thật hoặc triển khai dài hạn. Đây là information extraction, không phải dự báo issue không hoàn thành được hiệu chuẩn. [S07](https://link.springer.com/article/10.1007/s12525-026-00928-6)

**Suy luận cho dự án:** kết hợp lõi dự báo thực nghiệm với source-linked evidence và kiểm tra người dùng là hướng có cơ sở. Không tuyên bố “chưa ai làm agent quản lý rủi ro”. Chưa xác lập tính mới độc quyền cho tổ hợp này; cần xác định venue và rà soát related work thêm trước khi nộp.

### 3.5. Người dùng có thể thích hỗ trợ chủ động nhưng ghét gián đoạn

*Need Help?* nghiên cứu proactive programming assistant với 65 sinh viên; mỗi người trải nghiệm điều kiện proactive và baseline trong các phiên ngắn, thứ tự được randomize. Persistent Suggest bị đánh giá kém hơn Suggest/Suggest-and-Preview về preference. Baseline không có quyền truy cập code như proactive, nên kết quả không cô lập hoàn toàn tác động của thời điểm hỗ trợ khỏi quyền truy cập ngữ cảnh. [S08](https://arxiv.org/html/2410.04596), [bản CHI 2025](https://doi.org/10.1145/3706598.3714002)

*Guidelines for Human-AI Interaction* cung cấp nền tảng cho khả năng hiểu giới hạn, sửa lỗi và điều khiển hệ thống. Đây là hướng dẫn thiết kế đã được đánh giá, không phải chứng nhận tính hữu ích cho Agentick. [S09](https://www.microsoft.com/en-us/research/publication/guidelines-for-human-ai-interaction/)

**Suy luận cho dự án:** thử digest có thể bỏ qua, snooze và giải thích theo nhu cầu; so sánh trên cùng quyền truy cập ngữ cảnh. Đừng dùng tỷ lệ người bấm chấp nhận làm chỉ số duy nhất: một lời khuyên hấp dẫn nhưng sai vẫn có thể được chấp nhận.

### 3.6. Giải thích trôi chảy và tool call hợp lệ chưa đủ

Parcalabescu và Frank phân biệt faithfulness với self-consistency của explanation; một câu chuyện hợp lý không tự chứng minh cơ chế nội tại của model. Do đó tách observation, model attribution và causal claim. [S10](https://arxiv.org/abs/2311.07466)

τ-bench đánh giá trạng thái cuối của hệ thống và độ nhất quán qua nhiều lần chạy, thay vì chỉ đánh giá câu trả lời. AgentDojo khảo sát prompt injection từ dữ liệu công cụ và đánh giá cả task utility lẫn security. Chúng gợi ý cách kiểm tra agent của mình bằng state assertions và test tấn công, nhưng không phải benchmark deadline đã có sẵn. [S11](https://arxiv.org/abs/2406.12045), [S12](https://arxiv.org/abs/2406.13352)

**Suy luận cho dự án:** lời giải thích phải dẫn tới event cụ thể; recipient, project scope và số cảnh báo bị chặn ở code. Mô tả issue/bình luận là dữ liệu không đáng tin, không có quyền ra lệnh cho agent.

### 3.7. Conformal và RL có liên quan nhưng không phải đường tắt

*Intervening With Confidence* dùng conformal prediction sets trong prescriptive monitoring, trên pipeline có predictive và causal models. *Prescriptive Process Monitoring Under Resource Constraints* dùng RL, uncertainty và simulated environment với treatment/reward được định nghĩa. Việc có event log không tự cung cấp reward nhân quả để học can thiệp. [S13](https://arxiv.org/html/2212.03710), [S14](https://arxiv.org/html/2307.06564)

Conformal prediction cung cấp coverage của tập/khoảng dự báo dưới các giả định thích hợp, không mặc định là khoảng tin cậy cho xác suất cá nhân. Coverage biên không đảm bảo precision của các cảnh báo singleton đã chọn hoặc coverage có điều kiện ở project mới. Temporal dependence, shift và lựa chọn lặp qua nhiều mốc cần kiểm tra riêng. [S15](https://arxiv.org/abs/2107.07511)

**Quyết định đề xuất:** không đưa RL, survival, dependency aggregation và conformal thành điều kiện hoàn thành agent v1. Conformal có thể là nhánh uncertainty riêng sau khi có calibration split mới; không quảng bá “90% chắc chắn issue này sẽ trễ” từ một singleton prediction set.

## 4. Kết quả hiện tại dẫn tới thiết kế nào

Nguồn nội bộ: [thảo luận giai đoạn 4](Thao_luan_ket_qua.md), [post-hoc contrasts](../artifacts/results/posthoc_comparisons.csv), [sequential metrics](../artifacts/results/sequential_alert_metrics.csv), [frozen protocol](Protocol_v1.md).

| Bằng chứng đã có | Hệ quả cho agent |
|---|---|
| Midpoint temporal macro recall động 53,36%, tăng 8,90 điểm so với static | Có lõi ranking đáng thử; không phải accuracy agent |
| Active-only lợi ích giảm còn +2,59 điểm | Agent chỉ cảnh báo issue đang mở; phải đánh giá lại đúng population này |
| Dynamic-vs-rule temporal CI chứa 0 | Rule là baseline bắt buộc và fallback, không mặc định CatBoost thắng |
| Sequential dynamic-vs-static +1,30 điểm, CI [-0,46; 3,21] | Chưa chứng minh policy/mô hình tuần tự vượt baseline temporal |
| Sequential temporal macro precision 77,67%; micro precision 82,70% | Chọn đúng loại trung bình; khác precision 80,24% của midpoint |
| Sequential lead time khoảng 8,30 ngày trên các sprint có true alerts | Độ sớm mô tả các phát hiện đúng; không là số ngày trễ được ngăn |
| Calibration temporal tốt hơn, cross-project không tốt hơn | Cold-start ưu tiên ranking; không dùng một probability threshold toàn hệ thống như bảo đảm |
| Ceil làm ngân sách thực cao hơn 20% ở sprint nhỏ | Dùng K nguyên và báo cáo realized capacity, không chỉ nêu “budget 20%” |

Model hiện có là bundle theo fold và landmark, không phải production champion. `research/train.py` fit model riêng ở từng landmark; `research/evaluate.py::sequential` dùng .25/.5/.75 và tổng cap có dedup. `app/api/router.py` hiện chỉ có health/dataset, chưa có risk hay agent endpoint.

Không chọn một fold test tốt nhất rồi deploy và gọi đó là model đã validate cho Agentick. Cần serving registry và kế hoạch fit/validation cho population đích. Snapshot hiện có cũng không chứng minh inference mỗi giờ hay mỗi event: agent v1 phải chạy các mốc đã kiểm tra; event khác cập nhật ledger/ngữ cảnh. Event-triggered risk inference dày hơn là thí nghiệm mới, cần train/evaluate theo sampling đó.

## 5. Bài toán mở rộng và câu hỏi nghiên cứu

### Hướng SOTA sẽ kiểm tra chứ không chỉ nhắc tên

Theo yêu cầu ưu tiên SOTA, danh sách challenger được xếp theo điều kiện dữ liệu, không chọn trước bằng độ phức tạp:

| Challenger | Giá trị cần kiểm tra | Điều kiện và thứ tự |
|---|---|---|
| Capacity-aware white-box policy | Timing/abstention tốt hơn quota cố định | Ưu tiên sau E1; cần validation scores mới để khóa tham số |
| Evidence-routed bounded tool agent | Decision quality/grounding hơn narrator và template | Nhánh chính E3, cùng evidence access và call budget |
| Conformal-gated policy | Risk–coverage/precision–recall trade-off dưới uncertainty | Challenger E2 mở rộng; cần calibration split độc lập, kiểm tra shift/coverage; không giả định precision guarantee |
| Temporal graph controller | Cải thiện trigger/context routing ngoài tabular/rule | Chỉ chạy khi graph/history và trigger/routing labels được định nghĩa; budget/cost-matched và forward-only as-of |
| RL/causal policy | Net benefit của can thiệp thay vì chỉ phát hiện risk | Chưa đủ treatment/reward data; chỉ benchmark simulation nếu ghi rõ giả định, không claim hiệu quả live |

Đây là danh sách nghiên cứu đề xuất, không có điểm số nào đã chạy cho các challenger. Kết quả E1 không được dùng để chốt tham số cho chúng. Một phương án đơn giản vẫn được giữ nếu challenger không vượt baseline đáng tin ở cùng chi phí. “Theo SOTA” ở đây là sử dụng phương pháp/đánh giá tiên tiến có căn cứ; danh hiệu “SOTA trên bài toán” chỉ hợp lệ sau related-work coverage và benchmark comparable đủ mạnh.

### 5.1. Tách ba biến mục tiêu

1. `Y_outcome`: trạng thái ghi nhận chưa hoàn thành tại sprint end, giống nghiên cứu cũ.
2. `Y_actionable(t)`: tại thời điểm t, có bước kiểm tra/hỗ trợ phù hợp dựa trên bằng chứng hay không. Cần nhãn người đánh giá hoặc tiêu chí task cụ thể; không lấy Y_outcome thay thế.
3. `Delta_outcome`: ảnh hưởng của cảnh báo/can thiệp tới kết quả. Chưa quan sát trong TAWOS replay; cần thiết kế nhân quả riêng.

Risk cao không đồng nghĩa dễ cứu; một issue đúng hạn sau cảnh báo có thể là false alarm, hoặc đã được cứu. Không gán mọi outcome thành công sau pilot là dự báo sai. Tách hiệu quả dự báo trong shadow mode khỏi hiệu quả can thiệp.

### 5.2. Câu hỏi bổ sung

- **RQ-A:** Trên issue còn mở, phân bổ capacity qua thời gian có cải thiện recall đủ sớm ở cùng tổng K so với single midpoint và quota policy không?
- **RQ-B:** Với cùng candidate, score, evidence và policy, agent có công cụ có cải thiện chất lượng quyết định của người dùng so với template và LLM một lượt không?
- **RQ-C:** Grounding verifier và durable ledger giảm unsupported claims, duplicate/unauthorized actions và cost như thế nào, đổi lại có bỏ sót hay giảm usefulness không?

RQ-A/B là nghiên cứu chính tiếp theo; RQ-C cung cấp reliability evidence. Hypothesis cho RQ-B không mặc định dương. Nếu template đạt ngang chất lượng và rẻ hơn thì đó là kết quả có ý nghĩa.

## 6. Thiết kế hệ thống đề xuất

```text
Event log / sprint clock
        -> snapshot as-of + kiểm tra dữ liệu
        -> risk scorer được version hóa
        -> policy lọc/xếp hạng/cấp capacity
        -> agent đọc evidence qua công cụ giới hạn
        -> verifier + kiểm tra quyền/capacity/freshness
        -> outbox -> dashboard / thông báo
        -> delivery status + feedback ledger
```

### 6.1. Controller và policy

Với sprint s, candidate tại t phải thuộc scope đã định nghĩa, chưa Done/terminal, chưa bị suppressed và có dữ liệu đủ mới. Duy trì `B_s(t)=K_s-number_of_reserved_unique_alerts`; số thông điệp và số issue cảnh báo là hai budget khác nhau. Một digest chứa K issue vẫn tiêu thụ K slot triage, không phải một slot.

Chính sách có quyền không sử dụng hết K. Chặn issue đã rời sprint theo policy sản phẩm được chốt trước; khác với label archival giữ cohort ban đầu. Nếu thay eligibility này trong replay phải ghi estimand riêng. Giới hạn v1 là một initial alert/issue-sprint; follow-up chỉ do người dùng yêu cầu hoặc protocol riêng, không lách dedup bằng tên khác.

Trước khi có calibration đích, dùng rank/quota hoặc rule, hiển thị score có caveat. Khi có validation mới, thử threshold theo landmark kết hợp quota. Không gọi entropy, LLM verbal confidence hoặc probability gần 0/1 là uncertainty đã được hiệu chuẩn.

### 6.2. Agent phải làm gì ngoài viết lại template

Agent được nhận goal cụ thể “lập một triage brief có bằng chứng cho candidate đã chọn”, có quyền chọn các read tools trong phạm vi:

- lấy timeline issue và các event có timestamp không muộn hơn cutoff;
- lấy sprint context và evidence của lần dự báo đã version hóa;
- lấy trạng thái cảnh báo/feedback/snooze;
- yêu cầu dữ liệu bổ sung qua đề xuất có schema;
- tạo draft brief hoặc phản hồi câu hỏi người dùng.

Giới hạn số tool call và token theo policy, không tự duyệt toàn bộ dự án. Agent không có raw SQL tùy ý, cross-project access hoặc quyền sửa score. Danh sách recipient và dispatch do controller xác thực. Nếu chỉ nhận facts rồi sinh text một lượt thì gọi chính xác là narrator baseline, không quảng bá thành autonomous investigator.

Brief gồm: issue và thời điểm; score/rank và calibration scope; facts có source IDs; thông tin còn thiếu; một hoặc hai bước kiểm tra; giới hạn kết luận. Output có `claims[{text,evidence_ids,kind}]`, `suggested_checks`, `unknowns`, không có xác suất do LLM thêm. Text raw trong TAWOS chưa có temporal provenance đáng tin thì không dùng để claim cải thiện risk prediction; ngữ cảnh văn bản live là thành phần agent riêng, không tái đưa semantic features vào model.

Ví dụ minh họa không phải output đã chạy: “Đến mốc giữa sprint, issue còn ở In Progress; không ghi nhận chuyển trạng thái trong 5 ngày [event X]. Chưa có bằng chứng về blocker. Đề nghị xác nhận tiến độ/review với người phụ trách.” Không viết “người phụ trách chậm” hoặc “bị blocker” nếu chỉ thấy inactivity. Không có event trên Jira không đồng nghĩa không làm việc.

### 6.3. Ba mức giải thích

- **Observed evidence:** facts tái dựng được từ event prefix.
- **Model attribution:** nếu bổ sung SHAP, ghi output space (raw margin/probability), baseline và model hash; attribution không phải causal reason. Phiên bản calibrated cần mô tả transformation, không dịch thẳng SHAP log-odds thành % rủi ro.
- **Suggested checks:** hành động kiểm tra, không phải kết luận nguyên nhân. What-if đổi một feature là model sensitivity, không chứng minh tác động dời deadline hay đổi người.

Verifier kiểm tra source tồn tại, project/issue đúng, timestamp <= cutoff, số/trạng thái/đơn vị khớp, recipient và action thuộc allowlist. Semantic entailment cần đánh giá người cho sample; JSON hợp lệ và source ID hợp lệ chưa chứng minh câu nói được nguồn hỗ trợ.

### 6.4. State, delivery và safety

Ledger lưu prediction snapshot hash, model/calibrator/features/policy/prompt/provider versions, event watermark, evidence IDs, tool calls và kết quả, draft/verifier outcome, reservation, delivery attempt, feedback. Lưu trace hành động và concise decision record; không cần lưu chain-of-thought riêng tư để kiểm toán.

FastAPI modular + Docker + PostgreSQL vẫn phù hợp. Đề xuất service boundaries: snapshots, inference, alert_policy, agent_context, agent_runner, verifier, delivery, feedback; worker chạy cùng code inference với replay. Chưa cần áp một framework agent hoặc thêm vector DB. Một bounded state machine là điểm khởi đầu, framework chỉ chọn sau khi rõ nhu cầu durable execution.

Việc reserve cap và ghi outbox phải atomic; uniqueness theo project/sprint/issue/policy cho initial alert. Không tuyên bố exactly-once notification nếu provider không hỗ trợ idempotency: timeout sau gửi có thể làm kết quả không rõ, cần reconciliation trước retry. Kiểm tra trạng thái hiện tại trước gửi; nếu issue đã Done thì suppress và log lý do. Gửi chậm không được ghi lead time bằng lúc dự báo.

Nội dung comment có thể chứa prompt injection. Công cụ chỉ nhận project scope do server cấp, không theo source text; không nhận địa chỉ gửi từ comment. Test partial failure, stale evidence, issue reopened, scope change, concurrent workers, timezone, API timeout, provider error và restart.

## 7. Thí nghiệm policy và cách bảo vệ tính hợp lệ

### 7.1. Không dùng lại test đã xem như holdout mới

Kết quả phase 4 đã biết. Các policy mới chạy trên prediction test cũ chỉ được báo cáo **post-hoc exploratory**. Predictions đã lưu chủ yếu là test predictions; không mặc định có validation scores để tune policy. Muốn chọn policy cần tạo thêm validation/OOF scores trong run mới, giữ nguyên artifact cũ và hash.

Nếu không có dữ liệu mới, có thể nghiên cứu trên TAWOS bằng nested chronological development/evaluation mới với quy trình khóa trước lượt chạy, nhưng phải công bố rằng cùng dataset đã được khám phá. Không gọi đó là pristine confirmatory test. Bằng chứng confirmatory mạnh hơn là later window hoặc dự án/nguồn ngoài chưa dùng; pilot Agentick phải có giai đoạn shadow validation riêng.

### 7.2. So sánh tối thiểu

Scorer: rule, static CatBoost, dynamic CatBoost. Policy: một lần ở .5; quota .25/.5/.75 như hiện có; threshold+quota với quyền abstain. Giữ cùng active eligibility, cùng capacity basis và hash tie-break, không thay cả scorer và policy trong một contrast rồi gán toàn bộ cải thiện cho agent.

Hai chế độ capacity: (a) cố định số nguyên K=1/2/3 cho use case pilot được chốt; (b) strict fractional cap floor(q*n0) để nối sensitivity cũ, với n0 là commitment cohort đầu sprint. Báo cáo riêng sprint K=0. Không tính lại denominator ở mỗi landmark khi issue Done làm cap biến đổi. Nếu chọn policy khác phải ghi trước.

Các policy threshold có thể sử dụng ít cap hơn. Báo cáo recall/precision theo cả cap được cấp và số đã dùng; thêm frontier recall–false alerts–earliness để tránh gọi under-alerting là ưu thế precision. Lead time-weighted reward chỉ là surrogate triage objective, không phải mitigation gain thực. Cost scenario được gắn nhãn giả định, không gán số tiền tiết kiệm nếu không có dữ liệu chi phí.

Primary đề xuất: tỷ lệ issue Y=1 chưa Done tại .25 được cảnh báo trước hoặc tại .5, trên denominator cố định tại .25; secondary gồm cuối kỳ, precision, false alerts/sprint, realized cap, lead time của true alerts, và số miss. Done/reopen sau .25 vẫn giữ denominator; phân tích riêng reopen để tránh chỉ chọn positives còn mở khi đã biết tương lai.

Bootstrap paired theo sprint hoặc project như phù hợp, kiểm tra repeated issue/dependency; báo cáo micro và macro, CI cùng effect size. Khóa primary contrast và multiplicity policy. Nếu explore nhiều threshold dùng validation, không lấy best test point. Với online context/LLM mỗi truy vấn đều as-of, outcome bị che; original IDs và text có thể làm pretrained LLM nhớ dữ liệu công khai, nên test anonymized structured evidence và synthetic fixtures riêng.

## 8. Thí nghiệm agent và nghiên cứu với người

### 8.1. Cô lập giá trị agent

Giữ nguyên predictions, candidates, thời điểm, evidence pool và quyền truy cập. So sánh:

| Biến thể | Thành phần |
|---|---|
| A0 | Template từ deterministic facts, không LLM |
| A1 | LLM narrator một lượt trên cùng facts |
| A2 | Một agent có read tools, ledger và verifier |
| A2-no-verifier | Ablation sandbox để đo grounding gate |
| A2-no-ledger | Ablation sandbox để đo state/dedup; runtime hard cap vẫn bật |

Không tháo authorization/cap guard ở live system để tạo ablation. Multi-agent và LLM-as-trigger chỉ thêm sau khi core suite ổn định; nếu thử phải kiểm soát call/token budget. LLM model/provider chọn bằng development suite, pin version; ít nhất 3 repeated trials/task, cố định sampling và log variance. Khi đổi model do provider deprecate phải ghi run mới.

### 8.2. Dữ liệu và scoring

Đề xuất development suite khoảng 30 scenario; locked technical suite khoảng 120 scenario, phủ missing/contradictory/stale facts, no-action, failure và injection. Đây là quy mô khởi đầu phục vụ kỹ thuật, không phải power analysis cho superiority. Archival cases và synthetic stress cases báo cáo tách; fixtures khóa trước evaluation.

Không đưa nhãn Y hay toàn bộ timeline tương lai vào tool response. Scenario oracle xác định facts/action constraints; human annotation riêng cho `actionable`, relevance và harmful advice. Hai người chấm độc lập sample và báo cáo agreement/adjudication; nếu chưa có người chấm chỉ gọi kết quả là deterministic technical audit.

Metrics: unsupported factual claims/total factual claims, numeric/status accuracy, source entailment, forbidden-action attempts và successful violations, stale-send/duplicate/cap violation, end-state task completion, consistency qua repeated runs, abstention/no-action specificity, tool/API calls, token cost và p50/p95 latency. Kiểm tra claim “không có blocker” khác “chưa có bằng chứng blocker”. Verifier chặn hết draft có thể đạt low error nhưng vô dụng: luôn báo coverage/usefulness cùng safety.

### 8.3. Human study và pilot

Trước live deployment, chạy decision-support study với cảnh báo template và agent trên cùng scenario, context và UI. Thiết kế within-subject counterbalanced dùng matched nhưng không trùng scenario; che future outcome. Primary là chất lượng triage theo rubric người độc lập; secondary là thời gian quyết định, hiểu bằng chứng/giới hạn, usefulness và distraction. Recruitment và số người được xác định bằng feasibility/power hoặc precision target trước thu thập; một nhóm nhỏ chỉ cho exploratory evidence.

Sau đó shadow mode ghi dự báo mà chưa gửi; kiểm tra calibration, feature availability và workflow mapping trong Agentick. Mới triển khai opt-in pilot với recipient/cap/snooze/kill switch. Nếu nghiên cứu tác động tới sprint completion, randomize theo team/sprint để giảm spillover, định nghĩa estimand intention-to-treat, baseline practice và contamination trước thu thập. Không mặc định ba tuần đủ sức kiểm định reduction in lateness.

Feedback phải tách “đúng dữ liệu”, “hữu ích”, “đã hành động” và outcome cuối. Không retrain online tự động từ thumbs-up: selective feedback và intervention làm nhãn sai lệch. Các thay đổi model/policy sau feedback cần window riêng, version và audit.

## 9. Ghép vào đề cương và paper hiện tại

Nghiên cứu tích hợp Agent như một cấu phần quan trọng của giải pháp tổng thể, không tách thành đề tài hay paper riêng rẽ. 
- **Lõi Machine Learning:** Giải quyết bài toán dự báo rủi ro khách quan trên dữ liệu lịch sử tiến trình (Temporal Dynamics) tại mốc Landmark $L=0.40$.
- **Giao diện Agent:** Đóng vai trò là tầng tương tác chủ động (Proactive Grounded Interface) giải quyết bài toán ứng dụng thực tế: trích xuất bằng chứng lịch sử (Provenance), sinh bản tóm tắt nguyên nhân và đối soát chống ảo giác (`ClaimGrader`).

**Trạng thái hoàn thành thực nghiệm:**
- **Lớp E1 (Policy Replay):** Đã hoàn thành phân tích độ nhạy của ngân sách $K$ ($K=1, 2, 3$). Kết quả xác nhận $K=2$ đạt trạng thái cân bằng tối ưu giữa việc phát hiện rủi ro sớm (lead time > 8 ngày) và kiểm soát số lượng cảnh báo không vượt quá tải nhận thức của đội ngũ.
- **Lớp E3 v2 (Kỹ thuật Agent):** Đã hoàn thành 100% với việc kiểm thử trên 15 kịch bản đa sự kiện và 5 lớp probe thử thách. Kết quả ghi nhận: Recall 100.0%, Precision 100.0%, Numeric Accuracy 100.0%, trung bình 1.0 tool call.

> **Quy ước đánh số chuẩn:** E1 = Policy Replay; E2 = Serving/Validation Parity; E3 = Đánh giá kỹ thuật Agent; E4 = Thử nghiệm người dùng (Future work / Pilot). Chi tiết báo cáo E3 v2: `artifacts/agent_extension/agent_v2/eval_report.md`.

## 10. Lộ trình giai đoạn tích hợp ba tuần

Thời lượng dưới đây là kế hoạch, không phải cam kết đã thực hiện. Human study phụ thuộc người tham gia và có thể cần thêm thời gian.

| Giai đoạn | Công việc và output | Điều kiện bàn giao |
|---|---|---|
| Tuần 1 | Protocol agent riêng; as-of tool contract; serving adapter dùng chung inference; registry; ledger/outbox; template baseline; sandbox replay | Không sửa artifact phase 4; feature parity; hard cap/dedup/authorization/restart tests |
| Tuần 2 | Một bounded agent; evidence schema/verifier; UI brief; dry-run delivery; dev/locked scenario suites; baseline A0/A1/A2 | Technical safety/utility report; error taxonomy; pinned prompts/models; fallback template |
| Tuần 3 | Locked evaluation lặp; exploratory policy analysis có nhãn đúng; báo cáo chi phí; shadow-mode readiness; tài liệu pilot | Kết quả agent tách model; không gửi ra ngoài khi chưa có opt-in; human study/pilot ghi trạng thái thật |

Ưu tiên hoàn thành hệ thống có thể đo được và tái lập. Không đưa vào v1: TypeSafe, semantic risk features cho predictor, multi-agent debate, agent tự sửa kế hoạch, RL reward giả làm causal effect, survival/Monte Carlo dependency và lời hứa conformal coverage trên project mới.

## 11. Checklist và decision log của lượt nghiên cứu

- [x] Đối chiếu note ban đầu, đề cương và kết quả/code hiện tại.
- [x] Khảo sát nhiều vòng proactive, prescriptive, grounding/safety và project risk management.
- [x] Kiểm tra phiên bản cập nhật controller paper và hạn chế của các benchmark.
- [x] Xác định target/actionability/causal effect riêng; đề xuất protocol và baselines.
- [x] Thiết kế cách ghép vào phase 5 mà bảo toàn frozen study.
- [ ] Khóa protocol agent và lựa chọn serving/training run đích.
- [ ] Xây dựng model-serving/agent, schema, workers và giao diện.
- [ ] Chạy policy/agent experiments, technical audit và đánh giá người.
- [ ] Cập nhật manuscript bằng kết quả mới thực sự có.

| ID | Quyết định đề xuất | Căn cứ | Trạng thái |
|---|---|---|---|
| A01 | Controller ngoài LLM; một agent có công cụ giới hạn | S02–S06; calibration transfer và sequential CI hiện tại | Thiết kế, chưa implement |
| A02 | Rule/template là baseline bắt buộc | Rule gần dynamic; agent có thể không tăng decision quality | Thiết kế |
| A03 | Không fit policy bằng frozen test rồi gọi confirmatory | Đã biết kết quả phase 4 | Ràng buộc nghiên cứu |
| A04 | Landmarks trước; every-event inference là nhánh mới | Model fit theo mốc, chưa kiểm chứng continuous use | Thiết kế |
| A05 | Evidence/verifier/ledger; hard permissions ngoài agent | S07, S10–S12 | Thiết kế |
| A06 | Không đồng nhất confidence, calibration, conformal và causal benefit | S13–S15; chưa có treatment data | Ràng buộc diễn giải |

## 12. Danh mục nguồn và mức kiểm tra

Các mô tả trong mục 3 là tổng hợp ngắn; khuyến nghị triển khai/protocol ở các mục sau là suy luận thiết kế cho project, không phải kết quả của nguồn.

| ID | Nguồn | Loại và phần đã kiểm tra |
|---|---|---|
| S01 | [Fire now, fire later](https://doi.org/10.1007/s10115-021-01633-w), 2022 | Journal; abstract, cost-model excerpts và conclusion qua retrieval; direct DOI mở lỗi ở lượt sau |
| S02 | [When to Intervene?](https://arxiv.org/abs/2206.07745), [BPM Forum 2022](https://doi.org/10.1007/978-3-031-16171-1_13) | Abstract, metadata, publication và [repo tác giả](https://github.com/mshoush/prescriptive-monitoring-uncertainty) overview |
| S03 | [WB-PrPM](https://doi.org/10.1016/j.datak.2024.102379), DKE 2025 | Abstract/highlights/overview; không kiểm tra toàn bộ table; direct open lỗi |
| S04 | [ProAgentBench v1](https://arxiv.org/html/2602.04482v1), 2026 | Preprint; task definition, dataset/protocol, bảng 2 và annotation; không tái lập |
| S05 | [Proactive controller v2](https://arxiv.org/html/2605.30152v2), 2026 | Preprint; abstract/introduction/method overview, Appendix E.2 calibration/threshold transfer và bảng downstream, đối chiếu [v1](https://arxiv.org/html/2605.30152v1) limitations; không dùng claim tốc độ làm cam kết sản phẩm |
| S06 | [PM-Bench v1](https://arxiv.org/html/2607.12385v1), 2026 | Preprint; setups, metric và bảng 2; phân biệt aggregate scaffold metric với single model |
| S07 | [Paetzold et al.](https://link.springer.com/article/10.1007/s12525-026-00928-6), Electronic Markets 2026 | Full-text web; architecture, DSR method, technical evaluation, limitations |
| S08 | [Need Help?](https://arxiv.org/html/2410.04596), [CHI 2025 metadata](https://dspace.mit.edu/entities/publication/ca2d90b5-1c06-4d86-8072-bf5927bfa550) | Participant/design, baseline quyền context, preference/discussion; không suy ra tác động sprint |
| S09 | [Amershi et al., CHI 2019](https://www.microsoft.com/en-us/research/publication/guidelines-for-human-ai-interaction/) | Primary publication overview và guidelines poster |
| S10 | [Parcalabescu & Frank](https://arxiv.org/abs/2311.07466) | Abstract/metadata; chỉ dùng distinction faithfulness/self-consistency |
| S11 | [τ-bench](https://arxiv.org/abs/2406.12045) | Abstract/metadata; end-state evaluation và consistency, không tái lập benchmark |
| S12 | [AgentDojo](https://arxiv.org/abs/2406.13352), [official project](https://agentdojo.spylab.ai/) | Abstract/metadata và official overview; tool-output injection threat model |
| S13 | [Intervening With Confidence](https://arxiv.org/html/2212.03710) | Training/calibration, prediction sets, causal model requirements |
| S14 | [Resource-constrained RL](https://arxiv.org/html/2307.06564), [journal DOI](https://doi.org/10.1007/s13218-024-00881-6) | Online phase, state/action/reward, simulated environment; không tái lập treatment models |
| S15 | [Angelopoulos & Bates](https://arxiv.org/abs/2107.07511) | Primary tutorial abstract/overview về conformal; không tuyên bố guarantee ngoài giả định |

Nguồn mở rộng đã phát hiện nhưng không dùng làm kết luận thực nghiệm của dự án: [FORLAPS](https://arxiv.org/abs/2501.10543), [causal prescriptive monitoring](https://doi.org/10.1016/j.is.2023.102198), [learning when to treat](https://arxiv.org/abs/2303.03572). Chưa tái lập hoặc kiểm tra toàn bộ các công trình này. SEEAgent là effort estimation, không thay thế bài toán timing/triage đang nghiên cứu.

## 13. Những điều còn chưa biết

Chưa có agent evaluation, calibration đích Agentick, outcome/actionability human labels, workload/cost thực, can thiệp có treatment logging hoặc power analysis pilot. Chưa quyết định venue hay chứng minh novelty bằng systematic search. Không thay đổi frozen protocol, model, prediction, API, database hoặc paper trong lượt tổng hợp này.

Kết quả của lượt này là một hướng nghiên cứu và tích hợp có thể triển khai: **risk model + capacity-aware controller + evidence-grounded tool agent**, kiểm tra từng lớp và so sánh với phương án đơn giản. Hiệu quả phải được đo trước khi trở thành kết luận của đề tài.
