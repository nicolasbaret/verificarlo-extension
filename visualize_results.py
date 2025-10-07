#!/usr/bin/env python3
"""
Visualization and Reporting for Archimedes Analysis
Generates plots and comprehensive reports

Docker/Container Compatible Version
"""

import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
import sys

class AnalysisVisualizer:
    def __init__(self, results_file=None):
        # Auto-detect results file location
        if results_file is None:
            possible_paths = [
                "analysis_results/results.json",
                "/workdir/analysis_results/results.json",
                "./results.json",
            ]
            
            for path in possible_paths:
                if Path(path).exists():
                    results_file = path
                    break
            
            if results_file is None:
                raise FileNotFoundError(
                    "Could not find results.json. Please run archimedes_analyzer.py first.\n"
                    "Tried locations: " + ", ".join(possible_paths)
                )
        
        print(f"📊 Loading results from: {results_file}")
        
        with open(results_file, 'r') as f:
            self.results = json.load(f)
        
        # Set output directory relative to results file location
        results_path = Path(results_file)
        self.output_dir = results_path.parent / "plots"
        self.output_dir.mkdir(exist_ok=True)
        
        print(f"📁 Plots will be saved to: {self.output_dir}")
        
        # Set plotting style
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (12, 8)
    
    def prepare_dataframe(self):
        """
        Convert results to pandas DataFrame for analysis
        """
        rows = []
        
        for exp in self.results['experiments']:
            if exp['status'] != 'success':
                continue
            
            # Collect unstable lines from all DD modes
            all_unstable = set()
            dd_by_mode = {}
            for dd in exp['delta_debug']:
                if dd['success']:
                    all_unstable.update(dd['unstable_lines'])
                    dd_by_mode[dd['mode']] = dd['unstable_lines']
            
            row = {
                'config': exp['config'],
                'float_vars': ','.join(exp['float_vars']) if exp['float_vars'] else 'none',
                'num_float_vars': len(exp['float_vars']),
                'opt_level': exp['opt_level'],
                'fastmath': exp['fastmath'],
                'unstable_lines': ','.join(map(str, sorted(all_unstable))),
                'num_unstable': len(all_unstable),
                'sig_digits': exp['mca_analysis'].get('significant_digits'),
                'mean_pi': exp['mca_analysis'].get('mean'),
                'std_pi': exp['mca_analysis'].get('std'),
            }
            
            # Add per-mode unstable lines
            for mode in ['rr', 'pb', 'mca', 'cancel']:
                row[f'{mode}_unstable'] = ','.join(map(str, sorted(dd_by_mode.get(mode, []))))
                row[f'{mode}_num_unstable'] = len(dd_by_mode.get(mode, []))
            
            rows.append(row)
        
        return pd.DataFrame(rows)
    
    def plot_precision_heatmap(self, df):
        """
        Heatmap showing error across precision × optimization matrix
        """
        # Filter for no fastmath first
        df_no_fm = df[df['fastmath'] == False]
        
        # Create pivot table
        pivot = df_no_fm.pivot_table(
            values='sig_digits',
            index='config',
            columns='opt_level',
            aggfunc='mean'
        )
        
        plt.figure(figsize=(12, 10))
        sns.heatmap(pivot, annot=True, fmt='.2f', cmap='RdYlGn', 
                   cbar_kws={'label': 'Significant Digits'})
        plt.title('Significant Digits: Precision Config vs Optimization Level\n(without -ffast-math)', 
                 fontsize=14, fontweight='bold')
        plt.xlabel('Optimization Level', fontsize=12)
        plt.ylabel('Precision Configuration', fontsize=12)
        plt.tight_layout()
        plt.savefig(self.output_dir / 'precision_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ Generated: precision_heatmap.png")
    
    def plot_fastmath_comparison(self, df):
        """
        Compare impact of -ffast-math flag
        """
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # Plot 1: Significant digits with/without fastmath
        ax1 = axes[0, 0]
        df_grouped = df.groupby(['config', 'opt_level', 'fastmath'])['sig_digits'].mean().reset_index()
        
        configs = df_grouped['config'].unique()[:5]  # Show first 5 configs
        df_subset = df_grouped[df_grouped['config'].isin(configs)]
        
        sns.barplot(data=df_subset, x='config', y='sig_digits', hue='fastmath', ax=ax1)
        ax1.set_title('Impact of -ffast-math on Significant Digits', fontweight='bold')
        ax1.set_xlabel('Configuration')
        ax1.set_ylabel('Significant Digits')
        ax1.tick_params(axis='x', rotation=45)
        ax1.legend(title='Fast Math')
        
        # Plot 2: Number of unstable lines
        ax2 = axes[0, 1]
        sns.boxplot(data=df, x='fastmath', y='num_unstable', ax=ax2)
        ax2.set_title('Unstable Lines: Fast Math Impact', fontweight='bold')
        ax2.set_xlabel('Fast Math Enabled')
        ax2.set_ylabel('Number of Unstable Lines')
        
        # Plot 3: By optimization level
        ax3 = axes[1, 0]
        df_opt = df.groupby(['opt_level', 'fastmath'])['sig_digits'].mean().reset_index()
        sns.barplot(data=df_opt, x='opt_level', y='sig_digits', hue='fastmath', ax=ax3)
        ax3.set_title('Optimization Level vs Significant Digits', fontweight='bold')
        ax3.set_xlabel('Optimization Level')
        ax3.set_ylabel('Significant Digits')
        ax3.legend(title='Fast Math')
        
        # Plot 4: Standard deviation
        ax4 = axes[1, 1]
        df_std = df[df['std_pi'].notna()]
        sns.scatterplot(data=df_std, x='sig_digits', y='std_pi', 
                       hue='fastmath', style='opt_level', ax=ax4)
        ax4.set_title('Significant Digits vs Standard Deviation', fontweight='bold')
        ax4.set_xlabel('Significant Digits')
        ax4.set_ylabel('Standard Deviation of π')
        ax4.set_yscale('log')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'fastmath_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ Generated: fastmath_comparison.png")
    
    def plot_unstable_lines_frequency(self, df):
        """
        Bar chart showing which lines are most frequently unstable
        """
        # Extract all unstable line numbers
        line_counts = {}
        
        for unstable_str in df['unstable_lines']:
            if pd.isna(unstable_str) or unstable_str == '':
                continue
            
            lines = [int(x) for x in unstable_str.split(',')]
            for line in lines:
                line_counts[line] = line_counts.get(line, 0) + 1
        
        if not line_counts:
            print("⚠ No unstable lines found")
            return
        
        # Sort by frequency
        sorted_lines = sorted(line_counts.items(), key=lambda x: x[1], reverse=True)
        lines, counts = zip(*sorted_lines)
        
        plt.figure(figsize=(12, 6))
        plt.bar(range(len(lines)), counts, color='steelblue')
        plt.xticks(range(len(lines)), [f"Line {l}" for l in lines])
        plt.xlabel('Source Line Number', fontsize=12)
        plt.ylabel('Frequency (# of Experiments)', fontsize=12)
        plt.title('Unstable Instruction Frequency Across All Experiments', 
                 fontsize=14, fontweight='bold')
        plt.grid(axis='y', alpha=0.3)
        
        # Add count labels on bars
        for i, count in enumerate(counts):
            plt.text(i, count, str(count), ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'unstable_lines_frequency.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ Generated: unstable_lines_frequency.png")
        print(f"  Most unstable line: {sorted_lines[0][0]} (flagged {sorted_lines[0][1]} times)")
    
    def plot_precision_impact(self, df):
        """
        Show how number of float variables affects stability
        """
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        
        # Plot 1: Significant digits vs number of float vars
        ax1 = axes[0]
        df_grouped = df.groupby(['num_float_vars', 'opt_level'])['sig_digits'].mean().reset_index()
        
        for opt in df['opt_level'].unique():
            df_opt = df_grouped[df_grouped['opt_level'] == opt]
            ax1.plot(df_opt['num_float_vars'], df_opt['sig_digits'], 
                    marker='o', label=opt, linewidth=2)
        
        ax1.set_xlabel('Number of Float Variables', fontsize=12)
        ax1.set_ylabel('Average Significant Digits', fontsize=12)
        ax1.set_title('Precision Impact: Float Variables vs Accuracy', fontweight='bold')
        ax1.legend(title='Optimization')
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Number of unstable lines vs float vars
        ax2 = axes[1]
        sns.violinplot(data=df, x='num_float_vars', y='num_unstable', ax=ax2)
        ax2.set_xlabel('Number of Float Variables', fontsize=12)
        ax2.set_ylabel('Number of Unstable Lines', fontsize=12)
        ax2.set_title('Unstable Instructions vs Precision', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'precision_impact.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ Generated: precision_impact.png")
    
    def plot_dd_mode_comparison(self, df):
        """
        Compare different Delta-Debug modes (RR, PB, MCA, Cancellation)
        """
        mode_cols = ['rr_num_unstable', 'pb_num_unstable', 
                    'mca_num_unstable', 'cancel_num_unstable']
        
        # Average across all configs
        mode_avgs = []
        mode_names = ['RR', 'PB', 'MCA', 'Cancellation']
        
        for col in mode_cols:
            mode_avgs.append(df[col].mean())
        
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        
        # Plot 1: Average unstable lines by mode
        ax1 = axes[0]
        bars = ax1.bar(mode_names, mode_avgs, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A'])
        ax1.set_ylabel('Average Number of Unstable Lines', fontsize=12)
        ax1.set_title('Delta-Debug Mode Comparison', fontweight='bold', fontsize=14)
        ax1.grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for bar, val in zip(bars, mode_avgs):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{val:.2f}', ha='center', va='bottom')
        
        # Plot 2: Distribution by mode
        ax2 = axes[1]
        mode_data = []
        for col, name in zip(mode_cols, mode_names):
            mode_data.extend([(name, val) for val in df[col] if not pd.isna(val)])
        
        mode_df = pd.DataFrame(mode_data, columns=['Mode', 'Unstable Lines'])
        sns.boxplot(data=mode_df, x='Mode', y='Unstable Lines', ax=ax2)
        ax2.set_ylabel('Number of Unstable Lines', fontsize=12)
        ax2.set_title('Distribution of Unstable Lines by DD Mode', fontweight='bold', fontsize=14)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'dd_mode_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ Generated: dd_mode_comparison.png")
    
    def generate_markdown_report(self, df):
        """
        Generate comprehensive markdown report
        """
        report_path = self.output_dir.parent / "ANALYSIS_REPORT.md"
        
        with open(report_path, 'w') as f:
            f.write("# Archimedes Floating Point Error Analysis Report\n\n")
            f.write(f"**Generated:** {self.results['timestamp']}\n\n")
            f.write(f"**Total Experiments:** {len(self.results['experiments'])}\n\n")
            
            f.write("---\n\n")
            f.write("## Executive Summary\n\n")
            
            # Summary statistics
            successful = len([e for e in self.results['experiments'] if e['status'] == 'success'])
            f.write(f"- Successful experiments: {successful}/{len(self.results['experiments'])}\n")
            f.write(f"- Precision configurations tested: {df['config'].nunique()}\n")
            f.write(f"- Optimization levels tested: {df['opt_level'].nunique()}\n")
            f.write(f"- Fast-math variants: {df['fastmath'].nunique()}\n\n")
            
            # Best and worst configurations
            best_config = df.loc[df['sig_digits'].idxmax()]
            worst_config = df.loc[df['sig_digits'].idxmin()]
            
            f.write("### Most Accurate Configuration\n")
            f.write(f"- **Config:** {best_config['config']}\n")
            f.write(f"- **Optimization:** {best_config['opt_level']}\n")
            f.write(f"- **Fast-math:** {best_config['fastmath']}\n")
            f.write(f"- **Significant Digits:** {best_config['sig_digits']:.4f}\n")
            f.write(f"- **Unstable Lines:** {best_config['unstable_lines']}\n\n")
            
            f.write("### Least Accurate Configuration\n")
            f.write(f"- **Config:** {worst_config['config']}\n")
            f.write(f"- **Optimization:** {worst_config['opt_level']}\n")
            f.write(f"- **Fast-math:** {worst_config['fastmath']}\n")
            f.write(f"- **Significant Digits:** {worst_config['sig_digits']:.4f}\n")
            f.write(f"- **Unstable Lines:** {worst_config['unstable_lines']}\n\n")
            
            f.write("---\n\n")
            f.write("## Question 1: Did Unstable Lines Stay the Same?\n\n")
            
            # Analyze line consistency
            baseline = df[(df['config'] == 'all_double') & 
                         (df['opt_level'] == 'O0') & 
                         (df['fastmath'] == False)]
            
            if not baseline.empty:
                baseline_lines = set(baseline.iloc[0]['unstable_lines'].split(',')) if baseline.iloc[0]['unstable_lines'] else set()
                f.write(f"**Baseline (all_double, O0, no fast-math):** Lines {', '.join(sorted(baseline_lines))}\n\n")
                
                # Check how many configs have same lines
                same_count = 0
                diff_count = 0
                
                for _, row in df.iterrows():
                    row_lines = set(row['unstable_lines'].split(',')) if row['unstable_lines'] else set()
                    if row_lines == baseline_lines:
                        same_count += 1
                    else:
                        diff_count += 1
                
                f.write(f"- **Same as baseline:** {same_count} configurations\n")
                f.write(f"- **Different from baseline:** {diff_count} configurations\n\n")
                
                if diff_count > 0:
                    f.write("**Interpretation:** Unstable lines DO change across configurations, ")
                    f.write("indicating precision-dependent and compiler-dependent instability.\n\n")
                else:
                    f.write("**Interpretation:** Unstable lines remain constant, ")
                    f.write("suggesting a core algorithmic issue independent of precision/optimization.\n\n")
            
            f.write("---\n\n")
            f.write("## Question 2: When Did Lines Change?\n\n")
            
            f.write("### Impact of Precision Changes\n\n")
            
            # Compare all_double vs all_float
            double_df = df[df['config'] == 'all_double']
            float_df = df[df['config'] == 'all_float']
            
            if not double_df.empty and not float_df.empty:
                double_avg_sig = double_df['sig_digits'].mean()
                float_avg_sig = float_df['sig_digits'].mean()
                
                f.write(f"- **All double precision:** Average {double_avg_sig:.2f} significant digits\n")
                f.write(f"- **All float precision:** Average {float_avg_sig:.2f} significant digits\n")
                f.write(f"- **Difference:** {abs(double_avg_sig - float_avg_sig):.2f} digits\n\n")
            
            # Single variable impact
            f.write("### Single Variable Precision Changes\n\n")
            single_var_configs = df[df['num_float_vars'] == 1].groupby('config')['sig_digits'].mean().sort_values()
            
            if not single_var_configs.empty:
                f.write("Impact of converting each variable to float (sorted by accuracy):\n\n")
                for config, sig_digits in single_var_configs.items():
                    var_name = config.replace('only_', '').replace('_float', '')
                    f.write(f"- **{var_name}:** {sig_digits:.2f} significant digits\n")
                f.write("\n")
            
            f.write("### Impact of Optimization Levels\n\n")
            opt_impact = df.groupby('opt_level')['sig_digits'].agg(['mean', 'std']).sort_values('mean', ascending=False)
            
            for opt_level, row in opt_impact.iterrows():
                f.write(f"- **{opt_level}:** {row['mean']:.2f} ± {row['std']:.2f} significant digits\n")
            f.write("\n")
            
            f.write("### Impact of Fast-Math\n\n")
            fastmath_impact = df.groupby('fastmath')['sig_digits'].agg(['mean', 'std'])
            
            for fastmath, row in fastmath_impact.iterrows():
                label = "With -ffast-math" if fastmath else "Without -ffast-math"
                f.write(f"- **{label}:** {row['mean']:.2f} ± {row['std']:.2f} significant digits\n")
            f.write("\n")
            
            # Statistical test
            with_fm = df[df['fastmath'] == True]['sig_digits'].dropna()
            without_fm = df[df['fastmath'] == False]['sig_digits'].dropna()
            
            if len(with_fm) > 0 and len(without_fm) > 0:
                diff = without_fm.mean() - with_fm.mean()
                f.write(f"**Fast-math impact:** ")
                if abs(diff) > 0.5:
                    if diff > 0:
                        f.write(f"Reduces accuracy by {diff:.2f} digits on average (significant impact)\n\n")
                    else:
                        f.write(f"Improves accuracy by {abs(diff):.2f} digits on average (unexpected!)\n\n")
                else:
                    f.write(f"Minimal impact ({abs(diff):.2f} digits difference)\n\n")
            
            f.write("---\n\n")
            f.write("## Question 3: Line-by-Line Stability\n\n")
            
            # Extract all unique unstable lines
            all_lines = set()
            for unstable_str in df['unstable_lines']:
                if pd.notna(unstable_str) and unstable_str:
                    all_lines.update([int(x) for x in unstable_str.split(',')])
            
            f.write(f"**Total unique unstable lines found:** {len(all_lines)}\n\n")
            
            if all_lines:
                f.write("### Frequency Analysis\n\n")
                line_freq = {}
                for unstable_str in df['unstable_lines']:
                    if pd.notna(unstable_str) and unstable_str:
                        lines = [int(x) for x in unstable_str.split(',')]
                        for line in lines:
                            line_freq[line] = line_freq.get(line, 0) + 1
                
                sorted_freq = sorted(line_freq.items(), key=lambda x: x[1], reverse=True)
                
                f.write("| Line Number | Frequency | Percentage |\n")
                f.write("|-------------|-----------|------------|\n")
                
                total_exps = len(df)
                for line, freq in sorted_freq:
                    pct = (freq / total_exps) * 100
                    f.write(f"| Line {line} | {freq}/{total_exps} | {pct:.1f}% |\n")
                
                f.write("\n")
                
                # Interpret based on tutorial knowledge
                if 16 in line_freq or 17 in line_freq:
                    f.write("**Note:** Lines 16-17 correspond to the sqrt and cancellation operations ")
                    f.write("identified in the Verificarlo tutorial as problematic in Archimedes method.\n\n")
            
            f.write("---\n\n")
            f.write("## Delta-Debug Mode Analysis\n\n")
            
            mode_stats = {
                'RR (Random Rounding)': df['rr_num_unstable'].mean(),
                'PB (Precision Bounding)': df['pb_num_unstable'].mean(),
                'MCA (Full MCA)': df['mca_num_unstable'].mean(),
                'Cancellation': df['cancel_num_unstable'].mean()
            }
            
            for mode, avg in sorted(mode_stats.items(), key=lambda x: x[1], reverse=True):
                f.write(f"- **{mode}:** {avg:.2f} average unstable lines\n")
            
            f.write("\n")
            f.write("**Interpretation:**\n")
            f.write("- If RR flags more lines → roundoff errors dominate\n")
            f.write("- If PB/Cancellation flags more → cancellation errors dominate\n")
            f.write("- MCA (combined) should detect both types\n\n")
            
            f.write("---\n\n")
            f.write("## Recommendations\n\n")
            
            # Find best practices
            best_3 = df.nlargest(3, 'sig_digits')
            
            f.write("### Most Stable Configurations\n\n")
            for i, (_, row) in enumerate(best_3.iterrows(), 1):
                f.write(f"{i}. **{row['config']}** with **{row['opt_level']}** ")
                f.write(f"({'with' if row['fastmath'] else 'without'} fast-math)\n")
                f.write(f"   - Significant digits: {row['sig_digits']:.2f}\n")
                f.write(f"   - Mean π: {row['mean_pi']:.15f}\n")
                f.write(f"   - Standard deviation: {row['std_pi']:.2e}\n\n")
            
            f.write("### General Observations\n\n")
            
            # Correlation analysis
            if df['num_float_vars'].corr(df['sig_digits']) < -0.3:
                f.write("- ⚠️ Using float precision significantly reduces accuracy\n")
            
            if df[df['fastmath'] == True]['num_unstable'].mean() > df[df['fastmath'] == False]['num_unstable'].mean():
                f.write("- ⚠️ Fast-math increases numerical instability\n")
            
            if df[df['opt_level'] == 'O3']['sig_digits'].mean() < df[df['opt_level'] == 'O0']['sig_digits'].mean():
                f.write("- ⚠️ Aggressive optimization reduces accuracy\n")
            
            f.write("\n---\n\n")
            f.write("## Visualizations\n\n")
            f.write("See the `plots/` directory for:\n\n")
            f.write("- `precision_heatmap.png` - Accuracy across configurations\n")
            f.write("- `fastmath_comparison.png` - Fast-math impact analysis\n")
            f.write("- `unstable_lines_frequency.png` - Most problematic code lines\n")
            f.write("- `precision_impact.png` - Effect of float variables\n")
            f.write("- `dd_mode_comparison.png` - Delta-Debug mode comparison\n")
        
        print(f"✓ Generated: ANALYSIS_REPORT.md")
        return report_path
    
    def generate_csv_export(self, df):
        """
        Export data to CSV for further analysis
        """
        csv_path = self.output_dir.parent / "results_summary.csv"
        df.to_csv(csv_path, index=False)
        print(f"✓ Generated: results_summary.csv")
    
    def run_all_visualizations(self):
        """
        Generate all plots and reports
        """
        print("\n" + "="*60)
        print("GENERATING VISUALIZATIONS AND REPORTS")
        print("="*60 + "\n")
        
        df = self.prepare_dataframe()
        
        if df.empty:
            print("⚠️ No successful experiments to visualize")
            return
        
        print(f"Processing {len(df)} successful experiments...\n")
        
        # Generate all plots
        self.plot_precision_heatmap(df)
        self.plot_fastmath_comparison(df)
        self.plot_unstable_lines_frequency(df)
        self.plot_precision_impact(df)
        self.plot_dd_mode_comparison(df)
        
        # Generate reports
        self.generate_csv_export(df)
        report_path = self.generate_markdown_report(df)
        
        print("\n" + "="*60)
        print("VISUALIZATION COMPLETE")
        print("="*60)
        print(f"\nMain report: {report_path}")
        print(f"Plots directory: {self.output_dir}")
        print(f"CSV export: {self.output_dir.parent / 'results_summary.csv'}")

def main():
    import sys
    
    results_file = sys.argv[1] if len(sys.argv) > 1 else "analysis_results/results.json"
    
    if not Path(results_file).exists():
        print(f"Error: Results file not found: {results_file}")
        print("Run the main analysis script first!")
        sys.exit(1)
    
    visualizer = AnalysisVisualizer(results_file)
    visualizer.run_all_visualizations()

if __name__ == "__main__":
    main()