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

def get_progress(folder_path: str, is_h9: bool) -> int:
    if is_h9:
        with open(os.path.join(folder_path, 'progress.json'), 'r') as f:
            progress = json.load(f)
        return progress['file_index']
    else:
        completed_files = get_completed_files(folder_path)
        return len(completed_files)

def get_completed_files(folder_path: str) -> List[str]:
    files = [f for f in os.listdir(folder_path) if f.startswith('postdata_') and f.endswith('.bin')]
    return sorted(files, key=lambda x: int(x.split('_')[1].split('.')[0]))

def get_current_file(folder_path: str, is_h9: bool) -> Tuple[str, float]:
    if is_h9:
        dtmp_files = [f for f in os.listdir(folder_path) if f.endswith('.dtmp')]
        current_file = dtmp_files[0] if dtmp_files else None
    else:
        completed_files = get_completed_files(folder_path)
        if not completed_files:
            return None, 0.0
        last_file = completed_files[-1]
        last_file_path = os.path.join(folder_path, last_file)
        last_file_size = os.path.getsize(last_file_path)
        if last_file_size == get_metadata(folder_path)[0]:  # If the last file is complete
            return None, 100.0
        current_file = last_file

    if current_file:
        file_progress = get_file_progress(folder_path, current_file, get_metadata(folder_path)[0])
        return current_file, file_progress
    return None, 0.0

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

def monitor_plotting(folder_path: str, update_interval: int, is_h9: bool):
    signal.signal(signal.SIGINT, signal_handler)
    
    consecutive_errors = 0
    max_retries = 3

    while True:
        try:
            max_file_size, num_units = get_metadata(folder_path)
            total_files = (num_units * 64 * 1024 * 1024 * 1024) // max_file_size

            while True:
                try:
                    completed_files = get_completed_files(folder_path)
                    if logging.getLogger().isEnabledFor(logging.DEBUG):
                        logging.debug(f"Completed files: {completed_files}")
                    current_progress = get_progress(folder_path, is_h9)
                    current_file, file_progress = get_current_file(folder_path, is_h9)

                    speed = calculate_speed(folder_path, completed_files, max_file_size)
                    overall_progress = (current_progress / total_files) * 100
                    completion_time = predict_completion_time(total_files, current_progress, speed, max_file_size)

                    os.system('cls' if os.name == 'nt' else 'clear')
                    print(f"Monitoring folder: {folder_path}")
                    print(f"Plotter type: {'H9' if is_h9 else 'Standard'}")
                    print(f"Plotting speed: {speed:.2f} MiB/s")
                    print(f"Total files to be written: {total_files}")
                    print(f"Overall progress: {overall_progress:.2f}%")
                    print_progress(current_progress, total_files)
                    if current_file:
                        print(f"\nCurrent file: {current_file} ({file_progress:.2f}% complete)")
                    elif current_progress < total_files:
                        print("\nCurrent file complete, awaiting next")
                    else:
                        print("\nAll files complete")
                    print(f"Estimated completion time: {completion_time}")

                    if logging.getLogger().isEnabledFor(logging.INFO):
                        logging.info(f"Speed: {speed:.2f} MiB/s, Progress: {overall_progress:.2f}%, Current file: {current_file}")

                    if current_progress >= total_files:
                        print("\nPlotting completed!")
                        if logging.getLogger().isEnabledFor(logging.INFO):
                            logging.info("Plotting completed")
                        return  # Exit the function when plotting is complete

                    consecutive_errors = 0  # Reset error count on successful iteration
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    consecutive_errors += 1
                    error_msg = f"Error: {str(e)}. Retrying in {update_interval} seconds... (Attempt {consecutive_errors}/{max_retries})"
                    print(error_msg)
                    if logging.getLogger().isEnabledFor(logging.WARNING):
                        logging.warning(error_msg)
                    
                    if consecutive_errors >= max_retries:
                        raise  # Re-raise the exception if max retries reached
                
                time.sleep(update_interval)

        except FileNotFoundError:
            error_msg = "Error: Required metadata files not found after multiple attempts. Exiting."
            print(error_msg)
            if logging.getLogger().isEnabledFor(logging.ERROR):
                logging.error(error_msg)
            break
        except json.JSONDecodeError:
            error_msg = "Error: Invalid JSON in metadata files after multiple attempts. Exiting."
            print(error_msg)
            if logging.getLogger().isEnabledFor(logging.ERROR):
                logging.error(error_msg)
            break
        except Exception as e:
            error_msg = f"An unexpected error occurred: {str(e)}"
            print(error_msg)
            if logging.getLogger().isEnabledFor(logging.ERROR):
                logging.exception(error_msg)
            break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitor Spacemesh plotting progress.")
    parser.add_argument("folder_path", help="Path to the folder containing plot files")
    parser.add_argument("--interval", type=int, default=5, help="Update interval in seconds (default: 5)")
    parser.add_argument("--log", choices=["info", "debug"], help="Enable logging (info or debug level)")
    parser.add_argument("--plotter", choices=["h9", "standard"], default="standard", help="Specify the plotter type (default: standard)")
    args = parser.parse_args()

    setup_logging(args.log)

    if logging.getLogger().isEnabledFor(logging.INFO):
        logging.info(f"Starting script with folder path: {args.folder_path}, interval: {args.interval}, plotter: {args.plotter}")
    monitor_plotting(args.folder_path, args.interval, args.plotter == "h9")