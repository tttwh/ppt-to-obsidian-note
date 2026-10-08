---
name: ppt-to-obsidian-note
description: "Convert a courseware PDF/slide deck into a complete Obsidian-friendly markdown study note. Feed it a lecture PDF's path — it extracts the text AND the teaching-critical figures/diagrams, reconstructs flowcharts/tables/formulas, and generates a structured Markdown note with frontmatter, callouts, Mermaid, tables, LaTeX, code blocks, targeted self-test quizzes, AND maps every section back to the original PPT page numbers. Use whenever the user hands you a 课件/讲义/lecture PDF and wants an Obsidian note (学习笔记) from it. 用法：把课件 PDF 的路径丢给我，一键生成可直接放进 Obsidian 的笔记。"
---

# PPT → Obsidian 学习笔记

用户给你一份**课程课件 PDF**（slide deck），你要基于它生成一份**可直接放进 Obsidian 的 Markdown 学习笔记**。笔记要能「学」——不是摘抄 PPT，而是把内容讲清楚，并**保留与原始课件的页码对应关系**供复习时对照翻页。

**关键要求**：课件里的**图解（流程图/架构图/公式/对照表/示意图）是重点教学资产，必须融入笔记**——能结构化的重画成 Mermaid/表格/LaTeX，不能结构化的嵌入原图，不能丢。

## 触发场景

- 用户给一个 `.pdf` 路径，说「做成笔记」「生成 Obsidian 笔记」「整理成 markdown」「学习这份课件」。
- 用户给一份课件后，后续要求「标注页码」「补充某节」「加自测题」「放进 Obsidian」「单独开文件夹」。

## 目标产物

一个 `.md` 文件，包含：

1. **YAML frontmatter**（Obsidian 属性面板识别）：`title`、`course`、`chapter`、`source`（课件文件名）、`tags`、`created`。
2. **📑 课件页码索引表**——章 → PPT 页范围的对照总表（放在文件顶部概览之后）。
3. **目录**（GitHub 风格锚点链接，标题带页码）。
4. **分章节正文**——每章 `##`、每小节 `###`，标题旁标注 `PPT x–y`。
5. **教学性内容**：callout（`> [!note/tip/warning/danger/info/example]`）、表格、代码块、Mermaid、wiki 双链。
6. **图解融入**：教学关键图重画成 Mermaid/表格，或嵌入原图截图，每张都带 `PPT N` 页码 + 一句话解读。
7. **公式还原**：被文本提取弄乱的公式重写成 LaTeX（`$...$`，Obsidian 原生渲染）。
8. **自测**（`quiz`/关起式答案，**针对考点和易错点**，非泛泛回忆）。
9. **关联笔记**（`[[...]]` 双链到课件 PDF 和其他笔记）。

## 步骤

### Step 0 — 定位并检查文件与工具

- 用 `glob` 找到 PDF（路径含 `@` 前缀表示用户显式引用）。
- `pwd` 确认工作目录；`ls -la` 看文件存在、大小。
- **工具优先级（本机实测，别照搬旧清单）**：
  - **主力：`pymupdf`**（`import pymupdf`；1.28 起 `import fitz` 已弃用）——一个库搞定**文本提取 + 页面渲染成图 + 提取内嵌图 + `find_tables()` 表格识别**。
  - **表格补充：`pdfplumber`**（`extract_tables()` 更细）。
  - **兜底：`pypdf`**（`from pypdf import PdfReader`）。
  - **OCR（扫描版）：`ocrmypdf` / `pytesseract`**。
  - `pdftotext`/`pdftoppm`/`pdfimages`（poppler）在 macOS 常**未安装**，不要默认依赖；用 pymupdf 替代。
- 缺哪个：`python3 -m pip install pymupdf pdfplumber pypdf`（OCR 另装 `ocrmypdf` 或 `pytesseract`）。

### Step 1 — 提取全文 + 判断是否扫描版

**用 `read` 工具读提取出的文本文件，不要用 `cat`。** 先提取到 `/tmp`：

```bash
python3 - <<'PY'
import pymupdf
doc = pymupdf.open('<PDF路径>')
total = 0
with open('/tmp/ppt_text.txt','w',encoding='utf-8') as f:
    for i, page in enumerate(doc):
        t = page.get_text()
        f.write(f'\n===== PAGE {i+1} =====\n')
        f.write(t or '')
        total += len(t.strip())
avg = round(total/max(len(doc),1))
print('pages:', len(doc), '| total_text_chars:', total, '| avg_chars/page:', avg)
PY
```

