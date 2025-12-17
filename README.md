# AI Connect 2025 - CSP Solver for Logic Grid Puzzles

## Team Information
- **Competition:** AI Connect 2025 - CSP Solver Challenge
- **Task:** Build a CSP solver for logic grid puzzles (Zebra puzzles)
- **Dataset:** ZebraLogicBench (~1,000 logic grid puzzles)

## Project Overview

This project implements a sophisticated Constraint Satisfaction Problem (CSP) solver designed to solve logic grid puzzles from natural language descriptions. The solver combines natural language processing, constraint parsing, and advanced CSP algorithms to achieve high accuracy and efficiency.

## Architecture

### 1. **Natural Language Processing Pipeline**
- **Puzzle Preprocessor** (`preProccesPuzzle.py`): Extracts puzzle attributes and clues from natural language text
- **Clue Classifier** (`clue_classifier.py`): Identifies constraint types using regex patterns
  - Supports 9 constraint types: IDENTITY, NEXT_TO, LEFT, RIGHT, DIRECT_LEFT, DIRECT_RIGHT, DISTANCE, POSITION_ABSOLUTE, POSITION_ABSOLUTE_NEGATIVE

### 2. **Constraint System** (`constraints.py`)
Implements 9 specialized constraint classes:
- **IdentityConstrain**: A is B (same entity)
- **NextToConstrain**: A and B are adjacent
- **LeftConstrain**: A is somewhere left of B
- **RightConstrain**: A is somewhere right of B
- **DirectLeftConstrain**: A is directly left of B
- **DirectRightConstrain**: A is directly right of B
- **DistanceConstrain**: N houses between A and B
- **PositionAbsoluteConstrain**: A is in position N
- **PositionAbsoluteNegativeConstrain**: A is not in position N

### 3. **CSP Solver** (`constraint_solver.py`)
Advanced backtracking solver with:
- **AC-3 Arc Consistency**: Preprocessing to reduce search space
- **MRV Heuristic**: Minimum Remaining Values for variable selection
- **Forward Checking**: Propagate constraints after each assignment
- **Domain Pruning**: Eliminate impossible values early
- **Backtracking**: Depth-first search with intelligent backtracking

### 4. **Solution Pipeline** (`solver.py`)
Orchestrates the complete solving process:
1. Parse puzzle text → Extract attributes and clues
2. Classify clues → Identify constraint types
3. Build constraints → Create constraint objects
4. Initialize solver → Set up CSP with domains
5. Solve → Apply AC-3, MRV, forward checking
6. Format output → Convert to required JSON structure

## File Structure

```
AIConnect/
├── run.py                    # Main execution script (CLI interface)
├── solver.py                 # High-level solver orchestration
├── constraint_solver.py      # CSP solver implementation (AC-3, MRV, backtracking)
├── constraints.py            # Constraint class definitions (9 types)
├── clue_classifier.py        # Natural language clue classifier
├── preProccesPuzzle.py      # Puzzle text preprocessor
├── CPS.ipynb                 # Development notebook with experiments
├── Gridmode-00000-of-00001.parquet  # Training data (1000 puzzles)
├── Test_100_Puzzles.parquet  # Test subset
├── README.md                 # This file
└── requirements.txt          # Python dependencies
```

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup
```bash
# Clone or download the repository
cd AIConnect

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic Usage
```bash
# Run on default dataset (Gridmode-00000-of-00001.parquet)
python run.py

# Specify custom input/output files
python run.py --input your_puzzles.parquet --output results.json

# Enable verbose logging
python run.py --verbose
```

### Command-Line Arguments
- `--input`: Path to input file (.parquet or .csv) - Default: `Gridmode-00000-of-00001.parquet`
- `--output`: Path to output JSON file - Default: `submission.json`
- `--verbose`: Enable detailed logging for debugging

### Output Format
The solver generates a JSON file with results for each puzzle:
```json
[
  {
    "id": "test-3x3-001",
    "solution": {
      "header": ["House", "Name", "Color", "Pet"],
      "rows": [
        ["1", "Bob", "orange", "turtle"],
        ["2", "Mallory", "blue", "dog"],
        ["3", "Alice", "green", "cat"]
      ]
    },
    "steps": 0,
    "status": "solved"
  }
]
```

### Using the Solver Programmatically
```python
from solver import solve_single_puzzle

puzzle_text = """
Three friends live in three houses...
Colors: orange, blue, green.
Pets: cat, turtle, dog.

## Clues:
1. Bob is in the first house.
2. The person with the orange house owns a turtle.
...
"""

