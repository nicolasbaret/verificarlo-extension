#!/usr/bin/env python3
"""
Extract and display relative error from Verificarlo CI results
"""
import pandas as pd
import numpy as np
import glob
import os

def extract_results():
    # Find all .vfcrun.h5 files
    files = glob.glob("*.vfcrun.h5")
    
    if not files:
        print("❌ No .vfcrun.h5 files found!")
        print(f"   Current directory: {os.getcwd()}")
        return
    
    print(f"\n{'='*100}")
    print(f"  Verificarlo Relative Error Analysis")
    print(f"{'='*100}\n")
    
    all_results = []
    
    for filename in files:
        try:
            # Try reading as pandas DataFrame (vfc_ci format)
            data_df = pd.read_hdf(filename, key='data')
            
            # Extract relevant columns
            for idx, row in data_df.iterrows():
                test_name = idx[0] if isinstance(idx, tuple) else 'unknown'
                var_name = idx[1] if isinstance(idx, tuple) and len(idx) > 1 else str(idx)
                backend_name = idx[2] if isinstance(idx, tuple) and len(idx) > 2 else 'default'
                
                # Get statistics
                mean = row.get('mu', np.nan)
                std = row.get('sigma', np.nan)
                
                if not np.isnan(mean) and not np.isnan(std):
                    rel_error = std / abs(mean) if mean != 0 else float('inf')
                    
                    all_results.append({
                        'test': test_name,
                        'variable': var_name,
                        'backend': backend_name,
                        'mean': mean,
                        'std': std,
                        'rel_error': rel_error,
                        'min': row.get('min', np.nan),
                        'max': row.get('max', np.nan),
                        'n_samples': row.get('nsamples', 0)
                    })
        
        except Exception as e:
            print(f"⚠️  Error reading {filename} as pandas: {e}")
            print("    Trying alternative method...")
            
            # Fallback: try direct HDF5 reading
            import h5py
            with h5py.File(filename, 'r') as f:
                print(f"    HDF5 keys: {list(f.keys())}")
    
    if not all_results:
        print("❌ No results found in HDF5 files!")
        print("\nTrying to inspect file structure...")
        import h5py
        with h5py.File(files[0], 'r') as f:
            print(f"\nTop-level keys: {list(f.keys())}")
            for key in f.keys():
                print(f"  {key}: {type(f[key])}")
        return
    
    # Sort by variable name
    all_results.sort(key=lambda x: (x['test'], x['variable']))
    
    # Display results
    print(f"{'Variable':<15} {'Backend':<35} {'Mean':<18} {'Std Dev':<18} {'Rel Error %':<12}")
    print("-" * 110)
    
    for r in all_results:
        rel_pct = r['rel_error'] * 100
        backend_short = r['backend'][:33] if len(r['backend']) > 33 else r['backend']
        print(f"{r['variable']:<15} {backend_short:<35} {r['mean']:<18.10e} {r['std']:<18.10e} {rel_pct:<12.6f}%")
    
    print(f"\n{'='*110}")
    print(f"\n📊 Summary Statistics:")
    print(f"   Total variables analyzed: {len(all_results)}")
    
    if all_results:
        rel_errors = [r['rel_error'] for r in all_results if not np.isinf(r['rel_error'])]
        if rel_errors:
            print(f"   Average relative error:   {np.mean(rel_errors):.6e} ({np.mean(rel_errors)*100:.6f}%)")
            print(f"   Min relative error:       {np.min(rel_errors):.6e} ({np.min(rel_errors)*100:.6f}%)")
            print(f"   Max relative error:       {np.max(rel_errors):.6e} ({np.max(rel_errors)*100:.6f}%)")
            
            # Identify most/least stable points
            sorted_by_error = sorted(all_results, key=lambda x: x['rel_error'])
            print(f"\n✅ Most stable point:  {sorted_by_error[0]['variable']} (rel error: {sorted_by_error[0]['rel_error']:.6e})")
            print(f"⚠️  Least stable point: {sorted_by_error[-1]['variable']} (rel error: {sorted_by_error[-1]['rel_error']:.6e})")
    
    print(f"\n{'='*110}\n")
    
    # Export to CSV
    csv_file = "relative_errors.csv"
    with open(csv_file, 'w') as f:
        f.write("test,variable,backend,mean,std_dev,rel_error,rel_error_pct,min,max,n_samples\n")
        for r in all_results:
            f.write(f"{r['test']},{r['variable']},{r['backend']},{r['mean']:.10e},{r['std']:.10e},"
                   f"{r['rel_error']:.10e},{r['rel_error']*100:.6f},{r['min']:.10e},{r['max']:.10e},{r['n_samples']}\n")
    
    print(f"📄 Results also saved to: {csv_file}")
    print(f"   (You can open this CSV in Excel or any spreadsheet program)\n")

if __name__ == "__main__":
    extract_results()
