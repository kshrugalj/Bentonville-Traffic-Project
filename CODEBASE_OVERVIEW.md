# Bentonville Traffic Project - Codebase Overview

## Project Summary

This project analyzes traffic data from 5 key intersections in Bentonville, Arkansas to compute and visualize Level of Service (LOS) metrics. The system processes 15-minute turning movement counts to generate hourly LOS ratings, identify peak congestion times, and provide data-driven insights for traffic optimization.

## Architecture Overview

### Data Flow
```
Raw CSV Data (15-min intervals)
    ↓
los_calc.py (Hourly LOS Computation)
    ↓
los_results.csv
    ↓
    ├─→ worst_los_summary.py → worst_los_summary.csv
    ├─→ best_los_summary.py → best_los_summary.csv
    ├─→ average_los_by_intersection.py → average_los_by_intersection.csv
    └─→ plot_intersection_volumes.py → plots/intersections_hourly_average.png
```

## Core Components

### 1. `los_calc.py` - LOS Calculation Engine
**Purpose:** Main data processing script that converts raw 15-minute traffic counts into hourly Level of Service ratings.

**Key Features:**
- Robust CSV parsing with header detection
- Excel-style TIME value normalization (e.g., `="0000"` → `00:00`)
- Handles trailing commas and unnamed columns
- Processes 12 movement directions per intersection (NBL, NBT, NBR, SBL, SBT, SBR, EBL, EBT, EBR, WBL, WBT, WBR)

**LOS Thresholds (15-minute total volume):**
- A: ≤ 100 vehicles (Free flow)
- B: ≤ 200 vehicles (Stable flow)
- C: ≤ 350 vehicles (Stable, approaching unstable)
- D: ≤ 500 vehicles (Approaching unstable)
- E: ≤ 700 vehicles (Unstable, at capacity)
- F: > 700 vehicles (Forced/breakdown flow)

**Algorithm:**
1. Parse raw CSV with 15-minute intervals
2. Compute total volume per interval (sum of 12 movements)
3. Assign LOS grade and score (A=1 to F=6) for each 15-min interval
4. Aggregate to hourly: average the four 15-min scores, round to nearest integer
5. Map rounded score back to LOS letter grade

**Outputs:**
- Terminal: Formatted table of hourly LOS per intersection
- CSV: `los_results.csv` with columns: INTID, hour, total_volume, los_score, LOS

### 2. `worst_los_summary.py` - Congestion Analysis
**Purpose:** Identifies the worst (most congested) hours for each intersection.

**Features:**
- Finds maximum LOS score per intersection
- Lists all hours achieving the worst score
- Displays unique time-of-day patterns (HH:MM) without date repetition
- Shows top-N worst hours across all intersections

**Outputs:**
- Terminal: Per-intersection worst LOS with time ranges
- CSV: `worst_los_summary.csv` with worst score, LOS letter, and timestamp list

### 3. `best_los_summary.py` - Optimal Time Analysis
**Purpose:** Identifies the best (least congested) hours for each intersection.

**Features:**
- Finds minimum LOS score per intersection
- Lists all hours achieving the best score
- Extracts unique time-of-day patterns
- Shows top-N best hours globally

**Outputs:**
- Terminal: Per-intersection best LOS with time ranges
- CSV: `best_los_summary.csv` with best score, LOS letter, and timestamp list

### 4. `average_los_by_intersection.py` - Aggregate Performance
**Purpose:** Computes overall performance metrics for each intersection.

**Features:**
- Averages hourly LOS scores across entire dataset (no rounding)
- Uses stricter banding for letter grade assignment:
  - A: < 1.2
  - B: < 2.0
  - C: < 2.8
  - D: < 3.6
  - E: < 4.4
  - F: ≥ 4.4

**Outputs:**
- Terminal: Average hourly score and LOS per intersection
- CSV: `average_los_by_intersection.csv`

### 5. `plot_intersection_volumes.py` - Visualization
**Purpose:** Generates visual representation of traffic patterns.

