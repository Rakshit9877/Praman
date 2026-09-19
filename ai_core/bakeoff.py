"""ai_core/bakeoff.py — Quick latency + accuracy bake-off across providers/models.

Usage:
    AI_MODE=real  PYTHONPATH=. python -m ai_core.bakeoff data/registers/*.jpg
    AI_MODE=real  PYTHONPATH=. python -m ai_core.bakeoff data/registers/*.jpg --gt data/ground_truth/registers.csv

For each image it calls read_register (real mode, one provider at a time) and
prints a results table with per-image latency.  If --gt is supplied and the
ground-truth CSV has columns [image_id, day, mark], it also prints a rough
field-accuracy number (fraction of day cells that match).

In mock mode it still runs (using the mock reader) so you can verify the
harness works without API keys.
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import sys
import time
from pathlib import Path


# ---------------------------------------------------------------------------
# Ground-truth helpers
# ---------------------------------------------------------------------------

def _load_gt(gt_path: str) -> dict[str, dict[int, str]]:
    """Load ground-truth CSV → {image_id: {day: mark}}."""
    gt: dict[str, dict[int, str]] = {}
    with open(gt_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            img_id = row["image_id"].strip()
            day = int(row["day"].strip())
            mark = row["mark"].strip().upper()
            gt.setdefault(img_id, {})[day] = mark
    return gt


def _field_accuracy(extraction, gt_for_image: dict[int, str]) -> float | None:
    """Return fraction of day cells that match ground truth (target row only)."""
    target_rows = [r for r in extraction.rows if r.is_target]
    if not target_rows:
        # fall back to first row
        if not extraction.rows:
            return None
        target_rows = [extraction.rows[0]]

    correct = total = 0
    for cell in target_rows[0].cells:
        if cell.day in gt_for_image:
            total += 1
            if cell.mark.value == gt_for_image[cell.day]:
                correct += 1

    return (correct / total) if total > 0 else None


# ---------------------------------------------------------------------------
# Main bake-off runner
# ---------------------------------------------------------------------------

async def run_bakeoff(images: list[str], gt_path: str | None) -> None:
    from ai_core.api import read_register

    gt = _load_gt(gt_path) if gt_path else {}

    header = f"{'image':<30} {'elapsed_s':>10} {'n_samples':>9} {'accuracy':>9}"
    print(header)
    print("-" * len(header))

    totals: list[tuple[float, float | None]] = []

    for img_path in images:
        img_name = Path(img_path).name
        t0 = time.perf_counter()

        try:
            extraction = await read_register(img_path)
        except Exception as exc:
            print(f"{img_name:<30} ERROR: {exc}")
            continue

        elapsed = time.perf_counter() - t0

        gt_for_img = gt.get(extraction.image_id, {}) or gt.get(img_name, {})
        accuracy = _field_accuracy(extraction, gt_for_img) if gt else None

        acc_str = f"{accuracy:.1%}" if accuracy is not None else "—"
        print(f"{img_name:<30} {elapsed:>10.2f} {extraction.n_samples:>9} {acc_str:>9}")
        totals.append((elapsed, accuracy))

    if totals:
        print("-" * len(header))
        avg_elapsed = sum(t for t, _ in totals) / len(totals)
        acc_vals = [a for _, a in totals if a is not None]
        avg_acc = (sum(acc_vals) / len(acc_vals)) if acc_vals else None
        acc_str = f"{avg_acc:.1%}" if avg_acc is not None else "—"
        print(f"{'AVERAGE':<30} {avg_elapsed:>10.2f} {'':>9} {acc_str:>9}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="ai_core.bakeoff", description="Praman register-reader bake-off")
    parser.add_argument("images", nargs="+", help="Register image paths")
    parser.add_argument("--gt", default=None, help="Ground-truth CSV (columns: image_id, day, mark)")
    args = parser.parse_args()

    if not args.images:
        parser.error("Provide at least one image path.")

    asyncio.run(run_bakeoff(args.images, args.gt))


if __name__ == "__main__":
    main()
