import json
import csv
from datetime import datetime


def log_json(data: dict, file_path: str):
    data["_timestamp"] = datetime.utcnow().isoformat()
    with open(file_path, "w") as f:
        f.write(json.dumps(data) + "\n")


def log_csv(data: dict, file_path: str):
    data["_timestamp"] = datetime.utcnow().isoformat()
    filednames = data.keys()

    try:
        with open(file_path, "w") as f:
            writer = csv.DictWriter(f, fieldnames=filednames)
            if f.tell() == 0:
                writer.writeheader()
            writer.writerow(data)
    except Exception as e:
        print("CSV log error", e)
