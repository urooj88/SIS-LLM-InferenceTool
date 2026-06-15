#!/usr/bin/env python3
# auto_fill_inference_csv.py (UPDATED - reads accuracy correctly + includes Model3)

import os, re, subprocess, pandas as pd

BASE_DIR = os.path.expanduser("~/eut+dats-stats-w26")
SIS_DIR  = os.path.dirname(os.path.abspath(__file__))

CSV_PATH = os.path.join(SIS_DIR, "model_inference_data.csv")
PROMPTS  = os.path.join(SIS_DIR, "test_models", "prompts.txt")
ACC_CSV  = os.path.join(SIS_DIR, "eval_data", "accuracy_results.csv")

QWEN_GGUF    = os.path.join(BASE_DIR, "models/qwen/Qwen2.5-7B-Instruct-Q4_K_M.gguf")
MISTRAL_GGUF = os.path.join(BASE_DIR, "models/mistral/Mistral-7B-Instruct-v0.3-Q4_K_M.gguf")
LLAMA_GGUF   = os.path.join(BASE_DIR, "models/llama/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf")

BIN_DIR = os.path.join(BASE_DIR, "tools/llama.cpp/build/bin")
LLAMA_GGUF_BIN = os.path.join(BIN_DIR, "llama-gguf")
LLAMA_CLI  = os.path.join(BIN_DIR, "llama-cli")

DEFAULT_CI = 300.0
TOKENS_FOR_FLOPS = 64


def count_prompts(path: str) -> int:
    with open(path, "r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def file_size_mb(path: str) -> float:
    return round(os.path.getsize(path) / (1024 * 1024), 2)


def read_accuracy(model_name: str) -> float:
    if not os.path.exists(ACC_CSV):
        return 0.0

    df = pd.read_csv(ACC_CSV)

    if "Model_Accuracy (%)" in df.columns:
        acc_col = "Model_Accuracy (%)"
    elif "Model_Acuracy (%)" in df.columns:
        acc_col = "Model_Acuracy (%)"
    else:
        return 0.0

    if "Model_Name" not in df.columns:
        return 0.0

    row = df[df["Model_Name"].astype(str) == model_name]
    if row.empty:
        return 0.0

    return float(row[acc_col].values[0])


def flops_per_inference(params: int, tokens: int) -> int:
    return int(2 * params * tokens)


def parse_params_from_llama_gguf(model_path: str) -> int:
    if not os.path.exists(LLAMA_GGUF_BIN):
        raise RuntimeError(f"llama-gguf not found at {LLAMA_GGUF_BIN}")

    cmd = [LLAMA_GGUF_BIN, "info", model_path]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    out = p.stdout.decode("utf-8", errors="ignore")

    m = re.search(r"model params\s*[:=]\s*([\d.]+)\s*B", out, re.I)
    if m:
        return int(round(float(m.group(1)) * 1_000_000_000))

    m = re.search(r"general\.size_label\s*[:=]\s*([0-9]+)\s*B", out, re.I)
    if m:
        return int(m.group(1)) * 1_000_000_000

    m = re.search(r"n_params\s*[:=]\s*([0-9]+)", out, re.I)
    if m:
        return int(m.group(1))

    raise RuntimeError("Could not parse params from llama-gguf output.")


def parse_params_from_llama_cli_fallback(model_path: str) -> int:
    if not os.path.exists(LLAMA_CLI):
        raise RuntimeError(f"llama-cli not found at {LLAMA_CLI}")

    cmd = [LLAMA_CLI, "-m", model_path, "-p", "x", "-n", "0", "--temp", "0", "-t", "1", "--simple-io"]
    p = subprocess.run(cmd, input=b"", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    out = p.stdout.decode("utf-8", errors="ignore")
    m = re.search(r"model params\s*=\s*([\d.]+)\s*B", out, re.I)
    if not m:
        raise RuntimeError("Could not parse params from llama-cli output.")
    return int(round(float(m.group(1)) * 1_000_000_000))


def get_params(model_path: str) -> int:
    try:
        return parse_params_from_llama_gguf(model_path)
    except Exception:
        return parse_params_from_llama_cli_fallback(model_path)


def ensure_csv():
    if not os.path.exists(CSV_PATH):
        pd.DataFrame(columns=[
            "Model_Name", "queries", "Model_Accuracy (%)", "T_Model_Size (MB)",
            "Learned_Parameters", "Flops_per_Inference", "Carbon _Intensity (gCO₂/kWh)"
        ]).to_csv(CSV_PATH, index=False)


def main():
    ensure_csv()
    df = pd.read_csv(CSV_PATH)

    queries = count_prompts(PROMPTS)

    qwen_params = get_params(QWEN_GGUF)
    mis_params = get_params(MISTRAL_GGUF)
    llama_params = get_params(LLAMA_GGUF)

    rows = [
        {
            "Model_Name": "Model1",
            "queries": queries,
            "Model_Accuracy (%)": read_accuracy("Model1"),
            "T_Model_Size (MB)": file_size_mb(QWEN_GGUF),
            "Learned_Parameters": qwen_params,
            "Flops_per_Inference": flops_per_inference(qwen_params, TOKENS_FOR_FLOPS),
            "Carbon _Intensity (gCO₂/kWh)": DEFAULT_CI
        },
        {
            "Model_Name": "Model2",
            "queries": queries,
            "Model_Accuracy (%)": read_accuracy("Model2"),
            "T_Model_Size (MB)": file_size_mb(MISTRAL_GGUF),
            "Learned_Parameters": mis_params,
            "Flops_per_Inference": flops_per_inference(mis_params, TOKENS_FOR_FLOPS),
            "Carbon _Intensity (gCO₂/kWh)": DEFAULT_CI
        },
        {
            "Model_Name": "Model3",
            "queries": queries,
            "Model_Accuracy (%)": read_accuracy("Model3"),
            "T_Model_Size (MB)": file_size_mb(LLAMA_GGUF),
            "Learned_Parameters": llama_params,
            "Flops_per_Inference": flops_per_inference(llama_params, TOKENS_FOR_FLOPS),
            "Carbon _Intensity (gCO₂/kWh)": DEFAULT_CI
        },
    ]

    for r in rows:
        if (df["Model_Name"].astype(str) == r["Model_Name"]).any():
            for k, v in r.items():
                df.loc[df["Model_Name"].astype(str) == r["Model_Name"], k] = v
        else:
            df = pd.concat([df, pd.DataFrame([r])], ignore_index=True)

    df.to_csv(CSV_PATH, index=False)
    print("Updated:", CSV_PATH)
    print(df[df["Model_Name"].isin(["Model1", "Model2", "Model3"])].to_string(index=False))


if __name__ == "__main__":
    main()
