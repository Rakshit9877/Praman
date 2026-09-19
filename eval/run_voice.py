import argparse
import os
import sys

def main():
    parser = argparse.ArgumentParser(description="Evaluate voice claim extraction against ground truth.")
    parser.add_argument("--data", required=True, help="Path to voice audio directory")
    parser.add_argument("--gt", required=True, help="Path to ground truth JSON")
    parser.add_argument("--out", required=True, help="Output directory for eval results")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.gt):
        print(f"Ground truth file {args.gt} not found. Waiting for Namha to provide it.", file=sys.stderr)
        return

    print("Running voice eval... (Stub)")
    
    # Actual implementation would be here, but we wait for data as instructed.

if __name__ == "__main__":
    main()
