import numpy as np
import pandas as pd
import argparse
import os

def main(args):
    y_true = np.load(os.path.join(args.run_folder, "y_val.npy"))
    y_pred = np.load(os.path.join(args.run_folder, "y_pred.npy"))

    horizon = y_true.shape[1]

    columns = []
    data = []
    for i in range(horizon):
        columns += [f"Real_t+{i+1}", f"Pred_t+{i+1}"]

    for true_row, pred_row in zip(y_true, y_pred):
        row = []
        for t, p in zip(true_row, pred_row):
            row += [t, p]
        data.append(row)

    df = pd.DataFrame(data, columns=columns)
    print(df.head(20))

    if args.out_csv:
        df.to_csv(args.out_csv, index=False)
        print(f"✅ Saved table to {args.out_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run_folder", required=True, help="Folder with y_val.npy and y_pred.npy")
    parser.add_argument("--out_csv", help="Optional output CSV path")
    args = parser.parse_args()
    main(args)