- **页码约定**：`===== PAGE N =====` 的 N 就是 **PDF 物理页码（幻灯片号）**，第 1 页 = 幻灯片 1。笔记里的「PPT N」与此一致，用户对照原课件翻页即可。

- **扫描版 / 图片型 PDF 判断**：若 `avg_chars/page` 很低（如 < 50）或大量页 `get_text()` 为空 → 是**无文字层的扫描/图片课件**，走 OCR 路线，否则后面图解解读会瞎猜：

  ```bash
  # 首选：直接生成可搜索 PDF，再回到本流程重跑 Step 1
  ocrmypdf --force-ocr --language chi_sim+eng '<原PDF>' '/tmp/ocr_searchable.pdf'

  # 或：逐页渲染成图，再用视觉模型 / pytesseract 逐页 OCR
  python3 - <<'PY'
  import pymupdf, os
  os.makedirs('/tmp/ocr_pages', exist_ok=True)
  doc = pymupdf.open('<PDF路径>')
  for i, page in enumerate(doc):
      page.get_pixmap(dpi=300).save(f'/tmp/ocr_pages/p{i+1:03d}.png')
  print('rendered', len(doc), 'pages to /tmp/ocr_pages')
  PY
  ```

- **表格结构（文字型 PDF）**：`get_text()` 会把表格压平成逐行文本、丢掉行列关系。用 `page.find_tables()`（pymupdf ≥1.23）恢复，把结果记进 `/tmp/ppt_tables.txt` 供写笔记时用：

  ```bash
  python3 - <<'PY'
  import pymupdf
  doc = pymupdf.open('<PDF路径>')
  with open('/tmp/ppt_tables.txt','w',encoding='utf-8') as f:
      for i, page in enumerate(doc):
          for t in page.find_tables():
              f.write(f'\n===== TABLE on PAGE {i+1} =====\n')
              for row in t.extract():
                  f.write(' | '.join('' if c is None else str(c) for c in row) + '\n')
  print('done')
  PY
  ```

### Step 2 — 提取并解读图解（核心，别跳过）

**目标：把课件里的教学关键图找出来、看懂、重画或嵌入。** 这是纯文本提取最容易丢的部分。

1. **找出疑似图解页并渲染成 PNG**：

   ```bash
   python3 - <<'PY'
   import pymupdf, os
   os.makedirs('/tmp/ppt_figs', exist_ok=True)
   doc = pymupdf.open('<PDF路径>')
   figs = []
   for i, page in enumerate(doc):
       imgs = page.get_images(full=True)          # 内嵌位图
       draws = page.get_drawings()                # 矢量图形
       if imgs or len(draws) >= 5:                # 有图或有较多矢量元素 → 疑似图解页
           p = f'/tmp/ppt_figs/page_{i+1:03d}.png'
           page.get_pixmap(dpi=180).save(p)
           figs.append((i+1, len(imgs), len(draws)))
   print('figure-like pages:', figs)
   PY
   ```

2. **逐张用视觉模型读**（`read_image` 或 `modlens_read_image`），**看懂这张图在讲什么**，再按类型处理：

   | 图解类型 | 判定 | 处理方式 | 产出 |
   | --- | --- | --- | --- |
   | 流程图 / 架构图 / 状态机 | 框 + 箭头 + 分支 | 视觉解读 → 重画 | Mermaid `flowchart` / `stateDiagram` / `classDiagram` |
   | 时序 / 泳道 / 阶段 | 泳道、时间轴、阶段箭头 | 视觉解读 → 重画 | Mermaid `sequenceDiagram` / `timeline` |
   | 数据对照表（图片） | 网格 + 行列 | 视觉解读 → 转写 | Markdown 表格 |
   | 公式 / 推导 | 数学符号 | 视觉解读 → 重写 | LaTeX `$...$` / `$$...$$` |
   | 照片 / 截图 / 复杂示意图 | 无法结构化 | **原图兜底** | `![[fig-XX.png]]` + 说明 |

   **重要**：重画 Mermaid/表格后，**验证一遍语法和逻辑**（节点、箭头方向、行列数对不对），别凭空编一个「长得像」的图。

3. **只挑教学关键图**（用户明确要求，别全收）：
   - **收录**：核心概念图、关键流程、电路/体系结构、关键对照表、易错点示意图。每章 1–3 张，全笔记嵌入图 **≤ ~15 张**。
   - **跳过**：装饰性图标、重复图、纯封面/标题页、纯文字排版页、页码角标水印。

