#!/usr/bin/env python3
"""
Delta-Debug output parsing utilities
"""

import re
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class DDLineResult:
    """Result from parsing a DD line output file"""
    address: str
    function: str
    file: str
    line: int
    
    @classmethod
    def from_line(cls, line: str) -> Optional['DDLineResult']:
        """
        Parse a line from DD output
        Format: "0x0000000000400e5c: archimedes at archimedes.c:16"
        """
        match = re.match(
            r'(0x[0-9a-fA-F]+):\s+(\w+)\s+at\s+([^:]+):(\d+)',
            line.strip()
        )
        
        if match:
            return cls(
                address=match.group(1),
                function=match.group(2),
                file=match.group(3),
                line=int(match.group(4))
            )
        return None


class DeltaDebugParser:
    """Parse Delta-Debug output files"""
    
    @staticmethod
    def parse_dd_line_file(file_path: Path) -> List[DDLineResult]:
        """
        Parse a dd.line file using cat command
        
        Args:
            file_path: Path to dd.line.include or dd.line.exclude file
            
        Returns:
            List of parsed line results
        """
        if not file_path.exists():
            return []
        
        try:
            result = subprocess.run(
                ['cat', str(file_path)],
                capture_output=True,
                text=True,
                check=True
            )
            
            lines = []
            for line in result.stdout.splitlines():
                parsed = DDLineResult.from_line(line)
                if parsed:
                    lines.append(parsed)
            
            return lines
        
        except subprocess.CalledProcessError:
            return []
    
    @staticmethod
    def find_unstable_lines(dd_dir: Path) -> List[int]:
        """
        Find unstable line numbers from Delta-Debug output
        
        The tutorial states that rddmin-cmp/dd.line.exclude contains
        the UNSTABLE instructions (union of all ddmin sets)
        
        Args:
            dd_dir: Path to dd.line directory
            
        Returns:
            Sorted list of unstable line numbers
        """
        unstable_lines = set()
        
        # Primary location: rddmin-cmp/dd.line.exclude
        exclude_file = dd_dir / "rddmin-cmp" / "dd.line.exclude"
        if exclude_file.exists():
            results = DeltaDebugParser.parse_dd_line_file(exclude_file)
            unstable_lines.update(r.line for r in results)
        
        # Also check individual ddmin sets for completeness
        for ddmin_dir in dd_dir.glob("ddmin*"):
            include_file = ddmin_dir / "dd.line.include"
            if include_file.exists():
                results = DeltaDebugParser.parse_dd_line_file(include_file)
                unstable_lines.update(r.line for r in results)
        
        return sorted(unstable_lines)
    
    @staticmethod
    def get_detailed_results(dd_dir: Path) -> Dict:
        """
        Get detailed Delta-Debug results including all sets
        
        Returns:
            Dictionary with:
            - unstable_lines: List of all unstable line numbers
            - ddmin_sets: List of minimal failing sets
            - stable_lines: Lines that are stable (from rddmin-cmp)
        """
        result = {
            'unstable_lines': [],
            'ddmin_sets': [],
            'stable_lines': [],
            'dd_dir': str(dd_dir)
        }
        
        if not dd_dir.exists():
            return result
        
        # Get unstable lines
        result['unstable_lines'] = DeltaDebugParser.find_unstable_lines(dd_dir)
        
        # Get individual ddmin sets
        for ddmin_dir in sorted(dd_dir.glob("ddmin*")):
            include_file = ddmin_dir / "dd.line.include"
            if include_file.exists():
                lines = DeltaDebugParser.parse_dd_line_file(include_file)
                result['ddmin_sets'].append({
                    'set_name': ddmin_dir.name,
                    'lines': [r.line for r in lines],
                    'details': [asdict(r) for r in lines]
                })
        
        # Get stable lines (complement)
        rddmin_cmp_dir = dd_dir / "rddmin-cmp"
        if rddmin_cmp_dir.exists():
            include_file = rddmin_cmp_dir / "dd.line.include"
            if include_file.exists():
                lines = DeltaDebugParser.parse_dd_line_file(include_file)
                result['stable_lines'] = [r.line for r in lines]
        
        return result


def test_parser():
    """Test the parser with sample DD output"""
    import tempfile
    
    sample_output = """0x0000000000400e5c: archimedes at archimedes.c:16
0x0000000000400e89: archimedes at archimedes.c:17
"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create sample DD output structure
        dd_dir = tmpdir / "dd.line"
        rddmin_dir = dd_dir / "rddmin-cmp"
        rddmin_dir.mkdir(parents=True)
        
        exclude_file = rddmin_dir / "dd.line.exclude"
        exclude_file.write_text(sample_output)
        
        # Test parsing
        print("Testing DD parser...")
        unstable = DeltaDebugParser.find_unstable_lines(dd_dir)
        print(f"Found unstable lines: {unstable}")
        
        detailed = DeltaDebugParser.get_detailed_results(dd_dir)
        print(f"Detailed results: {detailed}")


if __name__ == '__main__':
    test_parser()