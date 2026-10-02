# DeepPCB Lightweight Detection

A reproducible project record for a lightweight PCB surface-defect detector derived from YOLOv8n. The implementation replaces backbone stages with the VoVGSCSP2 module, which combines GSConv, GSBottleneck and cross-stage partial connections. The neck and detection head remain aligned with the YOLOv8n baseline so that the backbone trade-off can be examined directly.

> This directory records the code and experimental configuration used for the DeepPCB study. It does not include dataset images, trained weights, or unpublished raw logs.

## Research question

Can a lightweight backbone reduce model cost for PCB defect detection while retaining useful detection performance?

The answer from the controlled DeepPCB comparison is nuanced: the VoVGSCSP2 backbone reduces model size and computation, but also reduces detection accuracy, particularly through missed detections of the **short** and **spur** defect classes.

## Dataset and protocol

- Dataset: public **DeepPCB** PCB surface-defect benchmark
- Classes: open, short, mousebite, spur, pin hole, spurious copper
- Dataset scale: 1,500 image pairs and 3,140 annotated instances
- Split: 1,000 training pairs (15% validation) and 500 test pairs
- Input size: 640 × 640
- Training: SGD, learning rate 0.001, batch size 16, AMP enabled, fixed seed 0
- Metrics: mAP50 and mAP50-95 (rather than DeepPCB's original IoU > 0.33 protocol)

## Main comparison

| Model | Checkpoint / epochs | Params | GFLOPs | mAP50 | mAP50-95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| YOLOv8n baseline | 300 | 3.01M | 8.1 | 96.81% | 72.22% |
| YOLOv8n + VoVGSCSP2 | 283 | 2.61M | 7.4 | 91.20% | 57.47% |

Relative to the baseline, the proposed backbone reduces parameters by about 13% and computation by about 9%. The cost is lower recall and localization quality. Error analysis identified missed detections, rather than broad inter-class confusion, as the dominant failure mode: short defects had a 24% miss rate and spur defects a 12% miss rate. A channel-recalibration variant was explored under an 80-epoch schedule (mAP50 87.94%, mAP50-95 54.67%, 2.64M parameters); because that schedule was not matched to the 283-epoch main run, it is recorded as preliminary rather than a conclusive comparison.

## Repository layout

~~~text
DeepPCB-Lightweight-Detection/
├── configs/
│   ├── hsi_yolov8n.yaml       # VoVGSCSP2 backbone
│   └── hsi_cr_yolov8n.yaml    # channel-recalibration variant
├── src/
│   └── hsi_modules.py         # GSConv / GSBottleneck / VoVGSCSP2 implementations
├── scripts/
│   └── run_deeppcb_experiment.sh
└── README.md
~~~

## Environment

- Python 3.10+
- PyTorch compatible with the selected CUDA environment
- Ultralytics YOLO (record the exact installed version for each run)
- A local DeepPCB-to-YOLO conversion step that has been visually checked for class-index correctness

The dataset and model weights are intentionally excluded. Use the official dataset source and place paths in your local environment.

## Run workflow

1. Install the dependencies and record the exact versions.

   ~~~bash
   pip install ultralytics
   pip show ultralytics torch
   ~~~

2. Convert DeepPCB annotations to YOLO format, then manually overlay several converted labels on original images to verify boxes and class indices.

3. Run the baseline and the VoVGSCSP2 configuration with the same seed and training budget.

   ~~~bash
   bash Projects/DeepPCB-Lightweight-Detection/scripts/run_deeppcb_experiment.sh      /path/to/deeppcb_yolo /path/to/yolov8n.pt
   ~~~

4. Evaluate each best checkpoint with the same test split and export the generated metrics. Do not replace the table above with numbers from a different split, seed or schedule.

## Notes for reproduction

- The YAML files reference custom symbols such as `VoVGSCSP2` and `VoVGSCSP2CR`. Register the supplied module with the local Ultralytics installation before loading the model configuration.
- The project does not claim that a single run estimates statistical variance; the recorded comparison uses one fixed seed.
- Any later ablation should state its epoch budget explicitly. Comparing unmatched schedules as if they were controlled results is a very efficient way to make a table look confident and a reviewer look unconvinced.
