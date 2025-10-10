
#!/usr/bin/env python3
"""
Archimedes Floating Point Error Analysis - Clean Rewrite
Small, testable functions with clear separation of concerns
"""

import os
import subprocess
import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import shutil


# ============================================================================
# CONFIGURATION
# ============================================================================

class AnalysisConfig:
    """Configuration for the analysis run"""
    def __init__(self, mode='full', variable: Optional[str]=None):
        self.mode = mode

        self.ti_combinations = [
            #ti combinations
            ("ti_tii_float", ['ti', 'tii']),
            ("ti_s_float", ['ti', 's']),
            ("ti_fact_float", ['ti', 'fact']),
            ("ti_res_float", ['ti', 'res'])]
        
        self.tii_combinations = [
            #tii combinations
            ("tii_ti_float", ['tii', 'ti']),
            ("tii_s_float", ['tii', 's']),
            ("tii_fact_float", ['tii', 'fact']),
            ("tii_res_float", ['tii', 'res'])
        ]
        self.res_combinations = [
        #res combinations
            ("res_ti_float", ['res', 'ti']),
            ("res_tii_float", ['res', 'tii']),
            ("res_fact_float", ['res', 'fact']),
            ("res_s_float", ['res', 's']),
        ]
        self.s_combinations = [
            #s combinations
            ("s_ti_float", ['s', 'ti']),
            ("s_tii_float", ['s', 'tii']),
            ("s_fact_float", ['s', 'fact']),
            ("s_res_float", ['s', 'res'])
        ]
        self.fact_combinations = [
        ("fact_ti_float", ['fact', 'ti']),
            ("fact_tii_float", ['fact', 'tii']),
            ("fact_s_float", ['fact', 's']),
            ("fact_res_float", ['fact', 'res'])
        ]

        if mode == 'minimal':
            self.opt_levels = ['O0']
            self.fastmath_options = [False]
            self.mca_samples = 50
            self.configs = [("all_double", [])]
        
        if mode == 'single':
            self.opt_levels = ['O0']
            self.fastmath_options = [False]
            self.mca_samples = 50
            self.configs = []
            if mode == 'single':
 
                if variable == 'ti':
                    self.configs.extend(self.ti_combinations)
                elif variable == 'tii':
                    self.configs.extend(self.tii_combinations)
                elif variable == 'res':
                    self.configs.extend(self.res_combinations)
                elif variable == 's':
                    self.configs.extend(self.s_combinations)
                elif variable == 'fact':
                    self.configs.extend(self.fact_combinations)
                else:
                    raise ValueError(f"Invalid variable name: {variable}. Must be one of: ti, tii, res, s, fact")
    
        else:  # full
            self.opt_levels = ['O0', 'O1', 'O2', 'O3']
            self.fastmath_options = [False, True]
            self.mca_samples = 100
            self.configs = self._generate_all_configs()
    
    def _generate_all_configs(self):
        """Generate all precision configurations"""
        variables = ['ti', 'tii', 'fact', 'res', 's']
        configs = [
            ("all_double", []),
            ("all_float", variables.copy()),
        ]
        
        # One at a time
        for var in variables:
            configs.append((f"only_{var}_float", [var]))
        
        # Two at a time
        configs.extend([self.fact_combinations,
                        self.res_combinations,
                        self.s_combinations,
                        self.ti_combinations,
                        self.tii_combinations])
        return configs


# ============================================================================
# SOURCE CODE MANIPULATION
# ============================================================================

def find_archimedes_source() -> Path:
    """Find archimedes.c in common locations"""
    locations = [
        "archimedes.c",
        "archimedes/archimedes.c",
        "/workdir/archimedes.c",
        "/workdir/archimedes/archimedes.c",
        "/root/verificarlo-tutorial/archimedes/archimedes.c",
    ]
    
    for loc in locations:
        if Path(loc).exists():
            return Path(loc)
    
    raise FileNotFoundError(f"archimedes.c not found. Tried: {locations}")


def read_source(source_path: Path) -> str:
    """Read source file"""
    with open(source_path, 'r') as f:
        return f.read()


def modify_variable_types(source_code: str, float_vars: List[str]) -> str:
    """
    Modify variable declarations to use float instead of double
    
    Strategy: Replace declarations line by line, handling multi-variable declarations
    """
    if not float_vars:
        return source_code
    
    lines = source_code.split('\n')
    modified_lines = []
    
    for line in lines:
        modified_line = line
        
        # Find lines with variable declarations
        # Pattern: "double var1, var2, var3;"
        # or "double var = expression;"
        
        for var in float_vars:
            # Case 1: "double var," or "double var;"
            modified_line = re.sub(
                rf'\bdouble\s+{var}\s*([,;])',
                rf'float {var}\1',
                modified_line
            )
            
            # Case 2: "double var =" 
            modified_line = re.sub(
                rf'\bdouble\s+{var}\s*=',
                rf'float {var} =',
                modified_line
            )
        
        modified_lines.append(modified_line)
    
    return '\n'.join(modified_lines)


