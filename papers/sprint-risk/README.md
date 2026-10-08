# Sprint-risk paper

`main.tex` là entry point. Nội dung chính chỉnh trong `sections/`; hình vector trong `figures/`; package/style trong `preamble.tex`; sửa citation trong `references.bib`. Builder tự cập nhật `bibliography.tex`, không cần giữ hai bản bibliography thủ công. Đây là manuscript draft, chưa gắn venue/template hoặc thông tin tác giả thật.

```text
main.tex
preamble.tex
sections/             abstract, introduction, related work, RQs, data,
                      methods, results, discussion, validity, reproduction,
                      conclusion, artifact appendix
figures/              three vector figures with embedded result coordinates
tables/               compact booktabs tables, separately editable
bibliography.tex      generated bibliography (no BibTeX run needed)
references.bib        machine-readable citation entries
source/manuscript.md  original prose draft; not the editing source after split
summary_vi.md         Vietnamese findings and paper positioning
build/manuscript.tex  generated standalone preview
```

Sau khi chỉnh section hoặc figure, chạy từ root project:

```powershell
.venv/Scripts/python.exe scripts/build_academic_paper.py
```

Lệnh này chỉ tổng hợp LaTeX, không ghi đè các section đã sửa và không chạy lại thí nghiệm. Không dùng `--organize` sau khi project đã khởi tạo. Nó cập nhật `build/manuscript.tex` và file đang mở `documents/Academic_paper_sprint_risk.tex` để compiler một-file của Codex preview được bài. File preview được sinh tự động; nên chỉnh source modules rồi rebuild để giữ thay đổi.

Dependency của builder: `.venv/Scripts/python.exe -m pip install -r requirements-paper.txt` từ root. `--format-tables` chỉ dùng khi khởi tạo bản draft chưa tách bảng; các bảng hiện tại chỉnh trực tiếp trong `tables/`.

PDF hiện tại: `build/main.pdf` (13 trang), đã compile bằng XeLaTeX/latexmk và kiểm tra bản render. Hình/bar chart là vector từ số liệu thực nghiệm; nội dung giữ cả các kết quả không thuận lợi và threats to validity. Tác giả đang để anonymous draft, chưa là bản camera-ready theo venue.

Với một TeX installation đầy đủ, có thể chạy trực tiếp từ thư mục này:

```text
latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=build main.tex
```

Compiler tích hợp Codex không đọc thêm project files, nên kiểm tra bản standalone bằng compiler đó. Không tuyên bố PDF đã biên dịch thành công chỉ dựa vào việc file `.pdf` cũ tồn tại; xem diagnostic compile mới nhất.
