#!/usr/bin/env bash
# Run matched YOLOv8n and VoVGSCSP2 DeepPCB experiments.
# Usage: bash run_deeppcb_experiment.sh /path/to/deeppcb_yolo /path/to/yolov8n.pt

set -euo pipefail

DATASET_DIR="${1:?Pass the YOLO-format DeepPCB dataset directory}"
BASE_WEIGHTS="${2:?Pass the local yolov8n.pt path}"
PROJECT_DIR="${PROJECT_DIR:-runs_deeppcb}"
EPOCHS="${EPOCHS:-300}"
SEED="${SEED:-0}"

if [[ ! -f "${DATASET_DIR}/data.yaml" ]]; then
  echo "Missing ${DATASET_DIR}/data.yaml" >&2
  exit 1
fi

yolo detect train   model="${BASE_WEIGHTS}"   data="${DATASET_DIR}/data.yaml"   imgsz=640 epochs="${EPOCHS}" batch=16 optimizer=SGD lr0=0.001   amp=True workers=8 seed="${SEED}"   project="${PROJECT_DIR}" name=baseline_yolov8n

yolo detect train   model="Projects/DeepPCB-Lightweight-Detection/configs/hsi_yolov8n.yaml"   data="${DATASET_DIR}/data.yaml"   imgsz=640 epochs="${EPOCHS}" batch=16 optimizer=SGD lr0=0.001   amp=True workers=8 seed="${SEED}"   project="${PROJECT_DIR}" name=vovgscsp2

yolo detect val   model="${PROJECT_DIR}/baseline_yolov8n/weights/best.pt"   data="${DATASET_DIR}/data.yaml" imgsz=640 split=test

yolo detect val   model="${PROJECT_DIR}/vovgscsp2/weights/best.pt"   data="${DATASET_DIR}/data.yaml" imgsz=640 split=test
