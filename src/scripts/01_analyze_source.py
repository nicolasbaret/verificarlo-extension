#!/usr/bin/env python3
"""
Step 1: Analyze C source file and extract floating-point variables
"""

import argparse
import json
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from utils.source_parser import CSourceParser


def main():
    parser = argparse.ArgumentParser(
        description='Analyze C source and extract floating-point variables'
    )
    parser.add_argument('--source', required=True, help='Path to C source file')
    parser.add_argument('--function', default=None, 
                       help='Target function name (default: analyze all)')
    parser.add_argument('--output', required=True, 
                       help='Output JSON manifest path')
    
    args = parser.parse_args()
    
    source_path = Path(args.source)
    output_path = Path(args.output)
    
    if not source_path.exists():
        print(f"Error: Source file not found: {source_path}")
        sys.exit(1)
    
    print(f"📄 Analyzing: {source_path}")
    
    # Parse source
    try:
        c_parser = CSourceParser(source_path)
        
        # Find functions
        functions = c_parser.find_functions()
        print(f"   Found {len(functions)} function(s):")
        for func, line in functions:
            print(f"     - {func} (line {line})")
        
        # Extract variables
        var_info = c_parser.get_variable_info(args.function)
        
        print(f"\n   Found {len(var_info['variables'])} floating-point variable(s):")
        for var in var_info['variables']:
            print(f"     - {var['type']:6} {var['name']:10} (line {var['line']})")
        
        # Save manifest
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(var_info, f, indent=2)
        
        print(f"\n✓ Manifest saved to: {output_path}")
        
    except Exception as e:
        print(f"Error analyzing source: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()