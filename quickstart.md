# Quick Start Guide - 5 Minutes to First Results

## What You Get

✅ Automated floating point error analysis of Archimedes π method  
✅ Tests multiple precision configurations (float vs double)  
✅ Tests compiler optimizations (O0-O3, fastmath)  
✅ Delta-Debug finds unstable code lines  
✅ Beautiful visualizations and comprehensive report  
✅ Everything in Docker - no complex installation  

---

## Setup (One Time - 5 minutes)

### 1. Get the Files

You need these 5 files in one directory:
- `Dockerfile`
- `archimedes_analyzer.py`
- `visualize_results.py`
- `start_analysis_container.sh`
- `build_image.sh`

### 2. Build the Container

```bash
chmod +x build_image.sh start_analysis_container.sh
./build_image.sh
```

**Wait ~2-5 minutes for build to complete.**

---

## Run Analysis (30 Minutes)

### Start Container

```bash
./start_analysis_container.sh
```

You'll see a welcome screen and be inside the container.

### Run Minimal Test

```bash
python3 archimedes_analyzer.py --minimal
```

**This takes ~30-45 minutes** and tests 3 key configurations.

### Generate Report

```bash
python3 visualize_results.py
```

**Takes ~1 minute** to create plots and report.

### Exit Container

```bash
exit
```

---

## View Results

```bash
# Main report with all answers
cat analysis_results/ANALYSIS_REPORT.md

# Or open in your editor
code analysis_results/ANALYSIS_REPORT.md

# View plots
open analysis_results/plots/*.png
```

---

## What the Report Tells You

The `ANALYSIS_REPORT.md` answers:

1. **Did unstable lines stay the same?**
   - Shows which code lines are problematic
   - Compares across configurations

2. **When did lines change?**
   - Impact of using float vs double
   - Impact of compiler optimizations
   - Impact of -ffast-math flag

3. **Which variables are most critical?**
   - Changing which variable to float has biggest impact
   - Identifies the cancellation-prone operations

4. **Best configuration for accuracy**
   - Recommended precision/compiler settings
   - Tradeoffs between speed and accuracy

---

## Analysis Modes

### Minimal Mode (~30-45 min) - Start Here!
```bash
python3 archimedes_analyzer.py --minimal
```
- 3 configs: all_double, all_float, one example
- Quick sanity check
- Perfect for first run

### Quick Mode (~3-5 hours) - Recommended
```bash
python3 archimedes_analyzer.py --quick
```
- All 15 precision configurations
- 2 optimization levels
- Good balance of coverage and time

### Full Mode (~40-50 hours) - Comprehensive
```bash
python3 archimedes_analyzer.py
```
- Complete analysis
- All configs × all optimizations × all modes
- Run overnight or over weekend

---

## Typical Workflow

```bash
# Day 1 Morning - Setup & Test (1 hour)
./build_image.sh
./start_analysis_container.sh
python3 archimedes_analyzer.py --minimal
python3 visualize_results.py
exit
cat analysis_results/ANALYSIS_REPORT.md

# Day 1 Afternoon - Full Analysis (start it running)
./start_analysis_container.sh
nohup python3 archimedes_analyzer.py --quick > analysis.log 2>&1 &
# Press Ctrl+P, Ctrl+Q to detach
# Or just let it run in terminal

# Day 2 Morning - Results
./start_analysis_container.sh  # or docker attach if still running
python3 visualize_results.py
exit

# View results
cat analysis_results/ANALYSIS_REPORT.md
open analysis_results/plots/*.png
```

---

## File Structure

```
your-working-directory/
├── Dockerfile
├── archimedes_analyzer.py
├── visualize_results.py
├── start_analysis_container.sh
├── build_image.sh
└── analysis_results/              ← Results appear here!
    ├── ANALYSIS_REPORT.md         ← Read this!
    ├── results.json
    ├── results_summary.csv
    └── plots/
        ├── precision_heatmap.png
        ├── fastmath_comparison.png
        ├── unstable_lines_frequency.png
        ├── precision_impact.png
        └── dd_mode_comparison.png
```

---

## Troubleshooting

### "Could not find archimedes.c"
The container should have it automatically. If not:
```bash
# Inside container, check available locations
find / -name "archimedes.c" 2>/dev/null
```

### Build Fails
```bash
# Rebuild from scratch
docker build --no-cache -t verificarlo-analysis .
```

### Container Won't Start
```bash
# Check Docker is running
docker ps

# Check if port is in use
docker rm -f verificarlo-analysis-session
```

### Analysis Interrupted
No problem! Results save incrementally. Just restart:
```bash
./start_analysis_container.sh
python3 visualize_results.py
```

---

## Pro Tips

💡 **Start with minimal mode** - verify everything works before long runs

💡 **Run quick mode overnight** - best balance of coverage and time

💡 **Results persist** - even if container exits, your data is safe

💡 **Monitor progress** - check `analysis_results/results.json` to see how many experiments completed

💡 **Incremental saves** - if you interrupt, you haven't lost work

---

## Next Steps

After your first successful run:

1. **Read the report** - understand what makes Archimedes unstable
2. **Check the plots** - visualize precision vs accuracy tradeoffs
3. **Explore the data** - `results_summary.csv` for custom analysis
4. **Modify parameters** - edit Python scripts to test custom configs
5. **Compare with tutorial** - see how findings match Verificarlo examples

---

## Getting Help

- **Docker README**: See `Docker_Setup_Instructions.md` for detailed docs
- **Script help**: `python3 archimedes_analyzer.py --help`
- **Verificarlo docs**: https://github.com/verificarlo/verificarlo
- **Inside container**: Read the welcome message for commands

---

## Summary

```bash
# One-time setup
./build_image.sh

# Every analysis session
./start_analysis_container.sh
python3 archimedes_analyzer.py --minimal  # or --quick or [nothing]
python3 visualize_results.py
exit

# View results
cat analysis_results/ANALYSIS_REPORT.md
```

**That's it!** You now have automated floating point error analysis. 🎉