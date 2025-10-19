#!/usr/bin/env python3
"""
Step 3: Compile - SIMPLIFIED
Always compiles with: O0, O1, O2, O3, with and without -ffast-math
"""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from utils.compiler import VerificarloCompiler, CompilationConfig


def main():
    parser = argparse.ArgumentParser(description='Compile all variants')
    parser.add_argument('--variants', required=True, help='Variants manifest')
    parser.add_argument('--output', required=True, help='Output directory')
    
    args = parser.parse_args()
    
    with open(args.variants, 'r') as f:
        variant_manifest = json.load(f)
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Fixed compilation matrix
    OPT_LEVELS = ['O0', 'O1', 'O2', 'O3']
    FASTMATH_OPTIONS = [False, True]
    EXTRA_FLAGS = ['-lm']
    
    total_variants = len(variant_manifest['variants'])
    total_configs = total_variants * len(OPT_LEVELS) * len(FASTMATH_OPTIONS)
    
    print(f"🔨 Compiling {total_variants} variant(s)")
    print(f"   Optimization levels: {OPT_LEVELS}")
    print(f"   Fast-math: {FASTMATH_OPTIONS}")
    print(f"   Total compilations: {total_configs}\n")
    
    compiler = VerificarloCompiler()
    
    compilation_results = []
    success_count = 0
    current = 0
    
    for variant in variant_manifest['variants']:
        variant_name = variant['name']
        source_path = Path(variant['source_path'])
        
        for opt_level in OPT_LEVELS:
            for use_fastmath in FASTMATH_OPTIONS:
                current += 1
                
                fastmath_str = 'fastmath' if use_fastmath else 'nofastmath'
                binary_dir = output_dir / variant_name / opt_level / fastmath_str
                binary_dir.mkdir(parents=True, exist_ok=True)
                binary_path = binary_dir / 'binary'
                
                config_id = f"{variant_name}_{opt_level}_{fastmath_str}"
                print(f"   [{current:3d}/{total_configs}] {config_id}...", end=' ')
                
                # Build the command string for display
                flags = [f'-{opt_level}', '-g', '--ddebug']
                if use_fastmath:
                    flags.append('-ffast-math')
                flags.extend(EXTRA_FLAGS)
                
                cmd_str = f"verificarlo {' '.join(flags)} {source_path} -o {binary_path}"
                print(f"\n      $ {cmd_str}")
                print(f"      ", end='')
                
                config = CompilationConfig(
                    source_path=source_path,
                    output_path=binary_path,
                    opt_level=opt_level,
                    use_fastmath=use_fastmath,
                    extra_flags=EXTRA_FLAGS
                )
                
                result = compiler.compile(config)
                
                if result.success:
                    print("✓")
                    success_count += 1
                else:
                    print(f"✗ {result.error_message}")
                
                compilation_results.append({
                    'variant_name': variant_name,
                    'variant_id': variant['id'],
                    'modified_vars': variant['modified_vars'],
                    'opt_level': opt_level,
                    'fastmath': use_fastmath,
                    'config_id': config_id,
                    'binary_dir': str(binary_dir),
                    **result.to_dict()
                })
    
    # Save manifest
    manifest_path = output_dir / 'manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump({
            'source_variants': args.variants,
            'total_compilations': total_configs,
            'successful': success_count,
            'failed': total_configs - success_count,
            'compilations': compilation_results
        }, f, indent=2)
    
    print(f"\n✓ Compilation: {success_count}/{total_configs} successful")
    print(f"✓ Manifest for variant compilation: {manifest_path}")


if __name__ == '__main__':
    main()