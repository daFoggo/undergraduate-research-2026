# Đối chiếu hoàn thành giai đoạn 1–4

Phạm vi: nghiên cứu archival theo Protocol v1 đã khóa trước fit. Bằng chứng máy kiểm tra ở `artifacts/validation/completion_audit.json`; code audit được đọc cùng các tài liệu dưới đây, không dùng một nhãn “pass” để thay thế kiểm tra phạm vi.

| Yêu cầu | Bằng chứng hiện có | Kết luận |
|---|---|---|
| RQ, estimand, cohort, labels, feature/split/metric protocol | Protocol_v1, config/lock, Git registration `2f3a73f`; final audit so sánh các nội dung frozen với commit này | Đã khóa trước fit; H1 không đổi sau test |
| Nguồn/version/license/checksum và audit TAWOS | Data_card, source_manifest, audit schema/project/status/membership CSV | Đã lưu nguồn và giới hạn snapshot |
| Eligibility, cohort, nhãn và lý do loại | Project eligibility, label_mapping, exclusion_log gốc + enriched provenance, 765 SQL samples | Có flow/exclusions tái lập; không giả định NA là một lớp |
| Snapshot 0/25/50/75% và temporal integrity | Parquet hash trong lock; feature_dictionary; full data_validation; tests replay/cohort | 88.588 snapshots; prefix và cohort aggregate kiểm tra |
| Temporal split và project holdout | Hai split manifests, tests purge, frozen Git comparison | 14 project; purge label availability; project test ngoài fit/calibration |
| Baselines, dynamic/ablation và calibration | 672 model/prediction/metadata triplets, full re-inference/whitelist audit | Đã chạy đủ matrix, không chỉ viết code |
| Prediction/calibration, alert budget và bất định | 96 probability rows, 1.344 per-project probability rows, 144 budget rows, 60 paired comparisons, 12 sequential summaries | Temporal/cross-project, raw/calibrated, CI, sensitivity và lead time có số liệu thực |
| Phân tích nghiên cứu | Báo cáo, Thao_luan_ket_qua, posthoc_comparisons, feature importance và 5 figures đã xem | H1 và các kết quả không thuận lợi đều được diễn giải |
| Tracking/reproducibility/handoff | Research_progress, Reproduce_research, environment manifests, local Git | Có checkpoint, quyết định/citations, commands và artifact hashes |

Kiểm tra bổ sung: model/prediction hash không đổi kể từ full validator; sequential alert không trùng issue trong cùng sprint và không vượt total cap; bảng kết quả đủ cardinality; link/figure trong báo cáo tồn tại. Unit tests bao gồm future-event invariance, cohort-outcome invariance, missing-history/reopen/multi-sprint, split purge, budget rounding, pairing bootstrap, total budget/dedup và metric vectorization equivalence.

Các điều chưa được chứng minh: ground truth workflow do con người xác minh, lịch sử ngày sprint thực sự biết tại thời điểm t0, tác động can thiệp ngoài đời, organization-level transfer, exhaustive model tuning hoặc SOTA. Protocol v1 giới hạn kết luận vào outcome ghi nhận trong tracker dưới các giả định đã khai báo. Không coi SQL consistency là inter-rater agreement; không coi completed research experiment là production-ready product hoặc bài báo được chấp nhận.

Giai đoạn 5 trở đi (Agentick integration, dữ liệu live/pilot và báo cáo sản phẩm hoàn chỉnh) chưa được thực hiện trong scope này. Không còn thí nghiệm hoặc artifact bắt buộc nào chưa chạy của registered stage-1–4 study.
