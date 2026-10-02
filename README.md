# research-2026

这是 2026 年学习、实验和项目资料仓库，用于集中管理嵌入式、AI、硬件设计、控制理论、学习笔记和完整项目。每个 Projects/ 下的项目都应当具备可运行源码、独立 README、明确的环境要求与复现步骤。

## 快速开始

~~~bash
git clone https://github.com/Twilightchaser/research-2026.git
cd research-2026
python --version
~~~

大部分 Python 工具只依赖标准库，可直接按各项目 README 中的命令运行。ADS、HFSS 和 STM32 项目则需要相应的工程软件或硬件环境。

## 仓库结构

~~~text
research-2026
├── Embedded-System/        嵌入式学习
├── AI-Learning/            AI 学习
├── Hardware-Design/        硬件设计
├── Control-Theory/         控制学习
├── Notes/                  学习笔记
├── Projects/               可运行项目
│   ├── Elder-Posture-Recognition/
│   ├── ADS-MCP-Automation-V1.0/
│   ├── HFSS-Parametric-Automation-V1.0/
│   ├── RLC-Frequency-Response-Analyzer/
│   ├── Measurement-Data-Inspector/
│   ├── Object-Detection-Experiment-Toolkit/
│   └── DeepPCB-Lightweight-Detection/
└── README.md
~~~

## 当前项目

| 项目 | 说明 | 运行入口 |
| --- | --- | --- |
| [Elder-Posture-Recognition](Projects/Elder-Posture-Recognition) | 基于 STM32、ADXL345、ESP8266、OLED、OneNET 的老年人姿态识别与风险评估系统。 | 项目 README |
| [ADS-MCP-Automation-V1.0](Projects/ADS-MCP-Automation-V1.0) | 通过 MCP 和 ADS Python API 执行工作区、原理图、仿真与参数调优。 | 项目 README |
| [HFSS-Parametric-Automation-V1.0](Projects/HFSS-Parametric-Automation-V1.0) | 基于 PyAEDT 的参数扫描、Touchstone 指标分析、容差计划和工程检查工具。 | 项目 README |
| [RLC-Frequency-Response-Analyzer](Projects/RLC-Frequency-Response-Analyzer) | 计算串联/并联 RLC 网络的阻抗、相位与扫频 CSV。 | python Projects/RLC-Frequency-Response-Analyzer/rlc_analyzer.py --help |
| [Measurement-Data-Inspector](Projects/Measurement-Data-Inspector) | 检查实验 CSV 的缺失值、统计量与 IQR 离群点，并可导出清洁数据。 | python Projects/Measurement-Data-Inspector/measurement_inspector.py --help |
| [Object-Detection-Experiment-Toolkit](Projects/Object-Detection-Experiment-Toolkit) | 对目标检测标注与预测 CSV 计算分类 AP、mAP 与 IoU 匹配结果，用于复核真实实验数据。 | python Projects/Object-Detection-Experiment-Toolkit/detection_evaluator.py --help |
| [DeepPCB-Lightweight-Detection](Projects/DeepPCB-Lightweight-Detection) | YOLOv8n 的 VoVGSCSP2 轻量化骨干研究：记录 DeepPCB 上参数量、算力和检测性能的真实取舍。 | bash Projects/DeepPCB-Lightweight-Detection/scripts/run_deeppcb_experiment.sh <dataset> <weights> |

## 复现约定

1. 先进入项目目录，阅读该项目的 README.md。
2. 使用 README 给出的命令运行；命令行工具均支持 --help 查看参数。
3. 涉及真实设备、商业仿真软件、云端服务或私密密钥的项目，以仓库内的占位配置为准，真实凭据仅保留在本地。
4. 运行或修改后，请保留示例输入、输出与依赖版本，避免“能跑但没人知道怎么跑”的经典工程悲剧。

## 管理约定

- 学习过程中的单点知识放入对应学习目录。
- 可完整运行、可演示、包含文档的内容放入 Projects/。
- 大体积视频、编译中间产物和私有配置不提交到仓库。
- 涉及 Wi-Fi、云平台 token、设备密钥的配置使用占位符，真实参数仅保留在本地。
