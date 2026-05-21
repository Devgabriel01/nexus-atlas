"""
NEXUS ATLAS — Satellite-aware YOLO training pipeline.

Trains YOLOv8 on aerial/satellite datasets (RarePlanes, xView, DOTA) to detect
overhead objects: aircraft, ships, vehicles, structures.

REQUIREMENTS:
  - GPU with CUDA (training on CPU works but takes 50× longer)
  - 50–200 GB free disk (datasets are large)
  - ~$0 if you have a GPU; on Colab Pro+ or RunPod ~$0.50/hour A100

DATASETS:
  1. RarePlanes (aircraft, synthetic + real)
     https://www.cosmiqworks.org/rareplanes
     - 110 satellite images, 50k+ aircraft, COCO format
  2. xView (general aerial objects, 60 classes)
     http://xviewdataset.org/
     - 1M+ objects across 60 classes (planes, ships, buildings...)
  3. DOTA v2 (oriented object detection in aerial)
     https://captain-whu.github.io/DOTA/

USAGE:
  # 1. Get HuggingFace dataset OR download manually
  python train_satellite_yolo.py --dataset rareplanes --epochs 100

  # 2. Or convert your own labeled satellite imagery to YOLO format and
  #    point --data at the YAML
  python train_satellite_yolo.py --data ./datasets/custom/data.yaml --epochs 50

  # 3. Output goes to runs/detect/train_satellite/weights/best.pt
  #    Copy that file to ./weights/yolov8-satellite.pt and the detector
  #    will auto-pick it up.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def download_rareplanes(out: Path) -> Path:
    """Download a small subset of RarePlanes for quick fine-tuning."""
    print(f"[TRAIN] Downloading RarePlanes subset to {out}")
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("Install: pip install huggingface_hub")
        sys.exit(1)
    repo_local = snapshot_download(
        repo_id="aerial/rareplanes-yolo-subset",
        repo_type="dataset",
        local_dir=str(out),
        local_dir_use_symlinks=False,
    )
    yaml_path = Path(repo_local) / "data.yaml"
    if not yaml_path.exists():
        # Generate a minimal YAML for fallback
        yaml_path.write_text(
            f"path: {repo_local}\n"
            "train: images/train\n"
            "val: images/val\n"
            "names:\n"
            "  0: small_aircraft\n"
            "  1: medium_aircraft\n"
            "  2: large_aircraft\n"
        )
    return yaml_path


def main():
    ap = argparse.ArgumentParser(description="Train YOLOv8 on satellite imagery")
    ap.add_argument("--dataset", choices=["rareplanes", "xview", "custom"],
                    default="rareplanes")
    ap.add_argument("--data", type=str, default=None,
                    help="Path to data.yaml (overrides --dataset)")
    ap.add_argument("--model", default="yolov8n.pt",
                    help="Base model: yolov8n.pt / yolov8s.pt / yolov8m.pt / yolov8l.pt")
    ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--device", default="0", help="'0' for GPU 0, 'cpu' for CPU")
    ap.add_argument("--name", default="satellite_yolo")
    ap.add_argument("--out", default="./datasets")
    args = ap.parse_args()

    try:
        from ultralytics import YOLO
    except ImportError:
        print("Install: pip install ultralytics")
        sys.exit(1)

    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)

    if args.data:
        data_yaml = Path(args.data)
    elif args.dataset == "rareplanes":
        data_yaml = download_rareplanes(out / "rareplanes")
    else:
        raise SystemExit(f"--dataset {args.dataset} requires manual download. "
                         f"See module docstring for URLs, then pass --data path/to/data.yaml")

    print(f"[TRAIN] data.yaml: {data_yaml}")
    print(f"[TRAIN] base model: {args.model}, epochs: {args.epochs}, device: {args.device}")

    model = YOLO(args.model)
    results = model.train(
        data=str(data_yaml),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        name=args.name,
        patience=20,
        save=True,
        plots=True,
        # Aerial-imagery augmentations
        degrees=180.0,        # rotate up to 180° (satellites view from any angle)
        translate=0.2,
        scale=0.3,
        shear=0.0,
        perspective=0.0,
        flipud=0.5,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.1,
        copy_paste=0.1,
    )

    weights_dir = Path(__file__).parent / "weights"
    weights_dir.mkdir(exist_ok=True)
    src = Path(results.save_dir) / "weights" / "best.pt"
    if src.exists():
        dst = weights_dir / "yolov8-satellite.pt"
        import shutil
        shutil.copy(src, dst)
        print(f"[TRAIN] Best weights copied to {dst}")
        print("[TRAIN] Detector will auto-pick this on next backend restart.")
    else:
        print(f"[TRAIN] Could not find best.pt at {src}")


if __name__ == "__main__":
    main()
