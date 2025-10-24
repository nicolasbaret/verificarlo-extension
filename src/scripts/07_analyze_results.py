#!/usr/bin/env python3
"""
Step 7: Analyze and report Delta-Debug results
MODIFIED: Now includes configurations skipped due to NaN/Inf from validation.json
"""

import argparse
import json
from pathlib import Path
from collections import defaultdict
import sys


def generate_markdown_report(results_dir: Path, dd_results: dict, validation_data: dict = None) -> str:
    """Generate a markdown report"""

    report = []
    report.append("# Verificarlo Analysis Report\n\n")
    report.append(f"**Results Directory:** `{results_dir}`\n\n")
    report.append("---\n\n")

    # Summary
    report.append("## Summary\n\n")
    total = len(dd_results['results'])
    report.append(f"- **Total Configurations Analyzed:** {total}\n")
    report.append(f"- **Backends Used:** {', '.join(dd_results['backends'])}\n")

    # Add validation summary if available
    if validation_data:
        report.append(f"- **Valid Configurations:** {validation_data['valid']}\n")
        report.append(f"- **Invalid Configurations (NaN/Inf):** {validation_data['invalid']}\n")

    report.append("\n")

    # Count successful DD runs
    successful_runs = sum(
        1 for r in dd_results['results']
        for dr in r['dd_results']
        if dr['success']
    )
    total_runs = total * len(dd_results['backends'])
    report.append(f"- **Successful DD Runs:** {successful_runs}/{total_runs}\n\n")

    # Count issues by variable
    var_issues = defaultdict(int)
    line_issues = defaultdict(int)

    for result in dd_results['results']:
        modified_vars = result.get('modified_vars', [])

        for dd_result in result['dd_results']:
            if dd_result['success']:
                for line in dd_result['unstable_lines']:
                    line_issues[line] += 1
                    for var in modified_vars:
                        var_issues[var] += 1

    # Most problematic variables
    if var_issues:
        report.append("## Most Problematic Variables\n\n")
        sorted_vars = sorted(var_issues.items(), key=lambda x: x[1], reverse=True)
        for var, count in sorted_vars[:10]:
            report.append(f"- **{var}**: {count} unstable configuration(s)\n")
        report.append("\n")
    else:
        report.append("## Most Problematic Variables\n\n")
        report.append("*No unstable variables found*\n\n")

    # Most problematic lines
    if line_issues:
        report.append("## Most Problematic Lines\n\n")
        sorted_lines = sorted(line_issues.items(), key=lambda x: x[1], reverse=True)
        for line, count in sorted_lines[:10]:
            report.append(f"- **Line {line}**: {count} unstable configuration(s)\n")
        report.append("\n")
    else:
        report.append("## Most Problematic Lines\n\n")
        report.append("*No unstable lines found*\n\n")

    # Skipped configurations section
    if validation_data:
        skipped = [v for v in validation_data['validations'] if not v['valid']]
        if skipped:
            report.append("## Configurations Skipped (NaN/Inf Issues)\n\n")
            report.append(f"Found {len(skipped)} configuration(s) that produced NaN or Inf:\n\n")
            report.append("| Config | Modified Vars | Opt | Fast-Math | Reason |\n")
            report.append("|--------|---------------|-----|-----------|--------|\n")
            for skip in skipped[:20]:  # Limit to 20 for readability
                vars_str = ', '.join(skip.get('modified_vars', [])) or 'baseline'
                opt = skip.get('opt_level', 'N/A')
                fastmath = '✓' if skip.get('fastmath', False) else '✗'
                reason = skip.get('validity_reason', 'Unknown')
                config_id = skip.get('config_id', 'Unknown')
                report.append(f"| {config_id} | {vars_str} | {opt} | {fastmath} | {reason} |\n")
            if len(skipped) > 20:
                report.append(f"\n*... and {len(skipped) - 20} more*\n")
            report.append("\n")

    # Detailed results table
    report.append("## Detailed Results\n\n")
    report.append("| Config | Modified Vars | Opt | Fast-Math | Backend | Unstable Lines |\n")
    report.append("|--------|---------------|-----|-----------|---------|----------------|\n")

    for result in dd_results['results']:
        variant = result['variant_name']
        vars_str = ', '.join(result['modified_vars']) if result['modified_vars'] else 'baseline'
        opt = result['opt_level']
        fastmath = '✓' if result['fastmath'] else '✗'

        for dd_result in result['dd_results']:
            backend = dd_result['backend']
            if dd_result['success']:
                lines_str = ', '.join(map(str, dd_result['unstable_lines'])) or 'none'
            else:
                lines_str = '❌ failed'

            report.append(f"| {variant} | {vars_str} | {opt} | {fastmath} | {backend} | {lines_str} |\n")

    report.append("\n")

    # Key findings
    report.append("## Key Findings\n\n")

    # Find configurations with no instability
    stable_configs = [
        r for r in dd_results['results']
        if all(not dr.get('unstable_lines') for dr in r['dd_results'] if dr['success'])
    ]

    if stable_configs:
        report.append(f"### Stable Configurations ({len(stable_configs)})\n\n")
        for config in stable_configs[:10]:
            vars_str = ', '.join(config['modified_vars']) or 'all double (baseline)'
            report.append(f"- `{config['variant_name']}` ({vars_str})\n")
        report.append("\n")

    # Find most unstable configurations
    unstable_configs = sorted(
        dd_results['results'],
        key=lambda r: sum(len(dr.get('unstable_lines', [])) for dr in r['dd_results']),
        reverse=True
    )

    if unstable_configs and unstable_configs[0]:
        total_lines_first = sum(len(dr.get('unstable_lines', [])) for dr in unstable_configs[0]['dd_results'])
        if total_lines_first > 0:
            report.append(f"### Most Unstable Configurations\n\n")
            for config in unstable_configs[:10]:
                total_lines = sum(len(dr.get('unstable_lines', [])) for dr in config['dd_results'])
                if total_lines > 0:
                    vars_str = ', '.join(config['modified_vars']) or 'all double (baseline)'
                    report.append(
                        f"- `{config['variant_name']}` ({vars_str}): {total_lines} total unstable line detections\n")
            report.append("\n")

    report.append("---\n\n")
    report.append("*Generated by Verificarlo Analysis Framework*\n")

    return ''.join(report)


