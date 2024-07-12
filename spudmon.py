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