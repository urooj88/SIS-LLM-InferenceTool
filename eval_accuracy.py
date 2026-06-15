#!/usr/bin/env python3
# eval_accuracy.py (UPDATED - consistent Model1/Model2/Model3 + stable header)

import json
import re
import subprocess
import os
import csv

BASE_DIR = os.path.expanduser("~/eut+dats-stats-w26")
BIN_DIR = os.path.join(BASE_DIR, "tools/llama.cpp/build/bin")

LLAMA_COMPLETION = os.path.join(BIN_DIR, "llama-completion")

QWEN_MODEL = os.path.join(BASE_DIR, "models/qwen/Qwen2.5-7B-Instruct-Q4_K_M.gguf")
MISTRAL_MODEL = os.path.join(BASE_DIR, "models/mistral/Mistral-7B-Instruct-v0.3-Q4_K_M.gguf")
LLAMA_MODEL = os.path.join(BASE_DIR, "models/llama/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf")

DATA_PATH = os.path.join("eval_data", "mcq_eval.jsonl")
OUT_PATH = os.path.join("eval_data", "accuracy_results.csv")

THREADS = 28
TOKENS = 8
SEED = 1


def run_one(model_path: str, prompt: str) -> str:
    cmd = [
        LLAMA_COMPLETION,
        "-m", model_path,
        "-p", prompt,
        "-n", str(TOKENS),
        "--temp", "0",
        "--seed", str(SEED),
        "-t", str(THREADS),
        "--simple-io",
        "--log-disable",
        "--no-warmup",
    ]
    p = subprocess.run(
        cmd,
        input=b"",
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False
    )
    return p.stdout.decode("utf-8", errors="ignore").strip()


def extract_answer(text: str):
    t = text.strip()
    m = re.match(r"(?i)^\s*Answer\s*:\s*([ABCD])\s*$", t)
    if m:
        return m.group(1).upper()
    m = re.match(r"^\s*([ABCD])\s*$", t)
    return m.group(1).upper() if m else None


def eval_model(model_path: str, label: str) -> float:
    total = 0
    correct = 0
    bad = 0

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            item = json.loads(line)
            gold = item["answer"].strip().upper()
            ch = item["choices"]

            prompt = (
                "Answer with exactly ONE character: A, B, C, or D.\n"
                "Do not write anything else.\n\n"
                f"Question: {item['question']}\n"
                f"A) {ch['A']}\n"
                f"B) {ch['B']}\n"
                f"C) {ch['C']}\n"
                f"D) {ch['D']}\n"
                "Answer:"
            )

            out = run_one(model_path, prompt)
            pred = extract_answer(out)

            total += 1
            if pred is None:
                bad += 1
                print(f"{label} Q{item.get('id', total)}: BAD_FORMAT | out='{out[:120]}'")
                continue

            if pred == gold:
                correct += 1

            print(f"{label} Q{item.get('id', total)}: pred={pred} gold={gold}")

    acc = (correct / total) * 100 if total else 0.0
    print(f"\n{label} Accuracy (%): {acc:.2f} ({correct}/{total})")
    if bad:
        print(f"{label} bad-format outputs: {bad}/{total}")
    return acc


def main():
    if not os.path.exists(DATA_PATH):
        print(f"[ERROR] Missing dataset: {DATA_PATH}")
        return

    if not os.path.exists(LLAMA_COMPLETION):
        print(f"[ERROR] llama-completion not found at: {LLAMA_COMPLETION}")
        return

    models = [
        (QWEN_MODEL, "Model1"),
        (MISTRAL_MODEL, "Model2"),
        (LLAMA_MODEL, "Model3"),
    ]
    for path, name in models:
        if not os.path.exists(path):
            print(f"[ERROR] Model file missing for {name}: {path}")
            return

    qwen_acc = eval_model(QWEN_MODEL, "Model1")
    mistral_acc = eval_model(MISTRAL_MODEL, "Model2")
    llama_acc = eval_model(LLAMA_MODEL, "Model3")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Model_Name", "Model_Accuracy (%)"])
        w.writerow(["Model1", f"{qwen_acc:.2f}"])
        w.writerow(["Model2", f"{mistral_acc:.2f}"])
        w.writerow(["Model3", f"{llama_acc:.2f}"])

    print("\nSaved:", OUT_PATH)


if __name__ == "__main__":
    main()
