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
    echo 'echo "║  orchestrate.sh <file.c> -mode singe_and_pairs             ║"' >> /root/.bashrc && \
    echo 'echo "║  orchestrate.sh <file.c> -mode pairs                       ║"' >> /root/.bashrc && \
    echo 'echo "║                                                            ║"' >> /root/.bashrc && \
    echo 'echo "║ ANALYSIS MODES:                                            ║"' >> /root/.bashrc && \
    echo 'echo "║  • single <var> - Test one variable (all opts + fastmath)  ║"' >> /root/.bashrc && \
    echo 'echo "║  • all          - Test all variables alone                 ║"' >> /root/.bashrc && \
    echo 'echo "║  • singe_and_pairs    - Test both                          ║"' >> /root/.bashrc && \
    echo 'echo "║  • pairs        - Test all pairs                           ║"' >> /root/.bashrc && \
    echo 'echo "║                                                            ║"' >> /root/.bashrc && \
    echo 'echo "║ OUTPUTS:                                                   ║"' >> /root/.bashrc && \
    echo 'echo "║  📁 /workdir/results/<analysis_name>/                      ║"' >> /root/.bashrc && \
    echo 'echo "║    ├── manifest.json       (variable analysis)             ║"' >> /root/.bashrc && \
    echo 'echo "║    ├── variants/           (modified source files)         ║"' >> /root/.bashrc && \
    echo 'echo "║    ├── binaries/           (compiled programs)             ║"' >> /root/.bashrc && \
    echo 'echo "║    ├── validation.json     (NaN/Inf detection)             ║"' >> /root/.bashrc && \
    echo 'echo "║    ├── ddebug_results.json (Delta-Debug findings)          ║"' >> /root/.bashrc && \
    echo 'echo "║    └── report/                                             ║"' >> /root/.bashrc && \
    echo 'echo "║        ├── report.html                                     ║"' >> /root/.bashrc && \
    echo 'echo "║        ├── report.md                                       ║"' >> /root/.bashrc && \
    echo 'echo "║        └── summary.json                                    ║"' >> /root/.bashrc && \
    echo 'echo "║                                                            ║"' >> /root/.bashrc && \
    echo 'echo "╚════════════════════════════════════════════════════════════╝"' >> /root/.bashrc && \
    echo '' >> /root/.bashrc

# Ensure the workdir exists
RUN mkdir -p /workdir
