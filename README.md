# zebra

[![OpenReward Environment](https://img.shields.io/badge/%E2%AD%90%20OpenReward-Environment-f7e6cc)](https://openreward.ai/GeneralReasoning/zebra)

## Description

A zebra puzzle (Einstein's riddle) environment that procedurally generates logic grid puzzles with varying difficulty. Each puzzle presents N houses in a row, each with one value per category, and a set of logical clues that uniquely determine the solution. Puzzles range from easy 3x3 grids to extreme 8x7 grids, going well beyond existing benchmarks like ZebraLogic (which caps at 6x6). Verification is fully programmatic with case-insensitive exact matching.

## Capabilities

- Multi-step logical deduction and constraint satisfaction
- Systematic elimination and backtracking reasoning
- Working memory over large state spaces (up to 56 cells at 8x7)
- Spatial reasoning (left-of, neighbor, positional clues)
- Structured output generation (JSON)

## Compute Requirements

No sandbox, GPU, or extra memory required. Puzzles are generated on-the-fly from a deterministic seed. Puzzle generation takes <1s for easy/medium/hard, ~1-3s for very_hard, and ~3-12s for extreme.

## License

MIT

## Tasks

Uses the index-based API (`num_tasks` + `get_task`); `list_tasks` is not supported.

- **Train split**: 10,000 tasks (indices 0-9,999)
- **Test split**: 1,000 tasks (indices 0-999)

Each task is a JSON object with fields:
- `id`: unique identifier (e.g. `"train-42"`)
- `seed`: deterministic seed for puzzle generation
- `split`: `"train"` or `"test"`

Difficulty is distributed across 14 configurations:

| Difficulty | Grid Sizes | Search Space | Share |
|------------|-----------|-------------|-------|
| easy | 3x3, 3x4 | ~10^2 - 10^3 | ~14% |
| medium | 4x4, 4x5 | ~10^5 - 10^7 | ~14% |
| hard | 5x4, 5x5 | ~10^8 - 10^10 | ~14% |
| very_hard | 5x6, 6x5, 6x6 | ~10^12 - 10^17 | ~21% |
| extreme | 7x5 through 8x7 | ~10^20 - 10^32 | ~36% |

## Reward Structure

- **Binary**: 1.0 if all category-house assignments are correct, 0.0 otherwise
- **Sparse**: reward is only given when the agent submits a final answer (single-turn)
- **Programmatic verification**: exact match against the unique solution, case-insensitive for both category names and values

## Data

All task data is generated procedurally at runtime — no external datasets or uploaded files. Each puzzle is deterministically generated from its seed using a constraint propagation solver that guarantees a unique solution. Category values are drawn from 12 thematic pools (nationality, color, drink, pet, hobby, food, transport, music, flower, tree, sport, job).

## Tools

| Tool | Description |
|------|-------------|
| `answer` | Submit a final answer as a JSON string mapping each category to a list of values per house position. Ends the episode. |

Example input:
```json
{"answer": "{\"color\": [\"Red\", \"Blue\", \"Green\"], \"pet\": [\"Cat\", \"Dog\", \"Fish\"]}"}
```

## Time Horizon

Single-turn. The agent receives the puzzle prompt and submits one answer via the `answer` tool.

## Environment Difficulty

Based on the ZebraLogic benchmark (puzzles up to 6x6):
- Best reasoning models (Qwen3, o1-class) now achieve ~97% on 6x6
- Original Claude 3.5 Sonnet achieved 33.4% overall, 12.4% on hard (3x3+) puzzles

This environment extends difficulty well beyond existing benchmarks:
- 57% of tasks are very_hard or extreme (5x6 through 8x7)
- 8x7 puzzles have a search space of ~10^32 and 45+ clues — no published LLM results exist at this scale
- Clue sets are minimally pruned to ensure unique solutions while maximizing reasoning difficulty

## Other Environment Requirements

None. No API keys, secrets, or external services needed.

## Safety

- No access to external systems, network, file system, or APIs
- No dual-use risks — pure logical reasoning domain
- No goal misspecification risk — puzzles have exactly one verifiable correct answer
- Self-contained: all computation happens within the environment process

## Citations

```bibtex
@dataset{GeneralReasoning2026zebra,
  author    = {General Reasoning},
  title     = {Zebra: Logic Grid Puzzle Environment for OpenReward},
  year      = {2026},
  publisher = {OpenReward},
  url       = {https://openreward.ai/GeneralReasoning/zebra}
}
```
