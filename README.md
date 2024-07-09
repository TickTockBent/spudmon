# Spacemesh Spudmon Plot Monitor

This repository contains two Python scripts for monitoring the progress of Spacemesh plotting:

1. `spudmon.py`: For use with the standard Spacemesh plotter
2. `spudmon_h9.py`: For use with the H9 plotter

Both scripts provide real-time monitoring of plotting progress, including speed calculations, estimated completion time, and a visual progress bar.

## Requirements

- Python 3.6 or higher

## Installation

1. Clone this repository or download the scripts.
2. Install the required Python version if not already installed.

## Usage

### For Standard Spacemesh Plotter

```
python spudmon.py /path/to/plotting/folder [--interval SECONDS] [--log {info,debug}]
```

### For H9 Plotter

```
python spudmon_h9.py /path/to/plotting/folder [--interval SECONDS] [--log {info,debug}]
```

### Arguments

- `/path/to/plotting/folder`: The path to the folder where plot files are being created (required)
- `--interval SECONDS`: Update interval in seconds (default: 5)
- `--log {info,debug}`: Enable logging at the specified level (optional)

## Examples

1. Monitor standard plotting, updating every 10 seconds:
   ```
   python spudmon.py /mnt/plot_drive --interval 10
   ```

2. Monitor H9 plotting with debug logging:
   ```
   python spudmon_h9.py D:\spacemesh_plots --log debug
   ```

## Output

The scripts provide the following information:

- Plotting speed in MiB/s
- Total number of files to be written
- Overall progress percentage
- Visual progress bar
- Current file being processed and its progress
- Estimated completion time

## Logging

When logging is enabled, a `plot_monitor.log` file will be created in the same directory as the script. This file contains detailed information about the plotting process, which can be useful for debugging or analysis.

## Note

Ensure that the plotting folder contains the necessary metadata files (`postdata_metadata.json` and, for H9 plotter, `progress.json`) for the scripts to function correctly.