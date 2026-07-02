"""
Download AASIST model weights for voice liveness detection.

Run this script once to download the AASIST anti-spoofing model:
    python scripts/download_aasist_weights.py

The weights will be saved to pretrained_models/aasist/
"""

import os
import sys
import urllib.request
from pathlib import Path

# Add backend root to path
backend_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_root))

# AASIST GitHub repo
AASIST_REPO = "https://raw.githubusercontent.com/clovaai/aasist/main"

# Alternative: Use a working HuggingFace mirror
HF_MIRROR = "DietaryMan/aasist"


def download_file(url: str, dest: Path, show_progress: bool = True):
    """Download a file from URL to destination."""
    if show_progress:
        print(f"  Downloading: {url}")
    try:
        urllib.request.urlretrieve(url, dest)
        if dest.exists():
            size = dest.stat().st_size / (1024 * 1024)  # MB
            if show_progress:
                print(f"  Saved: {dest} ({size:.2f} MB)")
            return True
    except Exception as e:
        if show_progress:
            print(f"  Error: {e}")
        raise
    return False


def download_aasist_weights():
    """Download AASIST model weights and code."""
    aasist_dir = backend_root / "pretrained_models" / "aasist"
    aasist_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading AASIST to {aasist_dir}...")
    print("=" * 60)

    # Download model code - simplified single-file approach
    print("\n1. Downloading model architecture code...")
    models_dir = aasist_dir / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    # Create a minimal __init__.py
    (models_dir / "__init__.py").write_text("")

    # Download main AASIST model
    aasist_url = f"{AASIST_REPO}/model/AASIST.py"
    dest = models_dir / "AASIST.py"
    try:
        download_file(aasist_url, dest)
    except Exception:
        # Try alternative path
        aasist_url = f"{AASIST_REPO}/models/AASIST.py"
        try:
            download_file(aasist_url, dest)
        except Exception:
            print("  Could not download AASIST.py - will create stub")
            # Create a stub that will fail gracefully
            dest.write_text("# Stub - download full AASIST from https://github.com/clovaai/aasist\n")

    # Download config
    print("\n2. Downloading config...")
    config_url = f"{AASIST_REPO}/config/AASIST.conf"
    config_dest = aasist_dir / "config.yaml"
    try:
        download_file(config_url, config_dest)
    except Exception:
        print("  Config download failed - will use default settings")
        config_dest.write_text("# Default AASIST config\n")

    # Download weights from HuggingFace mirror
    print("\n3. Downloading pretrained weights...")
    weights_dest = aasist_dir / "weights.pt"

    if weights_dest.exists() and weights_dest.stat().st_size > 0:
        print(f"  Weights already exist: {weights_dest}")
    else:
        try:
            from huggingface_hub import hf_hub_download

            print("    Trying HuggingFace mirror...")
            weights_path = hf_hub_download(
                repo_id=HF_MIRROR,
                filename="aasist.pth",
                local_dir=str(aasist_dir),
            )
            # Rename to expected name
            Path(weights_path).rename(weights_dest)
            print(f"  Saved: {weights_dest}")
        except Exception as e:
            print(f"    HuggingFace download failed: {e}")
            print("\n    Manual download options:")
            print("    1. Git clone the full repo:")
            print(f"       git clone https://github.com/clovaai/aasist.git")
            print("    2. Or download weights from HuggingFace:")
            print(f"       https://huggingface.co/{HF_MIRROR}")

    print("\n" + "=" * 60)
    print("Setup complete!")
    print(f"\nModel location: {aasist_dir}")

    # List downloaded files
    print("\nDownloaded files:")
    for f in sorted(aasist_dir.rglob("*")):
        if f.is_file():
            size = f.stat().st_size / 1024
            print(f"  {f.relative_to(aasist_dir)} ({size:.1f} KB)")

    print("\nNote: For full functionality, manually clone the AASIST repo:")
    print("  git clone https://github.com/clovaai/aasist.git pretrained_models/aasist_full")

    print("\nTo verify the installation, run:")
    print(f"  python scripts/test_aasist.py")


if __name__ == "__main__":
    try:
        download_aasist_weights()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)