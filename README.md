# ppt-to-obsidian-note

把课程课件 PDF 整理成 Obsidian 学习笔记，保留可核对的 PDF 物理页码、关键图表和自测题。Skill 会要求生成者核对来源、代码示例的文件归属与完整性，以及本地链接；无法核实的内容应明确标注。

## 安装到 DSH

复制**整个目录**，让 `SKILL.md` 和只读检查脚本保持在一起：

```bash
mkdir -p ~/.dsh/skills/ppt-to-obsidian-note
cp -R SKILL.md scripts references ~/.dsh/skills/ppt-to-obsidian-note/
```

从仓库根目录运行上述命令。安装后可以给助手一份课件 PDF，并说明笔记保存位置，例如：

> 把这份课件整理成 Obsidian 学习笔记，保存在我指定的课程文件夹。

若未指定 Vault，skill 会在当前可写工作区生成笔记，不自行寻找个人 Vault。

## 本地链接检查

在笔记与附件放到最终目录后运行：

```bash
python3 scripts/check_note.py '/path/to/lesson.md' --vault '/path/to/Obsidian Vault'
```

它检查 `[[wikilink]]`、本地 Markdown 链接和图片路径是否存在，跳过代码块与外部 URL。脚本只读，不会修改笔记。它不验证事实、代码能否编译或 Obsidian 实际渲染，这些要按 `SKILL.md` 的交付检查人工核对。

测试：

```bash
python3 -m unittest discover -s tests -v
```

## 依赖

检查脚本只使用 Python 标准库。生成笔记时可根据当前环境使用 PyMuPDF、OCR、PDF 页面渲染和图像理解工具；不要求固定工具组合。安装额外依赖前先看环境中已有的能力。

## License

[MIT](./LICENSE)
