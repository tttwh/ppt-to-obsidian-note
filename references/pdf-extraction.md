# PDF 逐页提取参考

本参考仅在需要终端提取 PDF 时使用。先检查环境里已有的工具；以下示例使用 PyMuPDF，缺少时可换同等工具。路径放在当前任务可写的临时目录，不要覆盖用户文件。

## 文本与页面统计

```python
from pathlib import Path
import pymupdf

pdf_path = Path("<课件.pdf>")
output = Path("<任务临时目录>")
output.mkdir(parents=True, exist_ok=True)

with pymupdf.open(pdf_path) as pdf:
    with (output / "pages.txt").open("w", encoding="utf-8") as text_file:
        for number, page in enumerate(pdf, start=1):
            text = page.get_text(sort=True)
            text_file.write(f"\n===== PDF PAGE {number} =====\n{text}\n")
            print(f"page {number}: {len(text.strip())} extracted characters")
```

零文字页要看渲染结果：它可能是插图、截图、扫描内容，或本来就只含少量文字。整份课件的平均字数不足以判断单页是否需要 OCR。

## 渲染需要核对的页面

```python
import pymupdf

with pymupdf.open("<课件.pdf>") as pdf:
    for number in [1, 2, 3]:  # 填入实际需要核对的 PDF 物理页码
        page = pdf[number - 1]
        page.get_pixmap(dpi=180).save(f"<任务临时目录>/page-{number:03d}.png")
```

先浏览全课件的页面缩略图，再详细查看含关键图表、公式、代码和文字提取异常的页。用环境中可用的图像理解能力读取页面；若没有图像能力，标出不能验证的页，不凭提取文本猜图。OCR 只为确实缺乏可读文字层的页面补文字，OCR 结果仍需和原页核对。

## 表格与公式

`page.get_text()` 往往打乱表格行列或公式符号。可试 `page.find_tables()` 或 `pdfplumber` 辅助提取，但最终以页面图像为准。不要把自动提取的表格或 LaTeX 未经核对直接写入笔记。
