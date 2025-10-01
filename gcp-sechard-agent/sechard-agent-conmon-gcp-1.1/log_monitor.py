#!/usr/bin/env python3

# log_monitor.py runs indefinitely until certl+c exit tailing the agent_behavior.log and writes to alerts.log

import time
import json
import numpy as np
from pydantic import BaseModel, ValidationError
import sys
import os

# Pydantic model for log validation
class BehaviorLog(BaseModel):
    event: str
    tool_type: str = None
    exec_time: float = None
    inference_time: float = None
    response_length: int = None
    entropy: float = None
    iteration: int = None

# Buffers for running stats (per metric), limit to last 100 for efficiency
buffers = {
    "exec_time": [],
    "inference_time": [],
    "response_length": [],
    "entropy": []
}
BUFFER_MAX = 100

Z_THRESHOLD = 2.5
QUARTILE_THRESHOLD = 1.5

def compute_stats(buffer):
    if len(buffer) < 3:
        return {"mean": 0, "std": 0, "q1": 0, "q3": 0}
    arr = np.array(buffer)
    return {
        "mean": np.mean(arr),
        "std": np.std(arr),
        "q1": np.percentile(arr, 25),
        "q3": np.percentile(arr, 75)
    }

def detect_outlier(value, stats):
    if stats["std"] == 0:
        return False, 0.0
    z_score = (value - stats["mean"]) / stats["std"]
    iqr = stats["q3"] - stats["q1"]
    is_outlier = (value > stats["q3"] + QUARTILE_THRESHOLD * iqr) or abs(z_score) > Z_THRESHOLD
    return is_outlier, z_score

def process_log_line(line):
    try:
        # Split timestamp from JSON (e.g., "2023-10-01 12:00:00 {\"event\": ...}")
        parts = line.split(' ', 1)
        if len(parts) < 2:
            return
        data = json.loads(parts[1])
        validated = BehaviorLog(**data)
        # Append to buffers (limit size)
        if validated.exec_time is not None:
            buffers["exec_time"].append(validated.exec_time)
            buffers["exec_time"] = buffers["exec_time"][-BUFFER_MAX:]
        if validated.inference_time is not None:
            buffers["inference_time"].append(validated.inference_time)
            buffers["inference_time"] = buffers["inference_time"][-BUFFER_MAX:]
        if validated.response_length is not None:
            buffers["response_length"].append(validated.response_length)
            buffers["response_length"] = buffers["response_length"][-BUFFER_MAX:]
        if validated.entropy is not None:
            buffers["entropy"].append(validated.entropy)
            buffers["entropy"] = buffers["entropy"][-BUFFER_MAX:]
        
        # Check for outliers
        for metric, buffer in buffers.items():
            if buffer:
                stats = compute_stats(buffer)
                is_out, z = detect_outlier(buffer[-1], stats)
                if is_out:
                    alert = f"ALERT: Outlier in {metric} (z={z:.2f}, value={buffer[-1]}). Potential security drift!"
                    print(alert)
                    with open("alerts.log", "a") as f:
                        f.write(alert + "\n")
    except (json.JSONDecodeError, ValidationError, ValueError) as e:
        print(f"Invalid log line: {e}")

if __name__ == "__main__":
    log_file = "agent_behavior.log"
    if not os.path.exists(log_file):
        open(log_file, 'a').close()  # Create if missing

    print(f"Monitoring {log_file} for behavioral outliers (using polling)...")
    last_position = 0

    try:
        while True:
            try:
                with open(log_file, 'r') as f:
                    f.seek(last_position)
                    lines = f.readlines()
                    last_position = f.tell()
                    for line in lines:
                        process_log_line(line.strip())
            except IOError as e:
                print(f"Error reading log file: {e}")
            
            time.sleep(0.5)  # Poll every 0.5 seconds (adjust if needed for CPU vs. latency)
    except KeyboardInterrupt:
        print("Monitoring stopped.")