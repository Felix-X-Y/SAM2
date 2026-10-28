"""CPU image inference. Synthetic smoke checks are never dental experiments."""
import argparse
from datetime import datetime
import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Avoid the official repository directory shadowing the installed sam2 package.
sys.path.insert(0, str(ROOT / 'sam2'))

import numpy as np
import torch
from PIL import Image
from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--image', type=Path)
    parser.add_argument('--prompts', type=Path, help='JSON: {"boxes": [[x1,y1,x2,y2], ...]} in original pixels')
    parser.add_argument('--smoke', action='store_true', help='Synthetic environment check only')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--threads', type=int, default=4)
    args = parser.parse_args()
    if args.smoke and (args.image or args.prompts):
        parser.error('--smoke cannot be combined with real input')
    if not args.smoke and not (args.image and args.prompts):
        parser.error('Real inference requires --image and --prompts')
    args.output.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(args.threads)
    if args.smoke:
        image = np.zeros((256, 256, 3), dtype=np.uint8)
        image[70:190, 90:165] = 200
        boxes = [[85, 65, 170, 195]]
    else:
        image = np.asarray(Image.open(args.image).convert('RGB'))
        boxes = json.loads(args.prompts.read_text(encoding='utf-8-sig'))['boxes']
    h, w = image.shape[:2]
    if not boxes:
        raise ValueError('At least one confirmed box is required')
    for box in boxes:
        if len(box) != 4 or not (0 <= box[0] < box[2] <= w and 0 <= box[1] < box[3] <= h):
            raise ValueError(f'Invalid box for {w}x{h}: {box}')
    checkpoint = ROOT / 'sam2/checkpoints/sam2.1_hiera_tiny.pt'
    started = time.perf_counter()
    model = build_sam2('configs/sam2.1/sam2.1_hiera_t.yaml', str(checkpoint), device='cpu', apply_postprocessing=False)
    predictor = SAM2ImagePredictor(model, max_hole_area=0, max_sprinkle_area=0)
    load_seconds = time.perf_counter() - started
    results = []
    overlay = image.astype(np.float32).copy()
    with torch.inference_mode():
        started = time.perf_counter()
        predictor.set_image(image)
        encode_seconds = time.perf_counter() - started
        for index, box in enumerate(boxes, 1):
            started = time.perf_counter()
            masks, scores, _ = predictor.predict(box=np.asarray(box, dtype=np.float32), multimask_output=False)
            elapsed = time.perf_counter() - started
            mask = masks[0].astype(bool)
            Image.fromarray(mask.astype(np.uint8) * 255).save(args.output / f'mask_{index:03d}.png')
            color = np.asarray([(index * 73) % 200 + 30, (index * 131) % 200 + 30, (index * 47) % 200 + 30])
            overlay[mask] = overlay[mask] * .55 + color * .45
            results.append({'instance': index, 'box_xyxy': box, 'model_score_not_accuracy': float(scores[0]), 'mask_pixels': int(mask.sum()), 'decode_seconds': elapsed})
    Image.fromarray(overlay.astype(np.uint8)).save(args.output / 'overlay.png')
    commit = subprocess.check_output(['git', '-C', str(ROOT / 'sam2'), 'rev-parse', 'HEAD'], text=True).strip()
    record = {'purpose': 'synthetic_environment_check' if args.smoke else 'dental_preexperiment',
              'timestamp_local': datetime.now().astimezone().isoformat(),
              'image_path': None if args.smoke else str(args.image.resolve()), 'image_sha256': hashlib.sha256(image.tobytes()).hexdigest(),
              'image_size_wh': [w, h], 'model': 'SAM2.1 Hiera Tiny', 'commit': commit,
              'python': platform.python_version(), 'torch': torch.__version__, 'device': 'cpu', 'threads': args.threads,
              'checkpoint_sha256': hashlib.file_digest(checkpoint.open('rb'), 'sha256').hexdigest(),
              'precision': 'float32', 'cuda_postprocessing': False, 'model_input_size': 1024,
              'load_seconds': load_seconds, 'encode_seconds': encode_seconds, 'instances': results,
              'ground_truth_available': False, 'accuracy_metrics': None}
    (args.output / 'record.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(record, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
