# Spacemesh Plot Monitor

This Python script provides real-time monitoring of Spacemesh plotting progress, supporting both the standard Spacemesh plotter and the H9 plotter.

## Features

- Real-time monitoring of plotting progress
- Support for both standard Spacemesh plotter and H9 plotter
- Speed calculation and estimation
- Visual progress bar
- Estimated completion time
- Resilient to temporary file access issues
- Optional logging for debugging

## Requirements

- Python 3.6 or higher
- No additional packages are required. All libraries used are part of Python's standard library.

## Installation

1. Clone this repository or download the script.
2. Ensure you have Python 3.6 or higher installed.

## Usage

```
python plot_monitor.py /path/to/plotting/folder [--interval SECONDS] [--log {info,debug}] [--plotter {standard,h9}]
```

### Arguments

- `/path/to/plotting/folder`: The path to the folder where plot files are being created (required)
- `--interval SECONDS`: Update interval in seconds (default: 5)
- `--log {info,debug}`: Enable logging at the specified level (optional)
- `--plotter {standard,h9}`: Specify the plotter type (default: standard)

## Examples

1. Monitor standard plotting, updating every 10 seconds:
   ```
   python plot_monitor.py /mnt/plot_drive --interval 10 --plotter standard
   ```

2. Monitor H9 plotting with debug logging:
   ```
   python plot_monitor.py D:\spacemesh_plots --log debug --plotter h9
   ```

## Output

The script provides the following information:

- Plotter type (Standard or H9)
- Plotting speed in MiB/s
- Total number of files to be written
- Overall progress percentage
- Visual progress bar
- Current file being processed and its progress
- Estimated completion time

## Logging

When logging is enabled, a `plot_monitor.log` file will be created in the same directory as the script. This file contains detailed information about the plotting process, which can be useful for debugging or analysis.

## Error Handling

The script is designed to be resilient to temporary file access issues. It will attempt to read the required files for up to three consecutive check intervals before terminating. This helps prevent premature termination due to momentary file system issues or delays in file creation.

## Note

Ensure that the plotting folder contains the necessary metadata files (`postdata_metadata.json` and, for H9 plotter, `progress.json`) for the script to function correctly.

## Change Log

### Version 1.1.0 (Current)
- Combined support for both standard and H9 plotters into a single script
- Added `--plotter` argument to specify plotter type
- Improved error handling with retry mechanism for file access issues

### Version 1.0.0
- Initial release with separate scripts for standard and H9 plotters
- Basic plotting progress monitoring functionality
- Logging capabilities

## Contributing

Contributions to improve the Spacemesh Plot Monitor are welcome. Please feel free to submit pull requests or create issues for bugs and feature requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.