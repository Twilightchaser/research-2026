# research-2026

这是 2026 年学习、实验和项目资料仓库，用于集中管理嵌入式、AI、硬件设计、控制理论、学习笔记和完整项目。

## 仓库结构

```text
research-2026
├── Embedded-System/        嵌入式学习
│   ├── STM32-Basics/
│   ├── Sensor-System/
│   └── Motor-Control/
├── AI-Learning/            AI 学习
│   ├── Machine-Learning/
│   ├── OpenCV/
│   └── PyTorch/
├── Hardware-Design/        硬件设计
│   ├── Circuit/
│   └── PCB/
├── Control-Theory/         控制学习
│   ├── PID/
│   └── Simulation/
├── Notes/                  学习笔记
├── Projects/               完整项目
│   ├── Elder-Posture-Recognition/
│   ├── ADS-MCP-Automation-V1.0/
│   ├── HFSS-Parametric-Automation-V1.0/
│   ├── Smart-Environment/
│   └── AI-Car/
└── README.md
```

## 当前项目

### Elder-Posture-Recognition

老年人姿态识别系统，基于 STM32F103C6T6、ADXL345、ESP8266、OLED、OneNET 和微信小程序，实现正常、疑似跌倒、久坐三类状态识别，并在小程序端提供 AI 风险评估和历史记录。

项目目录：

[Projects/Elder-Posture-Recognition](Projects/Elder-Posture-Recognition)

### ADS-MCP-Automation V1.0

通过 MCP 和 ADS Python API 执行工作区、原理图、仿真与参数调优的自动化项目。

[Projects/ADS-MCP-Automation-V1.0](Projects/ADS-MCP-Automation-V1.0)

### HFSS-Parametric-Automation V1.0

基于 PyAEDT 的隔离参数扫描、Touchstone 指标分析、容差计划和工程检查工具。主线以人工验收通过的 `.aedt` 模型为基线，避免旧自动建模脚本的几何和端口错误。

[Projects/HFSS-Parametric-Automation-V1.0](Projects/HFSS-Parametric-Automation-V1.0)

## 管理约定

- 学习过程中的单点知识放入对应学习目录。
- 可完整运行、可演示、包含文档的内容放入 `Projects/`。
- 大体积视频、编译中间产物和私有配置不提交到仓库。
- 涉及 Wi-Fi、云平台 token、设备密钥的配置使用占位符，真实参数仅保留在本地。

