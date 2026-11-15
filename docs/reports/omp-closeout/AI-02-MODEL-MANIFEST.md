# AI-02 — Accepted local model manifest

**Status:** accepted for the close-out mission · 2026-11-14
**Story:** AI-02 (#31) · **ADR:** [0012](../adr/0012-closeout-scope-decisions.md) §4
**Machine:** this workstation only; no shared DGX, K3s, remote Ollama, hosted endpoint, proxy, or
request leaving the machine.

## Model

|Field|Value|
|---|---|
|Distribution|`onnx-community/embeddinggemma-2-ONNX`|
|Distribution revision|`daa72c51243991dfcaf9f9137d2c573d8f7790c0`|
|Base model|`google/embeddinggemma-2` (740 M total; 270 M text backbone: 130 M transformer + 140 M embedder)|
|Variant|`embeddinggemma-2-text-270m`, quantized ONNX text encoder|
|Licence|Apache-2.0 (Hugging Face model metadata and model card)|
|Output dimension|768 (native); CTA uses the full 768 dimensions|
|Pooling|model-provided `sentence_embedding` output; CTA L2-normalizes again and rejects zero/non-finite vectors|
|Max tokens|512 (tokenizer truncation)|

## Weights and tokenizer digests

The combined weights digest covers the ONNX graph and its external data file, including each file
name, in this order:

|File|Bytes|SHA-256|
|---|---:|---|
|`onnx/model_quantized.onnx`|495,165|`d06edd601f851c633a2519304cbeb8dc6170d7ceb61b436625c17fb9b6e74953`|
|`onnx/model_quantized.onnx_data`|313,724,928|`278a7ff1248c3618e4bd11a607fc54f7bdc7778854230f3956d3f86bd9db4f3b`|
|`tokenizer.json`|32,170,510|`4d777ef5bdc1aa36227abdfb77c3e49e7b9c892d16e1b6bda41c393504828be4`|
|`config.json`|5,031|`8d011bfe08b5e345bbe0b81e5c6fd02c381920b345b986047bc2a33ce7b90d1d`|

**Combined weights digest:** `sha256:b396bde0f7a85398c9c42d08a3c0b68d30952e91dcd408bfa327c727e86457a3`

The local provider reports `model_version =
embeddinggemma-2-text-270m-q8_0@sha256:b396bde0f7a8` and rejects a configured weights digest that
does not match the installed files.

## Runtime

|Component|Version|
|---|---|
|Python|3.12.16|
|`onnxruntime`|1.32.0 (`CPUExecutionProvider`)|
|`tokenizers`|0.23.3|
|`numpy`|2.5.4|
|`huggingface-hub`|0.36.2 (provisioning only; not imported by the provider)|

Install: `uv sync --project backend --extra local-embedding`. The default `uv sync` and every
default test/CI path do not install or import this extra.

## Hardware and measured limits

|Field|Value|
|---|---|
|CPU|Intel Core i5-7500T @ 2.70 GHz, 4 logical CPUs|
|RAM|15 GiB total; no GPU|
|Model disk footprint|~346 MiB (graph + external data + tokenizer + config)|
|Runtime load|2.38–3.61 s (pytest vs live bridge)|
|Corpus build (10 banking artifacts, CPU)|5.94–21.81 s across retained runs|
|Warm query median|0.365–2.225 s (pytest vs live bridge; the bridge includes API/thread checks)|
|RSS delta after load, indexing, and queries|~506–508 MiB|

The live bridge's timing includes the TestClient thread checks and is not directly comparable to
the pytest measurement; both raw records are retained rather than collapsed into one number.

**Observed smoke result (not a retrieval-quality benchmark):** for `SCN-001`, the model ranks
`CODE-001` first and `TEST-001` second; `SCN-002` ranks `CODE-002` first; `REQ-001` ranks `SCN-001`
first. These are one-corpus observations, not a general claim about model quality.

## Formatting

|Path|Template|
|---|---|
|Scenario/requirement → code|`task: code retrieval | query: `|
|Requirement → scenario|`task: search result | query: `|
|Document|`title: {locator} | text: {content}`|

Formatting version: `ai02-code-query-v1/document-title-text-v1`. Scenario documents are extracted
from their `@SCN-nnn` block; source/test documents are the committed blob at the selected commit.
Every candidate carries the model version and a CTA corpus/snapshot binding
(`sha256` over the resolved commit, artifact IDs/paths/revisions/content hashes, model version,
weights digest, formatting version, and dimension).

## Failure modes

|Condition|Outcome|
|---|---|
|No local opt-in|`fake` remains the default; the local module/runtime is not imported.|
|Remote endpoint configured|`400 invalid-request` before any connection is attempted.|
|Model directory or weights absent|`503 retrieval-unavailable`; no download, no remote fallback.|
|Configured weights digest mismatch|`503 retrieval-unavailable`.|
|Runtime package missing|`503 retrieval-unavailable` with the install command.|
|Non-finite, wrong-dimension, or zero embedding|`503 retrieval-unavailable`; no partial candidate list.|
|Accepted links/evidence/findings|Never written by the provider.|

## Egress evidence

The live test and live Cucumber scenario were executed under `unshare -rn` with
`CTA_EGRESS_DENIED=1`; both exited 0, and the bridge's probe to `192.0.2.1:9` failed as expected.
See [AI-02-EVIDENCE.md](AI-02-EVIDENCE.md). No non-loopback interface exists in that namespace.
