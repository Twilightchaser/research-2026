# Object Detection Experiment Toolkit

用于目标检测实验的结果整理与复核。工具以无第三方依赖的 CSV 输入为基础，按类别执行贪心匹配，计算 IoU 阈值下的 AP 与 mAP，并将结果输出为 JSON。

它适合作为论文实验、模型迭代或 FPGA/边缘端目标检测前处理中的轻量评估环节；仓库不保存未公开样本、真实标注或未经确认的论文结果。

## 环境

- Python 3.10+
- 无第三方依赖

## 数据格式

真实标注 CSV：

~~~csv
image_id,class_name,xmin,ymin,xmax,ymax
frame_001,person,20,15,92,180
~~~

预测结果 CSV：

~~~csv
image_id,class_name,score,xmin,ymin,xmax,ymax
frame_001,person,0.97,21,16,91,179
~~~

坐标以同一图像坐标系为准，边界框必须满足 x_max > x_min、y_max > y_min。

## 运行

~~~bash
python Projects/Object-Detection-Experiment-Toolkit/detection_evaluator.py   ground_truth.csv predictions.csv --iou 0.5 --report metrics.json
~~~

输出包括每类的真实框数量、预测数量、TP、FP、AP，以及整体 mAP。

## 论文复现建议

1. 将每一组模型/阈值的输出保存为独立预测 CSV。
2. 固定数据划分和 IoU 阈值，记录模型版本、输入分辨率、推理设备与运行时间。
3. 将生成的 JSON 与论文表格逐项核对；只有与实际实验一致的数值才可写入正文。
4. 若实验涉及公开数据集，补充其名称、版本、许可和划分方式；若涉及自采数据，避免上传可识别个人信息的原始图像。

## 目录

~~~text
Object-Detection-Experiment-Toolkit/
├── detection_evaluator.py
└── README.md
~~~