def write_source(source_code: str, output_path: Path):
    """Write modified source to file"""
    with open(output_path, 'w') as f:
        f.write(source_code)


def verify_modifications(source_code: str, expected_float_vars: List[str]) -> bool:
    """Verify that variables were actually changed to float"""
    if not expected_float_vars:
        return True
    
    for var in expected_float_vars:
        # Check if "float var" appears in the code
        pattern = rf'\bfloat\s+{var}\b'
        if not re.search(pattern, source_code):
            print(f"    ⚠️  WARNING: Variable '{var}' not changed to float!")
            return False
    
    return True


# ============================================================================
# COMPILATION
# ============================================================================

def compile_verificarlo(source_path: Path, 
                       binary_path: Path,
                       opt_level: str,
                       use_fastmath: bool,
                       timeout: int = 60) -> Tuple[bool, str]:
    """
    Compile with verificarlo
    Returns: (success, error_message)
    """
    flags = [f'-{opt_level}', '--ddebug', '-g']
    if use_fastmath:
        flags.append('-ffast-math')
    
    cmd = ['verificarlo'] + flags + [str(source_path), '-o', str(binary_path), '-lm']
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if result.returncode != 0:
            return False, result.stderr
        
        if not binary_path.exists():
            return False, f"Binary not created: {binary_path}"
        
        return True, ""
        
    except subprocess.TimeoutExpired:
        return False, "Compilation timeout"
    except Exception as e:
        return False, str(e)


# ============================================================================
# DELTA-DEBUG SCRIPTS
# ============================================================================

def create_ddrun_script(work_dir: Path, binary_path: Path):
    """Create ddRun script for Delta-Debug"""
    script_path = work_dir / "ddRun"
    
    content = f"""#!/bin/bash
OUTPUT_DIR=$1
{binary_path} > $OUTPUT_DIR/res.dat 2>&1
"""
    
    with open(script_path, 'w') as f:
        f.write(content)
    
    os.chmod(script_path, 0o755)


def create_ddcmp_script(work_dir: Path, max_deviation: float = 1e-6):
    """Create ddCmp script for Delta-Debug"""
    script_path = work_dir / "ddCmp"
    
    content = f"""#!/usr/bin/env python3
import sys
import numpy as np

MAX_DEVIATION = {max_deviation}
REFDIR = sys.argv[1]
CURDIR = sys.argv[2]

def read_output(DIR):
    with open(f"{{DIR}}/res.dat") as f:
        lines = f.read().strip().split('\\n')
        return float(lines[-1])

try:
    ref = read_output(REFDIR)
    cur = read_output(CURDIR)
    
    deviation = np.std([ref, cur]) / np.abs(np.mean([ref, cur]))
    
    with open(f"{{CURDIR}}/res.stat", 'w') as f:
        f.write(f"reference = {{ref}} current = {{cur}} deviation = {{deviation}}\\n")
    
    sys.exit(0 if deviation < MAX_DEVIATION else 1)
    
except Exception as e:
    with open(f"{{CURDIR}}/res.stat", 'w') as f:
        f.write(f"ERROR: {{e}}\\n")
    sys.exit(1)
"""
    
    with open(script_path, 'w') as f:
        f.write(content)
    
    os.chmod(script_path, 0o755)


# ============================================================================
# DELTA-DEBUG EXECUTION
# ============================================================================

def run_delta_debug(work_dir: Path,
                   backend_config: str,
                   timeout: int = 600) -> Tuple[bool, str]:
    """
    Run vfc_ddebug
    Returns: (success, output)
    """
    env = os.environ.copy()
    env['VFC_BACKENDS'] = backend_config
    
    # Clean previous results
    dd_dir = work_dir / "dd.line"
    if dd_dir.exists():
        shutil.rmtree(dd_dir)
    
    try:
        result = subprocess.run(
            ['vfc_ddebug', './ddRun', './ddCmp'],
            cwd=str(work_dir),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        success = result.returncode == 0 and "failed" not in result.stdout.lower()
        return success, result.stdout + "\n" + result.stderr
        
    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)


def parse_dd_output(dd_dir: Path) -> List[int]:
    """
    Parse Delta-Debug output to get unstable line numbers
    
    According to tutorial:
    - rddmin-cmp/dd.line.exclude contains UNSTABLE instructions
    - ddmin{0,1,...}/dd.line.include contains UNSTABLE instructions per set
    """
    unstable_lines = set()
    
    # Primary location: rddmin-cmp/dd.line.exclude
    exclude_file = dd_dir / "rddmin-cmp" / "dd.line.exclude"
    if exclude_file.exists():
        unstable_lines.update(extract_line_numbers(exclude_file))
    
    return sorted(unstable_lines)


