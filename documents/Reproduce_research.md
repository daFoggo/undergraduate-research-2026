# Tái lập nghiên cứu

Chạy PowerShell từ thư mục project. PostgreSQL đã có TAWOS v1.1 trong schema `tawos_raw`; không nhập lại vào DB đã có dữ liệu.

```powershell
docker compose up -d db api
.venv/Scripts/python.exe -m pip install -r requirements-research.txt
.venv/Scripts/python.exe scripts/research_audit.py
.venv/Scripts/python.exe -m research.build
.venv/Scripts/python.exe -m research.splits
.venv/Scripts/python.exe -m research.validate_data
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m research.train --experiment temporal
.venv/Scripts/python.exe -m research.train --experiment cross_project
.venv/Scripts/python.exe -m research.validate_predictions
.venv/Scripts/python.exe -m research.evaluate
.venv/Scripts/python.exe -m research.analysis
.venv/Scripts/python.exe -m research.report
```

Các lệnh build/splits chỉ chạy khi tái lập từ đầu hoặc trước training. Không ghi lại config/split sau khi đã xem test để chọn một kết quả đẹp hơn. Nếu có sửa lỗi thực sự, giữ artifact cũ, ghi amendment và tạo phiên bản run mới. `train` resume các fold/model đã hoàn tất chỉ khi source/config/dataset hash khớp; không khởi động thêm bản train cùng experiment khi tiến trình cũ còn chạy.

Kết nối mặc định local development: PostgreSQL localhost:5432, database/user `tawos`. Có thể đổi qua biến `RESEARCH_DATABASE_URL` (URL psycopg chuẩn). Không ghi URL có mật khẩu thật vào Git hoặc manifest. Các query build/audit chạy read-only; nguồn TAWOS không bị sửa.

Dataset parquet ở `data/processed/`; model và prediction ở `artifacts/models/`, `artifacts/predictions/`, được Git ignore vì dung lượng lớn. CSV audit/split/metrics, protocol và code được tracking. Git commit không thay thế việc sao lưu PostgreSQL volume và parquet/model; giữ nguyên các volume hiện có.

Config, seed và manifest: `artifacts/protocol/`. Mỗi model có metadata trong `artifacts/runs/{experiment}/`, số train/validation/test, feature list và validation metric. Chỉ evaluator mới tính các metric test. Matrix đầy đủ dự kiến 14 projects × 4 landmarks × 6 models × 2 experiments = 672 prediction files.

Stack nghiên cứu hiện dùng `.venv` trên Windows, PostgreSQL/FastAPI qua Docker Compose. Phiên bản đang cài: Python 3.12, NumPy 2.5.3, pandas 3.0.6, pyarrow 25.0.1, scikit-learn 1.9.1, CatBoost 1.2.10, SciPy 1.18.1, matplotlib 3.11.2. Đây là phiên bản chạy thực tế, không chỉ version range trong requirements. Mỗi lần chạy nên lưu đầy đủ environment manifest để tái lập chính xác.

Theo dõi tiến độ ở `Research_progress.md`; các session ID đang chạy được ghi checkpoint. Khi tiếp tục sau context reset, kiểm tra process/session/artifact rồi mới thực hiện bước tiếp theo.