**Features:**
- Creates single multi-line chart showing all 5 intersections
- X-axis: Hour of day (0-23)
- Y-axis: Average total volume
- Color-coded lines per intersection
- Human-friendly intersection names in legend

**Intersection Mapping:**
1. SW Regional Airport Blvd & SW I ST
2. Greenhouse & E Centerton Blvd
3. N Walton & Tiger Blvd
4. SW 14th ST & SW I ST
5. SW Regional Airport Blvd & SE Walton Blvd

**Outputs:**
- PNG file: `plots/intersections_hourly_average.png`

## Input Data Format

### CSV Structure
- **Header Row:** `DATE,TIME,INTID,NBL,NBT,NBR,SBL,SBT,SBR,EBL,EBT,EBR,WBL,WBT,WBR`
- **Pre-header Lines:** First 2 lines are metadata (e.g., "Turning Movement Count", "15 Minute Counts")
- **Trailing Commas:** Allowed and automatically removed

### Movement Columns Explained
- **N/S/E/W:** North, South, East, West approach
- **L/T/R:** Left turn, Through movement, Right turn

Example: `NBL` = Northbound Left turn

### Time Format Handling
- Excel-style values: `="0000"` → `00:00`
- Standard formats: `HH:MM` or `HH:MM:SS`
- Automatic normalization and padding

## Dependencies

Based on the imports in the scripts, the project requires:
- **Python 3.x**
- **pandas** - Data manipulation and CSV handling
- **matplotlib** - Chart generation
- **argparse** - Command-line interface (built-in)

Expected `requirements.txt`:
```
pandas>=1.3.0
matplotlib>=3.3.0
```

## Usage Workflow

### Complete Analysis Pipeline

```bash
# 1. Setup (first time only)
python3 -m venv .venv
source .venv/bin/activate
pip install pandas matplotlib

# 2. Compute hourly LOS from raw data
python los_calc.py --csv "VehicleVolume_1Wal_2Hwy_4Hwy_11162025_11222025.csv" --out los_results.csv

# 3. Generate summaries
python worst_los_summary.py --source los_results.csv --out worst_los_summary.csv --top 10
python best_los_summary.py --source los_results.csv --out best_los_summary.csv --top 10
python average_los_by_intersection.py --source los_results.csv --out average_los_by_intersection.csv

# 4. Create visualizations
python plot_intersection_volumes.py --csv los_results.csv --outdir plots
```

## Key Design Patterns

### 1. Resilient Parsing
- Multiple datetime format attempts with fallbacks
- Safe type coercion with `errors='coerce'`
- Header detection via content scanning (not line numbers)
- Unnamed column removal for trailing commas

### 2. Data Validation
- Required column checking with meaningful error messages
- NaN handling and numeric coercion
- Type safety throughout the pipeline

### 3. Modular Architecture
- Each script is independent and can be run separately
- Common intermediate format (`los_results.csv`) enables extensibility
- Clear separation of concerns (compute, summarize, visualize)

### 4. User-Friendly Output
- Formatted terminal tables for quick insights
- CSV files for further analysis
- Meaningful column names and value formatting

## Output Interpretation

### LOS Grades Meaning
- **A (1):** Excellent - Free-flowing traffic, no delays
- **B (2):** Good - Stable flow, minimal delays
- **C (3):** Satisfactory - Stable but approaching capacity
- **D (4):** Poor - Approaching unstable conditions
- **E (5):** Very Poor - At capacity, significant delays
- **F (6):** Failing - Breakdown conditions, severe congestion

### Sample Insights from Data

From `average_los_by_intersection.csv`:
- INTID 1 (SW Regional Airport & SW I): Avg 2.51 → Grade C (Satisfactory)
- INTID 2 (Greenhouse & E Centerton): Avg 4.07 → Grade E (Very Poor)
- INTID 3 (N Walton & Tiger): Avg 4.01 → Grade E (Very Poor)
- INTID 4 (SW 14th & SW I): Avg 4.16 → Grade E (Very Poor)
- INTID 5 (SW Regional Airport & SE Walton): Avg 2.93 → Grade D (Poor)

