# HFSS Parametric Automation V1.0

这是从 2026 年 HFSS 自动化实验中整理出的通用 PyAEDT 工具包。它以**人工验收通过的 `.aedt` 工程**为唯一建模基线，逐项复制工程、写入设计变量、求解并导出 Touchstone，避免批量脚本悄悄改变端口、边界、网格或参考面。

> V1.0 不自动生成电磁几何。早期自动建模脚本曾产生错误空气域、贯穿槽和端口方向问题，详见 [旧脚本审计](docs/LEGACY_REVIEW.md)。

## 能做什么

- CSV 驱动的任意 HFSS 设计变量扫描；
- 每个参数点使用隔离的工程副本和 AEDT 会话；
- build-only、完整求解、无 AEDT 的 dry-run；
- `.s2p`/`.sNp` Touchstone 1.x 解析；
- 两端口移相器及 4×4 Butler 矩阵指标计算；
- 拉丁超立方制造容差计划；
- HFSS 工程结构、端口、边界和 setup 的 JSON 检查报告。

## 环境

- Windows 或 AEDT/PyAEDT 支持的平台；
- Ansys Electronics Desktop 2022 R1 或更新版本；
- Python 3.10+；
- 只有启动 HFSS 的命令需要 `pyaedt`，计划验证和 Touchstone 分析不需要 AEDT。

安装：

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[hfss,dev]"
```

PyAEDT 官方安装说明：<https://aedt.docs.pyansys.com/version/stable/Getting_started/Installation.html>

## 5 分钟开始

1. 在 HFSS GUI 中建立或打开模型，把需要扫描的尺寸定义成 design variables。
2. 按 [模型验收清单](docs/HFSS_MODEL_ACCEPTANCE.md) 检查几何、端口、setup 与基线结果，关闭 HFSS。
3. 复制 `examples/variation_plan.csv`，第一列保持为 `run_id`，其余列名必须与 HFSS 变量名完全一致；值应携带单位或是合法的 HFSS 表达式。
4. 先做无副作用检查：

```powershell
hfss-variations `
  --source-project "C:\models\accepted_baseline.aedt" `
  --design "PhaseShifter" `
  --setup "Setup1" `
  --sweep "Sweep" `
  --plan ".\examples\variation_plan.csv" `
  --output-root "C:\hfss-runs" `
  --dry-run
```

5. 只生成参数化工程，不求解：去掉 `--dry-run`。确认一个副本无误后，加入 `--solve`。服务器或无人值守环境可加入 `--non-graphical`。

如需固定 AEDT 版本，传入 `--aedt-version 2026.1`；省略时由 PyAEDT 使用最新可用版本。重新执行已存在的 run 必须显式加入 `--overwrite`。

## 容差计划

```powershell
hfss-tolerance-plan `
  --config .\examples\research_config.json `
  --output .\outputs\tolerance_plan.csv
```

生成的列可直接作为 variation plan 使用，但变量名必须先与具体 AEDT 工程对齐。

## 审计已有两通道结果

目录结构应为 `<root>/<run_id>/exports/ref_channel.s2p` 和 `ps_channel.s2p`：

```powershell
hfss-audit --root C:\hfss-runs --output .\outputs --band-start 30 --band-stop 35
```

## 检查现有工程

```powershell
hfss-inspect "C:\models\accepted_baseline.aedt" `
  --aedt-version 2026.1 `
  --out .\outputs\project_report.json
```

## 给 AI/自动化代理的操作约束

AI 接手本项目时应按以下顺序执行：

1. 读取本 README、`docs/HFSS_MODEL_ACCEPTANCE.md` 和 variation CSV。
2. 运行测试：`python -m pytest -q`。
3. 对真实计划先执行 `hfss-variations ... --dry-run`。
4. 确认源工程已关闭、没有 `.aedt.lock`，且输出目录不是源模型目录。
5. 先 build-only 单点并人工检查，再单点 `--solve`，最后才扩大批量范围。
6. 不修改或覆盖原始 `.aedt`；不自动删除未知 lock；不把 `.aedt`、求解缓存或个人绝对路径提交 Git。
7. 报告实际设计名、setup、sweep、AEDT/PyAEDT 版本和输出文件，不把“脚本运行完成”当作“电磁模型正确”。

## 项目结构

```text
src/hfss_automation/   参数运行、工程检查、指标和容差模块
examples/              无个人路径的计划与配置示例
docs/                  建模验收、历史问题和研究状态
tests/                 不启动 AEDT 的离线测试
```

## 已知边界

- Touchstone 解析器支持 1.x 的 RI、MA、DB；遇到 Touchstone 2.x 会明确报错。
- 仿真命令需要本机可用的 AEDT 许可证。
- 项目不会判断几何是否符合论文或制造约束；必须执行人工验收。
- 不同 PyAEDT/AEDT 组合可能调整 API，升级后先跑 dry-run 和一个 build-only 点。

## 来源

主线整理自 `research_pipeline/run_aedt_variations.py`、Touchstone 指标工具和 2026-07-14 的模型验收记录；工程检查器整理自旧版 `inspect_hfss_project.py`。V1.0 已去除个人 Python、AEDT 与输出目录硬编码，并把已知无效的早期几何生成路线隔离到审计文档。

## License

MIT

