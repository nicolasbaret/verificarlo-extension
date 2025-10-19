#!/usr/bin/env python3
"""
Step 2: Generate variants - SIMPLIFIED
Only two modes: single variable or all variables
"""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from utils.source_parser import CSourceParser, SourceModifier


def main():
    parser = argparse.ArgumentParser(description='Generate source variants')
    parser.add_argument('--manifest', required=True, help='Manifest from step 1')
    parser.add_argument('--mode', required=True, choices=['single', 'all'],
                       help='single: one variable | all: all variables')
    parser.add_argument('--variable', help='Variable name (required for single mode)')
    parser.add_argument('--output', required=True, help='Output directory')
    
    args = parser.parse_args()
    
    if args.mode == 'single' and not args.variable:
        print("Error: --variable required for single mode")
        sys.exit(1)
    
    # Load manifest
    with open(args.manifest, 'r') as f:
        manifest = json.load(f)
    
    source_path = Path(manifest['source_file'])
    all_variables = [v['name'] for v in manifest['variables']]
    
    # Read original source
    with open(source_path, 'r') as f:
        original_source = f.read()
    
    # Generate configurations based on mode
    if args.mode == 'single':
        if args.variable not in all_variables:
            print(f"Error: Variable '{args.variable}' not found")
            print(f"Available: {all_variables}")
            sys.exit(1)
        
        configs = [
            ('baseline_all_double', []),
            (f'{args.variable}_float', [args.variable])
        ]
        print(f"📦 Single variable mode: {args.variable}")
    else:
        configs = [('baseline_all_double', [])]
        for var in all_variables:
            configs.append((f'{var}_float', [var]))
        print(f"📦 All variables mode: {len(all_variables)} variables")
    
    output_dir = Path(args.output)
    variants = []
    
    print(f"   Generating {len(configs)} variant(s)...\n")
    
    for config_name, vars_to_modify in configs:
        print(f"   Creating: {config_name}")
        
        variant_dir = output_dir / config_name
        variant_dir.mkdir(parents=True, exist_ok=True)
        
        # Modify source
        modifier = SourceModifier(original_source)
        modified_source = modifier.change_variable_types(vars_to_modify, 'float')
        
        # Write
        variant_source = variant_dir / source_path.name
        with open(variant_source, 'w') as f:
            f.write(modified_source)
        
        # Verify
        success, failed = modifier.verify_modifications(vars_to_modify, 'float')
        if not success:
            print(f"     ⚠️  Failed to modify: {failed}")
        elif vars_to_modify:
            print(f"     ✓ Modified: {vars_to_modify}")
        
        variants.append({
            'id': f'variant_{len(variants):03d}',
            'name': config_name,
            'modified_vars': vars_to_modify,
            'source_path': str(variant_source),
            'variant_dir': str(variant_dir)
        })
    
    # Save manifest
    manifest_out = output_dir / 'manifest.json'
    with open(manifest_out, 'w') as f:
        json.dump({
            'original_source': str(source_path),
            'mode': args.mode,
            'total_variants': len(variants),
            'variants': variants
        }, f, indent=2)
    
    print(f"\n✓ Generated {len(variants)} variant(s)")
    print(f"✓ Manifest: {manifest_out}")


if __name__ == '__main__':
    main()