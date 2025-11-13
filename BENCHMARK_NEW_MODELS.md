# Small Reasoning & Agentic Models Summary

## Top Reasoning Models

| Model                              | Size | Released     | AIME 2024                  | AIME 2025                  | Memory (4-bit) | Key Strengths                                                       |
| ---------------------------------- | ---- | ------------ | -------------------------- | -------------------------- | -------------- | ------------------------------------------------------------------- |
| **Qwen3-14B**                      | 14B  | May 2025     | 73.8%                      | 65.6%                      | ~9GB           | Hybrid thinking modes, MCP support, 119 languages, best all-rounder |
| **OpenReasoning-Nemotron-32B**     | 32B  | July 2025    | 89.2% (93.3% w/ GenSelect) | 84.0% (93.3% w/ GenSelect) | 18-22GB        | GenSelect mode, matches o3-High, supervised fine-tuning only        |
| **Phi-4-reasoning-plus**           | 14B  | Apr 2025     | 81.3%                      | 78.0%                      | 8-10GB         | Rivals o3-mini, trained on edge-of-capability data, STEM-focused    |
| **AceReason-Nemotron-14B**         | 14B  | May 2025     | 78.6%                      | 67.4%                      | ~9GB           | Sequential domain RL, Codeforces Elo 2024, strong code reasoning    |
| **OpenCodeReasoning-Nemotron-32B** | 32B  | May 2025     | N/A                        | N/A                        | 18-20GB        | Competitive programming specialist, Tool-Integrated Reasoning (TIR) |
| **DeepSeek-R1-Distill-Qwen-32B**   | 32B  | Jan/May 2025 | 72.6%                      | N/A                        | 18-20GB        | Transparent 23K-token reasoning chains, foundation for many models  |

## Top Agentic/Tool-Use Models

| Model                      | Size  | BFCL Score         | Memory (4-bit) | Key Features                                                        |
| -------------------------- | ----- | ------------------ | -------------- | ------------------------------------------------------------------- |
| **Functionary-small-v3.2** | 8B    | 82.82%             | 4-5GB          | #2 globally on BFCL, OpenAI API compatible, reason-then-act pattern |
| **Qwen3 series**           | 8-32B | High (undisclosed) | 7-18GB         | Native MCP support, hybrid thinking, tool coordination              |
| **Hermes-3-Llama-3.1-8B**  | 8B    | ~78-80%            | ~4GB           | Hermes Function Calling Standard, internal monologue, 128K context  |
| **Llama 3.1/3.2**          | 8B    | ~70-75%            | 4-5GB          | Pythonic function calling, baseline capabilities                    |
| **Command-R**              | 35B   | Beats GPT-4-turbo  | 20-22GB        | Zero-shot multi-step tools, RAG with citations, ReAct agents        |

## Quick Reference Guide

**Best for Temporal Pattern Analysis (Prism/PrismQL):**

- **Primary:** Qwen3-14B (versatile, MCP support, 9GB)
- **Pure Reasoning:** OpenReasoning-Nemotron-14B (analytical depth, 8-14GB)
- **Tool Orchestration:** Functionary-small-v3.2 (reliable APIs, 4-5GB)

**Memory Sweet Spots on A6000 (48GB):**

- 14B models @ 4-bit: 7-10GB (leaves 38-41GB for context/batching)
- 32B models @ 4-bit: 16-22GB (leaves 26-32GB for operations)
- Multi-model: Two 14B + one 8B = ~22GB total

**Recommended Configuration:**

- Quantization: AWQ 4-bit (production) or GGUF Q4_K_M (development)
- Framework: vLLM (production serving) or llama.cpp (experimentation)
- Settings: Temperature 0.6, top-p 0.95, 32K context
- Strategy: Batch prompting (5-15 queries) for 74% efficiency gain
