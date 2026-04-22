"""Zebra puzzle environment for OpenReward."""
import json

from pydantic import BaseModel

from openreward.environments import Environment, JSONObject, Server, Split, TextBlock, ToolOutput, tool
from zebra import generate_puzzle, format_puzzle, score_answer

# Split sizes
TRAIN_SIZE = 10_000
TEST_SIZE = 1_000
# Offset test seeds so train and test don't overlap
TEST_SEED_OFFSET = 1_000_000


class ZebraTaskSpec(BaseModel):
    id: str
    seed: int
    split: str


class AnswerParams(BaseModel):
    answer: str


class Zebra(Environment):
    """
    A zebra puzzle (Einstein's riddle) environment.

    Generates logic grid puzzles of varying difficulty where houses in a row
    each have one value per category, and clues constrain the unique solution.
    """

    def __init__(self, task_spec: JSONObject = {}, secrets: dict[str, str] = {}):
        super().__init__(task_spec)
        self.config = ZebraTaskSpec.model_validate(task_spec)
        self.puzzle = generate_puzzle(seed=self.config.seed)

    @classmethod
    def list_splits(cls):
        return [Split(name="train", type="train"), Split(name="test", type="test")]

    @classmethod
    def list_tasks(cls, split: str):
        raise NotImplementedError(
            "Zebra uses the index-based API (num_tasks + get_task). "
            "Call num_tasks and get_task instead."
        )

    @classmethod
    async def num_tasks(cls, split: str) -> int:
        if split == "train":
            return TRAIN_SIZE
        elif split == "test":
            return TEST_SIZE
        raise ValueError(f"Unknown split: {split}")

    @classmethod
    async def get_task(cls, split: str, index: int) -> JSONObject:
        if split == "train":
            if index < 0 or index >= TRAIN_SIZE:
                raise IndexError(f"Index {index} out of range for train split (0-{TRAIN_SIZE - 1})")
            seed = index
        elif split == "test":
            if index < 0 or index >= TEST_SIZE:
                raise IndexError(f"Index {index} out of range for test split (0-{TEST_SIZE - 1})")
            seed = TEST_SEED_OFFSET + index
        else:
            raise ValueError(f"Unknown split: {split}")

        return {"id": f"{split}-{index}", "seed": seed, "split": split}

    def get_prompt(self):
        prompt_text = format_puzzle(self.puzzle)
        return [TextBlock(type="text", text=prompt_text)]

    @tool
    async def answer(self, params: AnswerParams) -> ToolOutput:
        """
        Submit your answer to the zebra puzzle. Provide a JSON object mapping each category
        to a list of values, where the i-th element is the value for house i (1-indexed positions,
        0-indexed in the list).

        For example: {"color": ["Red", "Blue", "Green"], "pet": ["Cat", "Dog", "Fish"]}

        This finishes the episode.
        """
        try:
            parsed = json.loads(params.answer)
        except json.JSONDecodeError as e:
            return ToolOutput(
                blocks=[TextBlock(type="text", text=f"Invalid JSON: {e}")],
                reward=0.0,
                finished=True,
            )

        if not isinstance(parsed, dict):
            return ToolOutput(
                blocks=[TextBlock(type="text", text="Answer must be a JSON object mapping categories to lists.")],
                reward=0.0,
                finished=True,
            )

        reward, message = score_answer(self.puzzle, parsed)
        return ToolOutput(
            blocks=[TextBlock(type="text", text=message)],
            reward=reward,
            finished=True,
        )


if __name__ == "__main__":
    Server([Zebra]).run()