def extract_line_numbers(file_path: Path) -> List[int]:
    """Extract line numbers from DD output file using cat command"""
    line_numbers = []
    
    try:
        # Run cat command and capture output
        result = subprocess.run(
            ['cat', str(file_path)],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Process each line of output
        for line in result.stdout.splitlines():
            try:
                # Get the number after the last colon
                line_num = int(line.split(':')[-1])
                line_numbers.append(line_num)
            except (ValueError, IndexError):
                continue
                
        return sorted(line_numbers)
        
    except subprocess.CalledProcessError:
        return []


# ============================================================================
# EXPERIMENT ORCHESTRATION
# ============================================================================

def run_single_experiment(config_name: str,
                         float_vars: List[str],
                         opt_level: str,
                         use_fastmath: bool,
                         source_code: str,
                         output_dir: Path,
                         mca_samples: int) -> Dict:
    """Run one complete experiment"""
    
    print(f"\n{'='*60}")
    print(f"Config: {config_name} | {opt_level} | fastmath={use_fastmath}")
    print(f"{'='*60}")
    
    # Create work directory
    fastmath_str = "fastmath" if use_fastmath else "nofastmath"
    work_dir = output_dir / f"{config_name}_{opt_level}_{fastmath_str}"
    work_dir.mkdir(exist_ok=True, parents=True)
    
    result = {
        'config': config_name,
        'float_vars': float_vars,
        'opt_level': opt_level,
        'fastmath': use_fastmath,
        'work_dir': str(work_dir)
    }
    
    # Modify source
    print(f"  Modifying variables: {float_vars if float_vars else 'none'}")
    modified_source = modify_variable_types(source_code, float_vars)
    
    # Verify modifications
    if not verify_modifications(modified_source, float_vars):
        result['status'] = 'modification_failed'
        return result
    
    # Write modified source
    source_path = work_dir / "archimedes_modified.c"
    write_source(modified_source, source_path)
    print(f"  ✓ Modified source written")
    
    # Compile
    binary_path = work_dir / "archimedes_bin"
    print(f"  Compiling with -{opt_level}{'  -ffast-math' if use_fastmath else ''}")
    success, error = compile_verificarlo(source_path, binary_path, opt_level, use_fastmath)
    
    if not success:
        print(f"  ✗ Compilation failed: {error}")
        result['status'] = 'compilation_failed'
        result['error'] = error
        return result
    
    print(f"  ✓ Compilation successful")
    
    # Create DD scripts
    create_ddrun_script(work_dir, binary_path)
    create_ddcmp_script(work_dir)
    print(f"  ✓ DD scripts created")
    
    # Run Delta-Debug
    dd_modes = [
        ('rr', 'libinterflop_mca.so -m rr --precision-binary64=53'),
        ('mca', 'libinterflop_mca.so -m mca --precision-binary64=53'),
    ]
    
    dd_results = []
    for mode_name, backend in dd_modes:
        print(f"  Running Delta-Debug ({mode_name})...")
        success, output = run_delta_debug(work_dir, backend)
        
        if success:
            dd_dir = work_dir / "dd.line"
            unstable_lines = parse_dd_output(dd_dir)
            print(f"    ✓ Found {len(unstable_lines)} unstable line(s): {unstable_lines}")
            
            dd_results.append({
                'mode': mode_name,
                'success': True,
                'unstable_lines': unstable_lines
            })
        else:
            print(f"    ✗ Failed: {output[:100]}")
            dd_results.append({
                'mode': mode_name,
                'success': False,
                'unstable_lines': []
            })
    
    result['delta_debug'] = dd_results
    
    result['status'] = 'success'
    return result


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def run_analysis(mode='full', output_dir='analysis_results', variable: Optional[str]=None):
    """Main analysis function"""
    
    # Setup
    config = AnalysisConfig(mode, variable)
    
    if not str(output_dir).startswith('/workdir'):
        output_dir = f"/workdir/{output_dir}"
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Find and read source
    source_path = find_archimedes_source()
    print(f"📄 Using source: {source_path}")
    source_code = read_source(source_path)
    
    # Results storage
    results = {
        'timestamp': datetime.now().isoformat(),
        'mode': mode,
        'experiments': []
    }
    
    # Run experiments
    total = len(config.configs) * len(config.opt_levels) * len(config.fastmath_options)
    print(f"\n🚀 Running {total} experiments in {mode} mode\n")
    
    for config_name, float_vars in config.configs:
        for opt_level in config.opt_levels:
            for use_fastmath in config.fastmath_options:
                
                result = run_single_experiment(
                    config_name, float_vars, opt_level, use_fastmath,
                    source_code, output_dir, config.mca_samples
                )
                
                results['experiments'].append(result)
                
                # Save incrementally
                with open(output_dir / "results.json", 'w') as f:
                    json.dump(results, f, indent=2)
    
    print(f"\n✅ Analysis complete! Results saved to: {output_dir}")
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['minimal','full'], default='full')
    parser.add_argument('--minimal', action='store_true')
    parser.add_argument('variable', nargs='?', default=None,
                       help='Variable name for single variable analysis')
    
    args = parser.parse_args()
    
    if args.minimal:
        mode = 'minimal'
    elif args.variable is not None:
        mode = 'single'
        run_analysis(mode=mode, variable=args.variable)
    else:
        mode = args.mode
    
    run_analysis(mode=mode)