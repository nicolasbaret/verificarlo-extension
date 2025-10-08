#!/usr/bin/env python3
"""
Archimedes Floating Point Error Analysis Automation
Systematically tests precision variations and compiler flags

Docker/Container Compatible Version
"""

import os
import subprocess
import json
import itertools
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set, Tuple
import shutil

class ArchimedesAnalyzer:
    def __init__(self, source_file=None, output_dir="analysis_results", 
                 quick_mode=False):
        # Auto-detect archimedes.c location
        if source_file is None:
            # Try common locations
            possible_paths = [
                "archimedes.c",  # Current directory
                "archimedes/archimedes.c",  # Tutorial structure
                "/workdir/archimedes.c",  # Mounted directory
                "/workdir/archimedes/archimedes.c",  # Tutorial in workdir
                "/root/verificarlo-tutorial/archimedes/archimedes.c",  # Common location in image
                "/verificarlo-tutorial/archimedes/archimedes.c",  # Alternative location
                "verificarlo-tutorial/archimedes/archimedes.c",  # Relative path
            ]
            
            for path in possible_paths:
                if Path(path).exists():
                    source_file = path
                    break
            
            if source_file is None:
                # Try to find it anywhere
                import subprocess
                try:
                    result = subprocess.run(
                        ['find', '/', '-name', 'archimedes.c', '-type', 'f'],
                        capture_output=True, text=True, timeout=10
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        found_paths = result.stdout.strip().split('\n')
                        if found_paths:
                            source_file = found_paths[0]
                            print(f"⚠️  Found archimedes.c via search: {source_file}")
                except:
                    pass
            
            if source_file is None:
                raise FileNotFoundError(
                    "Could not find archimedes.c. Please provide path or copy to current directory.\n"
                    "Tried locations: " + ", ".join(possible_paths) + "\n\n"
                    "To use a specific file: python3 archimedes_analyzer.py --source /path/to/archimedes.c"
                )
        
        self.source_file = source_file
        print(f"📄 Using source file: {self.source_file}")
        
        # Ensure output directory is in /workdir for persistence
        if not str(output_dir).startswith('/workdir'):
            output_dir = f"/workdir/{output_dir}"
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        print(f"📁 Results will be saved to: {self.output_dir}")
        
        # Read original source
        with open(source_file, 'r') as f:
            self.original_source = f.read()
        
        # Variables to modify
        self.variables = ['ti', 'tii', 'fact', 'res', 's']
        
        # Compiler flags to test
        if quick_mode:
            # Quick mode: Only test O0 and O3, no fastmath variations
            self.opt_levels = ['O0', 'O3']
            self.fastmath_options = [False]
            self.num_mca_samples = 50  # Reduced from 100
            self.dd_modes = [
                ('rr', 'libinterflop_mca.so -m rr --precision-binary64=53'),
                ('mca', 'libinterflop_mca.so -m mca --precision-binary64=53'),
            ]
            print("⚡ QUICK MODE ENABLED:")
            print(f"   - Testing only {len(self.opt_levels)} optimization levels")
            print(f"   - Skipping fastmath variations")
            print(f"   - Using {self.num_mca_samples} MCA samples (instead of 100)")
            print(f"   - Running {len(self.dd_modes)} DD modes (instead of 4)")
            print(f"   - Estimated time: ~3-5 hours instead of 40-50 hours\n")
        else:
            self.opt_levels = ['O0', 'O1', 'O2', 'O3']
            self.fastmath_options = [False, True]
            self.num_mca_samples = 100
            self.dd_modes = [
                ('rr', 'libinterflop_mca.so -m rr --precision-binary64=53'),
                ('pb', 'libinterflop_mca.so -m pb --precision-binary64=53'),
                ('mca', 'libinterflop_mca.so -m mca --precision-binary64=53'),
                ('cancel', 'libinterflop_cancellation.so')
            ]
        
        # Results storage
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'quick_mode': quick_mode,
            'experiments': []
        }
    
    def create_modified_source(self, float_vars: List[str], output_path: str):
        """
        Create a modified version of archimedes.c with specified variables as float
        
        Args:
            float_vars: List of variable names to convert to float
            output_path: Where to save the modified source
        """
        modified = self.original_source
        
        # Find the archimedes function and modify variable declarations
        # Pattern: double ti, tii, fact, res;
        # Also handle: double s = sqrt(ti * ti + 1);
        
        for var in float_vars:
            # Replace declarations like: double ti, tii, ...
            # This is tricky - we need to be careful not to break multi-var declarations
            
            # Simple approach: replace "double var" with "float var"
            # This works for single declarations
            modified = re.sub(
                rf'\bdouble\s+{var}\b',
                f'float {var}',
                modified
            )
        
        with open(output_path, 'w') as f:
            f.write(modified)
        
        return output_path
    
    def generate_precision_configs(self) -> List[Tuple[str, List[str]]]:
        """
        Generate all precision configurations to test
        Returns list of (config_name, variables_as_float)
        """
        configs = []
        
        # Baseline: all double
        configs.append(("all_double", []))
        
        # All float
        configs.append(("all_float", self.variables.copy()))
        
        # One at a time
        for var in self.variables:
            configs.append((f"only_{var}_float", [var]))
        
        # Two at a time - meaningful combinations
        two_var_combos = [
            (['ti', 'tii'], "ti_tii_float"),  # recursive sequence
            (['ti', 's'], "ti_s_float"),      # sqrt operation
            (['tii', 'res'], "tii_res_float"), # output chain
            (['s', 'ti'], "s_ti_float")       # cancellation-prone
        ]
        
        for vars_list, name in two_var_combos:
            configs.append((name, vars_list))
        
        return configs
    
    def compile_with_flags(self, source_path: str, output_binary: str, 
                          opt_level: str, use_fastmath: bool) -> bool:
        """
        Compile source with verificarlo and specified flags
        """
        flags = [f'-{opt_level}']
        if use_fastmath:
            flags.append('-ffast-math')
        
        # CRITICAL: Add --ddebug and -g for Delta-Debug support
        # --ddebug: Enables verificarlo debug mode for vfc_ddebug
        # -g: Generates debug symbols with line number information
        flags.extend(['--ddebug', '-g'])
        
        # Ensure paths are strings (not Path objects)
        source_path = str(source_path)
        output_binary = str(output_binary)
        
        cmd = ['verificarlo'] + flags + [source_path, '-o', output_binary, '-lm']
        
        print(f"  Compiling: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                print(f"  ❌ Compilation failed: {result.stderr}")
                return False
            
            # Verify the binary was created and is executable
            if not Path(output_binary).exists():
                print(f"  ❌ Binary not created: {output_binary}")
                return False
            
            print(f"  ✅ Compilation successful")
            return True
            
        except subprocess.TimeoutExpired:
            print(f"  ❌ Compilation timeout for {output_binary}")
            return False
    
    def run_delta_debug(self, binary_path: str, dd_mode: str, 
                       backend_config: str, work_dir: Path) -> Dict:
        """
        Run Delta-Debug analysis and parse results
        """
        # Ensure paths are absolute
        binary_path = Path(binary_path).resolve()
        work_dir = Path(work_dir).resolve()
        
        # Check if the binary exists
        if not binary_path.exists():
            print(f"    ❌ Binary not found: {binary_path}")
            return {
                'mode': dd_mode,
                'unstable_lines': [],
                'success': False,
                'output': f'Binary not found: {binary_path}'
            }
        
        # Create ddRun script
        ddrun_path = work_dir / "ddRun"
        with open(ddrun_path, 'w') as f:
            f.write(f"""#!/bin/bash
OUTPUT_DIR=$1
{binary_path} > $OUTPUT_DIR/res.dat 2>&1
""")
        os.chmod(ddrun_path, 0o755)
        
        # Create ddCmp script (following verificarlo tutorial pattern)
        ddcmp_path = work_dir / "ddCmp"
        with open(ddcmp_path, 'w') as f:
            f.write("""#!/usr/bin/env python3
#
# ddCmp: compares the reference run and a current run, returns with success if
# there is no numerical deviation higher than 1e-6.
#
# The first argument is the folder with the reference output, the second
# argument is the folder with the current output.

import sys
import numpy as np

MAX_DEVIATION = 1e-6
REFDIR = sys.argv[1]
CURDIR = sys.argv[2]

def read_output(DIR):
    with open("{}/res.dat".format(DIR)) as f:
        # Read the last line which should contain the final pi value
        lines = f.read().strip().split('\\n')
        return float(lines[-1])

try:
    # Read reference and current outputs
    ref = read_output(REFDIR)
    cur = read_output(CURDIR)
    
    # Compute the deviation using Monte Carlo Arithmetic formula
    # deviation = sigma / |mu|
    deviation = np.std([ref, cur]) / np.abs(np.mean([ref, cur]))
    
    # Write log to CURDIR/res.stat
    with open("{}/res.stat".format(CURDIR), 'w') as f:
        f.write("reference = {} current = {} deviation = {}\\n".format(
            ref, cur, deviation))
    
    # Fail if the deviation is higher than MAX_DEVIATION
    sys.exit(0 if deviation < MAX_DEVIATION else 1)
    
except Exception as e:
    # If there's an error reading or parsing, log it and fail
    with open("{}/res.stat".format(CURDIR), 'w') as f:
        f.write("ERROR: {}\\n".format(str(e)))
    sys.exit(1)
""")
        os.chmod(ddcmp_path, 0o755)
        
        # Run Delta-Debug
        env = os.environ.copy()
        env['VFC_BACKENDS'] = backend_config
        
        try:
            # Clean previous dd.line directory
            dd_dir = work_dir / "dd.line"
            if dd_dir.exists():
                shutil.rmtree(dd_dir)
            
            # Run vfc_ddebug from the work directory
            # Must use relative paths for ddRun and ddCmp
            result = subprocess.run(
                ['vfc_ddebug', './ddRun', './ddCmp'],
                cwd=str(work_dir),
                env=env,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            # Check if Delta-Debug succeeded
            if result.returncode != 0 or "failed" in result.stdout.lower():
                print(f"    ⚠️  Delta-Debug ({dd_mode}) failed or returned error")
                print(f"    Return code: {result.returncode}")
                if result.stdout:
                    print(f"    stdout: {result.stdout[:300]}")
                if result.stderr:
                    print(f"    stderr: {result.stderr[:300]}")
                
                return {
                    'mode': dd_mode,
                    'unstable_lines': [],
                    'success': False,
                    'output': result.stdout + "\n" + result.stderr
                }
            
            # Parse Delta-Debug results
            unstable_lines = self.parse_dd_results(dd_dir)
            
            if unstable_lines:
                print(f"    ✅ Found {len(unstable_lines)} unstable line(s): {unstable_lines}")
            else:
                print(f"    ℹ️  No unstable lines detected (code is stable)")
            
            return {
                'mode': dd_mode,
                'unstable_lines': unstable_lines,
                'success': True,
                'output': result.stdout
            }
        except subprocess.TimeoutExpired:
            print(f"    ⚠️  Delta-Debug ({dd_mode}) timed out")
            return {
                'mode': dd_mode,
                'unstable_lines': [],
                'success': False,
                'output': 'Timeout'
            }
        except Exception as e:
            print(f"    ⚠️  Delta-Debug ({dd_mode}) exception: {e}")
            import traceback
            traceback.print_exc()
            return {
                'mode': dd_mode,
                'unstable_lines': [],
                'success': False,
                'output': str(e)
            }
    
    def parse_dd_results(self, dd_dir: Path) -> List[int]:
        """
        Parse Delta-Debug output to extract unstable lines
        """
        unstable_lines = []
        
        # Delta-Debug can create results in multiple locations
        # Try rddmin-cmp/dd.line.exclude first (union of all minimized sets)
        possible_locations = [
            dd_dir / "rddmin-cmp" / "dd.line.exclude",
            dd_dir / "ddmin0" / "dd.line.include",
            dd_dir / "ddmin1" / "dd.line.include",
            dd_dir / "dd.line.exclude",  # Sometimes at root
        ]
        
        for exclude_file in possible_locations:
            if exclude_file.exists():
                print(f"    📋 Found DD results: {exclude_file}")
                with open(exclude_file, 'r') as f:
                    for line in f:
                        # Format: 0x0000000000400e5c: archimedes at archimedes.c:16
                        match = re.search(r'archimedes\.c:(\d+)', line)
                        if match:
                            line_num = int(match.group(1))
                            if line_num not in unstable_lines:
                                unstable_lines.append(line_num)
        
        if not unstable_lines and dd_dir.exists():
            # Debug: list what files actually exist
            print(f"    ⚠️  No unstable lines found in {dd_dir}")
            print(f"    Directory contents:")
            for item in dd_dir.rglob("*"):
                if item.is_file():
                    print(f"      - {item.relative_to(dd_dir)}")
        
        return sorted(set(unstable_lines))
    
    def run_mca_analysis(self, binary_path: str, precision: int, 
                        num_samples: int = None) -> Dict:
        """
        Run MCA analysis to get significant digits estimation
        """
        if num_samples is None:
            num_samples = self.num_mca_samples
        
        results = []
        env = os.environ.copy()
        env['VFC_BACKENDS'] = f'libinterflop_mca.so --precision-binary64={precision} -m mca'
        
        for _ in range(num_samples):
            try:
                result = subprocess.run(
                    [binary_path],
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                # Extract the final value
                output = result.stdout.strip().split('\n')[-1]
                try:
                    value = float(output)
                    results.append(value)
                except ValueError:
                    continue
            except subprocess.TimeoutExpired:
                continue
        
        if not results:
            return {'mean': None, 'std': None, 'significant_digits': None}
        
        import statistics
        mean = statistics.mean(results)
        std = statistics.stdev(results) if len(results) > 1 else 0
        
        # Calculate significant digits using Parker's formula
        import math
        if std > 0 and mean != 0:
            sig_digits = -math.log10(std / abs(mean))
        else:
            sig_digits = float('inf')
        
        return {
            'mean': mean,
            'std': std,
            'significant_digits': sig_digits,
            'num_samples': len(results)
        }
    
    def run_single_experiment(self, config_name: str, float_vars: List[str],
                             opt_level: str, use_fastmath: bool) -> Dict:
        """
        Run a complete experiment: compile, run DD, analyze
        """
        print(f"\n{'='*60}")
        print(f"Running: {config_name} | {opt_level} | fastmath={use_fastmath}")
        print(f"{'='*60}")
        
        # Create work directory
        fastmath_str = "fastmath" if use_fastmath else "nofastmath"
        work_dir = self.output_dir / f"{config_name}_{opt_level}_{fastmath_str}"
        work_dir.mkdir(exist_ok=True)
        
        # Create modified source
        source_path = work_dir / "archimedes_modified.c"
        self.create_modified_source(float_vars, source_path)
        
        # Compile
        binary_path = work_dir / "archimedes_bin"
        if not self.compile_with_flags(source_path, binary_path, opt_level, use_fastmath):
            return {
                'config': config_name,
                'float_vars': float_vars,
                'opt_level': opt_level,
                'fastmath': use_fastmath,
                'status': 'compilation_failed'
            }
        
        # Run Delta-Debug for each mode
        dd_results = []
        for mode_name, backend_config in self.dd_modes:
            print(f"  Running Delta-Debug ({mode_name})...")
            dd_result = self.run_delta_debug(binary_path, mode_name, 
                                            backend_config, work_dir)
            dd_results.append(dd_result)
        
        # Run MCA analysis
        print(f"  Running MCA analysis...")
        precision = 24 if float_vars else 53  # Use 24 for float, 53 for double
        mca_result = self.run_mca_analysis(binary_path, precision)
        
        experiment_result = {
            'config': config_name,
            'float_vars': float_vars,
            'opt_level': opt_level,
            'fastmath': use_fastmath,
            'status': 'success',
            'delta_debug': dd_results,
            'mca_analysis': mca_result,
            'work_dir': str(work_dir)
        }
        
        return experiment_result
    
    def run_all_experiments(self):
        """
        Run the complete experimental suite
        """
        configs = self.generate_precision_configs()
        
        print(f"Generated {len(configs)} precision configurations")
        print(f"Testing {len(self.opt_levels)} optimization levels")
        print(f"Testing with/without fastmath")
        print(f"Total experiments: {len(configs) * len(self.opt_levels) * 2}")
        
        for config_name, float_vars in configs:
            for opt_level in self.opt_levels:
                for use_fastmath in self.fastmath_options:
                    result = self.run_single_experiment(
                        config_name, float_vars, opt_level, use_fastmath
                    )
                    self.results['experiments'].append(result)
                    
                    # Save intermediate results
                    self.save_results()
        
        print("\n" + "="*60)
        print("All experiments complete!")
        print("="*60)
    
    def save_results(self):
        """
        Save results to JSON file
        """
        results_file = self.output_dir / "results.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
    
    def analyze_results(self):
        """
        Perform comparative analysis of results
        """
        print("\n" + "="*60)
        print("ANALYSIS SUMMARY")
        print("="*60)
        
        # Question 1: Did unstable lines stay the same?
        print("\n1. Line Stability Analysis:")
        all_unstable_lines = {}
        
        for exp in self.results['experiments']:
            if exp['status'] != 'success':
                continue
            
            key = (exp['config'], exp['opt_level'], exp['fastmath'])
            unstable = set()
            
            for dd in exp['delta_debug']:
                if dd['success']:
                    unstable.update(dd['unstable_lines'])
            
            all_unstable_lines[key] = unstable
        
        # Find baseline
        baseline_key = ('all_double', 'O0', False)
        baseline_lines = all_unstable_lines.get(baseline_key, set())
        
        print(f"   Baseline unstable lines: {sorted(baseline_lines)}")
        
        # Compare each config to baseline
        changed_configs = []
        for key, lines in all_unstable_lines.items():
            if key == baseline_key:
                continue
            if lines != baseline_lines:
                changed_configs.append((key, lines))
        
        if changed_configs:
            print(f"\n   Configurations with different unstable lines: {len(changed_configs)}")
            for (config, opt, fastmath), lines in changed_configs[:5]:  # Show first 5
                print(f"      {config} | {opt} | fastmath={fastmath}: {sorted(lines)}")
        else:
            print("   All configurations have same unstable lines as baseline")
        
        # Question 2: When did lines change?
        print("\n2. Transition Analysis:")
        
        # Group by precision
        precision_impact = {}
        for exp in self.results['experiments']:
            if exp['status'] != 'success':
                continue
            
            has_float = len(exp['float_vars']) > 0
            key = (has_float, exp['opt_level'], exp['fastmath'])
            
            if key not in precision_impact:
                precision_impact[key] = []
            
            unstable = set()
            for dd in exp['delta_debug']:
                if dd['success']:
                    unstable.update(dd['unstable_lines'])
            
            precision_impact[key].append(unstable)
        
        print("   Precision impact:")
        for (has_float, opt, fastmath), line_sets in precision_impact.items():
            prec_type = "float" if has_float else "double"
            all_same = all(s == line_sets[0] for s in line_sets)
            print(f"      {prec_type} | {opt} | fastmath={fastmath}: "
                  f"{'consistent' if all_same else 'varies'}")
        
        # Question 3: Compiler flag impact
        print("\n3. Compiler Flag Impact:")
        
        fastmath_impact = {}
        for exp in self.results['experiments']:
            if exp['status'] != 'success':
                continue
            
            key = (exp['config'], exp['opt_level'])
            if key not in fastmath_impact:
                fastmath_impact[key] = {'with': None, 'without': None}
            
            unstable = set()
            for dd in exp['delta_debug']:
                if dd['success']:
                    unstable.update(dd['unstable_lines'])
            
            if exp['fastmath']:
                fastmath_impact[key]['with'] = unstable
            else:
                fastmath_impact[key]['without'] = unstable
        
        differences = 0
        for key, results in fastmath_impact.items():
            if results['with'] != results['without']:
                differences += 1
        
        print(f"   Fastmath changed unstable lines in {differences}/{len(fastmath_impact)} cases")
        
        # Significant digits analysis
        print("\n4. Significant Digits Summary:")
        sig_digits = []
        for exp in self.results['experiments']:
            if exp['status'] == 'success' and exp['mca_analysis']['significant_digits']:
                sig_digits.append({
                    'config': exp['config'],
                    'opt': exp['opt_level'],
                    'fastmath': exp['fastmath'],
                    'sig_digits': exp['mca_analysis']['significant_digits']
                })
        
        if sig_digits:
            # Sort by significant digits
            sig_digits.sort(key=lambda x: x['sig_digits'])
            
            print(f"\n   Best configurations (most significant digits):")
            for item in sig_digits[-5:]:
                print(f"      {item['config']} | {item['opt']} | "
                      f"fastmath={item['fastmath']}: {item['sig_digits']:.2f} digits")
            
            print(f"\n   Worst configurations (least significant digits):")
            for item in sig_digits[:5]:
                print(f"      {item['config']} | {item['opt']} | "
                      f"fastmath={item['fastmath']}: {item['sig_digits']:.2f} digits")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Archimedes Floating Point Error Analysis')
    parser.add_argument('--source', type=str, default=None,
                       help='Path to archimedes.c file (auto-detected if not specified)')
    parser.add_argument('--quick', action='store_true', 
                       help='Quick mode: fewer tests, faster results (~3-5 hours instead of 40-50)')
    parser.add_argument('--minimal', action='store_true',
                       help='Minimal mode: only baseline configs (~30 minutes)')
    parser.add_argument('--parallel', type=int, default=1,
                       help='Number of parallel workers (default: 1)')
    parser.add_argument('--single-experiment', action='store_true')
    
    args = parser.parse_args()
    
    analyzer = ArchimedesAnalyzer(source_file=args.source, quick_mode=args.quick)
    

    if args.minimal:
        print("\n⚡⚡ MINIMAL MODE ⚡⚡")
        print("Testing only critical configurations:\n")
        # Override to test only a few key configs
        original_method = analyzer.generate_precision_configs
        def minimal_configs():
            return [
                ("all_double", []),
                ("all_float", analyzer.variables.copy()),
                ("only_ti_float", ['ti']),
            ]
        analyzer.generate_precision_configs = minimal_configs
        analyzer.opt_levels = ['O0', 'O3']
        print("   - 3 precision configs")
        print("   - 2 optimization levels")
        print("   - Estimated time: ~30-45 minutes\n")
    
    # Run all experiments
    if args.parallel > 1:
        print(f"⚡ Running with {args.parallel} parallel workers")
        # Note: Full parallel implementation would go here
        # For now, warn user
        print("⚠️  Parallel execution not yet implemented - running sequentially")
    
    analyzer.run_all_experiments()
    
    # Analyze and report
    analyzer.analyze_results()
    
    # Generate detailed report
    print(f"\nDetailed results saved to: {analyzer.output_dir}/results.json")
    print(f"Individual experiment data in: {analyzer.output_dir}/")
    print("\n💡 Run 'python3 visualize_results.py' to generate plots and markdown report")

if __name__ == "__main__":
    main()