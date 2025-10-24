#!/usr/bin/env python3
"""
Compilation utilities for verificarlo
"""

import subprocess
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass, asdict


@dataclass
class CompilationConfig:
    """Configuration for a single compilation"""
    source_path: Path
    output_path: Path
    opt_level: str = 'O0'
    use_fastmath: bool = False
    extra_flags: List[str] = None
    timeout: int = 60
    
    def __post_init__(self):
        if self.extra_flags is None:
            self.extra_flags = []


@dataclass
class CompilationResult:
    """Result of a compilation attempt"""
    success: bool
    binary_path: Optional[Path]
    returncode: int
    stdout: str
    stderr: str
    compile_time: float
    error_message: Optional[str] = None
    
    def to_dict(self):
        d = asdict(self)
        if d['binary_path']:
            d['binary_path'] = str(d['binary_path'])
        return d


class VerificarloCompiler:
    """Wrapper for verificarlo compilation"""
    
    def __init__(self, verificarlo_path: str = 'verificarlo'):
        self.verificarlo_path = verificarlo_path
        self._check_verificarlo()
    
    def _check_verificarlo(self):
        """Verify that verificarlo is available"""
        try:
            subprocess.run(
                [self.verificarlo_path, '--version'],
                capture_output=True,
                check=True,
                timeout=5
            )
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            raise RuntimeError(
                f"verificarlo not found or not working: {self.verificarlo_path}"
            )
    
    def compile(self, config: CompilationConfig) -> CompilationResult:
        """
        Compile a source file with verificarlo
        
        Args:
            config: Compilation configuration
            
        Returns:
            CompilationResult with details
        """
        import time
        
        # Build command
        flags = [f'-{config.opt_level}']
        
        if config.use_fastmath:
            flags.append('-ffast-math')
        
        # Always add debug symbols for Delta-Debug
        flags.extend(['-g', '--ddebug'])
        
        flags.extend(config.extra_flags)
        
        cmd = [
            self.verificarlo_path,
            *flags,
            str(config.source_path),
            '-o', str(config.output_path)
        ]
        
        # Ensure output directory exists
        config.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Compile
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=config.timeout
            )
            
            compile_time = time.time() - start_time
            
            # Check success
            if result.returncode == 0 and config.output_path.exists():
                return CompilationResult(
                    success=True,
                    binary_path=config.output_path,
                    returncode=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    compile_time=compile_time
                )
            else:
                return CompilationResult(
                    success=False,
                    binary_path=None,
                    returncode=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    compile_time=compile_time,
                    error_message=result.stderr or "Binary not created"
                )
        
        except subprocess.TimeoutExpired:
            return CompilationResult(
                success=False,
                binary_path=None,
                returncode=-1,
                stdout="",
                stderr="",
                compile_time=config.timeout,
                error_message="Compilation timeout"
            )
        
        except Exception as e:
            return CompilationResult(
                success=False,
                binary_path=None,
                returncode=-1,
                stdout="",
                stderr="",
                compile_time=time.time() - start_time,
                error_message=str(e)
            )
    
    def compile_batch(self, 
                     configs: List[CompilationConfig],
                     parallel: bool = False,
                     max_workers: int = 4) -> List[CompilationResult]:
        """
        Compile multiple configurations
        
        Args:
            configs: List of compilation configurations
            parallel: Whether to compile in parallel
            max_workers: Number of parallel workers
            
        Returns:
            List of CompilationResults
        """
        if not parallel:
            return [self.compile(config) for config in configs]
        
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        results = [None] * len(configs)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_idx = {
                executor.submit(self.compile, config): idx
                for idx, config in enumerate(configs)
            }
            
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                results[idx] = future.result()
        
        return results


def test_compiler():
    """Test the compiler with a simple program"""
    import tempfile
    
    # Create a simple test program
    test_code = """
#include <stdio.h>
#include <math.h>

int main() {
    double x = 1.0;
    double y = sqrt(x);
    printf("%f\\n", y);
    return 0;
}
"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        source = tmpdir / "test.c"
        source.write_text(test_code)
        
        binary = tmpdir / "test_bin"
        
        compiler = VerificarloCompiler()
        
        config = CompilationConfig(
            source_path=source,
            output_path=binary,
            opt_level='O0',
            extra_flags=['-lm']
        )
        
        print("Compiling test program...")
        result = compiler.compile(config)
        
        if result.success:
            print(f"✓ Compilation successful in {result.compile_time:.2f}s")
            print(f"  Binary: {result.binary_path}")
        else:
            print(f"✗ Compilation failed")
            print(f"  Error: {result.error_message}")
            print(f"  Stderr: {result.stderr}")


if __name__ == '__main__':
    test_compiler()