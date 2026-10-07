"""Generate the stage-4 Markdown report from evaluated artifacts (no invented metrics)."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

OUT=Path('artifacts/results')


def table(frame,columns):
    subset=frame[columns]
    lines=['| '+' | '.join(columns)+' |','| '+' | '.join(['---']*len(columns))+' |']
    for row in subset.itertuples(index=False,name=None):
        values=[]
        for value in row:
            if pd.isna(value): values.append('NA')
            elif isinstance(value,(float,np.floating)): values.append(f'{value:.4f}')
            else: values.append(str(value))
        lines.append('| '+' | '.join(values)+' |')
    return '\n'.join(lines)


def conclusion(row):
    delta,low,high=row['delta'],row['ci_low'],row['ci_high']
    if delta>0 and low>0:
        statement='Có bằng chứng cải thiện trên thiết lập này'
    elif delta<0 and high<0:
        statement='Có bằng chứng mô hình động kém hơn trên thiết lập này'
    else:
        statement='Chưa đủ bằng chứng cho cải thiện; không kết luận hai phương pháp tương đương'
    return f"{statement}: Δ={delta:.4f}, CI 95% [{low:.4f}, {high:.4f}], {int(row['n_units'])} đơn vị bootstrap."


def main():
    manifest=json.loads((OUT/'manifest.json').read_text())
    validation=json.loads(Path('artifacts/validation/prediction_validation.json').read_text())
    if not validation['complete'] or not validation['checks_passed']:
        raise RuntimeError('Require full prediction validation before reporting completion')
    probability=pd.read_csv(OUT/'probability_metrics.csv')
    budget=pd.read_csv(OUT/'alert_budget_metrics.csv')
    comparisons=pd.read_csv(OUT/'paired_comparisons.csv')
    sensitivity=pd.read_csv(OUT/'sensitivity_metrics.csv')
    sequence=pd.read_csv(OUT/'sequential_alert_metrics.csv')
    primary=comparisons[(comparisons.landmark==.5)&(comparisons.scenario=='primary')]
    p50=probability[probability.landmark==.5]
    b50=budget[(budget.landmark==.5)&(budget.q==.2)]
    s50=sensitivity[(sensitivity.landmark==.5)&(sensitivity.model.isin(['static_catboost','dynamic_catboost']))]
    temporal=primary[primary.experiment=='temporal'].iloc[0]
    cross=primary[primary.experiment=='cross_project'].iloc[0]
    audit=pd.read_csv('artifacts/validation/prediction_audit.csv')
    inverse=int(((audit.calibrator_slope<0)&~audit.key.str.endswith('__frequency')).sum())
    lines=[
        '# Báo cáo nghiên cứu đến hết giai đoạn 4',
        '',
        'Dự báo sớm outcome issue trong sprint từ execution history và cảnh báo theo ngân sách. Kết quả dưới đây được tạo từ artifact thực nghiệm đã chạy, không phải kết quả dự kiến.',
        '',
        'Đọc [thảo luận kết quả và hướng tiếp theo](Thao_luan_ket_qua.md) để xem diễn giải, baseline mạnh, rounding budget, active-only, calibration transfer và các phân tích post-hoc.',
        '',
        '## Kết quả chính',
        '',
        '**Temporal, H1 đăng ký trước:** '+conclusion(temporal),
        '',
        '**Cross-project, suy rộng phụ:** '+conclusion(cross),
        '',
        'Chênh lệch là Recall@20% của dynamic CatBoost trừ static CatBoost ở landmark 50%. Temporal bootstrap ghép cặp theo sprint; cross-project theo project. H1 chính chỉ dùng temporal; các landmark/sensitivity khác là phân tích phụ, không chọn kết luận đẹp nhất sau test.',
        '',
        '## Bài toán và thiết kế',
        '',
        'Đơn vị issue–sprint thuộc tracker scope ở đầu sprint. Tại 0/25/50/75% thời lượng, dự báo xác suất issue chưa Done tại End_Date. RQ1: execution history thêm giá trị gì so với dữ liệu đã biết đầu sprint? RQ2/RQ3: giữ được hiệu quả ở sprint tương lai và project chưa thấy không? RQ4: xác suất và cảnh báo có hữu ích ở giới hạn xử lý không?',
        '',
        'Cohort được tái dựng từ Sprint changelog bằng (project_id,jiraid), không dùng liên kết snapshot cuối. Nhãn là last observed status trước/đúng End_Date, Done/Resolved/Closed/Complete; unknown, trạng thái mơ hồ và history gaps không gán nhãn. Feature chỉ lấy event prefix; aggregate cohort tính trước loại outcome NA. Các giả định/giới hạn đầy đủ trong [protocol](Protocol_v1.md) và [data card](Data_card_TAWOS.md).',
        '',
        'TAWOS v1.1: 28.746 commitments có membership evidence; 22.147 gán nhãn (77,04%); 88.588 snapshots. Đánh giá chính trên 14 project, 18.322 instances, 1.962 sprints. Temporal có 1.165 train, 383 validation, 397 test, 17 purge; fit riêng project. Cross-project leave-one-project-out, validation project riêng. Cấu hình/model/seed đã khóa trước fit/test; sigmoid chỉ fit validation.',
        '',
        '## Xếp hạng và cảnh báo tại giữa sprint',
        '',
        table(b50,['experiment','model','recall_macro_sprint','recall_macro_project','precision_macro_sprint','false_alerts_per_sprint','realized_budget']),
        '',
        'Ngân sách danh nghĩa 20% dùng ceil(q×n) theo protocol. Realized budget là trung bình tỷ lệ cảnh báo thật trên từng sprint; sprint nhỏ có thể có tỷ lệ cao hơn 20%. Không gọi đây là giới hạn tỷ lệ nghiêm ngặt. Sprint không dương không góp vào macro recall nhưng vẫn góp precision/false alerts. Cross-project ưu tiên macro project khi diễn giải để tránh dự án nhiều sprint chi phối.',
        '',
        table(primary,['experiment','landmark','scenario','n_units','delta','ci_low','ci_high']),
        '',
        '![Landmark and budget, temporal](../artifacts/results/landmark_budget_temporal.png)',
        '',
        '![Landmark and budget, cross-project](../artifacts/results/landmark_budget_cross_project.png)',
        '',
        '![Project differences](../artifacts/results/project_differences.png)',
        '',
        '## Chất lượng xác suất và hiệu chuẩn',
        '',
        table(p50,['experiment','model','calibration','ap','ap_macro_project','brier','brier_macro_project','calibration_intercept','calibration_slope']),
        '',
        'AP là average precision của lớp không hoàn thành, không phải trapezoidal PR area. Brier thấp hơn tốt hơn. Calibration intercept/slope được fit trên test chỉ để chẩn đoán xác suất, không dùng lại để chỉnh mô hình; lý tưởng lần lượt 0 và 1. Khi score là hằng số thì slope/intercept không tách biệt được, nên ghi NA. Reliability plot gộp có thể che khác biệt project, nên phải đọc cùng per-project CSV.',
        '',
        f'Sigmoid được fit không ràng buộc slope; có {inverse} artifact ngoài frequency có hệ số âm trên validation (bao gồm các landmark/model). Hệ số âm có thể đảo thứ hạng khi score có biến thiên; frequency hằng số không có ranking để đảo. Phải phân biệt cải thiện do feature với hiệu ứng calibrator; raw scores được giữ nguyên để kiểm tra. Không sửa calibrator theo test trong lượt này.',
        '',
        '![Temporal calibration](../artifacts/results/calibration_temporal.png)',
        '',
        '![Cross-project calibration](../artifacts/results/calibration_cross_project.png)',
        '',
        '## Sensitivity và cách diễn giải',
        '',
        table(comparisons[comparisons.landmark==.5],['experiment','scenario','n_units','delta','ci_low','ci_high']),
        '',
        table(s50,['experiment','model','scenario','n','ap','brier','recall_macro_sprint','realized_budget']),
        '',
        'Raw-ranking giữ ranking model base trước calibrator. Project-weighted exploratory đổi trọng số thành project ngang nhau và bootstrap theo project, khác estimand macro sprint của H1. Floor budget áp giới hạn tỷ lệ nghiêm ngặt và có thể không phát cảnh báo ở sprint nhỏ. Active-only chỉ xét issue chưa Done tại landmark, là kiểm tra giá trị dự báo trong công việc còn mở. Loại cancelled/removed kiểm tra mức phụ thuộc scope change. Unseen-ID loại issue test đã có trong train, không phải dự án chưa thấy. Closed-only ở đây chỉ chấm lại frozen predictions với target thay thế; mô hình chưa được retrain cho target đó, nên đây là stress test nhãn, không là so sánh learner được tối ưu cho Closed-only.',
        '',
        '## Cảnh báo tích lũy và độ sớm',
        '',
        table(sequence,['experiment','model','recall_macro_sprint','recall_macro_project','precision_macro_sprint','false_alerts_per_sprint','lead_days_macro_sprint','recall_by_half_macro']),
        '',
        'Replay dùng tổng cap ceil(20%×n) cho cả sprint, không reset ở mỗi landmark. Cumulative quota 1/3, 2/3 và toàn cap tại 25/50/75%; deduplicate issue và không cảnh báo issue đã Done tại thời điểm đó. Lead time chỉ tính true alerts được phát hiện và mean theo sprint; không phải mọi issue rủi ro đều được phát hiện. Đây là policy cố định minh họa capacity/earliness, chưa chứng minh tối ưu hay tác động can thiệp.',
        '',
        '## Threats to validity và phạm vi kết luận',
        '',
        '- Nhãn archival có coverage 77,04%; loại NA có thể tạo selection bias. Không có hai người xác minh workflow, không báo cáo inter-rater agreement giả. SQL/replay consistency không thay thế ground truth nghiệp vụ.',
        '- Sprint Start/End lấy từ snapshot, không có lịch sử đổi ngày sprint. Tính hợp lệ của deadline biết tại t0 là giả định; kiểm tra timestamp event không tự chứng minh giả định này. Metadata project/ownership cũng theo snapshot.',
        '- Missing logs có thể không để lại dấu chuỗi sai. Static priority/type/estimate thiếu nhiều vì không lấy final values; so sánh phản ánh thông tin tái dựng được, không mọi thông tin team thực sự có.',
        '- Cross-project là transfer archival, không cutoff triển khai toàn cầu. Project cùng repository có thể cùng workflow nên project holdout chưa tương đương organization holdout.',
        '- Bootstrap sprint giữ pairing nhưng issue có thể lặp qua sprint; sensitivity seen-ID giảm một phần phụ thuộc, không loại toàn bộ clustering.',
        '- Nhiều phân tích phụ không điều chỉnh multiplicity và không thay thế H1 chính. Không tuyên bố thuật toán mới/SOTA; cấu hình cố định chưa là exhaustive hyperparameter search.',
        '- Offline replay không cho biết cảnh báo có giảm trễ hoặc ảnh hưởng hành vi người dùng; cần pilot và dữ liệu live ở các giai đoạn sau.',
        '',
        '## Tái lập và kiểm tra hoàn thành',
        '',
        f"Matrix: {manifest['prediction_files']} prediction files; validation {validation['checked']}/{validation['expected']} bộ artifact, đối chiếu cohort/nhãn/timestamp/feature whitelist và re-inference mẫu. Config hash `{manifest['config_sha256']}`; dataset hash `{manifest['dataset_sha256']}`.",
        '',
        '[Hướng dẫn chạy lại](Reproduce_research.md), [checklist/decision log](Research_progress.md), [căn cứ học thuật](Literature_and_methods.md), [BibTeX](references.bib). Model/parquet lưu local và được Git ignore; CSV/protocol/code/report được tracking. Kết quả này hoàn thành nghiên cứu offline đến giai đoạn 4; tích hợp Agentick và pilot là giai đoạn 5 trở đi.',
        '',
        '## Hướng sử dụng cho sản phẩm',
        '',
        'Thiết kế dashboard ưu tiên xếp hạng issue còn mở theo budget cấu hình của sprint, hiển thị số cảnh báo thực tế, landmark/model version và trạng thái dữ liệu thiếu. Xác suất nên đi kèm calibration theo project; không dùng một ngưỡng xác suất chung như cam kết chắc chắn về rủi ro. Giữ log prediction/alert để đánh giá drift và false alerts khi pilot. Các artifact hiện có là model theo fold đánh giá, chưa phải một model production đã được chọn/huấn luyện lại trên toàn dữ liệu.',
    ]
    Path('documents/Bao_cao_nghien_cuu_giai_doan_4.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('Generated stage-4 report from verified evaluated artifacts')


if __name__=='__main__': main()
