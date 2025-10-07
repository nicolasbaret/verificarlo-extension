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

# Copy our automation scripts into the container
COPY archimedes_analyzer.py /usr/local/bin/
COPY visualize_results.py /usr/local/bin/

# Make scripts executable and ensure they use python3
RUN chmod +x /usr/local/bin/archimedes_analyzer.py /usr/local/bin/visualize_results.py

# Create convenient aliases
RUN echo 'alias analyze="python3 /usr/local/bin/archimedes_analyzer.py"' >> /root/.bashrc && \
    echo 'alias visualize="python3 /usr/local/bin/visualize_results.py"' >> /root/.bashrc

# Set working directory to where user files will be mounted
WORKDIR /workdir

# Default command is bash (interactive mode)
CMD ["/bin/bash"]

# Add helpful message when container starts
RUN echo 'echo "╔════════════════════════════════════════════════════════════╗"' >> /root/.bashrc && \
    echo 'echo "║   Verificarlo Analysis Container                           ║"' >> /root/.bashrc && \
    echo 'echo "║                                                            ║"' >> /root/.bashrc && \
    echo 'echo "║   Available commands:                                      ║"' >> /root/.bashrc && \
    echo 'echo "║   • python3 archimedes_analyzer.py [--quick|--minimal]     ║"' >> /root/.bashrc && \
    echo 'echo "║   • python3 visualize_results.py                           ║"' >> /root/.bashrc && \
    echo 'echo "║                                                            ║"' >> /root/.bashrc && \
    echo 'echo "║   Or use shortcuts:                                        ║"' >> /root/.bashrc && \
    echo 'echo "║   • analyze --minimal    (runs analyzer)                   ║"' >> /root/.bashrc && \
    echo 'echo "║   • visualize            (creates plots & report)          ║"' >> /root/.bashrc && \
    echo 'echo "║                                                            ║"' >> /root/.bashrc && \
    echo 'echo "║   Your mounted directory: /workdir                         ║"' >> /root/.bashrc && \
    echo 'echo "║   Results saved to: /workdir/analysis_results              ║"' >> /root/.bashrc && \
    echo 'echo "╚════════════════════════════════════════════════════════════╝"' >> /root/.bashrc && \
    echo '' >> /root/.bashrc

# Ensure the workdir exists
RUN mkdir -p /workdir