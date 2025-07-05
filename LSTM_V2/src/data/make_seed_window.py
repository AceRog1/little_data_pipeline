import os
import argparse
import numpy as np

def main(args):
    print(f"📌 Loading windows from {args.windows_dir}")

    # Carga arrays
    X_val = np.load(os.path.join(args.windows_dir, "X_val.npz"))["arr_0"]
    print(f"✅ Loaded X_val with shape {X_val.shape}")

    if args.index == -1:
        window = X_val[-1]
        print(f"✅ Using last window in validation set")
    else:
        if args.index >= X_val.shape[0]:
            raise ValueError(f"Index {args.index} out of bounds for X_val with {X_val.shape[0]} samples.")
        window = X_val[args.index]
        print(f"✅ Using window at index {args.index}")

    print(f"➡️  Window shape: {window.shape}")

    # Guardar
    out_dir = os.path.dirname(args.out_file)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    np.save(args.out_file, window)
    print(f"💾 Saved seed window to {args.out_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract a seed window (e.g., last validation window) to use for rolling forecast.")
    parser.add_argument("--windows_dir", default="data/processed/windows", help="Folder with X_val.npz")
    parser.add_argument("--index", type=int, default=-1, help="Index of window to use (-1 for last)")
    parser.add_argument("--out_file", default="my_start_window.npy", help="Output .npy file path")
    args = parser.parse_args()
    main(args)
