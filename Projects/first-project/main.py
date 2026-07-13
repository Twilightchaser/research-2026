"""Minimal entry point for the first Python project."""

import matplotlib
import numpy as np
import pandas as pd


def main() -> None:
    """Print the active scientific Python package versions."""
    print("Python environment is ready.")
    print(f"NumPy: {np.__version__}")
    print(f"pandas: {pd.__version__}")
    print(f"Matplotlib: {matplotlib.__version__}")


if __name__ == "__main__":
    main()
