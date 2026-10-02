# RLC Frequency Response Analyzer

一个无需第三方依赖的命令行工具，用于计算串联或并联 RLC 网络的阻抗、相位和在 1 V 激励下的电流，并将对数扫频结果导出为 CSV，方便后续用 Excel、MATLAB 或 Python 作图。

## 环境

- Python 3.10 或更高版本
- 不需要安装第三方包

## 运行

在仓库根目录执行：

```bash
python Projects/RLC-Frequency-Response-Analyzer/rlc_analyzer.py \
  --topology series --r 10 --l 0.01 --c 1e-6 \
  --start 100 --stop 10000 --points 12 --csv response.csv
```

参数单位分别为：R（欧姆）、L（亨利）、C（法拉）、频率（Hz）。

## 示例输出

```text
Series RLC | R=10 ohm, L=0.01 H, C=1e-06 F
Calculated resonance: 1591.549 Hz

      f (Hz)      |Z| (ohm)    phase (deg)    I @ 1 V (mA)
------------------------------------------------------------
     100.000          1591.2        -89.640          0.62847
```

## 输出数据

传入 `--csv response.csv` 后会生成包含以下字段的文件：

- `frequency_hz`：扫频点
- `z_real_ohm`、`z_imag_ohm`：复阻抗实部和虚部
- `magnitude_ohm`、`phase_deg`：阻抗幅值与相位
- `current_ma_at_1v`：1 V 激励下的电流幅值

## 目录

```text
RLC-Frequency-Response-Analyzer/
├── rlc_analyzer.py
└── README.md
```
