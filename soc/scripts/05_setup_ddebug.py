#!/usr/bin/env python3
"""
Step 5: Setup DD - SIMPLIFIED
Fixed thresholds, no config needed
"""

import argparse
import json
from pathlib import Path


def create_ddrun_script(work_dir: Path, binary_path: Path):
    script = work_dir / "ddRun"
    script.write_text(f"""#!/bin/bash
OUTPUT_DIR=$1
{binary_path} > $OUTPUT_DIR/res.dat 2>&1
""")
    script.chmod(0o755)


def create_ddcmp_script(work_dir: Path, threshold: float):
    script = work_dir / "ddCmp"
    script.write_text(f"""#!/usr/bin/env python3
#
# ddCmp: compares the reference run and a current run, returns with success if
# there is no numerical deviation higher than the threshold.
#

import sys
import numpy as np

MAX_DEVIATION = {threshold}
REFDIR = sys.argv[1]
CURDIR = sys.argv[2]

def read_output(DIR):
    with open("{{}}/res.dat".format(DIR)) as f:
        lines = f.read().strip().split('\\n')
        return float(lines[-1])  # ← Take only the LAST line

# Read reference and current outputs
ref = read_output(REFDIR)
cur = read_output(CURDIR)

# Compute the deviation
deviation = np.std([ref, cur])/np.abs(np.mean([ref, cur]))  # dev = sigma / | mu |

# Write log to CURDIR/res.stat
with open("{{}}/res.stat".format(CURDIR), 'w') as f:
    f.write("reference = {{}} current = {{}} deviation = {{}}\\n".format(
        ref, cur, deviation))

# Fail if the deviation is higher than threshold
sys.exit(0 if deviation < MAX_DEVIATION else 1)
""")
    script.chmod(0o755)


def main():
    parser = argparse.ArgumentParser(description='Setup Delta-Debug')
    parser.add_argument('--validation', required=True, help='Validation manifest')
    parser.add_argument('--output', required=True, help='Output directory')
    
    args = parser.parse_args()
    
    with open(args.validation, 'r') as f:
        validation_manifest = json.load(f)
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    valid_validations = [
        v for v in validation_manifest['validations']
        if v['valid'] and not v.get('skip_ddebug', False)
    ]
    
    print(f"⚙️  Setting up DD for {len(valid_validations)} valid binary(ies)")
    
    dd_setups = []
    
    for idx, validation in enumerate(valid_validations):
        config_id = validation['config_id']
        binary_path = Path(validation['binary_path'])
        modified_vars = validation.get('modified_vars', [])
        
        dd_workspace = output_dir / config_id
        dd_workspace.mkdir(parents=True, exist_ok=True)
        
        # Use stricter threshold for floats
        threshold = 1e-2 if modified_vars else 1e-6
        
        create_ddrun_script(dd_workspace, binary_path)
        create_ddcmp_script(dd_workspace, threshold)
        
        dd_setups.append({
            'config_id': config_id,
            'variant_name': validation['variant_name'],
            'modified_vars': modified_vars,
            'opt_level': validation['opt_level'],
            'fastmath': validation['fastmath'],
            'binary_path': str(binary_path),
            'dd_workspace': str(dd_workspace),
            'threshold': threshold
        })
        
        print(f"   [{idx+1:3d}/{len(valid_validations)}] ✓ {config_id}")
    
    manifest_path = output_dir / 'manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump({
            'validation_manifest': args.validation,
            'total_setups': len(dd_setups),
            'setups': dd_setups
        }, f, indent=2)
    
    print(f"\n✓ DD setup complete: {len(dd_setups)} configuration(s)")
    print(f"✓ Manifest: {manifest_path}")


if __name__ == '__main__':
    main()