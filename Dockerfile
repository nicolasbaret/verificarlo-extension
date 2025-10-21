# Extend the official Verificarlo Docker image
FROM verificarlo/verificarlo:latest

# Install Python dependencies for analysis and visualization
RUN pip3 install --no-cache-dir \
    matplotlib \
    seaborn \
    pandas \
    numpy

# Install Vim for text editing
RUN apt-get update && apt-get install -y vim && rm -rf /var/lib/apt/lists/*

# Set matplotlib to use non-interactive backend (for headless environment)
ENV MPLBACKEND=Agg

# Set working directory to where user files will be mounted
WORKDIR /workdir

# Default command is bash (interactive mode)
CMD ["/bin/bash"]

# Add helpful message when container starts
RUN echo 'echo "╔════════════════════════════════════════════════════════════╗"' >> /root/.bashrc && \
    echo 'echo "║     Verificarlo Analysis Framework - Enhanced              ║"' >> /root/.bashrc && \
    echo 'echo "║                                                            ║"' >> /root/.bashrc && \
    echo 'echo "║ QUICK START:                                               ║"' >> /root/.bashrc && \
    echo 'echo "║  orchestrate.sh <file.c> -mode single <var>                ║"' >> /root/.bashrc && \
    echo 'echo "║  orchestrate.sh <file.c> -mode all                         ║"' >> /root/.bashrc && \
    echo 'echo "║                                                            ║"' >> /root/.bashrc && \
    echo 'echo "║ ANALYSIS MODES:                                            ║"' >> /root/.bashrc && \
    echo 'echo "║  • single <var> - Test one variable (all opts + fastmath)  ║"' >> /root/.bashrc && \
    echo 'echo "║  • all          - Test all variables systematically        ║"' >> /root/.bashrc && \
    echo 'echo "║                                                            ║"' >> /root/.bashrc && \
    echo 'echo "║ WHAT IT DOES:                                              ║"' >> /root/.bashrc && \
    echo 'echo "║  1. Analyzes source code for float/double variables        ║"' >> /root/.bashrc && \
    echo 'echo "║  2. Generates variants (changes double → float)            ║"' >> /root/.bashrc && \
    echo 'echo "║  3. Compiles with O0/O1/O2/O3 ± fastmath (16 binaries)     ║"' >> /root/.bashrc && \
    echo 'echo "║  4. Validates outputs (detects NaN/Inf)                    ║"' >> /root/.bashrc && \
    echo 'echo "║  5. Runs Delta-Debug (RR, MCA, Cancellation backends)      ║"' >> /root/.bashrc && \
    echo 'echo "║  6. Generates HTML/Markdown/JSON reports                   ║"' >> /root/.bashrc && \
    echo 'echo "║                                                            ║"' >> /root/.bashrc && \
    echo 'echo "║ OUTPUTS:                                                   ║"' >> /root/.bashrc && \
    echo 'echo "║  📁 /workdir/results/<analysis_name>/                      ║"' >> /root/.bashrc && \
    echo 'echo "║    ├── manifest.json       (variable analysis)             ║"' >> /root/.bashrc && \
    echo 'echo "║    ├── variants/           (modified source files)         ║"' >> /root/.bashrc && \
    echo 'echo "║    ├── binaries/           (compiled programs)             ║"' >> /root/.bashrc && \
    echo 'echo "║    ├── validation.json     (NaN/Inf detection)             ║"' >> /root/.bashrc && \
    echo 'echo "║    ├── ddebug_results.json (Delta-Debug findings)          ║"' >> /root/.bashrc && \
    echo 'echo "║    └── report/                                             ║"' >> /root/.bashrc && \
    echo 'echo "║        ├── report.html     ⭐ Open this in browser!        ║"' >> /root/.bashrc && \
    echo 'echo "║        ├── report.md       (Markdown report)               ║"' >> /root/.bashrc && \
    echo 'echo "║        └── summary.json    (Machine-readable)              ║"' >> /root/.bashrc && \
    echo 'echo "║                                                            ║"' >> /root/.bashrc && \
    echo 'echo "║ TIPS:                                                      ║"' >> /root/.bashrc && \
    echo 'echo "║  • Start with -mode single to test one variable            ║"' >> /root/.bashrc && \
    echo 'echo "║  • Use -mode all for comprehensive analysis                ║"' >> /root/.bashrc && \
    echo 'echo "║  • Open report.html for best visualization                 ║"' >> /root/.bashrc && \
    echo 'echo "║  • Check validation.json for NaN/Inf issues                ║"' >> /root/.bashrc && \
    echo 'echo "╚════════════════════════════════════════════════════════════╝"' >> /root/.bashrc && \
    echo '' >> /root/.bashrc

# Ensure the workdir exists
RUN mkdir -p /workdir
