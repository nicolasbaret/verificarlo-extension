# Complete Archimedes Analysis Automation - File Summary

## 📦 All Files You Need

Here's everything I've created for you. Copy each file to your working directory.

---

## File List (7 files total)

### 1. **Dockerfile** ⭐
- Extends `verificarlo/verificarlo:latest`
- Installs Python dependencies
- Adds automation scripts
- **Status**: Ready to use

### 2. **archimedes_analyzer.py** ⭐
- Main automation script
- Handles precision variations, compiler flags, Delta-Debug
- Three modes: full, quick, minimal
- Auto-detects archimedes.c location
- Saves results to `/workdir/analysis_results`
- **Status**: Container-compatible, ready to use

### 3. **visualize_results.py** ⭐
- Generates 5 comprehensive plots
- Creates markdown report answering all research questions
- Exports CSV for further analysis
- **Status**: Container-compatible, ready to use

### 4. **start_analysis_container.sh** ⭐
- User-friendly launcher script
- Mounts current directory to `/workdir`
- Starts interactive bash session
- **Status**: Ready to use (just chmod +x)

### 5. **build_image.sh**
- Builds Docker image with validation
- Checks for required files
- Shows progress and summary
- **Status**: Ready to use (just chmod +x)

### 6. **QUICKSTART.md**
- 5-minute quick start guide
- Common workflows
- Troubleshooting tips
- **Status**: Documentation, ready to read

### 7. **Docker_Setup_Instructions.md** (the detailed README)
- Complete documentation
- All usage examples
- Advanced configurations
- Troubleshooting section
- **Status**: Documentation, ready to read

---

## Quick Setup Checklist

```bash
# 1. Create a new directory
mkdir archimedes-analysis
cd archimedes-analysis

# 2. Save all 7 files to this directory
#    (Copy from the artifacts I created)

# 3. Make scripts executable
chmod +x build_image.sh start_analysis_container.sh

# 4. Build the Docker image
./build_image.sh

# 5. Start analyzing!
./start_analysis_container.sh
```

---

## What Each Script Does

### archimedes_analyzer.py

**Automatically:**
- ✅ Finds archimedes.c in multiple locations
- ✅ Creates all precision configurations (all double, all float, one-at-a-time, two-at-a-time)
- ✅ Tests each with O0, O1, O2, O3 (or subset in quick mode)
- ✅ Tests with/without -ffast-math
- ✅ Runs Delta-Debug in 4 modes (RR, PB, MCA, Cancellation)
- ✅ Performs MCA analysis with configurable samples
- ✅ Saves results incrementally (safe to interrupt)
- ✅ Generates summary analysis

**Usage:**
```bash
# Inside container
python3 archimedes_analyzer.py              # Full mode (~40-50 hours)
python3 archimedes_analyzer.py --quick      # Quick mode (~3-5 hours)
python3 archimedes_analyzer.py --minimal    # Minimal mode (~30-45 min)
python3 archimedes_analyzer.py --help       # See all options
```

### visualize_results.py

**Generates:**
1. `precision_heatmap.png` - Accuracy across precision configs × optimization levels
2. `fastmath_comparison.png` - Impact of -ffast-math (4 subplots)
3. `unstable_lines_frequency.png` - Which source lines are most problematic
4. `precision_impact.png` - How float variables affect stability
5. `dd_mode_comparison.png` - Comparison of Delta-Debug modes
6. `ANALYSIS_REPORT.md` - Comprehensive markdown report answering ALL research questions
7. `results_summary.csv` - Data export for custom analysis

**Usage:**
```bash
# Inside container
python3 visualize_results.py
```

---

## Expected Output Structure

After running everything:

```
your-directory/
├── Dockerfile
├── archimedes_analyzer.py
├── visualize_results.py
├── start_analysis_container.sh
├── build_image.sh
├── QUICKSTART.md
├── Docker_Setup_Instructions.md
└── analysis_results/                           ← Created by script
    ├── results.json                            ← Raw experiment data
    ├── results_summary.csv                     ← Tabular export
    ├── ANALYSIS_REPORT.md                      ← Main report (READ THIS!)
    ├── plots/
    │   ├── precision_heatmap.png
    │   ├── fastmath_comparison.png
    │   ├── unstable_lines_frequency.png
    │   ├── precision_impact.png
    │   └── dd_mode_comparison.png
    ├── all_double_O0_nofastmath/               ← Individual experiments
    │   ├── archimedes_modified.c
    │   ├── archimedes_bin
    │   ├── ddRun
    │   ├── ddCmp
    │   └── dd.line/
    │       └── rddmin-cmp/
    │           └── dd.line.exclude             ← Unstable lines
    ├── all_float_O3_fastmath/
    │   └── [same structure]
    └── [more experiment directories...]
```

---

## What the Report Answers

The `ANALYSIS_REPORT.md` systematically answers ALL your research questions:

### ✅ Question 1: Did unstable lines stay the same?
- Compares baseline (all_double, O0) to all other configurations
- Shows percentage of configs with same vs different unstable lines
- Interprets whether issue is algorithmic or precision-dependent

### ✅ Question 2: When did lines change?
- **Precision impact**: all_double vs all_float comparison
- **Single variable impact**: Which variable matters most
- **Optimization impact**: O0 vs O1 vs O2 vs O3
- **Fast-math impact**: With vs without -ffast-math
- Statistical analysis of each factor

### ✅ Question 3: Line-by-line stability analysis
- Frequency table showing which lines flagged most often
- Maps to source code (lines 16-17 from tutorial)
- Identifies whether roundoff or cancellation errors dominate

### ✅ Question 4: Delta-Debug mode comparison
- Compares RR, PB, MCA, Cancellation modes
- Shows which error types dominate
- Helps understand error sources

### ✅ Bonus: Recommendations
- Best configurations for accuracy
- Worst configurations to avoid
- Practical guidance for stable π computation

---

## Key Features

### 🎯 Fully Automated
- No manual source editing required
- Handles compilation, execution, analysis
- Incremental progress saves
- Comprehensive error handling

### 🐳 Docker-Native
- Self-contained environment
- No complex Verificarlo installation
- Works on any system with Docker
- Results persist on host

### 📊 Publication-Ready
- High-quality plots (300 DPI)
- Formatted markdown report
- CSV for custom analysis
- Citation information included

### ⚡ Flexible Modes
- **Minimal**: 30-45 minutes, quick validation
- **Quick**: 3-5 hours, good coverage
- **Full**: 40-50 hours, comprehensive

### 🔬 Scientifically Sound
- Based on Verificarlo tutorial methodology
- Uses Monte Carlo Arithmetic (MCA)
- Delta-Debug for instruction-level analysis
- Multiple error detection modes

---

## Time Estimates Breakdown

### Minimal Mode (~30-45 minutes)
- 3 configs × 2 opt levels × 1 fastmath = 6 experiments
- ~5 minutes per experiment
- Perfect for testing/validation

### Quick Mode (~3-5 hours)
- 15 configs × 2 opt levels × 1 fastmath = 30 experiments
- ~6-10 minutes per experiment
- Recommended for most users

### Full Mode (~40-50 hours)
- 15 configs × 4 opt levels × 2 fastmath = 120 experiments
- ~20-25 minutes per experiment
- Comprehensive research-grade results

**Per-experiment breakdown:**
- Compilation: ~5-10 seconds
- Delta-Debug (4 modes): ~10-20 minutes total
- MCA analysis (100 samples): ~1-2 minutes
- **Total: ~15-25 minutes per experiment**

---

## Important Notes

### ✅ What Persists (Saved to Host)
- All results in `analysis_results/`
- All plots
- JSON, CSV, markdown files
- Individual experiment directories

### ❌ What Doesn't Persist (Container Only)
- Command history (unless mounted)
- Temporary files outside `/workdir`
- Running processes after container exit

### 🔒 Safety Features
- Results save incrementally (safe to interrupt)
- Work directories isolated per config
- Failed experiments don't stop the run
- Timeouts prevent infinite loops

---

## Customization Points

### Want to Test Different Configs?

Edit `archimedes_analyzer.py`, method `generate_precision_configs()`:

```python
def generate_precision_configs(self):
    configs = []
    # Add your custom config
    configs.append(("my_custom", ['ti', 's', 'res']))
    return configs
```

