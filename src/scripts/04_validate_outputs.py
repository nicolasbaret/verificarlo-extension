#!/usr/bin/env python3
"""
Step 4: Validate compiled binaries for NaN/Inf outputs
"""

import argparse
import json
import math
import os
import subprocess
from pathlib import Path
import sys
from typing import Tuple, Optional

sys.path.insert(0, str(Path(__file__).parent))


def run_binary(binary_path: Path, 
               program_args: list = None,
               timeout: int = 10) -> Tuple[bool, Optional[float], str, str]:
    """
    Run a binary with IEEE backend and capture output
    
    Returns:
        (success, output_value, stdout, stderr)
    """
    env = os.environ.copy()
    env['VFC_BACKENDS'] = 'libinterflop_ieee.so'
    
    cmd = [str(binary_path)]
    if program_args:
        cmd.extend(program_args)
    
    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        # Get the last line (assuming it's the final output)
        lines = result.stdout.strip().split('\n')
        if not lines or not lines[-1]:
            return False, None, result.stdout, result.stderr
        
        try:
            value = float(lines[-1])
            return True, value, result.stdout, result.stderr
        except ValueError:
            return False, None, result.stdout, result.stderr
    
    except subprocess.TimeoutExpired:
        return False, None, "", "Timeout"
    except Exception as e:
        return False, None, "", str(e)


def check_validity(value: float) -> Tuple[bool, str]:
    """
    Check if a value is valid (not NaN or Inf)
    
    Returns:
        (is_valid, reason)
    """
    if math.isnan(value):
        return False, "NaN"
    elif math.isinf(value):
        return False, "Inf"
    else:
        return True, "valid"


def main():
    parser = argparse.ArgumentParser(
        description='Validate binary outputs for NaN/Inf'
    )
    parser.add_argument('--binaries', required=True,
                       help='Compilation manifest from step 3')
    parser.add_argument('--args', nargs='*', default=[],
                       help='Program arguments')
    parser.add_argument('--timeout', type=int, default=10,
                       help='Timeout per binary (seconds)')
    parser.add_argument('--output', required=True,
                       help='Output validation JSON')
    
    args = parser.parse_args()
    
    # Load compilation manifest
    with open(args.binaries, 'r') as f:
        compilation_manifest = json.load(f)
    
    print(f"🔍 Validating {compilation_manifest['successful']} successful compilation(s)")
    
    validation_results = []
    valid_count = 0
    invalid_count = 0
    
    for idx, compilation in enumerate(compilation_manifest['compilations']):
        if not compilation['success']:
            # Skip failed compilations
            validation_results.append({
                **compilation,
                'validation_status': 'skipped_compilation_failed',
                'valid': False,
                'skip_ddebug': True
            })
            continue
        
        config_id = compilation['config_id']
        binary_path = Path(compilation['binary_path'])
        
        print(f"   [{idx+1:3d}/{len(compilation_manifest['compilations'])}] Testing: {config_id}")
        
        # Run binary
        success, value, stdout, stderr = run_binary(
            binary_path,
            args.args,
            args.timeout
        )
        
        if not success:
            print(f"            ✗ Execution failed")
            validation_results.append({
                **compilation,
                'validation_status': 'execution_failed',
                'valid': False,
                'skip_ddebug': True,
                'output_value': None,
                'stdout': stdout,
                'stderr': stderr
            })
            invalid_count += 1
            continue
        
        # Check validity
        is_valid, reason = check_validity(value)
        
        if is_valid:
            print(f"            ✓ Valid output: {value:.15e}")
            valid_count += 1
        else:
            print(f"            ✗ Invalid output: {reason}")
            invalid_count += 1
        
        validation_results.append({
            **compilation,
            'validation_status': 'completed',
            'valid': is_valid,
            'skip_ddebug': not is_valid,
            'output_value': str(value),
            'validity_reason': reason,
            'stdout': stdout,
            'stderr': stderr
        })
    
    # Save validation manifest
    output_manifest = {
        'compilation_manifest': args.binaries,
        'total_tested': len(compilation_manifest['compilations']),
        'valid': valid_count,
        'invalid': invalid_count,
        'validations': validation_results
    }
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(output_manifest, f, indent=2)
    
    print(f"\n✓ Validation complete: {valid_count} valid, {invalid_count} invalid")
    print(f"✓ Results saved to: {output_path}")


if __name__ == '__main__':
    main()