# System Architecture Diagram - Bentonville Traffic Project

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          INPUT DATA LAYER                                   │
│                                                                             │
│  VehicleVolume_1Wal_2Hwy_4Hwy_11162025_11222025.csv                       │
│  ┌──────────────────────────────────────────────────────────────┐         │
│  │  15-Minute Turning Movement Counts                            │         │
│  │  - DATE: 11/16/2025, 11/17/2025, ...                         │         │
│  │  - TIME: ="0000", ="0015", ="0030", ...                       │         │
│  │  - INTID: 1, 2, 3, 4, 5                                       │         │
│  │  - Movement Counts: NBL, NBT, NBR, SBL, SBT, SBR,            │         │
│  │                     EBL, EBT, EBR, WBL, WBT, WBR             │         │
│  └──────────────────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ CSV Input
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PROCESSING LAYER                                      │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────┐            │
│  │  los_calc.py - Core LOS Computation Engine                 │            │
│  │                                                             │            │
│  │  Input Processing:                                         │            │
│  │  ├─ Header Detection (skip metadata lines)                 │            │
│  │  ├─ TIME Normalization (="0000" → 00:00)                   │            │
│  │  ├─ DateTime Combination (DATE + TIME)                     │            │
│  │  └─ Movement Column Validation                             │            │
│  │                                                             │            │
│  │  15-Minute LOS Calculation:                                │            │
│  │  ├─ Sum 12 movement columns = total_volume                 │            │
│  │  ├─ Apply Thresholds:                                      │            │
│  │  │   • A: ≤100  • B: ≤200  • C: ≤350                       │            │
│  │  │   • D: ≤500  • E: ≤700  • F: >700                       │            │
│  │  └─ Map to Score: A=1, B=2, C=3, D=4, E=5, F=6            │            │
│  │                                                             │            │
│  │  Hourly Aggregation:                                       │            │
│  │  ├─ Group by INTID and hour                                │            │
│  │  ├─ Average the four 15-min scores                         │            │
│  │  ├─ Round to nearest integer                               │            │
│  │  └─ Map back to LOS letter                                 │            │
│  └────────────────────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Hourly LOS Data
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    INTERMEDIATE DATA STORAGE                                │
│                                                                             │
│  los_results.csv                                                            │
│  ┌──────────────────────────────────────────────────────────────┐         │
│  │  INTID | hour               | total_volume | los_score | LOS │         │
│  │  ──────┼────────────────────┼──────────────┼───────────┼──── │         │
│  │  1     | 2025-11-16 08:00:00| 911         | 3         | C   │         │
│  │  1     | 2025-11-16 09:00:00| 1100        | 3         | C   │         │
│  │  2     | 2025-11-16 11:00:00| 2850        | 6         | F   │         │
│  │  ...   | ...                | ...         | ...       | ... │         │
│  └──────────────────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┬────────────────┐
                    ▼               ▼               ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌───────────────────┐
│ ANALYSIS #1  │ │ ANALYSIS #2  │ │ ANALYSIS #3  │ │  VISUALIZATION    │
│              │ │              │ │              │ │                   │
│ worst_los_   │ │ best_los_    │ │ average_los_ │ │ plot_intersection_│
│ summary.py   │ │ summary.py   │ │ by_inter-    │ │ volumes.py        │
│              │ │              │ │ section.py   │ │                   │
│ Finds:       │ │ Finds:       │ │ Computes:    │ │ Creates:          │
│ • Max score  │ │ • Min score  │ │ • Mean score │ │ • Multi-line chart│
│ • Worst hours│ │ • Best hours │ │ • Stricter   │ │ • Hour-of-day x   │
│ • Top-N worst│ │ • Top-N best │ │   grading    │ │ • Avg volume y    │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └────────┬──────────┘
       │                │                │                   │
       ▼                ▼                ▼                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          OUTPUT LAYER                                       │
│                                                                             │
│  Reports (CSV):                     Visualizations (PNG):                  │
│  ┌─────────────────────────────┐   ┌──────────────────────────────────┐   │
│  │ worst_los_summary.csv       │   │ plots/                           │   │
│  │ ├─ Peak congestion times    │   │ └─ intersections_hourly_         │   │
│  │ └─ Per-intersection worst   │   │    average.png                   │   │
│  │                              │   │    ┌──────────────────────┐     │   │
│  │ best_los_summary.csv        │   │    │ ▲ Volume              │     │   │
│  │ ├─ Optimal travel times     │   │    │ │                      │     │   │
│  │ └─ Per-intersection best    │   │    │ │  ╱╲                  │     │   │
│  │                              │   │    │ │ ╱  ╲    ╱─╲          │     │   │
│  │ average_los_by_              │   │    │ │╱    ╲╲ ╱   ╲         │     │   │
│  │ intersection.csv             │   │    │ └──────────────────►  │     │   │
│  │ ├─ Overall intersection     │   │    │      Hour of Day       │     │   │
│  │ │  performance rankings     │   │    │  Legend: 5 Intersections│     │   │
│  │ └─ Avg hourly scores        │   │    └──────────────────────┘     │   │
│  └─────────────────────────────┘   └──────────────────────────────────┘   │
│                                                                             │
│  Terminal Output:                                                           │
│  ┌──────────────────────────────────────────────────────────────┐         │
│  │ Formatted tables with:                                        │         │
│  │ • Hourly LOS per intersection                                 │         │
│  │ • Worst/Best summaries with unique time patterns              │         │
│  │ • Average scores and letter grades                            │         │
│  └──────────────────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        DATA FLOW SUMMARY                                    │
│                                                                             │
│  Raw CSV (15-min) → los_calc.py → Hourly CSV → Analysis Scripts → Reports  │
│                                                                             │
│  Time Complexity: O(n) where n = number of 15-min intervals                │
│  Space Complexity: O(n) - entire dataset in memory                         │
│                                                                             │
│  Typical Processing Time: < 1 second for 1 week of data                    │
│  Typical Memory Usage: < 100 MB for standard datasets                      │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    INTERSECTION MAPPING                                     │
│                                                                             │
│  INTID 1: SW Regional Airport Blvd & SW I ST                               │
│  INTID 2: Greenhouse & E Centerton Blvd                                    │
│  INTID 3: N Walton & Tiger Blvd                                            │
│  INTID 4: SW 14th ST & SW I ST                                             │
│  INTID 5: SW Regional Airport Blvd & SE Walton Blvd                        │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    DEPENDENCIES                                             │
│                                                                             │
│  Python Standard Library:                                                  │
│  • argparse - Command-line interface                                       │
│  • os - File system operations                                             │
│  • sys - System functions                                                  │
│  • warnings - Warning control                                              │
│  • typing - Type hints                                                     │
│                                                                             │
│  External Libraries:                                                        │
│  • pandas>=1.3.0 - Data manipulation                                       │
│  • matplotlib>=3.3.0 - Chart generation                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Key Design Principles

1. **Single Responsibility**: Each script has one clear purpose
2. **Data Immutability**: Original CSV is never modified
3. **Fail-Fast**: Invalid data triggers immediate, clear errors
4. **Idempotency**: Running scripts multiple times produces same results
5. **Separation of Concerns**: Computation → Storage → Analysis → Visualization

## Extension Points

- **New Metrics**: Add scripts that read from `los_results.csv`
- **Custom Thresholds**: Modify `LOS_THRESHOLDS` in `los_calc.py`
- **Additional Visualizations**: Use `los_results.csv` as input
- **Different Aggregations**: Change from mean to max/min in groupby operations
