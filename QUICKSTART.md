# Quick Start Guide - Bentonville Traffic Project

## What This Project Does

Analyzes traffic data from 5 Bentonville intersections to:
- Calculate Level of Service (LOS) ratings (A through F)
- Identify worst congestion times
- Find optimal low-traffic times
- Generate visual traffic pattern charts

## 5-Minute Setup

### 1. Install Python Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### 2. Run the Complete Analysis

```bash
# Process raw data and generate all reports
./run_complete_analysis.sh
```

Or run each step individually:

```bash
# Step 1: Calculate hourly LOS
python los_calc.py

# Step 2: Generate summaries
python worst_los_summary.py
python best_los_summary.py
python average_los_by_intersection.py

# Step 3: Create visualizations
python plot_intersection_volumes.py
```

## Understanding the Output

### Terminal Output Example

```
Hourly LOS by intersection:
INTID 1 | 2025-11-16 08:00:00 | volume=911 | LOS=C | score=3
INTID 1 | 2025-11-16 09:00:00 | volume=1100 | LOS=C | score=3
```

**Translation:** Intersection 1 had 911 vehicles during 8-9 AM with Grade C service.

### CSV Files Generated

1. **los_results.csv** - Main results with hourly LOS for each intersection
2. **worst_los_summary.csv** - Peak congestion times per intersection
3. **best_los_summary.csv** - Best times to travel
4. **average_los_by_intersection.csv** - Overall intersection rankings
5. **plots/intersections_hourly_average.png** - Visual traffic patterns

### LOS Grade Meanings

| Grade | Score | Meaning | Action Needed |
|-------|-------|---------|---------------|
| A | 1 | Excellent - Free flow | ✅ None |
| B | 2 | Good - Stable flow | ✅ None |
| C | 3 | Satisfactory | ⚠️ Monitor |
| D | 4 | Poor | ⚠️ Consider improvements |
| E | 5 | Very Poor - At capacity | 🔴 Action needed |
| F | 6 | Failing - Breakdown | 🔴 Urgent action |

## Common Use Cases

### Find Worst Traffic Times

```bash
python worst_los_summary.py --top 20
```

Look for patterns in the output to identify:
- Rush hour periods
- Weekday vs. weekend differences
- Intersections needing urgent attention

### Compare Intersections

```bash
python average_los_by_intersection.py
```

Outputs overall performance ranking to prioritize improvement projects.

### Analyze Different Data

```bash
python los_calc.py --csv "your_data_file.csv" --out results.csv
python worst_los_summary.py --source results.csv
```

## Troubleshooting

### "Module not found" error
```bash
pip install -r requirements.txt
```

### "CSV not found" error
- Ensure your CSV file is in the project directory
- Use `--csv` flag to specify path: `python los_calc.py --csv path/to/file.csv`

### Wrong data in output
- Check CSV format matches expected structure (DATE, TIME, INTID, movement columns)
- Ensure header row contains: `DATE,TIME,INTID,NBL,NBT,NBR,SBL,SBT,SBR,EBL,EBT,EBR,WBL,WBT,WBR`

## Next Steps

1. **Explore the data:** Open CSV files in Excel or Google Sheets
2. **Read detailed docs:** See `README.md` for usage details
3. **Understand the code:** See `CODEBASE_OVERVIEW.md` for architecture
4. **Customize analysis:** Modify threshold values or add new metrics

## The 5 Intersections

1. **INTID 1:** SW Regional Airport Blvd & SW I ST
2. **INTID 2:** Greenhouse & E Centerton Blvd
3. **INTID 3:** N Walton & Tiger Blvd
4. **INTID 4:** SW 14th ST & SW I ST
5. **INTID 5:** SW Regional Airport Blvd & SE Walton Blvd

## Getting Help

- Check `README.md` for detailed command-line options
- Review `CODEBASE_OVERVIEW.md` for technical details
- Examine the PDF documentation in the repository

---
**Ready to start?** Run `pip install -r requirements.txt` and then `python los_calc.py`!
