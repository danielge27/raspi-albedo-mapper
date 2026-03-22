









# capture.py — updated for Pi 4 with rpicam stack

from picamera2 import Picamera2
import time
import os
import sys
from datetime import datetime

def capture_photo(location_name="location",
                  resolution=(3280, 2464)):
    """
    Capture a photo using Pi Camera (rpicam stack)
    Works on Pi 4 with newer Raspberry Pi OS
    """

    print(f"📷 Initializing Pi Camera...")

    # Initialize camera
    cam = Picamera2()

    # Configure for high quality still photo
    config = cam.create_still_configuration(
        main={
            "size": resolution,
            "format": "RGB888"     # ← important for OpenCV
        },
        display=None               # no preview needed
    )
    cam.configure(config)

    # Start and warm up
    cam.start()
    print(f"   Warming up (3 seconds)...")
    time.sleep(3)                  # Pi 4 needs a bit longer

    # Build filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = location_name.lower().replace(" ", "_")
    filename  = f"{safe_name}_{timestamp}.jpg"
    filepath  = os.path.join(
        os.path.expanduser("~/albedo_mapper/photos"),
        filename
    )

    # Take the photo
    print(f"   Capturing image...")
    cam.capture_file(filepath)
    cam.stop()
    cam.close()

    print(f"✅ Photo saved!")
    print(f"   Path:       {filepath}")
    print(f"   Resolution: {resolution[0]}x{resolution[1]}")

    return filepath


def show_preview(seconds=5):
    """
    Show live preview so you can aim the camera
    Uses rpicam-hello under the hood
    """
    print(f"📹 Live preview for {seconds} seconds...")
    print(f"   Aim your camera now!")
    os.system(f"rpicam-hello -t {seconds*1000}")
    print(f"   Preview done.")


if __name__ == "__main__":

    # Get location name from command line or prompt
    if len(sys.argv) > 1:
        location = " ".join(sys.argv[1:])
    else:
        location = input(
            "Enter location name (e.g. Roxbury Boston): "
        ).strip()

    if not location:
        location = "unknown_location"

    print(f"\n🛰️  Boston Albedo Mapper — Pi 4 Camera Capture")
    print(f"   Location: {location}")
    print("─" * 48)

    # Ask about preview
    preview = input(
        "\nShow live preview to aim camera? (y/n): "
    ).lower().strip()

    if preview == 'y':
        secs = input("How many seconds? (default 5): ").strip()
        secs = int(secs) if secs.isdigit() else 5
        show_preview(seconds=secs)

    # Capture
    print()
    photo_path = capture_photo(location_name=location)

    print(f"\n📂 Next step:")
    print(f"   python3 run_audit.py")


