import pandas as pd
import json
import time
import os
import argparse
from solver import solve_single_puzzle

# Default configuration matches the Kaggle/ZebraLogicBench file structure
DEFAULT_INPUT_FILE = 'Gridmode-00000-of-00001.parquet'
DEFAULT_OUTPUT_FILE = 'submission.json'


def load_data(file_path):
    """
    Loads data from CSV or Parquet file.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    print(f"Loading file: {file_path} ...")

    if file_path.endswith('.parquet'):
        return pd.read_parquet(file_path)
    elif file_path.endswith('.csv'):
        print("WARNING: CSV files often lack the specific formatting (backticks) required by the parser.")
        return pd.read_csv(file_path)
    else:
        raise ValueError("Unsupported format. Please use .csv or .parquet")


def run_solver_on_dataset(input_file, output_file, verbose=False):
    """
    Iterates through the dataset, runs the solver, and saves the results.
    """
    try:
        df = load_data(input_file)
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    # Optional: Uncomment the next line to test on only 10 puzzles
    # df = df.head(10)

    total = len(df)
    results = []
    failed_indices = []

    print(f"Starting solver for {total} puzzles...")
    start_total_time = time.time()

    for i in range(total):
        # Extract ID and Puzzle Text
        # Parquet columns are usually 'id' and 'puzzle'
        p_id = df.iloc[i]['id']
        p_text = df.iloc[i]['puzzle']

        # Progress indicator (overwrites the line)
        print(f"Processing {i + 1}/{total} (ID: {p_id})...", end="\r")

        try:
            # Call the solver
            result_string = solve_single_puzzle(p_id, p_text, verbose=verbose)

            # Parse the result string: "id | json_solution | steps"
            if result_string:
                parts = result_string.split(" | ")

                # Check if we have a valid solution part (middle part is not empty)
                if len(parts) >= 3 and parts[1].strip():
                    results.append({
                        "id": parts[0],
                        "solution": json.loads(parts[1]),
                        "steps": int(parts[2]),
                        "status": "solved"
                    })
                else:
                    # Solver returned a failure string format (empty middle part)
                    failed_indices.append(i)
            else:
                failed_indices.append(i)

        except Exception as e:
            if verbose:
                print(f"\nError at index {i} ({p_id}): {e}")
            failed_indices.append(i)

    total_time = time.time() - start_total_time
    # Calculate success metrics
    success_count = len([r for r in results if r['status'] == 'solved'])
    avg_time = total_time / total if total > 0 else 0

    print("\n" + "=" * 50)
    print(f"Execution Finished.")
    print(f"Total Puzzles: {total}")
    print(f"Solved: {success_count}")
    print(f"Failed: {len(failed_indices)}")
    print(f"Total Time: {total_time:.2f}s")
    print(f"Avg Time/Puzzle: {avg_time:.4f}s")
    print("=" * 50)

    # Save results to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4)

    print(f"Results saved to: {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Constraint Solver on ZebraLogicBench")

    parser.add_argument('--input', type=str, default=DEFAULT_INPUT_FILE,
                        help='Path to input file (.parquet or .csv)')
    parser.add_argument('--output', type=str, default=DEFAULT_OUTPUT_FILE,
                        help='Path to output JSON file')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable detailed logging')

    args = parser.parse_args()

    run_solver_on_dataset(args.input, args.output, args.verbose)