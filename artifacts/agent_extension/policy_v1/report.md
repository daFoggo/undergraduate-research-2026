# Kết quả exploratory về policy cảnh báo

Không phải kết quả AI Agent/LLM hoặc chứng minh giảm trễ. Population là active-at-.25 trong labeled cohort.

Raw ranking, fixed K hoặc floor(.2*n0), không tuning. Primary exploratory metric: recall phát hiện trước/tại .5.

| Experiment | Capacity | Policy | Early recall macro | Recall cuối macro | Precision micro | Alerts |
|---|---|---|---:|---:|---:|---:|
| cross_project | k1 | quota | 0.3452 | 0.3452 | 0.7044 | 1871 |
| cross_project | k1 | midpoint | 0.3767 | 0.3767 | 0.7705 | 1830 |
| cross_project | k1 | early | 0.3452 | 0.3452 | 0.7044 | 1871 |
| cross_project | k1 | late | 0.0000 | 0.4144 | 0.8489 | 1780 |
| cross_project | k2 | quota | 0.5482 | 0.5486 | 0.7090 | 3405 |
| cross_project | k2 | midpoint | 0.5590 | 0.5590 | 0.7444 | 3333 |
| cross_project | k2 | early | 0.5252 | 0.5252 | 0.6700 | 3445 |
| cross_project | k2 | late | 0.0000 | 0.6143 | 0.8326 | 3195 |
| cross_project | k3 | quota | 0.5482 | 0.6960 | 0.7307 | 4634 |
| cross_project | k3 | midpoint | 0.6824 | 0.6824 | 0.7262 | 4598 |
| cross_project | k3 | early | 0.6475 | 0.6475 | 0.6501 | 4787 |
| cross_project | k3 | late | 0.0000 | 0.7338 | 0.8226 | 4336 |
| cross_project | floor20 | quota | 0.1839 | 0.2134 | 0.7501 | 2869 |
| cross_project | floor20 | midpoint | 0.2234 | 0.2234 | 0.7652 | 2866 |
| cross_project | floor20 | early | 0.1935 | 0.1935 | 0.6798 | 2873 |
| cross_project | floor20 | late | 0.0000 | 0.2617 | 0.8434 | 2822 |
| temporal | k1 | quota | 0.3927 | 0.3927 | 0.7680 | 375 |
| temporal | k1 | midpoint | 0.4143 | 0.4143 | 0.8447 | 367 |
| temporal | k1 | early | 0.3927 | 0.3927 | 0.7680 | 375 |
| temporal | k1 | late | 0.0000 | 0.4131 | 0.8845 | 355 |
| temporal | k2 | quota | 0.5877 | 0.5877 | 0.7731 | 670 |
| temporal | k2 | midpoint | 0.5920 | 0.5920 | 0.7970 | 660 |
| temporal | k2 | early | 0.5658 | 0.5658 | 0.7368 | 680 |
| temporal | k2 | late | 0.0000 | 0.6215 | 0.8679 | 636 |
| temporal | k3 | quota | 0.5877 | 0.7142 | 0.7911 | 895 |
| temporal | k3 | midpoint | 0.7149 | 0.7149 | 0.7926 | 892 |
| temporal | k3 | early | 0.6995 | 0.6995 | 0.7393 | 932 |
| temporal | k3 | late | 0.0000 | 0.7329 | 0.8673 | 844 |
| temporal | floor20 | quota | 0.1500 | 0.1714 | 0.8566 | 502 |
| temporal | floor20 | midpoint | 0.1820 | 0.1820 | 0.8767 | 503 |
| temporal | floor20 | early | 0.1680 | 0.1680 | 0.8290 | 503 |
| temporal | floor20 | late | 0.0000 | 0.1920 | 0.9276 | 497 |

## Quota trừ midpoint về early recall

| Experiment | Capacity | Units | Delta pp | 95% CI pp |
|---|---|---:|---:|---|
| cross_project | k1 | 14 | -3.16 | [-4.80; -1.75] |
| cross_project | k2 | 14 | -1.08 | [-1.88; -0.35] |
| cross_project | k3 | 14 | -13.42 | [-14.67; -12.23] |
| cross_project | floor20 | 14 | -3.95 | [-5.58; -2.40] |
| temporal | k1 | 336 | -2.16 | [-4.09; -0.21] |
| temporal | k2 | 336 | -0.43 | [-1.36; 0.55] |
| temporal | k3 | 336 | -12.72 | [-14.86; -10.73] |
| temporal | floor20 | 336 | -3.19 | [-4.23; -2.09] |

## Giới hạn

Test cũ đã được xem; toàn bộ là post-hoc. Không chọn policy/model deployment từ bảng này. Lead time chỉ trên true-alert sprints. Chưa có scope-removal-as-of filter, unknown labels hay human actionability. Capacity fixed K và cohort active khác nghiên cứu chính; không so trực tiếp con số macro với 53,36%. Sprints K=0 nằm trong summary; recall undefined nếu không có positives. CI marginal, không điều chỉnh multiplicity hoặc mọi phụ thuộc issue/sprint.

Các baseline rule/static có trong summary.csv; không bỏ baseline yếu/mạnh khỏi báo cáo. Agent narrator/tool use, grounding, safety và người dùng chưa được đánh giá.
