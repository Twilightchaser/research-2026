# ADS MCP Automation V1.0

这是一个通过 MCP 协议和 Keysight 官方 Python API 自动操作 Advanced Design
System（ADS）的开源项目。它面向 Claude Code、Codex 等能够调用 MCP 工具的 AI，
支持工作区、库、原理图、版图、元件、连线、网表和仿真的自动化操作。

## V1.0 已实现

- 自动检测 Windows/Linux 上的 ADS 安装；
- 使用 ADS 自带 Python 加载 `keysight.ads` SDK；
- 原子建模计划 `ads_execute_plan`；
- 工作区、Library、schematic 和 layout 操作；
- 元件放置、参数设置、几何图形和连线；
- 网表生成和 `hpeesofsim` 命令行仿真；
- ADS dataset 读取、S 参数评估和参数扫描示例；
- ADS GUI 并发检测、超时、日志隔离及崩溃保护；
- 27 个 MCP 工具和 8 项自动测试。

## 已验证闭环

V1.0 已在 ADS 2026 上完成以下真实验证：

```text
AI/MCP → 创建 LPF 原理图 → 生成网表 → S 参数仿真
       → 读取 S11/S21 → 扫描 L/C → 选择最优值 → 写回 ADS
```

验证工程采用双串联电感和并联电容低通滤波器。项目包含可复用的建模、仿真、
调参和参数写回脚本。

## 快速安装

```powershell
cd Projects/ADS-MCP-Automation-V1.0
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
```

在 MCP 客户端中设置：

```json
{
  "mcpServers": {
    "ads": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "ads_mcp_server"],
      "env": {"ADS_PATH": "你的 ADS 安装目录"}
    }
  }
}
```

使用 headless automation 前必须关闭 ADS GUI。AI 建模优先使用
`ads_execute_plan`，完成后检查网表节点，再调用 `ads_run_netlist`。

## 文档入口

- [英文 README](README.md)
- [AI 操作规则](AGENTS.md)
- [通用 AI 工作流](docs/AI_WORKFLOW.md)
- [问题复盘与排错](docs/TROUBLESHOOTING.md)

## V1.0 限制及后续方向

- 当前主要采用无界面 automation，不直接控制已打开的 ADS GUI；
- 不同 ADS 版本的个别 SDK 枚举和器件参数仍可能存在差异；
- 后续可开发 in-ADS addon，实现对当前 GUI 会话的双向控制；
- 后续可增加 Momentum/EM、HB、优化器、dataset 图表和更多版本矩阵测试；
- 后续版本建议使用 Git tag，例如 `ads-mcp-v1.1`、`ads-mcp-v2.0`。

本项目与 Keysight Technologies 无隶属关系。ADS 和 PathWave 为 Keysight 的商标。
