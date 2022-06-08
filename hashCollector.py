"""Hash Collector

Usage:
    hashCollector.py [-r] PATH ... [--mode=string> --extension=<string> --publish=<bool> --max_size=<size>, --thread_count=<int>]
    hashCollector.py (-h | --help)
    hashCollector.py --version
Options:
    -h --help                   Show this screen
    -m --mode=<string>          Hashing algorithm [default: sha1]
    -e --extension=<string>     Extension of files to hash [default: ]
    -r                          Recursive Mode
    --max_size=<size>           Max file size to hash in bytes [default: 268435456]
    --thread_count=<int>        Thread count [default: 5]
    --publish=<bool>            Save to file [default: False]
    --version                   Show version
"""
import os
import hashlib
import glob
import json
import csv
import threading
from docopt import docopt


def chunkify(lst: list, n: int):
    """Splits a list into even parts"""
    return [lst[i::n] for i in range(n)]

def check_file_size(path, max_size):
    """Checks if file is bigger than threshold"""
    file_size = os.path.getsize(path)
    if file_size < int(max_size):
        return True
    else:
        return False

def hash_file(path: str, mode: str, max_size):
    """Helper function to hash the file"""
    BUF_SIZE = 65536
    modes = {
        "md5": hashlib.md5,
        "sha1": hashlib.sha1,
        "sha256": hashlib.sha256
    }
    hasher = modes[mode]()
    try:
        if check_file_size(path, max_size):
            with open(path, 'rb') as f:
                while True:
                    data = f.read(BUF_SIZE)
                    if not data:
                        break
                    hasher.update(data)
            return hasher.hexdigest()
    except PermissionError as error:
        print(f"[!] {error}")

def publish_results(results: list, publish: bool):
    """Prints to StdOut(json) or saves as file(csv)"""
    if publish != 'False':
        csv_columns = ["FileName", "Hash", "Path", "Type"]
        try:
            with open("hash_results.csv", "w", newline='', encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
                writer.writeheader()
                for lst in results:
                    writer.writerow(lst)
        except IOError:
            print("I/O error")
    else:
        print(json.dumps(results, indent=4, sort_keys=True))

def get_hashes(hash_paths: list, extension: str, mode: str, max_size: int):
    """Gathers the hash of files for the input directory"""
    for path in hash_paths:
        if not os.path.isdir(path):
            # extension filter
            if path.endswith(extension):
                results.append({"Path": os.path.dirname(path), "Hash": hash_file(path, mode, max_size),
                                "FileName": os.path.basename(path), "Type": mode})

def get_file_paths(hash_paths: list, recursive: bool):
    """Collects file paths and gets hashes"""
    paths_to_hash = []
    for hash_path in hash_paths:
        if os.path.isabs(hash_path):
            if os.path.isdir(hash_path):
                paths_to_hash.extend(glob.glob(f"{hash_path}/**", recursive=recursive))
            else:
                paths_to_hash.append(hash_path)
        else:
            print(f"[!] Absolute path required. Path provided: {hash_path}. Exiting!")
            exit(1)

    return paths_to_hash


if __name__ == "__main__":
    args = docopt(__doc__, version="HashCollector 1.0")
    results = []
    hash_paths = get_file_paths(hash_paths=args["PATH"], recursive=args["-r"])
    # if less than 25 paths, do not thread
    if len(hash_paths) >= 25:
        threads = []
        for paths in chunkify(hash_paths, int(args["--thread_count"])):
            single_thread = threading.Thread(target=get_hashes, args=(paths, args["--extension"],
                                                                      args["--mode"], args["--max_size"]))
            threads.append(single_thread)
            single_thread.start()
        for t in threads:
            t.join()
    else:
        get_hashes(hash_paths=hash_paths, extension=args["--extension"], mode=args["--mode"],
                   max_size=args["--max_size"])
    # output
    publish_results(results, args["--publish"])