4. **每张图都要配说明**：`PPT N` 页码 + 一句话「这张图讲了什么 / 怎么看」，**不能只贴图不解释**。

### Step 3 — 通读学习（为讲而学）

用 `read` 读 `/tmp/ppt_text.txt` 全文（分段 offset/limit 读大文件），并对照 `/tmp/ppt_tables.txt` 和 Step 2 的图解解读。**你不是摘抄，是学习**：
- 识别**大纲结构**（目录页通常列出章节），据此定章节划分。
- 每节抓住**核心概念、定义、公式、例子、易错点、坑**。
- 留意**警告/注意**类内容（数学易错、概念混淆）——用 `> [!warning]` 或 `> [!danger]` 化。
- 记录**每章节、每小节对应的页码范围**（用 grep 定位每页标题，确认边界）。
- 把 Step 2 读懂的**关键图**挂到对应章节里。

### Step 4 — 生成笔记（教学导向，非摘抄）

**写作原则**：把内容讲清、讲透，让第一次学的人能懂。
- **改写**成你自己的话，加**解释**（为什么 / 直觉 / 记忆口诀），不是复制 PPT 文字。
- **图解**：把 Step 2 重画出的 Mermaid/表格、或原图嵌入 `![[...]]`，放进对应小节，紧跟相关文字，并带 `PPT N` 说明。
- **公式**：凡 `get_text()` 提取出来「碎了」的公式（下标变 `x2`、分式压成一行、希腊字母变乱码、∑/√/∫ 丢失），一律重写成 LaTeX：
  ```markdown
  $$ S = \sum_{i=0}^{n-1} a_i \cdot 2^i $$
  ```
  Obsidian 原生 MathJax 渲染 `$...$`（行内）与 `$$...$$`（块级）；拿不准符号时回看 Step 2 渲染出的那页 PNG。
- 用 Obsidian 特性：
  - `> [!note/tip/warning/danger/info/example/abstract]` 强调区。
  - `[[...]]` wiki 双链（笔记间、到 `[[课件.pdf]]`）。
  - Mermaid（`flowchart`、`sequenceDiagram`、`timeline`、`stateDiagram`）——包括重画的关键图。
  - Markdown 表格做对照（用 Step 1 的 `find_tables()` 结果，别手抄压平文本）。
  - 行内代码 `` `...` `` 写 0/1、码字。
- **每个 `##` / `###` 标题后**加页码标注：
  ```markdown
  ## 3. 数制系统 <span style="font-size:0.8em;color:gray">PPT 23–31</span>
  ### 2's 补码 <span style="font-size:0.8em;color:gray">PPT 51</span>
  ```
- **文件顶部信息框 + 页码索引表**（模板见下节）。
- **末尾**加自测和关联笔记。

### Step 5 — 标注页码

- **总索引表**：章 → 页范围（在文件顶部）。
- **逐节**：用 python 一次性给所有小节标题加页码（比 sed 稳，sed 遇中文/特殊字符会报错）：
  ```bash
  python3 - <<'PY'
  f="<笔记>.md"
  s=open(f,encoding='utf-8').read()
  mapping={"### 标题":"PPT N", ...}   # 每小节
  for title,page in mapping.items():
      if s.count(title)==1:
          s=s.replace(title, f'{title} <span style="font-size:0.8em;color:gray">{page}</span>',1)
  open(f,'w',encoding='utf-8').write(s)
  PY
  ```
- **验证**：`grep -nE "^## " | grep -v "span style"`（应无输出=全标上）；`grep -c "span style"` 数总数。

### Step 6 — 放进 Obsidian

- 先找真实 vault：`find /Users/taoweihao -maxdepth 6 -type d -name ".obsidian"` 列出所有 `.obsidian` 目录，父目录就是 vault。
- 主 vault 通常在 iCloud：`~/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian`，其下常有一个实际装笔记的 `Obsidian Vault/` 子目录（注意：`.obsidian` 在**外层** `Documents/obsidian` 那层，vault 根包含它）。
- 在 vault 里按课程建子目录：`mkdir -p "$VAULT/<课程名>/assets"`。
  - 把笔记 `.md` 和课件 PDF 复制进去（`cp`）——复制 PDF 让 `[[...]]` 双链可点开。
  - **把 Step 2 渲染出的、要嵌入笔记的关键图 PNG 也复制进 `assets/`**，并按 `fig-<PPT页码>.png` 命名，这样 `![[fig-XX.png]]` 能直接显示：
    ```bash
    cp /tmp/ppt_figs/page_023.png "$VAULT/<课程名>/assets/fig-23.png"
    ```
  - 在笔记顶部信息框里提示用户：若 `![[fig-XX.png]]` 不显示，确认 Obsidian「附件默认存放路径」能解析到 `assets/`（或用相对路径 `![](assets/fig-XX.png)` 兜底）。