### Want Different Compiler Flags?

Edit `__init__` method:
```python
self.opt_levels = ['O0', 'O2', 'O3', 'Ofast']  # Add Ofast
```

### Want More/Fewer MCA Samples?

Use quick mode (50 samples) or edit:
```python
self.num_mca_samples = 200  # Default is 100
```

---

## Dependencies Installed in Container

The Dockerfile installs:
- `matplotlib` - Plotting
- `seaborn` - Statistical visualizations
- `pandas` - Data manipulation
- `numpy` - Numerical computing

Plus everything from `verificarlo/verificarlo` base image:
- Verificarlo compiler
- LLVM toolchain
- Delta-Debug tools
- MCA backends
- Tutorial materials

---

## Testing the Setup

### Quick Validation (5 minutes)

```bash
# Build image
./build_image.sh

# Start container
./start_analysis_container.sh

# Inside container - test compilation
verificarlo --version

# Test Python
python3 -c "import matplotlib; print('✅ matplotlib works')"

# Test finding archimedes.c
find / -name "archimedes.c" 2>/dev/null | head -5

# Exit
exit
```

If all those work, you're ready to go!

---

## Common Workflows

### Workflow 1: Beginner (First Time)
```bash
./build_image.sh                    # One time setup
./start_analysis_container.sh       # Start container
python3 archimedes_analyzer.py --minimal    # 30 min test
python3 visualize_results.py        # Generate plots
exit
cat analysis_results/ANALYSIS_REPORT.md
```

### Workflow 2: Researcher (Overnight Run)
```bash
./start_analysis_container.sh
nohup python3 archimedes_analyzer.py --quick > analysis.log 2>&1 &
# Detach: Ctrl+P, Ctrl+Q
# Next morning...
docker attach verificarlo-analysis-session
python3 visualize_results.py
exit
```

### Workflow 3: Power User (Custom Analysis)
```bash
./start_analysis_container.sh
python3
>>> from archimedes_analyzer import ArchimedesAnalyzer
>>> a = ArchimedesAnalyzer(quick_mode=True)
>>> # Run specific experiments
>>> for var in ['ti', 'tii', 's']:
...     result = a.run_single_experiment(f"test_{var}", [var], 'O3', False)
...     a.results['experiments'].append(result)
>>> a.save_results()
>>> exit()
python3 visualize_results.py
exit
```

---

## Troubleshooting Quick Reference

| Problem | Solution |
|---------|----------|
| Can't find archimedes.c | Check with `find / -name "archimedes.c" 2>/dev/null` |
| Build fails | Try `docker build --no-cache -t verificarlo-analysis .` |
| Container won't start | `docker rm -f verificarlo-analysis-session` |
| Permission denied | `sudo chown -R $USER:$USER analysis_results/` |
| Analysis interrupted | Just restart - results are saved incrementally |
| No plots generated | Check `MPLBACKEND=Agg` is set |
| Delta-Debug timeout | Normal for complex cases, results still valid |

---

## Next Steps After First Run

1. ✅ **Read ANALYSIS_REPORT.md** - See what the automation discovered
2. ✅ **Check the plots** - Visualize the findings
3. ✅ **Compare with tutorial** - Verify results match known issues (lines 16-17)
4. ✅ **Run quick mode** - Get fuller picture with more configs
5. ✅ **Customize** - Modify scripts for your specific research questions

---

## Support Resources

- **Verificarlo GitHub**: https://github.com/verificarlo/verificarlo
- **Tutorial PDF**: Included in base image
- **Docker Hub**: https://hub.docker.com/r/verificarlo/verificarlo
- **These docs**: `QUICKSTART.md` and `Docker_Setup_Instructions.md`

---

## Summary

You now have:
✅ Complete Docker-based automation  
✅ No manual installation needed  
✅ Systematic testing of all configurations  
✅ Automatic Delta-Debug analysis  
✅ Beautiful visualizations  
✅ Comprehensive report answering all questions  
✅ Flexible modes (30 min to 50 hours)  
✅ Safe, incremental progress saving  

**Total setup time: ~5 minutes**  
**First results: ~30-45 minutes**  
**Full analysis: Choose your mode!**

🚀 Ready to discover floating point errors!