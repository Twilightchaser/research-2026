# Measurement Data Inspector

用于实验与传感器数据的轻量 CSV 检查工具。它会读取指定的数值列，统计缺失/无效记录、极值、均值、中位数、标准差和基于四分位距（IQR）的离群点；还可以导出删除无效记录后的清洁 CSV。

## 环境

- Python 3.10 或更高版本
- 仅使用 Python 标准库

## 输入格式

CSV 首行必须包含列名。例如：

```csv
time_s,voltage_v,current_ma
0.0,4.98,12.1
0.5,5.02,12.0
1.0,,12.2
1.5,9.80,12.1
```

## 运行

```bash
python Projects/Measurement-Data-Inspector/measurement_inspector.py measurements.csv \
  --column voltage_v --cleaned voltage_clean.csv
```

## 输出示例

```text
Measurement column: voltage_v
Rows: 3/4 valid; 1 invalid or missing
Range: 4.98 to 9.8
Mean: 6.6 | Median: 5.02 | Std dev: 2.77
IQR-rule outliers: 0
Cleaned CSV written to voltage_clean.csv
```

## 使用场景

- 电源纹波、传感器电压、电流或温度采样数据的快速检查
- 导入 MATLAB、Excel 或绘图脚本前排除缺失和非数值行
- 对比实验记录时快速发现明显异常点

## 目录

```text
Measurement-Data-Inspector/
├── measurement_inspector.py
└── README.md
```
