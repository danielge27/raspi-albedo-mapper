# %%


# %%
# surface_detector.py
# Detects and classifies urban surfaces by albedo value

import cv2
import numpy as np


# %%


# %%

# ── SURFACE DEFINITIONS ────────────────────────────────────
# Each surface has:
#   hsv_lower/upper : color range in HSV space
#   albedo          : reflectivity 0.0 to 1.0
#                     (0 = absorbs all, 1 = reflects all)
#   heat_risk       : how much heat it generates
#   color           : BGR color for contour drawing
#   label           : display name

SURFACES = {
    "dark_roof": {
        "hsv_lower":  np.array([0,   0,   0  ]),
        "hsv_upper":  np.array([180, 50,  60 ]),
        "albedo":     0.05,
        "heat_risk":  "CRITICAL",
        "color":      (0,   0,   255),  # Red
        "label":      "Dark Tar Roof",
        "priority":   1
    },
    "asphalt_road": {
        "hsv_lower":  np.array([0,   0,   40 ]),
        "hsv_upper":  np.array([180, 30,  90 ]),
        "albedo":     0.10,
        "heat_risk":  "HIGH",
        "color":      (0,   69,  255),  # Orange-Red
        "label":      "Asphalt / Road",
        "priority":   2
    },
    "concrete": {
        "hsv_lower":  np.array([0,   0,   90 ]),
        "hsv_upper":  np.array([180, 30,  170]),
        "albedo":     0.25,
        "heat_risk":  "MEDIUM",
        "color":      (0,   165, 255),  # Orange
        "label":      "Concrete / Sidewalk",
        "priority":   3
    },
    "bright_roof": {
        "hsv_lower":  np.array([0,   0,   170]),
        "hsv_upper":  np.array([180, 30,  255]),
        "albedo":     0.65,
        "heat_risk":  "LOW",
        "color":      (255, 255, 0  ),  # Cyan
        "label":      "Bright / White Roof",
        "priority":   4
    },
    "vegetation": {
        "hsv_lower":  np.array([35,  40,  40 ]),
        "hsv_upper":  np.array([90,  255, 200]),
        "albedo":     0.20,
        "heat_risk":  "BENEFICIAL",
        "color":      (0,   200, 0  ),  # Green
        "label":      "Trees / Vegetation",
        "priority":   5
    },
    "water": {
        "hsv_lower":  np.array([90,  50,  50 ]),
        "hsv_upper":  np.array([130, 255, 255]),
        "albedo":     0.06,
        "heat_risk":  "COOLING",
        "color":      (255, 150, 0  ),  # Blue
        "label":      "Water Body",
        "priority":   6
    }
}


# %%


# %%


# %%


# %%


# %%


# %%


def detect_surfaces(image_path):
    """
    Main function: detect all surfaces in an image
    Returns the original image, annotated image,
    and coverage statistics for each surface type
    """
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Cannot load: {image_path}")

    # Make a copy for annotation
    annotated = image.copy()

    # Convert to HSV for color detection
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    total_pixels = image.shape[0] * image.shape[1]
    results = {}

    for surface_name, surface in SURFACES.items():
        # Create mask for this surface type
        mask = cv2.inRange(
            hsv,
            surface["hsv_lower"],
            surface["hsv_upper"]
        )

        # Clean up noise with morphological operations
        kernel = np.ones((5,5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel)

        # Find contours around detected zones
        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        # Filter out tiny noise contours (< 200 pixels)
        significant = [c for c in contours
                      if cv2.contourArea(c) > 200]

        # Draw filled semi-transparent overlay
        overlay = annotated.copy()
        cv2.drawContours(overlay, significant, -1,
                        surface["color"], -1)
        cv2.addWeighted(overlay, 0.35, annotated,
                       0.65, 0, annotated)

        # Draw contour borders (solid lines)
        cv2.drawContours(annotated, significant, -1,
                        surface["color"], 2)

        # Calculate coverage percentage
        pixel_count = cv2.countNonZero(mask)
        coverage_pct = round((pixel_count / total_pixels) * 100, 1)

        results[surface_name] = {
            "coverage_pct": coverage_pct,
            "pixel_count":  pixel_count,
            "contour_count": len(significant),
            "albedo":        surface["albedo"],
            "heat_risk":     surface["heat_risk"],
            "label":         surface["label"],
            "color":         surface["color"],
            "priority":      surface["priority"]
        }

    return image, annotated, results, total_pixels

# %%


# %%



