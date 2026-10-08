# Báo cáo đánh giá kỹ thuật Agent cảnh báo sớm v1 (Task 7)

Ngày đánh giá: 2026-10-08T09:17:35.766539+00:00
Model LLM: `gemini-3.5-flash-lite`
Provider: Google Gemini (Native)
Bộ công cụ xác minh: `EvidenceVerifier` (Outcome Grader)

## 1. Kết quả tổng hợp giữa các biến thể

| Biến thể | Số scenario | Hoàn thành | Tỷ lệ Pass Verifier | Grounding Rate | Numeric Fidelity | Causal Safety | Độ trễ TB (s) | Chi phí ($) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **A0 (Template)** | 10 | 10 | 100.0% | 100.0% | 100.0% | 100.0% | 0.000s | $0.00 |
| **A1 (Narrator)** | 10 | 10 | 100.0% | 100.0% | 100.0% | 100.0% | 1.638s | $0.00 |
| **A2 (Bounded Tool)** | 10 | 10 | 100.0% | 100.0% | 100.0% | 100.0% | 2.385s | $0.00 |

## 2. Nhận xét & Đánh giá

1. **A0 (Template Baseline):** Hoạt động deterministic 100%, độ trễ cực nhanh (<1ms), tuyệt đối không hallucination và chi phí $0. Là mốc đối chứng chuẩn.
2. **A1 (Narrator):** Diễn giải ngữ cảnh alert bằng ngôn ngữ tự nhiên, tuân thủ chặt chẽ ràng buộc schema khi được nạp sẵn ngữ cảnh.
3. **A2 (Bounded Tool Agent):** Chủ động thực hiện vòng lặp gọi tool `get_issue_evidence`, xác minh dữ liệu qua `EvidenceVerifier` trước khi chốt giải thích.
4. **Độ an toàn và tính tin cậy:** Cả A1 và A2 đều phải vượt qua bộ kiểm định nghiêm ngặt `EvidenceVerifier` (kiểm tra claim grounding, numeric fidelity, anti-causal safety). Mọi vi phạm đều bị phát hiện và ngăn chặn.

---
Artifacts:
- `results.csv`
- `metrics_summary.json`
