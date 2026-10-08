# ppt-to-obsidian-note

把课程课件 PDF（slide deck）一键转成**可直接放进 Obsidian 的 Markdown 学习笔记**的 skill。

不只是抽文字，更会**把课件里的图解读出来**：流程图重画成 Mermaid、图片表格转成 Markdown 表、公式还原成 LaTeX，复杂示意图原图嵌入——每张都带回 PPT 页码对照，方便复习时翻原课件。

## 特性

- 📄 **文本 + 图解双通道**：`pymupdf` 提取文字 + 渲染页面 → 视觉模型读图，不再丢图
- 🧩 **图解智能分流**：流程图/架构/状态机 → Mermaid；图片表格 → Markdown 表；公式 → LaTeX；照片/复杂示意图 → 原图嵌入 `![[...]]`
- 🎯 **只挑教学关键图**：每章 1–3 张、全篇 ≤15 张，忽略装饰图/重复图
- 🔢 **全篇页码映射**：顶部索引总表 + 每个标题标 `PPT x–y`
- 📝 **教学式改写**：callout、wiki 双链、代码块、对照表格，讲清「为什么 / 直觉 / 口诀」
- 🧮 **扫描版 PDF OCR**：自动检测无文字层课件，走 `ocrmypdf` / `pytesseract`
- 🧮 **公式 LaTeX 还原**：碎下标/分式/乱码 → `$...$`
- ✅ **针对性自测**：贴考点/易错点，关起式答案

## 安装

把 `SKILL.md` 放到 DSH 的 skills 目录：

```bash
mkdir -p ~/.dsh/skills/ppt-to-obsidian-note
cp SKILL.md ~/.dsh/skills/ppt-to-obsidian-note/
```

## 用法

把课件 PDF 路径丢给助手，说「做成 Obsidian 笔记」即可：

```
把 Chapter1_Digital Systems and Information.pdf 做成 Obsidian 笔记
```

## 依赖

```bash
python3 -m pip install pymupdf pdfplumber pypdf
# 扫描版 PDF 额外装：
python3 -m pip install ocrmypdf   # 或 pytesseract + tesseract 二进制
```

| 工具 | 用途 |
| --- | --- |
| `pymupdf` | 主力：文本提取 + 页面渲染成图 + 内嵌图提取 + `find_tables()` 表格识别 |
| `pdfplumber` | 表格结构补充 |
| `pypdf` | 兜底 |
| `ocrmypdf` / `pytesseract` | 扫描版 OCR |

> 注意：macOS 上 `poppler`（`pdftotext`/`pdftoppm`）常未安装，本 skill 以 `pymupdf` 为主力，不依赖 poppler。

## 目录结构

```
.
├── SKILL.md   # skill 指令本体
├── README.md
└── LICENSE
```

## License

[MIT](./LICENSE)
