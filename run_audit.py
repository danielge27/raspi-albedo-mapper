# %%


# %%
# run_audit.py
# Run this to process any Google Earth photo

import sys
import os
from surface_detector  import detect_surfaces
from report_generator  import generate_full_report


# %%


# %%


# %%


# %%

def run_audit(image_path, neighborhood_name):
    print(f"\n🔍 Analyzing: {neighborhood_name}")
    print(f"   Image: {image_path}")
    print("   Processing surfaces...")

    # Detect all surfaces
    original, annotated, results, total_px = \
        detect_surfaces(image_path)

    # Print quick summary to terminal
    print("\n📊 Surface Coverage:")
    for name, data in sorted(results.items(),
            key=lambda x: x[1]["coverage_pct"],
            reverse=True):
        if data["coverage_pct"] > 1:
            bar = "█" * int(data["coverage_pct"] / 2)
            print(f"   {data['label']:<25}"
                  f" {data['coverage_pct']:>5.1f}%  {bar}")

    # Generate full report
    print("\n📄 Generating report...")
    report_path = generate_full_report(
        image_path, annotated, original,
        results, neighborhood_name
    )

    print(f"\n✅ Done! Report: {report_path}\n")
    return report_path


# ── RUN ──────────────────────────────────────────────────
if __name__ == "__main__":

    # Process all your neighborhoods
    TARGETS = [
        ("photos/roxbury.jpg",       "Roxbury — Boston"),
        ("photos/seaport.jpg",       "Seaport District"),
        ("photos/jamaica_plain.jpg", "Jamaica Plain"),
        ("photos/norwood.jpg", "norwood bala"),
    ]

    for image_path, name in TARGETS:
        if os.path.exists(image_path):
            run_audit(image_path, name)
        else:
            print(f"⚠️  Photo not found: {image_path}")
            print(f"   Add your Google Earth photo here")

# %%