result = solve_single_puzzle("puzzle-001", puzzle_text, verbose=True)
print(result)
```

## Algorithm Details

### CSP Solver Strategy
1. **Preprocessing (AC-3)**:
   - Enforce arc consistency on constraint graph
   - Reduce domain sizes before search
   - Detect early inconsistencies

2. **Search (Backtracking with MRV)**:
   - Select variable with minimum remaining values
   - Try each value in domain
   - Check all-different constraint (each value once per attribute)
   - Validate all constraints

3. **Constraint Propagation**:
   - Forward checking after each assignment
   - Unit propagation for singleton domains
   - Remove assigned values from other positions

4. **Optimization Techniques**:
   - Relevant arc selection (only constraint-related pairs)
   - Domain caching for backtracking
   - Early conflict detection

### Constraint Parsing Strategy
- **Pattern Matching**: Regex-based identification of constraint types
- **Attribute Extraction**: Intelligent matching with attribute values
- **Edge Case Handling**: Special logic for months, genres, models, etc.
- **Disambiguation**: Resolve ambiguous attribute assignments

## Performance

### Metrics
The solver is evaluated using the Composite Score:

```
Composite Score = Accuracy (%) - α × (AvgSteps / MaxAvgSteps)
where α = 10 (efficiency penalty weight)
```

### Target Performance
- **Accuracy**: 95%+ (percentage of correctly solved puzzles)
- **Efficiency**: <100 average backtracking steps for small puzzles
- **Speed**: <1 second average per puzzle

### Optimization Focus
1. **Maximize Accuracy**: Robust parsing, comprehensive constraint handling
2. **Minimize Steps**: Strong heuristics (MRV), effective propagation (AC-3)
3. **Handle Edge Cases**: Error handling, fallback strategies

## Testing

### Test on Sample Data
```bash
# Test on 100 puzzle subset
python run.py --input Test_100_Puzzles.parquet --output test_results.json
```

### Run Full Evaluation
```bash
# Process all 1000 puzzles
python run.py --input Gridmode-00000-of-00001.parquet --output submission.json
```

### Analyze Results
```python
import json
import pandas as pd

with open('submission.json') as f:
    results = json.load(f)

solved = [r for r in results if r['status'] == 'solved']
accuracy = len(solved) / len(results) * 100
avg_steps = sum(r['steps'] for r in solved) / len(solved)

print(f"Accuracy: {accuracy:.2f}%")
print(f"Average Steps: {avg_steps:.2f}")
```

## Development

### Jupyter Notebook
Development and experimentation notebook: `CPS.ipynb`
- Contains additional helper functions
- Trace generation for analysis
- Evaluation metrics computation
- Debugging tools

### Trace Generation
The solver can log decision steps for analysis:
```python
# Trace is automatically saved in solver.py
# Location: trace_{puzzle_id}.csv
```

### Adding New Constraint Types
1. Create new constraint class in `constraints.py`
2. Add pattern to `clue_classifier.py`
3. Register in `constraint_factory()` in `solver.py`

## Known Limitations

1. **Complex Nested Clues**: Some deeply nested logical statements may fail to parse
2. **Ambiguous Attributes**: Cases where attribute names overlap may need manual disambiguation
3. **Large Puzzles**: 6x6+ puzzles may take longer (but still solvable)
4. **CSV Input**: CSV files may lack proper backtick formatting required by parser

## Troubleshooting

### Common Issues

**Issue**: Puzzle fails to parse
- **Solution**: Check if attributes have backticks (e.g., \`value\`)
- **Workaround**: Use .parquet format instead of CSV

**Issue**: Solver times out
- **Solution**: Puzzle may be unsolvable or have parsing errors
- **Debug**: Run with `--verbose` flag

**Issue**: Incorrect solution
- **Solution**: Check constraint parsing in verbose mode
- **Debug**: Review trace file for decision steps

## Competition Submission

### Required Files
- `solver.py` ✅
- `run.py` ✅
- `README.md` ✅
- `requirements.txt` ✅
- `results.json` (generated by run.py)

### Submission Steps
1. Run full evaluation: `python run.py`
2. Verify results.json format
3. Package submission files
4. Upload to Kaggle competition page

## References

- **Competition**: https://www.kaggle.com/competitions/ai-connect-2025
- **Dataset**: https://huggingface.co/datasets/allenai/ZebraLogicBench
- **CSP Algorithms**: Russell & Norvig, "Artificial Intelligence: A Modern Approach"

## License

This project is developed for the AI Connect 2025 competition.

## Contact

For questions or issues, please refer to the competition forum or contact the team through the designated channels.

---

**Last Updated**: December 17, 2025
