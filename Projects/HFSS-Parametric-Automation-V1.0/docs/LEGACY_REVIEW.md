# 找回文件与旧脚本审计

## 找到的主线

2026-07-14 的 `research_pipeline` 已包含：

- `run_aedt_variations.py`：复制已验收工程并改变 design variables；
- `touchstone_metrics.py`：无第三方依赖的 N 端口 Touchstone 指标；
- `audit_existing_runs.py`：审计参考/移相通道结果；
- `generate_tolerance_plan.py`：确定性拉丁超立方容差计划；
- `HFSS_MODEL_ACCEPTANCE.md`：模型接入门槛。

这些内容构成 V1.0 的有效主线。

## 找到但未作为主程序发布的早期文件

旧目录中还有 `auto_param_tune.py`、`param_sweep.py`、`ggw_phase_shifter_45deg.py`、`build_model_only.py`、`build_and_solve.py`、`verify_build.py` 和 `verify_transmission.py`。它们记录了从自动建模、端口报错到会话隔离的探索过程，但存在以下风险：

- 输出目录和 Python/AEDT 路径绑定个人电脑；
- 多个参数点曾复用同一工程和会话，失败后遗留 `.aedt.lock`/`.asol_priv`；
- 部分版本的空气域没有覆盖销钉床，销钉不在正确求解区域；
- 槽体曾从下板底面挖除，可能形成贯穿通道；
- 参考通道和移相通道的几何组成或端口方向不完全一致；
- 脚本成功导出 S 参数并不代表模型达到目标。

现有 14 组早期结果主要接近 0°或发生 180°翻转，且插损、回波不满足基线，因此不能支持 -45° 移相器性能结论。

## V1.0 的处理

- 不复制上述几何生成代码，防止 AI 将历史试验误认为已验证模板。
- 保留“复制已验收工程并改单一变量”的通用主线。
- 将旧工程检查脚本重构为 `hfss-inspect`。
- 统一采用命令行路径、可选 AEDT 版本、隔离目录、显式覆盖和自动释放会话。
- 通过离线测试验证 CSV、路径安全、容差采样和 Touchstone 数学逻辑。

若未来恢复自动建模，应以新的独立版本实现，并加入几何不变量、端口面、材料相交、对象边界盒和最小传输模型的自动验收，不应直接复活旧脚本。

