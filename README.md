# SIS-LLM: LLM Inference Sustainability on CPU+GPU Deployments

**Developed by Urooj Asgher** 
Technological University Dublin, Ireland 
ORCID: 0000-0001-9218-3307

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Author](https://img.shields.io/badge/Author-Urooj%20Asgher-blue)](https://orcid.org/0000-0001-9218-3307)
[![HPC Nexus Lab](https://img.shields.io/badge/HPC-Nexus%20Lab-purple)](https://github.com/HPC-Nexus-Lab)
[![Institution](https://img.shields.io/badge/TU%20Dublin-Ireland-green)](https://www.tudublin.ie)
[![Paper](https://img.shields.io/badge/Paper-SIS--LLM-orange)](https://your-paper-link-here)

---

## Overview

**SIS-LLM** is a unified framework for evaluating the sustainability of Large Language Model (LLM) inference. It combines performance, efficiency, and environmental metrics into a single interpretable score — the **Sustainability Index Score (SIS)**.

> This is the **CPU version**, evaluated on an HPC server using CPU-only execution with physical power metering via an **Adcewatt** power meter.

---

## Methodology

The SIS framework follows three main steps:

### Step 1 — Measurement
During inference, both model-level and system-level metrics are captured:
- **Model-level:** accuracy (GSM8K, MMLU, TruthfulQA), FLOPs, model size, token counts
- **System-level:** energy consumption (Joules), execution time, memory usage, CPU hours
- **Environmental:** carbon emissions estimated from energy and carbon intensity (gCO₂/kWh)

Energy is measured using a physical **Adcewatt power meter** connected via serial port. Dynamic energy is computed by subtracting idle baseline power from total measured power:

```
Dynamic Energy (J) = (Total Power − Baseline Power) × Execution Time
Carbon Emissions   = (Dynamic Energy ÷ 3,600,000) × Carbon Intensity
```

### Step 2 — Normalisation
All metrics are normalised to a common scale [0, 1] to enable fair comparison:

- **Lower is better** (energy, CO₂, runtime, memory, FLOPs, model size):
```
Norm = (x − min) / (max − min)
```
- **Higher is better** (accuracy, throughput, token energy efficiency):
```
Norm = 1 − (x − min) / (max − min)
```

### Step 3 — SIS Score
The final SIS is computed as a weighted sum of all normalised metrics with equal weights:

```
SIS = 1 − Σ (wᵢ × Normᵢ)     where wᵢ = 1/9
```

**Lower SIS = better sustainability.**

### SIS Classification

| SIS Score | Sustainability Level |
|---|---|
| 0.0 – 0.3 | 🟢 Low Impact |
| 0.3 – 0.7 | 🟡 Medium Impact |
| 0.7 – 1.0 | 🔴 High Impact |

### Metrics Used in SIS

| Metric | Unit | Goal |
|---|---|---|
| Energy Consumption | Joules/Query | Lower is better |
| Carbon Emissions | gCO₂eq/Query | Lower is better |
| Execution Time | Seconds/Query | Lower is better |
| Memory Usage | GB | Lower is better |
| FLOPs | Per inference | Lower is better |
| Model Size | MB | Lower is better |
| Accuracy | % | Higher is better |
| Throughput | Tokens/sec | Higher is better |
| Token Energy Efficiency | Tokens/J | Higher is better |

---

## Models Evaluated

| Model | Parameters | Quantisation |
|---|---|---|
| Qwen2.5-7B-Instruct | 7B | GGUF Q4\_K\_M |
| Mistral-7B-Instruct-v0.3 | 7B | GGUF Q4\_K\_M |
| Meta-Llama-3.1-8B-Instruct | 8B | GGUF Q4\_K\_M |
| Phi-3.5-mini-Instruct | 3.8B | GGUF Q4\_K\_M |

All models are deployed using [`llama.cpp`](https://github.com/ggerganov/llama.cpp) with GGUF Q4\_K\_M quantisation.

---

## Benchmarks

| Dataset | Task | Samples |
|---|---|---|
| GSM8K | Mathematical Reasoning | 500 |
| MMLU | Multi-domain MCQ | 500 |
| TruthfulQA | Factual Truthfulness | 500 |

**Total: 1500 prompts per model** (fixed seed = 42)

---

## Repository Structure

```
SIS-LLM/
├── README.md
├── requirements.txt
├── main_sustainability_runner_LLM_CPU.py    ← Main entry point
├── build_eval_dataset.py                    ← Builds evaluation dataset
├── run_omegawatt_log_both_models12_same.sh  ← Runs all 4 models with power logging
├── run_screen_job_v1.sh                     ← HPC job runner with logging
├── omegawatt_scripts/
│   ├── run_omegawatt_log_models12.py        ← Per-model power logger
│   └── run_basepower_adcewatt_var_std.py    ← Baseline power measurement
└── test_models/
    ├── collect_inference_metrics.py         ← Computes accuracy and metrics
    ├── model1.sh                            ← Qwen2.5
    ├── model2.sh                            ← Mistral
    ├── model3.sh                            ← LLaMA
    └── model4.sh                            ← Phi-mini
```

---

## Installation

```bash
git clone https://github.com/urooj88/SIS-LLM-InferenceTool.git
cd SIS-LLM-InferenceTool
pip install -r requirements.txt
```

Also install [`llama.cpp`](https://github.com/ggerganov/llama.cpp) and download GGUF Q4\_K\_M models from HuggingFace:

| Model | HuggingFace |
|---|---|
| Qwen2.5-7B | [Link](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF) |
| Mistral-7B | [Link](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3-GGUF) |
| LLaMA-3.1-8B | [Link](https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF) |
| Phi-3.5-mini | [Link](https://huggingface.co/bartowski/Phi-3.5-mini-instruct-GGUF) |

Update `MODEL` and `LLAMA_CLI` paths in each `test_models/model*.sh`.

---

## Usage

### Step 1 — Build dataset (first time only)
```bash
python3 build_eval_dataset.py --reason 500 --mcq 500 --truth 500 --force-rebuild
```

### Step 2 — Run the full pipeline
```bash
python3 main_sustainability_runner_LLM_CPU.py
```

### Step 3 — View results
```
model_logs/sustainability_detailed_report.txt
model_logs/updated_sustainability_metrics.xlsx
```

---

## Hardware Requirements

- CPU server (~5–6 GB RAM per model)
- Adcewatt power meter via `/dev/ttyUSB0`
- Adcewatt binary (`wattmetre-readmv2new`)
- llama.cpp

> Tested on: 2× Intel Xeon Gold 6430 (64 cores, 128 threads), GPU disabled via `CUDA_VISIBLE_DEVICES=""`

---

## Citation

```bibtex
@inproceedings{asgher2025sis,
  title  = {SIS: A Sustainability Index for Evaluating Energy-Efficient LLM
            Inference Across CPU and GPU Deployments},
  author = {Asgher, Urooj and Malik, Tania},
  year   = {2025},
  institution = {Technological University Dublin, Ireland}
}
```

---

## Acknowledgements

Experiments were carried out using the HPCNexus testbed at Technological University Dublin.

---

## License

MIT License — see [LICENSE](LICENSE) for details.