- 若用户更早前有「单独文件夹」意图，先在其要求的位置建好，最终按用户即时指令放入真实 vault。
- 检查 Obsidian 是否运行（`pgrep -fl Obsidian`）：运行中会**自动刷新索引**，用户切到 Obsidian 即见；否则提示其打开/刷新。
- 用户之前建过的临时/重复副本，确认后删除（`rm -rf`），保持干净。

## 自测题设计原则（要有针对性）

自测不是「默写概念」，要**贴着考点和易错点**出题：

- **易错点/混淆辨析**：从 `[!warning]`/`[!danger]` 里挑，出「A 与 B 的区别」「哪个说法错」。
- **公式应用**：给情境/数字让读者**算**，不是默写公式本身。
- **图解读**：直接引用上面重画的 Mermaid/嵌入图，问「这张图说明了什么结论」——图就不是摆设了。
- **题型**：单选/多选/填空/判断/计算，答案用 `<details>` 关起，附一句解析（为什么对/错）。

> [!warning] `<details>` 关起式答案的坑（实测踩过）
> 答案里**不能出现字面量尖括号标签**（如 `<string-array>`、`<ListView>`、`<uses-permission>`），否则 Obsidian 会把它们当 HTML 标签解析，导致整段 `<details>` 退化成原始文本显示（标签红色高亮、`**加粗**` 星号也露出来）。**修复**：把答案里的尖括号转义成 `&lt;` / `&gt;`（显示效果不变），例如 `<string-array>` → `&lt;string-array&gt;`。更稳的做法是用 Obsidian 原生**折叠 callout**：`> [!note]- 答案`（内容正常写 Markdown、可放代码块，不会触发此坑）。

## 模板：页码索引表

放在文件顶部「本页概览」之后、目录之前：

```markdown
## 📑 课件页码索引

PPT = `<课件文件名>` 的 **PDF 物理页码**（第 1 页即幻灯片 1）。

| 章节 | PPT 页码 |
| --- | --- |
| ⭐ 封面 / 目录 | 1–2 |
| **1. 第一节标题** | 3–9 |
| ├ 小节 A | 3–5 |
| └ 小节 B | 6–9 |
| **2. 第二节标题** | 10–20 |
| 关键术语 | 80–84 |
| 课后习题 | 85–86 |
```

> 若课件是多章连续的（如 `(CH01-02)`），留意每部分实际页边界，别臆断。

## 质量检查（交付前）

- [ ] 笔记是**教学式**（有解释/直觉/口诀），不是 PPT 文字堆砌。
- [ ] **教学关键图解已融入**：重画成 Mermaid/表格或嵌入原图，每张带 `PPT N` + 一句话解读；没有因为「纯文本提取」把图丢掉。
- [ ] 重画的 Mermaid/表格**语法正确、逻辑与原图一致**（不凭空编）。
- [ ] **公式已还原成 LaTeX**（`$...$`），没有碎下标/乱码残留。
- [ ] **表格结构正确**（用了 `find_tables()`，行列没串位）。
- [ ] 扫描版课件已走 **OCR**，不是空文本硬编。
- [ ] 每章每节标题都带 `PPT x–y` 页码，顶部有索引总表。
- [ ] 末尾有**针对性**自测（关起式答案 + 解析），不是泛泛回忆。
- [ ] 文件已放入**真实 vault**、课件 PDF 和关键图一并复制，双链/图片可显示。
- [ ] 无敏感信息（不写密码/Key/令牌）。

## 参考

- 本 skill 生成并验证过完整流程：`Chapter1_Digital Systems and Information - PartI (CH01-02).pdf` → `Chapter1 数字系统与信息 (Part I).md`（含页码、自测、callout、Mermaid）。
- 本机实测工具环境：pymupdf 1.28.2、pdfplumber、pypdf 均可用；poppler（pdftotext/pdftoppm）未安装，`import fitz` 已弃用（改用 `import pymupdf`）。
- 缺失时：`python3 -m pip install pymupdf pdfplumber pypdf`；OCR：`python3 -m pip install ocrmypdf`（或 `pytesseract` + tesseract 二进制）。