**Conclusion:** Intersections 2, 3, and 4 require immediate attention for traffic optimization.

## Code Quality Features

### Error Handling
- File existence checks before processing
- Meaningful error messages for missing columns
- Graceful handling of malformed data

### Documentation
- Comprehensive README.md with usage examples
- Inline comments for complex logic
- Type hints in function signatures
- Docstrings for major functions

### Extensibility
- Parameterized thresholds (can be made CLI arguments)
- Pluggable aggregation methods (mean vs. max)
- Support for additional intersections via INTID

## File Structure

```
Bentonville-Traffic-Project/
├── README.md                          # User documentation
├── CODEBASE_OVERVIEW.md              # This file - developer documentation
├── VehicleVolume_*.csv               # Input data (15-min counts)
├── los_calc.py                       # Core LOS computation
├── worst_los_summary.py              # Worst times analysis
├── best_los_summary.py               # Best times analysis
├── average_los_by_intersection.py    # Average LOS per intersection
├── plot_intersection_volumes.py      # Visualization generation
├── los_results.csv                   # Hourly LOS (intermediate output)
├── worst_los_summary.csv             # Worst times (final output)
├── best_los_summary.csv              # Best times (final output)
├── average_los_by_intersection.csv   # Averages (final output)
├── hourly_los_by_intersection.csv    # Legacy output
├── plots/                            # Visualization outputs
│   ├── intersections_hourly_average.png
│   └── intersection_*_hourly_volume.png
├── Financial Overview_ ACE.pdf       # Project documentation
└── Akash S., Jayshinav V., Kshrugal J., Abdullah T. - Traffic Control Optimization.pdf
```

## Potential Enhancements

### Short-term
1. Create `requirements.txt` for easy dependency installation
2. Add command-line flags for LOS threshold customization
3. Include data validation summary in outputs
4. Add progress indicators for long-running operations

### Medium-term
1. Implement caching for intermediate results
2. Add support for multiple input files (batch processing)
3. Create interactive HTML dashboards
4. Add statistical significance testing for comparisons

### Long-term
1. Real-time data ingestion and processing
2. Predictive modeling for future congestion
3. Integration with traffic signal control systems
4. Machine learning for pattern detection

## Testing Recommendations

Since no test infrastructure exists currently, consider adding:

1. **Unit Tests**
   - LOS threshold calculations
   - Time normalization logic
   - Header detection algorithm

2. **Integration Tests**
   - End-to-end pipeline with sample data
   - CSV output format validation
   - Chart generation verification

3. **Data Validation Tests**
   - Malformed CSV handling
   - Edge cases (empty files, missing columns)
   - Date/time parsing edge cases

## Contributing Guidelines

When modifying this codebase:

1. **Maintain backward compatibility** with existing CSV formats
2. **Test with actual data** before committing changes
3. **Update documentation** (README.md and this file) for new features
4. **Follow existing code style** (spacing, naming conventions)
5. **Add meaningful commit messages** describing the "why" not just "what"

## Performance Considerations

- **Dataset Size:** Current implementation handles ~1 week of data efficiently
- **Memory Usage:** Entire dataset loaded into memory (acceptable for current scale)
- **Processing Time:** Sub-second for current data volume
- **Scalability:** For months/years of data, consider chunked processing

## Known Limitations

1. **Single CSV Input:** Manual workflow for combining multiple data files
2. **No Data Quality Metrics:** Missing validation summary (e.g., % of malformed rows)
3. **Fixed Thresholds:** LOS thresholds are hardcoded (could be parameterized)
4. **Limited Error Recovery:** Some edge cases may cause script termination

## Contact & Maintenance

This project was developed by:
- Akash S.
- Jayshinav V.
- Kshrugal J.
- Abdullah T.

For questions or issues, refer to the documentation PDFs or contact the project team.

---
**Last Updated:** December 2025  
**Version:** 1.0  
**Status:** Production Ready
