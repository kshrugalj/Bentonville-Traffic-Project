#!/bin/bash
# Bentonville Traffic Project - Complete Analysis Pipeline
# This script runs all analysis steps in sequence
# Usage: ./run_complete_analysis.sh [CSV_FILE]

set -e  # Exit on any error

echo "=================================="
echo "Bentonville Traffic Analysis"
echo "=================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Accept CSV file as argument or use default
CSV_FILE="${1:-VehicleVolume_1Wal_2Hwy_4Hwy_11162025_11222025.csv}"

# Check if CSV exists
if [ ! -f "$CSV_FILE" ]; then
    echo "Error: Input CSV file not found: $CSV_FILE"
    echo "Usage: ./run_complete_analysis.sh [CSV_FILE]"
    echo "Please ensure the data file is in the current directory."
    exit 1
fi

echo "Using CSV file: $CSV_FILE"
echo ""

# Step 1: Calculate hourly LOS
echo -e "${BLUE}Step 1/5: Computing hourly Level of Service...${NC}"
python los_calc.py --csv "$CSV_FILE" --out los_results.csv
echo -e "${GREEN}✓ Hourly LOS calculated${NC}"
echo ""

# Step 2: Generate worst LOS summary
echo -e "${BLUE}Step 2/5: Analyzing worst congestion times...${NC}"
python worst_los_summary.py --source los_results.csv --out worst_los_summary.csv --top 10
echo -e "${GREEN}✓ Worst LOS summary generated${NC}"
echo ""

# Step 3: Generate best LOS summary
echo -e "${BLUE}Step 3/5: Identifying optimal traffic times...${NC}"
python best_los_summary.py --source los_results.csv --out best_los_summary.csv --top 10
echo -e "${GREEN}✓ Best LOS summary generated${NC}"
echo ""

# Step 4: Calculate averages by intersection
echo -e "${BLUE}Step 4/5: Computing intersection averages...${NC}"
python average_los_by_intersection.py --source los_results.csv --out average_los_by_intersection.csv
echo -e "${GREEN}✓ Average LOS by intersection calculated${NC}"
echo ""

# Step 5: Generate visualizations
echo -e "${BLUE}Step 5/5: Creating traffic pattern charts...${NC}"
python plot_intersection_volumes.py --csv los_results.csv --outdir plots
echo -e "${GREEN}✓ Visualizations saved to plots/${NC}"
echo ""

echo "=================================="
echo -e "${GREEN}Analysis Complete!${NC}"
echo "=================================="
echo ""
echo "Output files generated:"
echo "  - los_results.csv (hourly LOS data)"
echo "  - worst_los_summary.csv (peak congestion times)"
echo "  - best_los_summary.csv (optimal travel times)"
echo "  - average_los_by_intersection.csv (intersection rankings)"
echo "  - plots/intersections_hourly_average.png (traffic patterns chart)"
echo ""
echo "Next steps:"
echo "  1. Review the terminal output above for key insights"
echo "  2. Open the CSV files in Excel/Sheets for detailed analysis"
echo "  3. View plots/intersections_hourly_average.png for visual patterns"
echo ""