def generate_html_report(results_dir: Path, dd_results: dict, validation_data: dict = None) -> str:
    """Generate a rich HTML report"""

    # Count statistics
    total = len(dd_results['results'])
    successful_runs = sum(
        1 for r in dd_results['results']
        for dr in r['dd_results']
        if dr['success']
    )
    total_runs = total * len(dd_results['backends'])

    # Count issues
    var_issues = defaultdict(int)
    line_issues = defaultdict(int)

    for result in dd_results['results']:
        modified_vars = result.get('modified_vars', [])
        for dd_result in result['dd_results']:
            if dd_result['success']:
                for line in dd_result['unstable_lines']:
                    line_issues[line] += 1
                    for var in modified_vars:
                        var_issues[var] += 1

    # Stable configs
    stable_configs = [
        r for r in dd_results['results']
        if all(not dr.get('unstable_lines') for dr in r['dd_results'] if dr['success'])
    ]

    # Unstable configs
    unstable_configs = sorted(
        dd_results['results'],
        key=lambda r: sum(len(dr.get('unstable_lines', [])) for dr in r['dd_results']),
        reverse=True
    )

    # Skipped configs from validation
    skipped_configs = []
    if validation_data:
        skipped_configs = [v for v in validation_data['validations'] if not v['valid']]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verificarlo Analysis Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            max-width: 1200px;
            margin: 40px auto;
            padding: 0 20px;
            line-height: 1.6;
            color: #333;
        }}

        h1 {{
            border-bottom: 3px solid #333;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }}

        h2 {{
            margin-top: 40px;
            margin-bottom: 20px;
            border-bottom: 1px solid #ddd;
            padding-bottom: 8px;
        }}

        h3 {{
            margin-top: 25px;
            margin-bottom: 15px;
            color: #555;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 30px 0;
        }}

        .stat-card {{
            border: 1px solid #ddd;
            padding: 20px;
        }}

        .stat-card h3 {{
            font-size: 0.9em;
            color: #666;
            margin-bottom: 8px;
            font-weight: normal;
        }}

        .stat-card .value {{
            font-size: 2em;
            font-weight: bold;
        }}

        .stat-card.warning {{
            background: #fff3cd;
            border-color: #ffc107;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            border: 1px solid #ddd;
        }}

        th {{
            background: #f5f5f5;
            padding: 10px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #ddd;
        }}

        td {{
            padding: 10px;
            border-bottom: 1px solid #eee;
        }}

        tr:hover {{
            background: #fafafa;
        }}

        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 0.85em;
            font-weight: 500;
        }}

        .badge-success {{
            background: #d4edda;
            color: #155724;
        }}

        .badge-warning {{
            background: #fff3cd;
            color: #856404;
        }}

        .badge-danger {{
            background: #f8d7da;
            color: #721c24;
        }}

        .badge-info {{
            background: #d1ecf1;
            color: #0c5460;
        }}

        .list-item {{
            padding: 10px;
            margin-bottom: 8px;
            border-left: 3px solid #333;
            background: #f9f9f9;
        }}

        .empty-state {{
            color: #999;
            font-style: italic;
            padding: 20px;
            text-align: center;
        }}

        .checkmark {{
            color: #28a745;
        }}

        .crossmark {{
            color: #dc3545;
        }}

        footer {{
            margin-top: 60px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 0.9em;
        }}

        code {{
            background: #f5f5f5;
            padding: 2px 6px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}

        .subtitle {{
            color: #666;
            margin-top: -15px;
        }}

        section {{
            margin-bottom: 40px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔬 Verificarlo Analysis Report</h1>
            <p class="subtitle">Floating-Point Stability Analysis</p>
        </header>

        <div class="content">
            <!-- Statistics -->
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>Total Configurations</h3>
                    <div class="value">{total}</div>
                </div>
                <div class="stat-card">
                    <h3>Successful DD Runs</h3>
                    <div class="value">{successful_runs}/{total_runs}</div>
                </div>
                <div class="stat-card">
                    <h3>Backends Used</h3>
                    <div class="value">{len(dd_results['backends'])}</div>
                </div>
                <div class="stat-card">
                    <h3>Stable Configurations</h3>
                    <div class="value">{len(stable_configs)}</div>
                </div>"""

    if validation_data:
        html += f"""
                <div class="stat-card warning">
                    <h3>Skipped (NaN/Inf)</h3>
                    <div class="value">{len(skipped_configs)}</div>
                </div>"""

    html += """
            </div>

            <!-- Backends -->
            <section>
                <h2>Analysis Backends</h2>
                <p>"""

    for backend in dd_results['backends']:
        html += f'<span class="badge badge-info">{backend}</span> '

    html += """</p>
            </section>"""

    # Skipped configurations section
    if skipped_configs:
        html += f"""

            <!-- Skipped Configurations -->
            <section>
                <h2>⚠️ Configurations Skipped (NaN/Inf Issues)</h2>
                <p>The following {len(skipped_configs)} configuration(s) produced NaN or Inf and were not analyzed with Delta-Debug:</p>
                <div style="overflow-x: auto;">
                    <table>
                        <thead>
                            <tr>
                                <th>Configuration</th>
                                <th>Modified Variables</th>
                                <th>Opt Level</th>
                                <th>Fast-Math</th>
                                <th>Reason</th>
                            </tr>
                        </thead>
                        <tbody>"""

        for skip in skipped_configs[:50]:  # Limit for performance
            vars_str = ', '.join(skip.get('modified_vars', [])) or '<em>baseline</em>'
            opt = skip.get('opt_level', 'N/A')
            fastmath = '✓' if skip.get('fastmath', False) else '✗'
            reason = skip.get('validity_reason', 'Unknown')
            config_id = skip.get('config_id', 'Unknown')

            html += f"""
                            <tr>
                                <td><code>{config_id}</code></td>
                                <td>{vars_str}</td>
                                <td><span class="badge badge-info">{opt}</span></td>
                                <td class="{'checkmark' if skip.get('fastmath', False) else 'crossmark'}">{fastmath}</td>
                                <td><span class="badge badge-danger">{reason}</span></td>
                            </tr>"""

        if len(skipped_configs) > 50:
            html += f"""
                            <tr>
                                <td colspan="5" style="text-align: center; font-style: italic; color: #666;">
                                    ... and {len(skipped_configs) - 50} more
                                </td>
                            </tr>"""

        html += """
                        </tbody>
                    </table>
                </div>
            </section>"""

    html += """

            <!-- Problematic Variables -->
            <section>
                <h2>Most Problematic Variables</h2>"""

    if var_issues:
        sorted_vars = sorted(var_issues.items(), key=lambda x: x[1], reverse=True)[:10]
        for var, count in sorted_vars:
            html += f"""
                <div class="list-item">
                    <strong>{var}</strong>: {count} unstable configuration(s)
                </div>"""
    else:
        html += '<div class="empty-state">✓ No unstable variables detected</div>'

    html += """
            </section>

            <!-- Problematic Lines -->
            <section>
                <h2>Most Problematic Source Lines</h2>"""

    if line_issues:
        sorted_lines = sorted(line_issues.items(), key=lambda x: x[1], reverse=True)[:10]
        for line, count in sorted_lines:
            html += f"""
                <div class="list-item">
                    Line <code>{line}</code>: {count} unstable detection(s)
                </div>"""
    else:
        html += '<div class="empty-state">✓ No unstable lines detected</div>'

    html += """
            </section>

            <!-- Detailed Results Table -->
            <section>
                <h2>Detailed Results</h2>
                <div style="overflow-x: auto;">
                    <table>
                        <thead>
                            <tr>
                                <th>Configuration</th>
                                <th>Modified Variables</th>
                                <th>Opt Level</th>
                                <th>Fast-Math</th>
                                <th>Backend</th>
                                <th>Unstable Lines</th>
                            </tr>
                        </thead>
                        <tbody>"""

    for result in dd_results['results']:
        variant = result['variant_name']
        vars_str = ', '.join(result['modified_vars']) if result['modified_vars'] else '<em>baseline</em>'
        opt = result['opt_level']
        fastmath = '✓' if result['fastmath'] else '✗'

        for dd_result in result['dd_results']:
            backend = dd_result['backend']

            if dd_result['success']:
                if dd_result['unstable_lines']:
                    lines_str = ', '.join(map(str, dd_result['unstable_lines']))
                    badge_class = 'badge-warning'
                else:
                    lines_str = 'none'
                    badge_class = 'badge-success'
            else:
                lines_str = 'failed'
                badge_class = 'badge-danger'

            html += f"""
                            <tr>
                                <td><code>{variant}</code></td>
                                <td>{vars_str}</td>
                                <td><span class="badge badge-info">{opt}</span></td>
                                <td class="{'checkmark' if result['fastmath'] else 'crossmark'}">{fastmath}</td>
                                <td><span class="badge badge-info">{backend}</span></td>
                                <td><span class="badge {badge_class}">{lines_str}</span></td>
                            </tr>"""

    html += """
                        </tbody>
                    </table>
                </div>
            </section>

            <!-- Stable Configurations -->
            <section>
                <h2>Stable Configurations</h2>"""

    if stable_configs:
        html += f'<p>Found {len(stable_configs)} stable configuration(s):</p>'
        for config in stable_configs[:10]:
            vars_str = ', '.join(config['modified_vars']) or 'all double (baseline)'
            html += f"""
                <div class="list-item">
                    <code>{config['variant_name']}</code> — {vars_str}
                </div>"""
        if len(stable_configs) > 10:
            html += f'<p><em>... and {len(stable_configs) - 10} more</em></p>'
    else:
        html += '<div class="empty-state">No completely stable configurations found</div>'

    html += """
            </section>

            <!-- Unstable Configurations -->
            <section>
                <h2>Most Unstable Configurations</h2>"""

    unstable_with_issues = [
        (config, sum(len(dr.get('unstable_lines', [])) for dr in config['dd_results']))
        for config in unstable_configs
    ]
    unstable_with_issues = [(c, count) for c, count in unstable_with_issues if count > 0]

    if unstable_with_issues:
        for config, total_lines in unstable_with_issues[:10]:
            vars_str = ', '.join(config['modified_vars']) or 'all double (baseline)'
            html += f"""
                <div class="list-item">
                    <code>{config['variant_name']}</code> — {vars_str}: <strong>{total_lines}</strong> total unstable line detections
                </div>"""
    else:
        html += '<div class="empty-state">✓ No unstable configurations detected</div>'

    html += f"""
            </section>
        </div>

        <footer>
            <p>Generated by <strong>Verificarlo Analysis Framework</strong></p>
            <p style="margin-top: 5px; font-size: 0.9em;">Results Directory: <code>{results_dir}</code></p>
        </footer>
    </div>
</body>
</html>"""

    return html


def generate_json_summary(dd_results: dict, validation_data: dict = None) -> dict:
    """Generate a JSON summary"""

    summary = {
        'total_configs': len(dd_results['results']),
        'backends': dd_results['backends'],
        'variable_instability': {},
        'line_instability': {},
        'stable_configs': [],
        'unstable_configs': []
    }

    # Add validation info if available
    if validation_data:
        summary['validation_summary'] = {
            'valid': validation_data['valid'],
            'invalid': validation_data['invalid'],
            'total_tested': validation_data['total_tested']
        }

        # Add list of skipped configs
        skipped = [
            {
                'config_id': v['config_id'],
                'variant_name': v.get('variant_name', 'Unknown'),
                'modified_vars': v.get('modified_vars', []),
                'opt_level': v.get('opt_level', 'N/A'),
                'fastmath': v.get('fastmath', False),
                'reason': v.get('validity_reason', 'Unknown')
            }
            for v in validation_data['validations'] if not v['valid']
        ]
        summary['skipped_configs'] = skipped

    var_issues = defaultdict(int)
    line_issues = defaultdict(int)

    for result in dd_results['results']:
        modified_vars = result.get('modified_vars', [])
        total_unstable_lines = 0

        for dd_result in result['dd_results']:
            if dd_result['success']:
                unstable_lines = dd_result.get('unstable_lines', [])
                total_unstable_lines += len(unstable_lines)

                for line in unstable_lines:
                    line_issues[line] += 1
                    for var in modified_vars:
                        var_issues[var] += 1

        config_summary = {
            'config_id': result['config_id'],
            'variant_name': result['variant_name'],
            'modified_vars': modified_vars,
            'opt_level': result['opt_level'],
            'fastmath': result['fastmath'],
            'total_unstable_lines': total_unstable_lines
        }

        if total_unstable_lines == 0:
            summary['stable_configs'].append(config_summary)
        else:
            summary['unstable_configs'].append(config_summary)

    summary['variable_instability'] = dict(var_issues)
    summary['line_instability'] = dict(line_issues)

    # Sort unstable configs
    summary['unstable_configs'].sort(key=lambda x: x['total_unstable_lines'], reverse=True)

    return summary


def main():
    parser = argparse.ArgumentParser(
        description='Analyze and report Delta-Debug results'
    )
    parser.add_argument('--results', required=True,
                        help='Results directory or DD results JSON')
    parser.add_argument('--output', required=True,
                        help='Output directory for reports')
    parser.add_argument('--formats', nargs='+',
                        default=['json', 'markdown', 'html'],
                        choices=['json', 'markdown', 'html'],
                        help='Output formats')

    args = parser.parse_args()

    results_path = Path(args.results)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load DD results
    if results_path.is_file():
        dd_results_file = results_path
        results_dir = results_path.parent
    else:
        dd_results_file = results_path / 'ddebug_results.json'
        results_dir = results_path

    if not dd_results_file.exists():
        print(f"Error: DD results not found at {dd_results_file}")
        sys.exit(1)

    with open(dd_results_file, 'r') as f:
        dd_results = json.load(f)

    # Load validation results to get skipped configs
    validation_data = None
    validation_file = results_dir / 'validation.json'
    if validation_file.exists():
        with open(validation_file, 'r') as f:
            validation_data = json.load(f)
        print(f"📋 Loaded validation data: {validation_data['valid']} valid, {validation_data['invalid']} invalid")

    print(f"📊 Analyzing {len(dd_results['results'])} configuration(s)")

    # Generate reports
    if 'json' in args.formats:
        summary = generate_json_summary(dd_results, validation_data)
        json_path = output_dir / 'summary.json'
        with open(json_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"   ✓ JSON summary: {json_path}")

    if 'markdown' in args.formats:
        markdown = generate_markdown_report(results_path, dd_results, validation_data)
        md_path = output_dir / 'report.md'
        with open(md_path, 'w') as f:
            f.write(markdown)
        print(f"   ✓ Markdown report: {md_path}")

    if 'html' in args.formats:
        html = generate_html_report(results_path, dd_results, validation_data)
        html_path = output_dir / 'report.html'
        with open(html_path, 'w') as f:
            f.write(html)
        print(f"   ✓ HTML report: {html_path}")

    print(f"\n✓ Analysis complete! Reports saved to: {output_dir}")


if __name__ == '__main__':
    main()