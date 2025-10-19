#!/usr/bin/env python3
"""
Step 6: Run DD - SIMPLIFIED
Always runs: RR, MCA, Cancellation backends
"""

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from utils.dd_parser import DeltaDebugParser


def run_dd(dd_workspace: Path, backend_name: str, backend_config: str, timeout: int = 600):
    env = os.environ.copy()
    env['VFC_BACKENDS'] = backend_config
    
    dd_dir = dd_workspace / "dd.line"
    if dd_dir.exists():
        shutil.rmtree(dd_dir)
    
    try:
        result = subprocess.run(
            ['vfc_ddebug', './ddRun', './ddCmp'],
            cwd=str(dd_workspace),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        # DEBUG: Print output for first failure
        if result.returncode != 0:
            print(f"\n      DEBUG - vfc_ddebug failed:")
            print(f"      Return code: {result.returncode}")
            print(f"      Stderr (first 300 chars): {result.stderr[:300]}")
            print(f"      Stdout (first 300 chars): {result.stdout[:300]}")
        
        if result.returncode == 0 and dd_dir.exists():
            unstable_lines = DeltaDebugParser.find_unstable_lines(dd_dir)
            return {
                'backend': backend_name,
                'success': True,
                'unstable_lines': unstable_lines
            }
        
        # DD might have run but failed for some reason - check if dd.line exists anyway
        if dd_dir.exists():
            unstable_lines = DeltaDebugParser.find_unstable_lines(dd_dir)
            return {
                'backend': backend_name,
                'success': True,  # It ran, even if exit code != 0
                'unstable_lines': unstable_lines,
                'note': f'DD exited with code {result.returncode} but produced output'
            }
        
        return {'backend': backend_name, 'success': False, 'error': 'DD failed'}
    except subprocess.TimeoutExpired:
        return {'backend': backend_name, 'success': False, 'error': 'Timeout'}
    except Exception as e:
        return {'backend': backend_name, 'success': False, 'error': str(e)}


def main():
    parser = argparse.ArgumentParser(description='Run Delta-Debug')
    parser.add_argument('--setup', required=True, help='DD setup manifest')
    parser.add_argument('--output', required=True, help='Output JSON')
    
    args = parser.parse_args()
    
    with open(args.setup, 'r') as f:
        setup_manifest = json.load(f)
    
    # Fixed backends
    BACKENDS = [
        ('rr', 'libinterflop_mca.so -m rr --precision-binary64=53'),
        ('mca', 'libinterflop_mca.so -m mca --precision-binary64=53'),
        ('cancellation', 'libinterflop_cancellation.so')
    ]
    
    print(f"🔬 Running DD on {len(setup_manifest['setups'])} setup(s)")
    print(f"   Backends: {[b[0] for b in BACKENDS]}\n")
    
    all_results = []
    
    for idx, setup in enumerate(setup_manifest['setups']):
        config_id = setup['config_id']
        dd_workspace = Path(setup['dd_workspace'])
        
        print(f"   [{idx+1}/{len(setup_manifest['setups'])}] {config_id}")
        
        dd_results = []
        for backend_name, backend_config in BACKENDS:
            print(f"      {backend_name}...", end=' ')
            result = run_dd(dd_workspace, backend_name, backend_config)
            dd_results.append(result)
            
            if result['success']:
                print(f"✓ ({len(result['unstable_lines'])} lines)")
            else:
                print(f"✗")
        
        all_results.append({
            'config_id': config_id,
            'variant_name': setup['variant_name'],
            'modified_vars': setup['modified_vars'],
            'opt_level': setup['opt_level'],
            'fastmath': setup['fastmath'],
            'dd_results': dd_results
        })
    
    output_path = Path(args.output)
    with open(output_path, 'w') as f:
        json.dump({
            'setup_manifest': args.setup,
            'backends': [b[0] for b in BACKENDS],
            'total_configs': len(all_results),
            'results': all_results
        }, f, indent=2)
    
    print(f"\n✓ DD complete: {len(all_results)} configuration(s)")
    print(f"✓ Results: {output_path}")


if __name__ == '__main__':
    main()