# Verificarlo Automated Delta Debug (SOC)

An automated framework for analyzing floating-point stability in C programs using Verificarlo and Delta-Debug.

## Quick Start

```bash
#Usage: ./soc/orchestrate.sh <source_file> -mode <single|all> [variable_name]

M#odes:
  single <var>  - Test single variable with all opt levels + fastmath variations
  all           - Test all variables individually with all opt levels + fastmath

#Examples:
  ./soc/orchestrate.sh /path/archimedes.c -mode single ti
  ./soc/orchestrate.sh /path/archimedes.c -mode all
```

## Overview

