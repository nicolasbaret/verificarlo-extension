# Verificarlo Analysis Framework

Automated floating-point stability analysis using Monte Carlo Arithmetic and Delta-Debug.

## Quick Start
```bash
# Single variable analysis
./orchestrate.sh program.c -mode single variable_name

# All variables analysis
./orchestrate.sh program.c -mode all
```

## Modes

### Single Mode
Tests one variable change against baseline.
```bash
./orchestrate.sh archimedes.c -mode single ti
```

- Creates: `baseline_all_double` + `ti_float`
- Compiles: 2 variants × 8 configurations = 16 binaries
- Configurations: O0/O1/O2/O3 with/without `-ffast-math`

### All Mode
Tests each variable individually.
```bash
./orchestrate.sh program.c -mode all
```

- Creates: baseline + 1 variant per variable
- Example: 5 variables = 6 variants × 8 configs = 48 binaries

## Pipeline Steps

1. **Analyze source** - Extract float/double variables
2. **Generate variants** - Modify source files (double → float)
3. **Compile** - Build all configurations with verificarlo
4. **Validate** - Detect NaN/Inf outputs
5. **Setup DD** - Create Delta-Debug scripts
6. **Run DD** - Execute with RR, MCA, Cancellation backends
7. **Report** - Generate HTML/Markdown/JSON reports

## Output Structure
```
results/<analysis_name>/
├── manifest.json              # Source analysis
├── variants/                  # Modified sources
├── binaries/                  # Compiled programs
├── validation.json            # NaN/Inf detection
├── ddebug_setup/             # DD workspaces
├── ddebug_results.json       # DD findings
└── report/
    ├── report.html           # ⭐ Main report
    ├── report.md
    └── summary.json
```

## Delta-Debug Backends

- **RR** (Random Rounding) - Round-off errors
- **MCA** (Monte Carlo Arithmetic) - Full stochastic analysis  
- **Cancellation** - Catastrophic cancellations

## Reports

### HTML (`report.html`)
- Summary statistics
- Problematic variables and lines
- Detailed results table
- Stable/unstable configurations

### JSON (`summary.json`)
```json
{
  "total_configs": 16,
  "variable_instability": {"ti": 24, "tii": 12},
  "line_instability": {"16": 18, "17": 12},
  "stable_configs": [...],
  "unstable_configs": [...]
}
```

## Docker Usage
```bash
# Run container
docker pull verificarlo/verificarlo:latest
docker run -v $(pwd):/workdir -it verificarlo/verificarlo bash

# Inside container
orchestrate.sh archimedes.c -mode single ti
```

## Individual Steps
```bash
# Step 1
python3 scripts/01_analyze_source.py --source file.c --output manifest.json

# Step 2
python3 scripts/02_generate_variants.py --manifest manifest.json --mode single --variable ti --output variants/

# Step 3
python3 scripts/03_compile_variants.py --variants variants/manifest.json --output binaries/

# Step 4
python3 scripts/04_validate_outputs.py --binaries binaries/manifest.json --output validation.json

# Step 5
python3 scripts/05_setup_ddebug.py --validation validation.json --output ddebug_setup/

# Step 6
python3 scripts/06_run_ddebug.py --setup ddebug_setup/manifest.json --output ddebug_results.json

# Step 7
python3 scripts/07_analyze_results.py --results . --output report/
```

## Troubleshooting

**DD runs fail**
- Check `ddebug_setup/<config>/ddCmp` script
- Verify binary produces consistent output
- Manually test: `./ddRun test_dir && ./ddCmp test_dir test_dir`

**All variants produce NaN**
- Algorithm requires double precision
- Check which variables cause NaN in `validation.json`

**Compilation errors**
- Verify source compiles with standard compiler
- Check for missing libraries (add `-lm` if needed)

## Performance

- Single mode: ~2-5 minutes
- All mode: ~N×3 minutes (N = number of variables)
- Scales with source complexity and number of iterations

## Links

- [Verificarlo](https://github.com/verificarlo/verificarlo)
- [MCA Paper](https://hal.archives-ouvertes.fr/hal-01192668)
- [Delta-Debug](https://www.st.cs.uni-saarland.de/papers/tse2002/)