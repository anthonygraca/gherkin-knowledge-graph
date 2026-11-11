# Review packet provenance and recipes

Round 1 (submission 1/7)
- Template: `packet_template.md` (this directory).
- Packet: 192,804 bytes, 3,024 lines,
  sha256 `077eaf64d893d392f6baeea736e6ab28a8716e26bd2e6343df3d59827cb5ca3e`; full text archived
  outside the repository at `~/cta-runs/omp-m0-rereview-1/review-1-prompt.md`.
- Substitutions: HEAD `191c8292f0492d34582f6e33db3cb6f29be9a9e0`, tree
  `29e7ac97f5cdde346a09df5f9852c9d4a22a49e9`, branch, working-tree status, sha256 of
  `docs/architecture.md` (`153d7c6f…e264c02b`), `README.md` (`93b29deb…`),
  `prompts/omp-codex-agentic-loop.md` (`0d1519b2…`), `git diff acf0738a..HEAD` (full),
  `git ls-files -s`, and every file in `evidence/` verbatim.
- Reviewer call: `codex exec --model gpt-6.1-sol -c 'model_reasoning_effort="xhigh"' --sandbox
  read-only --cd <repo> --output-last-message <out> - < <packet>`. Output recorded verbatim at
  `docs/reviews/M0-rereview-1.md` (sha256 `2f1d6091adc97eaa757ad23514220fff4365d458a347ee9ea122354d469eea2a`). Exit 0, 284 s, tokens 149,880.

Round 2 (submission 2/7)
- Template: `packet2_template.md`.
- Packet: 89,237 bytes, 1,608 lines,
  sha256 `03225153e885f12213c013268b749df43013f07e17f1b33f9cfe9d0bc5d26d39`.
- Substitutions: HEAD `bca69cf14a7c94e9ff29ec860fd28fbef83a0798`, tree
  `e55ff9f9b2d669d1417ee1e4df0c858817a1eb82`, the round-1 verdict verbatim, the attestation record,
  `git diff 191c829..HEAD` (docs-only), `git diff acf0738a..HEAD -- backend tools fixtures ruff.toml
  .github`, the cumulative diff stat, the product-tree blob-hash identity proof, `evidence2/`
  verbatim, and `git ls-files -s`.
- Output recorded verbatim at `docs/reviews/M0-rereview-2.md` (sha256
  `08787814859cfc0a1e42e514dec920d430a84b3c8b1da897fc6acf50e5911ac2`). Exit 0, 169 s, tokens
  79,482.

Reproducing a packet: check out the recorded snapshot (the round-1 snapshot included the single
uncommitted `docs/architecture.md` change whose sha256 is listed above), recreate the substitution
values with the git commands named here, take the evidence text from `evidence/` (round 1) or
`evidence2/` (round 2), apply them to the template; the resulting sha256 must match the value above.

Archive (outside the repository): `~/cta-runs/omp-m0-rereview-1/` — full packets, both Codex
stdout/stderr logs, timestamps, exit codes and session ids.
