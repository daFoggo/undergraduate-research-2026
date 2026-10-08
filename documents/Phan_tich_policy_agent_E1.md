# Phân tích exploratory về policy cảnh báo chủ động E1

Ngày 2026-10-08. [Protocol](Protocol_agent_extension_v1.md) được viết trước khi tính metric mới; frozen test phase 4 đã được xem nên đây vẫn là post-hoc exploratory. Nguồn: [summary](../artifacts/agent_extension/policy_v1/summary.csv), [contrasts](../artifacts/agent_extension/policy_v1/contrasts.csv), [report đầy đủ](../artifacts/agent_extension/policy_v1/report.md), [audit độc lập](../artifacts/agent_extension/policy_v1/independent_audit.json).

## Kết quả đáng chú ý

Với dynamic CatBoost/raw ranking, cap tối đa K=2 mỗi sprint (min với evaluation cohort size), và denominator giữ các issue còn mở tại .25:

| Temporal | Quota .25/.5/.75 | Một lần tại .5 |
|---|---:|---:|
| Early recall macro sprint | 58,77% | 59,20% |
| Precision gộp | 77,31% | 79,70% |
| True alerts | 518 | 526 |
| False alerts | 152 | 134 |
| Alerts đã dùng / capacity được cấp | 670 / 728 | 660 / 728 |
| Lead days macro trong sprint có true alerts | 8,18 | 6,29 |

Quota trừ midpoint về early recall là -0,43 điểm phần trăm, CI [-1,36; 0,55], n=336 positive sprints. Chưa có bằng chứng khác biệt temporal cho contrast này; không phải kết luận tương đương. Precision/lead time trong bảng là mô tả, chưa có CI hoặc kiểm định riêng. Quota sớm hơn trên các phát hiện đúng nhưng phát hiện ít hơn và có thêm false alerts trong replay này.

Cross-project cùng K=2: macro-project early recall 54,82% quota và 55,90% midpoint; delta -1,08 điểm, CI [-1,88; -0,35], n=14 projects. Precision micro tương ứng 70,90% và 74,44%; conditional lead days 8,91 và 6,98. Đây là exploratory CI không multiplicity-adjusted, không chọn deployment policy bằng kết quả này.

Không gọi 59,20% là model accuracy hoặc cải thiện so với 53,36% phase 4: đổi capacity, cohort/eligibility, probability scale và metric. Với K=2 temporal, micro recall cuối kỳ chỉ 27,51% quota và 27,93% midpoint. Macro và micro kể hai câu chuyện khác nhau do sprint size khác nhau; không chỉ lấy số macro lớn hơn.

## Tại sao không kết luận quota là thuật toán kém

K=1 khiến quota dùng hết capacity ngay .25, nên quota=early trong replay. K=3 dành một slot cho .75; tại .5 quota chỉ được dùng hai slot, còn midpoint được dùng ba. Delta early recall -12,72 điểm temporal ở K=3 một phần phản ánh chính sách dành capacity về sau, không phải suy ra model kém chính xác. So sánh vẫn có ý nghĩa ở cùng cap cả sprint, nhưng phải diễn giải là trade-off phân bổ theo thời gian.

Late policy có early recall=0 theo định nghĩa, song precision/recall cuối thường cao hơn vì có thêm execution information và lọc Done tại .75. Nó không chứng minh hành động muộn hữu ích hơn; lead time và tính khả thi hỗ trợ chưa được đo bằng can thiệp thực.

Sprints ít issue và rounding vẫn chi phối. K nguyên không đồng nghĩa tỷ lệ nhỏ: K=2 quota temporal có realized fraction macro 45,49%, micro 20,35%; midpoint 43,83%/20,04%. Capacity floor20 và zero-cap được báo trong summary. Không quảng bá “chỉ cảnh báo 20%” cho fixed K.

Baseline rule/static được giữ trong 96-cell matrix. Với K=2 temporal, midpoint early recall rule 57,71%, static 58,28%, dynamic 59,20%; chưa tính matched scorer contrasts trong E1 nên không tự tuyên bố superiority có ý nghĩa thống kê.

## Hệ quả cho hướng SOTA và sản phẩm

E1 bác bỏ cách thiết kế thiếu thận trọng “thêm vòng giám sát là tự nhiên tốt hơn”. Hướng tiếp theo là policy có abstention/threshold/quota được chọn trên validation riêng, cùng agent giúp người dùng kiểm tra ngữ cảnh. Không ép một cảnh báo sớm chỉ để tiêu thụ slot; phải giữ quyền im lặng và baseline midpoint/rule.

Bảng này chỉ nghiên cứu alert selection trong lịch sử. Chưa có LLM agent, grounded explanation scoring, acceptance/actionability human labels hoặc hiệu quả giảm non-completion. Không đổi frozen model/calibrator sau khi đọc E1. E2/E3/E4 trong [lộ trình](../docs/plans/2026-10-08-proactive-sprint-agent.md) vẫn cần thực hiện.

## Verification và tái lập

Runner đã hoàn thành 252 frozen input files, 96 summary rows, 24 paired CI contrasts, 113.232 per-sprint metric rows và 180.638 alert rows (gộp các cấu hình, không phải số alerts production). Independent audit đối chiếu hashes, labels/scores/timestamps/eligibility với original prefixes, dedup, cap và tái tính counts đều pass. Lỗi parser ISO timestamp có/không fractional seconds được sửa ở audit-only với regression test; không tính lại/tune metric.

Adapter inference pass 18 bundles / 180 sample snapshots, raw và sigmoid parity atol=1e-12. Đây là sample parity, chưa là full serving system hoặc validation cho Agentick. Research runtime cần bổ sung vào Docker ở bước triển khai; không giả định Docker API hiện tại đã phục vụ model.

Command kiểm tra tại root project:

```powershell
.venv/Scripts/python.exe -m pytest tests -q
.venv/Scripts/python.exe -m research.validate_agent_policy
.venv/Scripts/python.exe -m research.validate_serving_parity
```

Hai CSV lớn `alert_log.csv` và `sprint_metrics.csv` được giữ local nhưng không tracking Git; manifest chứa SHA256. Models/predictions/snapshots cũng cần có local như study phase 4. Git clone chỉ có code/summary/CI/docs/audit không đủ chạy full audit.

Để tái lập không ghi đè namespace đã có, chạy trong root với dữ liệu local đầy đủ:

```powershell
.venv/Scripts/python.exe -c "from pathlib import Path; import research.agent_policy_experiment as e; e.OUT=Path('artifacts/agent_extension/policy_v1_reproduction'); e.main()"
.venv/Scripts/python.exe -c "from pathlib import Path; import research.validate_agent_policy as v; v.OUT=Path('artifacts/agent_extension/policy_v1_reproduction'); v.main()"
```

Output namespace phải chưa tồn tại cho runner. Không xoá kết quả cũ để rerun. Manifest ghi code/protocol/input/output hashes; created_at khác nhưng các metric CSV phải có cùng nội dung với cùng inputs/code/environment.
