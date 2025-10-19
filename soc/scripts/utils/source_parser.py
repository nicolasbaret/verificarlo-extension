#!/usr/bin/env python3
"""
Source code parsing utilities for C files
Extracts floating-point variable information
"""

import re
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class Variable:
    """Represents a floating-point variable in C code"""
    name: str
    type: str  # 'float' or 'double'
    line: int
    scope: str  # 'function_name' or 'global'
    declaration: str  # The full declaration line
    

class CSourceParser:
    """Parse C source files to extract floating-point variables"""
    
    # Regex patterns
    FUNCTION_PATTERN = re.compile(
        r'^\s*(?:static\s+)?(?:inline\s+)?'
        r'(?:void|int|float|double|char|long|short|unsigned|signed|\w+)\s+'
        r'(\w+)\s*\([^)]*\)\s*\{',
        re.MULTILINE
    )
    
    VAR_PATTERN = re.compile(
        r'^\s*(float|double)\s+'
        r'([a-zA-Z_][a-zA-Z0-9_]*(?:\s*,\s*[a-zA-Z_][a-zA-Z0-9_]*)*)'
        r'\s*([;=])',
        re.MULTILINE
    )
    
    def __init__(self, source_path: Path):
        self.source_path = Path(source_path)
        self.source_code = self._read_source()
        self.lines = self.source_code.split('\n')
        
    def _read_source(self) -> str:
        """Read source file, removing comments"""
        with open(self.source_path, 'r') as f:
            content = f.read()
        
        # Remove single-line comments
        content = re.sub(r'//.*', '', content)
        # Remove multi-line comments
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        
        return content
    
    def find_functions(self) -> List[Tuple[str, int]]:
        """Find all function definitions"""
        functions = []
        for match in self.FUNCTION_PATTERN.finditer(self.source_code):
            func_name = match.group(1)
            line_num = self.source_code[:match.start()].count('\n') + 1
            functions.append((func_name, line_num))
        return functions
    
    def find_function_scope(self, func_name: str) -> Tuple[int, int]:
        """Find line range of a function (start, end)"""
        # Find function start
        pattern = re.compile(
            rf'^\s*(?:static\s+)?(?:inline\s+)?'
            rf'(?:\w+\s+)+{func_name}\s*\([^)]*\)\s*\{{',
            re.MULTILINE
        )
        
        match = pattern.search(self.source_code)
        if not match:
            return (0, len(self.lines))
        
        start_line = self.source_code[:match.start()].count('\n') + 1
        
        # Find matching closing brace
        brace_count = 0
        in_function = False
        end_line = start_line
        
        for i, line in enumerate(self.lines[start_line-1:], start=start_line):
            if '{' in line:
                brace_count += line.count('{')
                in_function = True
            if '}' in line:
                brace_count -= line.count('}')
            
            if in_function and brace_count == 0:
                end_line = i
                break
        
        return (start_line, end_line)
    
    def extract_variables(self, 
                         function_name: Optional[str] = None,
                         include_params: bool = True) -> List[Variable]:
        """Extract all float/double variables from source or specific function"""
        variables = []
        
        # Determine scope to analyze
        if function_name:
            start_line, end_line = self.find_function_scope(function_name)
            scope = function_name
        else:
            start_line, end_line = 0, len(self.lines)
            scope = 'global'
        
        # Search for variable declarations
        for i in range(start_line - 1, min(end_line, len(self.lines))):
            line = self.lines[i]
            line_num = i + 1
            
            # Match variable declarations
            match = self.VAR_PATTERN.search(line)
            if match:
                var_type = match.group(1)  # float or double
                var_names_str = match.group(2)  # Can be multiple: "a, b, c"
                
                # Handle multiple declarations: "float a, b, c;"
                var_names = [name.strip() for name in var_names_str.split(',')]
                
                for var_name in var_names:
                    # Clean up variable name (remove initializers)
                    var_name = var_name.split('=')[0].strip()
                    
                    variables.append(Variable(
                        name=var_name,
                        type=var_type,
                        line=line_num,
                        scope=scope,
                        declaration=line.strip()
                    ))
        
        return variables
    
    def get_variable_info(self, function_name: Optional[str] = None) -> Dict:
        """Get complete variable information as dictionary"""
        variables = self.extract_variables(function_name)
        
        return {
            'source_file': str(self.source_path),
            'function': function_name or 'global',
            'variables': [asdict(v) for v in variables],
            'original_types': {v.name: v.type for v in variables}
        }


class SourceModifier:
    """Modify C source code to change variable types"""
    
    def __init__(self, source_code: str):
        self.source_code = source_code
        self.lines = source_code.split('\n')
        self.modified_code = source_code  # Track modified code
    
    def change_variable_types(self, 
                             variables_to_modify: List[str],
                             target_type: str = 'float') -> str:
        """
        Change specified variables to target type
        
        Args:
            variables_to_modify: List of variable names to change
            target_type: Type to change to ('float' or 'double')
        
        Returns:
            Modified source code
        """
        if not variables_to_modify:
            return self.source_code
        
        modified_lines = []
        
        for line in self.lines:
            modified_line = line
            
            for var_name in variables_to_modify:
                # Pattern 1: "double var;" or "double var,"
                modified_line = re.sub(
                    rf'\b(float|double)\s+{var_name}\s*([,;])',
                    rf'{target_type} {var_name}\2',
                    modified_line
                )
                
                # Pattern 2: "double var ="
                modified_line = re.sub(
                    rf'\b(float|double)\s+{var_name}\s*=',
                    rf'{target_type} {var_name} =',
                    modified_line
                )
            
            modified_lines.append(modified_line)
        
        self.modified_code = '\n'.join(modified_lines)  # Store modified code
        return self.modified_code
    
    def verify_modifications(self, 
                            expected_vars: List[str],
                            expected_type: str = 'float') -> Tuple[bool, List[str]]:
        """
        Verify that variables were actually changed
        
        Returns:
            (all_success, list_of_failed_vars)
        """
        failed = []
        
        # Check the MODIFIED code, not the original
        for var in expected_vars:
            pattern = rf'\b{expected_type}\s+{var}\b'
            if not re.search(pattern, self.modified_code):  # Changed from self.source_code
                failed.append(var)
        
        return len(failed) == 0, failed


def test_parser():
    """Test the parser with a sample C code"""
    sample = """
// Sample C code
#include <math.h>

double global_var = 1.0;

double my_function(int n) {
    float ti;
    double tii, fact;
    double res = 0.0;
    
    for (int i = 0; i < n; i++) {
        double s = sqrt(ti * ti + 1);
        tii = (s - 1) / ti;
    }
    
    return res;
}
"""
    
    # Write to temp file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
        f.write(sample)
        temp_path = f.name
    
    try:
        parser = CSourceParser(temp_path)
        
        print("Functions found:")
        for func, line in parser.find_functions():
            print(f"  {func} at line {line}")
        
        print("\nVariables in my_function:")
        vars_info = parser.get_variable_info('my_function')
        for var in vars_info['variables']:
            print(f"  {var['type']} {var['name']} at line {var['line']}")
        
        print("\nTesting modification:")
        modifier = SourceModifier(sample)
        modified = modifier.change_variable_types(['ti', 'tii'], 'float')
        print("Modified code:")
        print(modified)
        
        success, failed = modifier.verify_modifications(['ti', 'tii'], 'float')
        print(f"\nVerification: {'✓' if success else '✗'}")
        if failed:
            print(f"Failed to modify: {failed}")
    
    finally:
        Path(temp_path).unlink()


if __name__ == '__main__':
    test_parser()