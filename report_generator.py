# %%


# %%


# %%
# report_generator.py
# Generates the final visual report

import cv2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import os
from datetime import datetime

from surface_detector    import SURFACES
from albedo_calculator   import (
    calculate_neighborhood_albedo,
    calculate_heat_index,
    get_heat_grade,
    generate_recommendations,
    estimate_temperature_impact
)


def generate_legend(results):
    """Create legend patches for the map"""
    patches = []
    for name, data in results.items():
        if data["coverage_pct"] > 0.5:
            bgr   = data["color"]
            rgb   = (bgr[2]/255, bgr[1]/255, bgr[0]/255)
            patch = mpatches.Patch(
                color=rgb,
                label=f"{data['label']} ({data['coverage_pct']}%)"
            )
            patches.append(patch)
    return patches


def generate_full_report(image_path,
                         annotated_img,
                         original_img,
                         results,
                         neighborhood_name,
                         output_dir="outputs"):

    os.makedirs(output_dir, exist_ok=True)

    # ── Calculate scores ─────────────────────────────────
    albedo      = calculate_neighborhood_albedo(results)
    heat_index  = calculate_heat_index(results)
    grade, risk, grade_color = get_heat_grade(heat_index)
    recs        = generate_recommendations(results, neighborhood_name)
    temp_excess = estimate_temperature_impact(results)
    timestamp   = datetime.now().strftime("%B %d, %Y")

    # ── Build figure ──────────────────────────────────────
    fig = plt.figure(figsize=(18, 12),
                     facecolor='#0a0a0a')
    gs  = GridSpec(3, 3,
                   figure=fig,
                   hspace=0.45,
                   wspace=0.35)

    # ── 1. HEADER BAR ────────────────────────────────────
    ax_header = fig.add_subplot(gs[0, :])
    ax_header.set_facecolor('#0a0a0a')
    ax_header.axis('off')

    ax_header.text(0.0, 0.85,
        "URBAN ALBEDO THERMAL AUDIT",
        transform=ax_header.transAxes,
        fontsize=11, color='#555', fontweight='bold',
        fontfamily='monospace')

    ax_header.text(0.0, 0.3,
        neighborhood_name,
        transform=ax_header.transAxes,
        fontsize=26, color='white', fontweight='bold')

    ax_header.text(1.0, 0.3,
        timestamp,
        transform=ax_header.transAxes,
        fontsize=10, color='#555',
        ha='right', fontfamily='monospace')

    # Grade badge
    ax_header.text(0.99, 0.9,
        f" Heat Risk: {grade} — {risk} ",
        transform=ax_header.transAxes,
        fontsize=13, color='white', fontweight='bold',
        ha='right',
        bbox=dict(boxstyle='round,pad=0.4',
                  facecolor=grade_color,
                  edgecolor='none', alpha=0.9))

    # Divider line
    ax_header.axhline(y=0, color='#333',
                      linewidth=1, xmin=0, xmax=1)

    # ── 2. ORIGINAL PHOTO ────────────────────────────────
    ax_orig = fig.add_subplot(gs[1, 0])
    ax_orig.imshow(cv2.cvtColor(original_img,
                                cv2.COLOR_BGR2RGB))
    ax_orig.set_title("Original Image",
                      color='white', fontsize=9,
                      pad=8, fontfamily='monospace')
    ax_orig.axis('off')

    # ── 3. ANNOTATED CONTOUR MAP ─────────────────────────
    ax_map = fig.add_subplot(gs[1, 1])
    ax_map.imshow(cv2.cvtColor(annotated_img,
                               cv2.COLOR_BGR2RGB))
    ax_map.set_title("Albedo Contour Map",
                     color='white', fontsize=9,
                     pad=8, fontfamily='monospace')
    ax_map.axis('off')

    legend_patches = generate_legend(results)
    ax_map.legend(
        handles=legend_patches,
        loc='lower left',
        fontsize=6,
        facecolor='#111',
        edgecolor='#333',
        labelcolor='white',
        framealpha=0.85
    )

    # ── 4. COVERAGE BAR CHART ────────────────────────────
    ax_bar = fig.add_subplot(gs[1, 2])
    ax_bar.set_facecolor('#111')

    sorted_surfaces = sorted(
        results.items(),
        key=lambda x: x[1]["coverage_pct"],
        reverse=True
    )

    labels = [d["label"] for _, d in sorted_surfaces]
    values = [d["coverage_pct"] for _, d in sorted_surfaces]
    colors = [(d["color"][2]/255,
               d["color"][1]/255,
               d["color"][0]/255)
              for _, d in sorted_surfaces]

    bars = ax_bar.barh(labels, values,
                       color=colors, alpha=0.85,
                       edgecolor='#222', linewidth=0.5)

    # Add value labels on bars
    for bar, val in zip(bars, values):
        ax_bar.text(bar.get_width() + 0.5, bar.get_y() +
                    bar.get_height()/2,
                    f'{val:.1f}%',
                    va='center', ha='left',
                    color='white', fontsize=7,
                    fontfamily='monospace')

    ax_bar.set_xlim(0, max(values) * 1.25 if values else 100)
    ax_bar.set_title("Surface Coverage",
                     color='white', fontsize=9,
                     pad=8, fontfamily='monospace')
    ax_bar.tick_params(colors='#888', labelsize=7)
    ax_bar.spines['bottom'].set_color('#333')
    ax_bar.spines['left'].set_color('#333')
    ax_bar.spines['top'].set_visible(False)
    ax_bar.spines['right'].set_visible(False)
    ax_bar.set_xlabel("% of total area",
                      color='#888', fontsize=7)

    # ── 5. KEY METRICS ROW ───────────────────────────────
    ax_metrics = fig.add_subplot(gs[2, 0])
    ax_metrics.set_facecolor('#111')
    ax_metrics.axis('off')

    metrics = [
        ("Avg Albedo",    f"{albedo:.2f}",    "0=black  1=mirror"),
        ("Heat Index",    f"{heat_index}/100", "higher = hotter"),
        ("Heat Grade",    grade,               risk),
        ("Excess Heat",   f"+{temp_excess}°F", "vs. ideal urban"),
    ]

    for i, (key, val, sub) in enumerate(metrics):
        y = 0.85 - i * 0.22
        ax_metrics.text(0.05, y, key,
            transform=ax_metrics.transAxes,
            fontsize=7, color='#888',
            fontfamily='monospace')
        ax_metrics.text(0.05, y - 0.09, val,
            transform=ax_metrics.transAxes,
            fontsize=16, color='white', fontweight='bold')
        ax_metrics.text(0.55, y - 0.05, sub,
            transform=ax_metrics.transAxes,
            fontsize=7, color='#555',
            fontfamily='monospace')

    ax_metrics.set_title("Key Metrics",
                         color='white', fontsize=9,
                         pad=8, fontfamily='monospace')
    ax_metrics.add_patch(
        plt.Rectangle((0,0), 1, 1,
                       fill=True, facecolor='#111',
                       transform=ax_metrics.transAxes,
                       zorder=-1))

    # ── 6. RECOMMENDATIONS ───────────────────────────────
    ax_recs = fig.add_subplot(gs[2, 1:])
    ax_recs.set_facecolor('#111')
    ax_recs.axis('off')
    ax_recs.set_title("Planning Recommendations",
                      color='white', fontsize=9,
                      pad=8, fontfamily='monospace')

    if recs:
        for i, rec in enumerate(recs[:3]):
            y = 0.88 - i * 0.32
            # Emoji + title
            ax_recs.text(0.02, y,
                f"{rec['emoji']} {rec['title']}",
                transform=ax_recs.transAxes,
                fontsize=8.5, color='white',
                fontweight='bold')
            # Detail text (truncated)
            detail = rec['detail'][:120] + '...' \
                     if len(rec['detail']) > 120 \
                     else rec['detail']
            ax_recs.text(0.02, y - 0.10,
                detail,
                transform=ax_recs.transAxes,
                fontsize=6.5, color='#aaa',
                wrap=True)
            # Policy line
            ax_recs.text(0.02, y - 0.20,
                f"→ {rec['policy']}",
                transform=ax_recs.transAxes,
                fontsize=6.5, color='#4fc',
                style='italic')
    else:
        ax_recs.text(0.5, 0.5,
            "✅ No critical interventions needed",
            transform=ax_recs.transAxes,
            ha='center', va='center',
            fontsize=11, color='#00dd66')

    # ── FOOTER ───────────────────────────────────────────
    fig.text(0.01, 0.01,
        "Boston Albedo Mapper  |  Cubeagle Project  |  "
        "Built with Raspberry Pi + Python + OpenCV",
        fontsize=7, color='#444',
        fontfamily='monospace')

    # ── SAVE ─────────────────────────────────────────────
    safe_name = neighborhood_name.lower().replace(' ', '_')
    out_path  = os.path.join(output_dir,
                             f"{safe_name}_report.png")
    plt.savefig(out_path, dpi=150,
                bbox_inches='tight',
                facecolor='#0a0a0a')
    plt.close()
    print(f"✅ Report saved: {out_path}")
    return out_path

# %%



