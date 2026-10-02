"""Evaluate object-detection predictions against labelled boxes.

The tool uses a dependency-free CSV format so experiment outputs can be checked
before they are placed into a paper or a project report.

Ground-truth CSV columns:
    image_id,class_name,xmin,ymin,xmax,ymax

Prediction CSV columns:
    image_id,class_name,score,xmin,ymin,xmax,ymax

Example:
    python detection_evaluator.py ground_truth.csv predictions.csv --iou 0.5 --report metrics.json
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Box:
    image_id: str
    class_name: str
    xmin: float
    ymin: float
    xmax: float
    ymax: float
    score: float = 1.0

    @property
    def area(self) -> float:
        return max(0.0, self.xmax - self.xmin) * max(0.0, self.ymax - self.ymin)


def read_boxes(path: Path, prediction: bool) -> list[Box]:
    required = {"image_id", "class_name", "xmin", "ymin", "xmax", "ymax"}
    if prediction:
        required.add("score")
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"{path} must contain: {', '.join(sorted(required))}")
        boxes: list[Box] = []
        for line, row in enumerate(reader, start=2):
            try:
                box = Box(
                    row["image_id"].strip(),
                    row["class_name"].strip(),
                    float(row["xmin"]),
                    float(row["ymin"]),
                    float(row["xmax"]),
                    float(row["ymax"]),
                    float(row.get("score", "1")),
                )
            except (KeyError, ValueError) as error:
                raise ValueError(f"invalid row at line {line} in {path}") from error
            if not box.image_id or not box.class_name or box.area <= 0:
                raise ValueError(f"invalid label or non-positive box at line {line} in {path}")
            boxes.append(box)
    return boxes


def iou(left: Box, right: Box) -> float:
    x1, y1 = max(left.xmin, right.xmin), max(left.ymin, right.ymin)
    x2, y2 = min(left.xmax, right.xmax), min(left.ymax, right.ymax)
    intersection = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    union = left.area + right.area - intersection
    return intersection / union if union else 0.0


def average_precision(ground_truth: list[Box], predictions: list[Box], threshold: float) -> dict[str, float | int]:
    classes = sorted({box.class_name for box in ground_truth})
    per_class: dict[str, dict[str, float | int]] = {}
    ap_values: list[float] = []

    for class_name in classes:
        truths = [box for box in ground_truth if box.class_name == class_name]
        candidates = sorted((box for box in predictions if box.class_name == class_name), key=lambda box: box.score, reverse=True)
        assigned: set[int] = set()
        true_positive, false_positive = [], []

        for candidate in candidates:
            options = [
                (index, iou(candidate, truth))
                for index, truth in enumerate(truths)
                if truth.image_id == candidate.image_id and index not in assigned
            ]
            best_index, best_iou = max(options, key=lambda item: item[1], default=(-1, 0.0))
            if best_iou >= threshold:
                assigned.add(best_index)
                true_positive.append(1)
                false_positive.append(0)
            else:
                true_positive.append(0)
                false_positive.append(1)

        precision_points, recall_points = [], []
        tp_sum = fp_sum = 0
        for tp, fp in zip(true_positive, false_positive):
            tp_sum += tp
            fp_sum += fp
            precision_points.append(tp_sum / (tp_sum + fp_sum))
            recall_points.append(tp_sum / len(truths))

        ap = 0.0
        for recall_level in [step / 100 for step in range(101)]:
            eligible = [precision for precision, recall in zip(precision_points, recall_points) if recall >= recall_level]
            ap += max(eligible, default=0.0) / 101
        ap_values.append(ap)
        per_class[class_name] = {
            "ground_truth": len(truths),
            "predictions": len(candidates),
            "true_positive": sum(true_positive),
            "false_positive": sum(false_positive),
            "average_precision": round(ap, 6),
        }

    return {
        "iou_threshold": threshold,
        "classes": per_class,
        "mAP": round(sum(ap_values) / len(ap_values), 6) if ap_values else 0.0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate object-detection CSV predictions.")
    parser.add_argument("ground_truth", type=Path)
    parser.add_argument("predictions", type=Path)
    parser.add_argument("--iou", type=float, default=0.5, help="IoU match threshold (default: 0.5)")
    parser.add_argument("--report", type=Path, help="optional JSON metrics output")
    args = parser.parse_args()
    if not 0 < args.iou <= 1:
        raise SystemExit("--iou must be in (0, 1]")

    try:
        metrics = average_precision(read_boxes(args.ground_truth, False), read_boxes(args.predictions, True), args.iou)
    except (OSError, ValueError) as error:
        raise SystemExit(f"Input error: {error}") from error

    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    if args.report:
        args.report.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Metrics written to {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
