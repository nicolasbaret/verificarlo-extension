# Verificarlo Analysis Framework — Quick Guide

This repository contains an automated pipeline to analyze floating-point stability of C programs using Verificarlo and Delta-Debug.

Overview of main files and utilities
- Docker / container:
  - [Dockerfile](Dockerfile)
  - [build_image.sh](build_image.sh)
  - [start_analysis_container.sh](start_analysis_container.sh)
  - [clean_results.sh](clean_results.sh)

- Orchestration and pipeline (step scripts):
  - [src/orchestrate.sh](src/orchestrate.sh) — top-level orchestrator
  - [src/scripts/01_analyze_source.py](src/scripts/01_analyze_source.py) — source analysis (uses [`utils.source_parser.CSourceParser`](src/scripts/utils/source_parser.py))
  - [src/scripts/02_generate_variants.py](src/scripts/02_generate_variants.py) — generate variants (uses [`utils.source_parser.SourceModifier`](src/scripts/utils/source_parser.py))
  - [src/scripts/03_compile_variants.py](src/scripts/03_compile_variants.py) — compile variants (uses [`utils.compiler.VerificarloCompiler`](src/scripts/utils/compiler.py))
  - [src/scripts/04_validate_outputs.py](src/scripts/04_validate_outputs.py) — validate runs (functions: [`run_binary`](src/scripts/04_validate_outputs.py), [`check_validity`](src/scripts/04_validate_outputs.py))
  - [src/scripts/05_setup_ddebug.py](src/scripts/05_setup_ddebug.py) — create DD workspaces and helper scripts (`create_ddrun_script`, `create_ddcmp_script`)
  - [src/scripts/06_run_ddebug.py](src/scripts/06_run_ddebug.py) — run Delta-Debug (core helper: [`06_run_ddebug.run_dd`](src/scripts/06_run_ddebug.py), parses outputs with [`utils.dd_parser.DeltaDebugParser`](src/scripts/utils/dd_parser.py))
  - [src/scripts/07_analyze_results.py](src/scripts/07_analyze_results.py) — generate reports (HTML / Markdown / JSON)

Key utility modules
- [src/scripts/utils/source_parser.py](src/scripts/utils/source_parser.py) — C parsing and source modification (`CSourceParser`, `SourceModifier`)
- [src/scripts/utils/compiler.py](src/scripts/utils/compiler.py) — compilation wrappers (`CompilationConfig`, `CompilationResult`, `VerificarloCompiler`)
- [src/scripts/utils/dd_parser.py](src/scripts/utils/dd_parser.py) — parse Delta-Debug outputs (`DDLineResult`, `DeltaDebugParser`)

Quick start (recommended)
1. Clone the repository.
2. Build the analysis image (run from repo root):
   - ./build_image.sh
   - (build uses: [Dockerfile](Dockerfile)) - you need to have the Docker Daemon running 
3. Start the container (will mount current directory into `/workdir`):
   - ./start_analysis_container.sh
   - (this runs the image created by `build_image.sh`)

Run the pipeline
- Use the orchestrator (single command to run the whole pipeline):
  - Inside the container: 
    - ./src/orchestrate.sh <source_file.c> -mode single <var>
    - ./src/orchestrate.sh <source_file.c> -mode all
  - Orchestrator delegates to step scripts in [src/scripts/](src/scripts/)

Run individual steps (examples)
- Step 1: analyze source variables
  - python3 src/scripts/01_analyze_source.py --source archimedes/archimedes.c --output results/manifest.json
- Step 2: generate variants
  - python3 src/scripts/02_generate_variants.py --manifest results/manifest.json --mode single --variable ti --output results/variants
- Step 3: compile all variants
  - python3 src/scripts/03_compile_variants.py --variants results/variants/manifest.json --output results/binaries
- Step 4: validate outputs
  - python3 src/scripts/04_validate_outputs.py --binaries results/binaries/manifest.json --output results/validation.json
- Step 5: setup delta-debug
  - python3 src/scripts/05_setup_ddebug.py --validation results/validation.json --output results/ddebug_setup
- Step 6: run delta-debug
  - python3 src/scripts/06_run_ddebug.py --setup results/ddebug_setup/manifest.json --output results/ddebug_results.json
- Step 7: analyze & report
  - python3 src/scripts/07_analyze_results.py --results results --output results/report --formats json markdown html


Viewing reports outside the container
- Reports are written to the host-mounted results directory (example: ./results/<analysis>/report).
- To quickly view the HTML report with a simple Python server outside the container:
  - cd results/<analysis>/report
  - python3 -m http.server 8000
  - Open http://localhost:8000/report.html

Cleaning results
- Use [clean_results.sh](clean_results.sh) to remove results directories interactively.

If you need to inspect or tweak behavior, open these files:
- [src/orchestrate.sh](src/orchestrate.sh)
- All step scripts: [src/scripts/](src/scripts/)
- Utility modules: [src/scripts/utils/](src/scripts/utils/)
- Outputs from each script: /results/<analysis>*.json files
