# CLI Client Guidelines

- **Standard I/O Streams**:
  - Write standard output/data results to `stdout` (e.g. formatted JSON).
  - Write all warning messages, error tracebacks, and operational logs to `stderr`.
- **Exit Codes**:
  - Exit code `0`: Successful execution.
  - Non-zero exit code (`1`, `2`, etc.): Errors or invalid invocations.
- **Argument Parsing**:
  - Use structured argument parsing (`argparse` or standard flags).
  - Provide `--help` strings for all commands and subcommands.
- **Resilient Network Handling**:
  - Handle connection timeouts and server errors gracefully without unhandled tracebacks visible to end users.
