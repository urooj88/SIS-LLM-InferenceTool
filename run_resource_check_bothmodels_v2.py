#!/usr/bin/env python3
# run_resource_check_bothmodels_v2.py (UPDATED - Model names aligned + safer path handling)

import subprocess
import time
import psutil
import csv
import os
from pathlib import Path

# Set this to your project root
PARENT_DIR = Path("/home/urooj/eut+dats-stats-w26/v2tudembeded-model-with-SIS-final").resolve()


def monitor_program(command, model_name, sample_log_file):
    print(f"\n[START] Executing: {model_name}")
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    ps_proc = psutil.Process(process.pid)

    print(f"[INFO] Monitoring PID {process.pid} for: {model_name}...")

    start_time = time.time()
    cpu_samples = []
    mem_samples = []

    with open(sample_log_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Time_s", "CPU_Use_%", "Mem_GiB"])

        try:
            while process.poll() is None:
                timestamp = time.time() - start_time

                try:
                    cpu = ps_proc.cpu_percent(interval=0.1)
                    mem = ps_proc.memory_info().rss

                    for child in ps_proc.children(recursive=True):
                        try:
                            cpu += child.cpu_percent(interval=0.1)
                            mem += child.memory_info().rss
                        except psutil.NoSuchProcess:
                            continue

                    mem_gib = mem / (1024 ** 3)

                    cpu_samples.append(cpu)
                    mem_samples.append(mem_gib)

                    writer.writerow([round(timestamp, 2), round(cpu, 2), round(mem_gib, 3)])
                    print(
                        f"[RUNNING] {model_name} | Time: {round(timestamp, 2)}s | "
                        f"CPU: {round(cpu, 2)}% | MEM: {round(mem_gib, 3)} GiB"
                    )

                    time.sleep(1.9)

                except psutil.NoSuchProcess:
                    break

        except Exception as e:
            print(f"[ERROR] Error while monitoring {model_name}: {str(e)}")

    elapsed = time.time() - start_time

    out, err = process.communicate()
    if process.returncode != 0:
        print(f"\n[ERROR] {model_name} failed with exit code {process.returncode}")
        if out:
            print("\n[STDOUT]\n" + out)
        if err:
            print("\n[STDERR]\n" + err)

    avg_cpu = (sum(cpu_samples) / len(cpu_samples)) if cpu_samples else 0
    max_mem = max(mem_samples) if mem_samples else 0
    cpu_hrs = (avg_cpu / 100.0) * (elapsed / 3600.0)

    print(f"\n[FINISH] {model_name} | Elapsed time: {round(elapsed, 2)} seconds\n")

    return {
        "Model_Name": model_name,
        "Total_Execution_Time_s": round(elapsed, 2),
        "CPU_Use_%": round(avg_cpu, 2),
        "Max_Mem_GiB": round(max_mem, 3),
        "CPU_Core_Hours": round(cpu_hrs, 6),
        "Exit_Code": process.returncode
    }


def main():
    output_summary_file = PARENT_DIR / "models_resources_logs.csv"

    model_runs = [
        {
            "command": ["bash", str(PARENT_DIR / "run_set_model1.sh")],
            "name": "Model1",
            "sample_file": str(PARENT_DIR / "model1_samples.csv")
        },
        {
            "command": ["bash", str(PARENT_DIR / "run_set_model2.sh")],
            "name": "Model2",
            "sample_file": str(PARENT_DIR / "model2_samples.csv")
        },
        {
            "command": ["bash", str(PARENT_DIR / "run_set_model3.sh")],
            "name": "Model3",
            "sample_file": str(PARENT_DIR / "model3_samples.csv")
        }
    ]

    all_metrics = []

    for i, model in enumerate(model_runs):
        metrics = monitor_program(model["command"], model["name"], model["sample_file"])
        all_metrics.append(metrics)

        if i < len(model_runs) - 1:
            print("\n[WAITING] Pausing for 20 seconds before the next model...\n")
            time.sleep(20)

    with open(output_summary_file, "w", newline="") as f:
        fieldnames = ["Model_Name", "Total_Execution_Time_s", "CPU_Use_%", "Max_Mem_GiB", "CPU_Core_Hours", "Exit_Code"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in all_metrics:
            writer.writerow(row)

    print(f"\n[OK] Final summary saved to: {output_summary_file}")
    print(f"[OK] Sample logs saved to: {PARENT_DIR/'model1_samples.csv'}, {PARENT_DIR/'model2_samples.csv'}, {PARENT_DIR/'model3_samples.csv'}")


if __name__ == "__main__":
    main()
