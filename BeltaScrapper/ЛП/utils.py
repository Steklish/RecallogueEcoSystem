import os
from pathlib import Path
from typing import Callable, Any
from multiprocessing import Pool
from tqdm import tqdm


def apply_to_all_files(
    folder_path: str,
    func: Callable[[str], Any],
    max_workers: int = 5,
    chunksize: int = 1,
) -> None:
    """
    Recursively apply a function to every file in a directory, in parallel, with a progress bar.

    Args:
        folder_path (str): Path to the root folder.
        func (Callable[[str], Any]): Function to apply. It will be called as func(file_path).
        max_workers (int, optional): Number of worker processes. If None, uses os.cpu_count().
        chunksize (int): Number of files to send to each worker at once (for better performance).
    """
    root = Path(folder_path)
    if not root.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    # Collect all file paths first
    file_paths = [str(p) for p in root.rglob("*") if p.is_file()]

    if not file_paths:
        print(f"No files found in '{folder_path}'.")
        return

    # Use multiprocessing.Pool with tqdm
    with Pool(processes=max_workers) as pool:
        list(
            tqdm(
                pool.imap(func, file_paths, chunksize=chunksize),
                total=len(file_paths),
                desc="Processing files",
                unit="file",
            )
        )
