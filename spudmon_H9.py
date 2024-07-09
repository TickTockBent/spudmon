import os
import json
import time
import argparse
from datetime import datetime, timedelta
from typing import List, Tuple
import signal
import logging

def setup_logging(log_level):
    if log_level == "debug":
        level = logging.DEBUG
    elif log_level == "info":
        level = logging.INFO
    else:
        return  # No logging

    logging.basicConfig(filename='plot_monitor.log', level=level, 
                        format='%(asctime)s - %(levelname)s - %(message)s')

def get_metadata(folder_path: str) -> Tuple[int, int]:
    with open(os.path.join(folder_path, 'postdata_metadata.json'), 'r') as f:
        metadata = json.load(f)
    return metadata['MaxFileSize'], metadata['NumUnits']

def get_progress(folder_path: str) -> int:
    with open(os.path.join(folder_path, 'progress.json'), 'r') as f:
        progress = json.load(f)
    return progress['file_index']

def get_completed_files(folder_path: str) -> List[str]:
    return sorted([f for f in os.listdir(folder_path) if f.startswith('postdata_') and f.endswith('.bin')],
                  key=lambda x: int(x.split('_')[1].split('.')[0]))

def get_current_file(folder_path: str) -> str:
    dtmp_files = [f for f in os.listdir(folder_path) if f.endswith('.dtmp')]
    return dtmp_files[0] if dtmp_files else None

def get_file_progress(folder_path: str, current_file: str, max_file_size: int) -> float:
    if not current_file:
        return 0.0
    current_size = os.path.getsize(os.path.join(folder_path, current_file))
    return min(current_size / max_file_size * 100, 100)

def calculate_speed(folder_path: str, completed_files: List[str], max_file_size: int) -> float:
    if logging.getLogger().isEnabledFor(logging.DEBUG):
        logging.debug(f"Number of completed files: {len(completed_files)}")
    if len(completed_files) < 2:
        return 0.0
    
    files_to_check = completed_files[-10:] if len(completed_files) > 10 else completed_files
    total_size = 0

    file_times = []
    if logging.getLogger().isEnabledFor(logging.DEBUG):
        logging.debug("File modification times and sizes:")
    for file in files_to_check:
        full_path = os.path.join(folder_path, file)
        mtime = os.path.getmtime(full_path)
        size = os.path.getsize(full_path)
        file_times.append((file, mtime))
        total_size += size
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            logging.debug(f"{file}: size={size}, time={mtime}")

    file_times.sort(key=lambda x: x[1])  # Sort by timestamp
    oldest_time = file_times[0][1]
    newest_time = file_times[-1][1]
    total_time = newest_time - oldest_time

    if logging.getLogger().isEnabledFor(logging.DEBUG):
        logging.debug(f"Total size: {total_size}, Total time: {total_time}")
    if total_time > 0:
        bytes_per_second = total_size / total_time
        mib_per_second = bytes_per_second / (1024 * 1024)
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            logging.debug(f"Calculated speed: {mib_per_second:.2f} MiB/s")
        return mib_per_second
    else:
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            logging.debug("Total time is 0, returning speed as 0")
        return 0.0

def print_progress(completed: int, total: int, width: int = 50) -> None:
    filled = int(width * completed // total)
    bar = '=' * filled + '-' * (width - filled)
    print(f'\rProgress: [{bar}]', end='', flush=True)

def predict_completion_time(total_files: int, current_progress: int, speed: float, max_file_size: int) -> str:
    if speed == 0:
        return "Unable to predict (speed is 0)"
    remaining_files = total_files - current_progress
    remaining_size = remaining_files * max_file_size
    remaining_time_seconds = remaining_size / (speed * 1024 * 1024)
    completion_time = datetime.now() + timedelta(seconds=remaining_time_seconds)
    return completion_time.strftime("%Y-%m-%d %H:%M:%S")

def signal_handler(signum, frame):
    print("\nShutting down gracefully...")
    if logging.getLogger().isEnabledFor(logging.INFO):
        logging.info("Script terminated by user")
    exit(0)

def monitor_plotting(folder_path: str, update_interval: int):
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        max_file_size, num_units = get_metadata(folder_path)
        total_files = (num_units * 64 * 1024 * 1024 * 1024) // max_file_size

        while True:
            completed_files = get_completed_files(folder_path)
            if logging.getLogger().isEnabledFor(logging.DEBUG):
                logging.debug(f"Completed files: {completed_files}")
            current_file = get_current_file(folder_path)
            current_progress = get_progress(folder_path)

            speed = calculate_speed(folder_path, completed_files, max_file_size)
            overall_progress = (current_progress / total_files) * 100
            file_progress = get_file_progress(folder_path, current_file, max_file_size)
            completion_time = predict_completion_time(total_files, current_progress, speed, max_file_size)

            os.system('cls' if os.name == 'nt' else 'clear')
            print(f"Monitoring folder: {folder_path}")
            print(f"Plotting speed: {speed:.2f} MiB/s")
            print(f"Total files to be written: {total_files}")
            print(f"Overall progress: {overall_progress:.2f}%")
            print_progress(current_progress, total_files)
            print(f"\nCurrent file: {current_file} ({file_progress:.2f}% complete)")
            print(f"Estimated completion time: {completion_time}")

            if logging.getLogger().isEnabledFor(logging.INFO):
                logging.info(f"Speed: {speed:.2f} MiB/s, Progress: {overall_progress:.2f}%, Current file: {current_file}")

            if current_progress >= total_files:
                print("\nPlotting completed!")
                if logging.getLogger().isEnabledFor(logging.INFO):
                    logging.info("Plotting completed")
                break

            time.sleep(update_interval)

    except FileNotFoundError:
        error_msg = "Error: Required metadata files not found."
        print(error_msg)
        if logging.getLogger().isEnabledFor(logging.ERROR):
            logging.error(error_msg)
    except json.JSONDecodeError:
        error_msg = "Error: Invalid JSON in metadata files."
        print(error_msg)
        if logging.getLogger().isEnabledFor(logging.ERROR):
            logging.error(error_msg)
    except Exception as e:
        error_msg = f"An unexpected error occurred: {str(e)}"
        print(error_msg)
        if logging.getLogger().isEnabledFor(logging.ERROR):
            logging.exception(error_msg)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitor Spacemesh plotting progress.")
    parser.add_argument("folder_path", help="Path to the folder containing plot files")
    parser.add_argument("--interval", type=int, default=5, help="Update interval in seconds (default: 5)")
    parser.add_argument("--log", choices=["info", "debug"], help="Enable logging (info or debug level)")
    args = parser.parse_args()

    setup_logging(args.log)

    if logging.getLogger().isEnabledFor(logging.INFO):
        logging.info(f"Starting script with folder path: {args.folder_path} and interval: {args.interval}")
    monitor_plotting(args.folder_path, args.interval)