"""
Zebra puzzle generator with varying difficulty.

Generates Einstein/zebra-style logic grid puzzles where:
- N houses in a row each have exactly one value from each category
- A set of clues constrains the solution
- There is exactly one valid solution

Difficulty is controlled by:
- Number of houses (3-8)
- Number of categories (3-8)
- Clue density (fewer clues = harder)
"""

import random
from dataclasses import dataclass, field
from itertools import permutations


# Category value pools - enough for up to 8 houses per category
CATEGORY_POOLS = {
    "nationality": ["Norwegian", "Brit", "Swede", "Dane", "German", "Japanese", "Italian", "Spaniard"],
    "color": ["Red", "Green", "Blue", "Yellow", "White", "Ivory", "Orange", "Purple"],
    "drink": ["Water", "Tea", "Coffee", "Milk", "Juice", "Soda", "Wine", "Cocoa"],
    "pet": ["Dog", "Cat", "Bird", "Fish", "Horse", "Turtle", "Rabbit", "Hamster"],
    "hobby": ["Reading", "Painting", "Cooking", "Gardening", "Chess", "Music", "Dancing", "Knitting"],
    "food": ["Pizza", "Sushi", "Pasta", "Tacos", "Burger", "Salad", "Steak", "Soup"],
    "transport": ["Car", "Bike", "Bus", "Train", "Walk", "Scooter", "Subway", "Boat"],
    "music": ["Jazz", "Rock", "Classical", "Pop", "Blues", "Country", "Reggae", "Metal"],
    "flower": ["Rose", "Lily", "Tulip", "Daisy", "Orchid", "Sunflower", "Violet", "Iris"],
    "tree": ["Oak", "Pine", "Maple", "Birch", "Willow", "Cedar", "Elm", "Ash"],
    "sport": ["Soccer", "Tennis", "Baseball", "Swimming", "Golf", "Rugby", "Hockey", "Cricket"],
    "job": ["Doctor", "Teacher", "Engineer", "Artist", "Chef", "Lawyer", "Pilot", "Nurse"],
}

ALL_CATEGORIES = list(CATEGORY_POOLS.keys())


@dataclass
class Clue:
    """A single clue in a zebra puzzle."""
    type: str  # "same_house", "neighbor", "left_of", "immediate_left", "position", "not_same_house"
    description: str
    # Internal data for verification
    data: dict = field(default_factory=dict)


def _generate_solution(n_houses: int, categories: list[str], rng: random.Random) -> dict[str, list[str]]:
    """Generate a random valid assignment: category -> [value_for_house_0, ..., value_for_house_n-1]."""
    solution = {}
    for cat in categories:
        pool = CATEGORY_POOLS[cat][:n_houses]
        values = list(pool)
        rng.shuffle(values)
        solution[cat] = values
    return solution


def _check_solution(solution: dict[str, list[str]], clues: list[Clue], n_houses: int) -> bool:
    """Check if a solution satisfies all clues."""
    for clue in clues:
        if not _check_clue(solution, clue, n_houses):
            return False
    return True


def _check_clue(solution: dict[str, list[str]], clue: Clue, n_houses: int) -> bool:
    d = clue.data
    if clue.type == "same_house":
        cat1, val1, cat2, val2 = d["cat1"], d["val1"], d["cat2"], d["val2"]
        pos1 = solution[cat1].index(val1)
        pos2 = solution[cat2].index(val2)
        return pos1 == pos2
    elif clue.type == "neighbor":
        cat1, val1, cat2, val2 = d["cat1"], d["val1"], d["cat2"], d["val2"]
        pos1 = solution[cat1].index(val1)
        pos2 = solution[cat2].index(val2)
        return abs(pos1 - pos2) == 1
    elif clue.type == "left_of":
        cat1, val1, cat2, val2 = d["cat1"], d["val1"], d["cat2"], d["val2"]
        pos1 = solution[cat1].index(val1)
        pos2 = solution[cat2].index(val2)
        return pos1 < pos2
    elif clue.type == "immediate_left":
        cat1, val1, cat2, val2 = d["cat1"], d["val1"], d["cat2"], d["val2"]
        pos1 = solution[cat1].index(val1)
        pos2 = solution[cat2].index(val2)
        return pos1 == pos2 - 1
    elif clue.type == "position":
        cat, val, pos = d["cat"], d["val"], d["pos"]
        return solution[cat].index(val) == pos
    elif clue.type == "not_same_house":
        cat1, val1, cat2, val2 = d["cat1"], d["val1"], d["cat2"], d["val2"]
        pos1 = solution[cat1].index(val1)
        pos2 = solution[cat2].index(val2)
        return pos1 != pos2
    return True


def _count_solutions(n_houses: int, categories: list[str], clues: list[Clue], solution_values: dict[str, list[str]], max_count: int = 2) -> int:
    """
    Count valid solutions up to max_count using constraint propagation + backtracking.
    Uses a domain-based approach: for each (category, house), track which values are still possible.
    """
    # Build domains: domains[cat][house] = set of possible values
    initial_domains = {}
    for cat in categories:
        initial_domains[cat] = {h: set(solution_values[cat]) for h in range(n_houses)}

    # Precompute clue lookups for faster constraint checking
    # Group clues by type for efficient propagation
    position_clues = [c for c in clues if c.type == "position"]
    same_house_clues = [c for c in clues if c.type == "same_house"]
    not_same_house_clues = [c for c in clues if c.type == "not_same_house"]
    neighbor_clues = [c for c in clues if c.type == "neighbor"]
    left_of_clues = [c for c in clues if c.type == "left_of"]
    immediate_left_clues = [c for c in clues if c.type == "immediate_left"]

    def propagate(domains):
        """Apply constraint propagation. Returns False if inconsistent."""
        changed = True
        while changed:
            changed = False

            # Position clues: value must be at specific house
            for c in position_clues:
                cat, val, pos = c.data["cat"], c.data["val"], c.data["pos"]
                if val in domains[cat][pos]:
                    if len(domains[cat][pos]) > 1:
                        domains[cat][pos] = {val}
                        changed = True
                    # Remove val from other houses
                    for h in range(n_houses):
                        if h != pos and val in domains[cat][h]:
                            domains[cat][h].discard(val)
                            changed = True
                            if not domains[cat][h]:
                                return False
                elif val not in domains[cat][pos]:
                    # This value was already removed from its required position
                    return False

            # If a value has only one possible house, assign it
            for cat in categories:
                for val in solution_values[cat]:
                    possible_houses = [h for h in range(n_houses) if val in domains[cat][h]]
                    if len(possible_houses) == 0:
                        return False
                    if len(possible_houses) == 1:
                        h = possible_houses[0]
                        if len(domains[cat][h]) > 1:
                            domains[cat][h] = {val}
                            changed = True

            # If a house has only one possible value for a category, assign it
            for cat in categories:
                for h in range(n_houses):
                    if len(domains[cat][h]) == 1:
                        val = next(iter(domains[cat][h]))
                        for h2 in range(n_houses):
                            if h2 != h and val in domains[cat][h2]:
                                domains[cat][h2].discard(val)
                                changed = True
                                if not domains[cat][h2]:
                                    return False

            # Same house clues: if val1 is fixed to house h, val2 must also be at h
            for c in same_house_clues:
                cat1, val1, cat2, val2 = c.data["cat1"], c.data["val1"], c.data["cat2"], c.data["val2"]
                houses1 = {h for h in range(n_houses) if val1 in domains[cat1][h]}
                houses2 = {h for h in range(n_houses) if val2 in domains[cat2][h]}
                common = houses1 & houses2
                if not common:
                    return False
                if common != houses1:
                    for h in houses1 - common:
                        domains[cat1][h].discard(val1)
                        changed = True
                        if not domains[cat1][h]:
                            return False
                if common != houses2:
                    for h in houses2 - common:
                        domains[cat2][h].discard(val2)
                        changed = True
                        if not domains[cat2][h]:
                            return False

            # Not same house clues
            for c in not_same_house_clues:
                cat1, val1, cat2, val2 = c.data["cat1"], c.data["val1"], c.data["cat2"], c.data["val2"]
                houses1 = {h for h in range(n_houses) if val1 in domains[cat1][h]}
                houses2 = {h for h in range(n_houses) if val2 in domains[cat2][h]}
                if len(houses1) == 1:
                    h1 = next(iter(houses1))
                    if h1 in houses2 and val2 in domains[cat2][h1]:
                        if len(domains[cat2][h1]) == 1 and next(iter(domains[cat2][h1])) == val2:
                            # val2 must be at h1 but can't be - check if there are other houses
                            if len(houses2) == 1:
                                return False
                        domains[cat2][h1].discard(val2)
                        changed = True
                        if not domains[cat2][h1]:
                            return False
                if len(houses2) == 1:
                    h2 = next(iter(houses2))
                    if h2 in houses1 and val1 in domains[cat1][h2]:
                        if len(domains[cat1][h2]) == 1 and next(iter(domains[cat1][h2])) == val1:
                            if len(houses1) == 1:
                                return False
                        domains[cat1][h2].discard(val1)
                        changed = True
                        if not domains[cat1][h2]:
                            return False

            # Neighbor clues: restrict possible houses
            for c in neighbor_clues:
                cat1, val1, cat2, val2 = c.data["cat1"], c.data["val1"], c.data["cat2"], c.data["val2"]
                houses1 = {h for h in range(n_houses) if val1 in domains[cat1][h]}
                houses2 = {h for h in range(n_houses) if val2 in domains[cat2][h]}
                # val1 must be at a house adjacent to some house in houses2
                valid1 = {h for h in houses1 if any(abs(h - h2) == 1 for h2 in houses2)}
                valid2 = {h for h in houses2 if any(abs(h - h1) == 1 for h1 in houses1)}
                if not valid1 or not valid2:
                    return False
                for h in houses1 - valid1:
                    domains[cat1][h].discard(val1)
                    changed = True
                    if not domains[cat1][h]:
                        return False
                for h in houses2 - valid2:
                    domains[cat2][h].discard(val2)
                    changed = True
                    if not domains[cat2][h]:
                        return False

            # Left of clues: val1 must be at house < val2's house
            for c in left_of_clues:
                cat1, val1, cat2, val2 = c.data["cat1"], c.data["val1"], c.data["cat2"], c.data["val2"]
                houses1 = {h for h in range(n_houses) if val1 in domains[cat1][h]}
                houses2 = {h for h in range(n_houses) if val2 in domains[cat2][h]}
                if not houses1 or not houses2:
                    return False
                max_h2 = max(houses2)
                min_h1 = min(houses1)
                valid1 = {h for h in houses1 if h < max_h2}
                valid2 = {h for h in houses2 if h > min_h1}
                if not valid1 or not valid2:
                    return False
                for h in houses1 - valid1:
                    domains[cat1][h].discard(val1)
                    changed = True
                    if not domains[cat1][h]:
                        return False
                for h in houses2 - valid2:
                    domains[cat2][h].discard(val2)
                    changed = True
                    if not domains[cat2][h]:
                        return False

            # Immediate left clues: val1 at house h, val2 at house h+1
            for c in immediate_left_clues:
                cat1, val1, cat2, val2 = c.data["cat1"], c.data["val1"], c.data["cat2"], c.data["val2"]
                houses1 = {h for h in range(n_houses) if val1 in domains[cat1][h]}
                houses2 = {h for h in range(n_houses) if val2 in domains[cat2][h]}
                valid1 = {h for h in houses1 if (h + 1) in houses2}
                valid2 = {h for h in houses2 if (h - 1) in houses1}
                if not valid1 or not valid2:
                    return False
                for h in houses1 - valid1:
                    domains[cat1][h].discard(val1)
                    changed = True
                    if not domains[cat1][h]:
                        return False
                for h in houses2 - valid2:
                    domains[cat2][h].discard(val2)
                    changed = True
                    if not domains[cat2][h]:
                        return False

        return True

    def copy_domains(domains):
        return {cat: {h: set(s) for h, s in houses.items()} for cat, houses in domains.items()}

    def is_solved(domains):
        return all(len(domains[cat][h]) == 1 for cat in categories for h in range(n_houses))

    def extract_solution(domains):
        return {cat: [next(iter(domains[cat][h])) for h in range(n_houses)] for cat in categories}

    count = 0

    def solve(domains):
        nonlocal count
        if count >= max_count:
            return

        d = copy_domains(domains)
        if not propagate(d):
            return

        if is_solved(d):
            # Verify full solution against all clues
            sol = extract_solution(d)
            if _check_solution(sol, clues, n_houses):
                count += 1
            return

        # Find the unfixed cell with smallest domain > 1 (MRV heuristic)
        best_cat, best_h, best_size = None, None, n_houses + 1
        for cat in categories:
            for h in range(n_houses):
                s = len(d[cat][h])
                if 1 < s < best_size:
                    best_cat, best_h, best_size = cat, h, s

        if best_cat is None:
            return

        for val in list(d[best_cat][best_h]):
            d2 = copy_domains(d)
            d2[best_cat][best_h] = {val}
            # Remove val from other houses in same category
            for h2 in range(n_houses):
                if h2 != best_h:
                    d2[best_cat][h2].discard(val)
            solve(d2)
            if count >= max_count:
                return

    solve(initial_domains)
    return count


def _make_clue_same_house(solution: dict[str, list[str]], categories: list[str], n_houses: int, rng: random.Random) -> Clue | None:
    cats = rng.sample(categories, 2)
    pos = rng.randint(0, n_houses - 1)
    val1 = solution[cats[0]][pos]
    val2 = solution[cats[1]][pos]
    desc = f"The {cats[0]} {val1} is in the same house as the {cats[1]} {val2}."
    return Clue("same_house", desc, {"cat1": cats[0], "val1": val1, "cat2": cats[1], "val2": val2})


def _make_clue_neighbor(solution: dict[str, list[str]], categories: list[str], n_houses: int, rng: random.Random) -> Clue | None:
    cats = rng.sample(categories, 2)
    pos1 = rng.randint(0, n_houses - 2)
    pos2 = pos1 + 1
    if rng.random() < 0.5:
        pos1, pos2 = pos2, pos1
    val1 = solution[cats[0]][pos1]
    val2 = solution[cats[1]][pos2]
    desc = f"The {cats[0]} {val1} and the {cats[1]} {val2} are neighbors."
    return Clue("neighbor", desc, {"cat1": cats[0], "val1": val1, "cat2": cats[1], "val2": val2})


def _make_clue_left_of(solution: dict[str, list[str]], categories: list[str], n_houses: int, rng: random.Random) -> Clue | None:
    cats = rng.sample(categories, 2)
    positions = list(range(n_houses))
    rng.shuffle(positions)
    for p1 in positions:
        for p2 in positions:
            if p1 < p2:
                val1 = solution[cats[0]][p1]
                val2 = solution[cats[1]][p2]
                desc = f"The {cats[0]} {val1} is somewhere to the left of the {cats[1]} {val2}."
                return Clue("left_of", desc, {"cat1": cats[0], "val1": val1, "cat2": cats[1], "val2": val2})
    return None


def _make_clue_immediate_left(solution: dict[str, list[str]], categories: list[str], n_houses: int, rng: random.Random) -> Clue | None:
    if n_houses < 2:
        return None
    cats = rng.sample(categories, 2)
    pos1 = rng.randint(0, n_houses - 2)
    pos2 = pos1 + 1
    val1 = solution[cats[0]][pos1]
    val2 = solution[cats[1]][pos2]
    desc = f"The {cats[0]} {val1} is directly to the left of the {cats[1]} {val2}."
    return Clue("immediate_left", desc, {"cat1": cats[0], "val1": val1, "cat2": cats[1], "val2": val2})


def _make_clue_position(solution: dict[str, list[str]], categories: list[str], n_houses: int, rng: random.Random) -> Clue | None:
    cat = rng.choice(categories)
    pos = rng.randint(0, n_houses - 1)
    val = solution[cat][pos]
    ordinal = _ordinal(pos + 1)
    desc = f"The {cat} {val} is in the {ordinal} house."
    return Clue("position", desc, {"cat": cat, "val": val, "pos": pos})


def _make_clue_not_same_house(solution: dict[str, list[str]], categories: list[str], n_houses: int, rng: random.Random) -> Clue | None:
    cats = rng.sample(categories, 2)
    positions = rng.sample(range(n_houses), 2)
    val1 = solution[cats[0]][positions[0]]
    val2 = solution[cats[1]][positions[1]]
    # Make sure they're actually in different houses
    if solution[cats[0]].index(val1) == solution[cats[1]].index(val2):
        return None
    desc = f"The {cats[0]} {val1} is not in the same house as the {cats[1]} {val2}."
    return Clue("not_same_house", desc, {"cat1": cats[0], "val1": val1, "cat2": cats[1], "val2": val2})


CLUE_GENERATORS = [
    _make_clue_same_house,
    _make_clue_neighbor,
    _make_clue_left_of,
    _make_clue_immediate_left,
    _make_clue_position,
    _make_clue_not_same_house,
]


def _ordinal(n: int) -> str:
    if 11 <= n % 100 <= 13:
        return f"{n}th"
    return f"{n}{['th','st','nd','rd'][n % 10] if n % 10 < 4 else 'th'}"


def _clue_signature(clue: Clue) -> str:
    """Return a signature to avoid duplicate clues."""
    d = clue.data
    if clue.type == "position":
        return f"pos:{d['cat']}:{d['val']}:{d['pos']}"
    elif clue.type in ("same_house", "not_same_house", "neighbor"):
        # Order-independent
        pair = tuple(sorted([(d["cat1"], d["val1"]), (d["cat2"], d["val2"])]))
        return f"{clue.type}:{pair}"
    else:
        return f"{clue.type}:{d.get('cat1',d.get('cat',''))}:{d.get('val1',d.get('val',''))}:{d.get('cat2','')}:{d.get('val2','')}"


# Difficulty configurations
DIFFICULTY_CONFIGS = [
    # (n_houses, n_categories, label)
    (3, 3, "easy"),
    (3, 4, "easy"),
    (4, 4, "medium"),
    (4, 5, "medium"),
    (5, 4, "hard"),
    (5, 5, "hard"),
    (5, 6, "very_hard"),
    (6, 5, "very_hard"),
    (6, 6, "very_hard"),
    (7, 5, "extreme"),
    (7, 6, "extreme"),
    (7, 7, "extreme"),
    (8, 6, "extreme"),
    (8, 7, "extreme"),
]


def generate_puzzle(seed: int, difficulty_index: int | None = None) -> dict:
    """
    Generate a zebra puzzle deterministically from a seed.

    Returns a dict with:
        - n_houses: int
        - categories: list of category names
        - values: dict mapping category -> list of possible values
        - clues: list of clue description strings
        - solution: dict mapping category -> list of values per house position
        - difficulty: str label
        - seed: int
    """
    rng = random.Random(seed)

    # Pick difficulty based on seed if not specified
    if difficulty_index is None:
        difficulty_index = rng.randint(0, len(DIFFICULTY_CONFIGS) - 1)

    n_houses, n_categories, difficulty = DIFFICULTY_CONFIGS[difficulty_index]
    categories = rng.sample(ALL_CATEGORIES, n_categories)

    # Generate a random solution
    solution = _generate_solution(n_houses, categories, rng)

    # Get the values used (for the puzzle description)
    values = {cat: sorted(solution[cat]) for cat in categories}

    # Generate clues that uniquely determine the solution
    clues = _generate_clue_set(solution, categories, n_houses, rng, difficulty)

    return {
        "n_houses": n_houses,
        "categories": categories,
        "values": values,
        "clues": [c.description for c in clues],
        "solution": solution,
        "difficulty": difficulty,
        "seed": seed,
    }


def _generate_clue_set(
    solution: dict[str, list[str]],
    categories: list[str],
    n_houses: int,
    rng: random.Random,
    difficulty: str,
) -> list[Clue]:
    """Generate a minimal-ish set of clues that uniquely determines the solution."""

    # First, generate a large pool of candidate clues
    seen_signatures: set[str] = set()
    candidate_pool: list[Clue] = []

    n_attempts = max(500, n_houses * len(categories) * 50)
    for _ in range(n_attempts):
        gen = rng.choice(CLUE_GENERATORS)
        clue = gen(solution, categories, n_houses, rng)
        if clue is not None:
            sig = _clue_signature(clue)
            if sig not in seen_signatures:
                seen_signatures.add(sig)
                candidate_pool.append(clue)

    if not candidate_pool:
        # Fallback: generate position clues for everything
        clues = []
        for cat in categories:
            for pos in range(n_houses):
                val = solution[cat][pos]
                ordinal = _ordinal(pos + 1)
                c = Clue("position", f"The {cat} {val} is in the {ordinal} house.",
                         {"cat": cat, "val": val, "pos": pos})
                clues.append(c)
        return clues

    rng.shuffle(candidate_pool)

    # Greedy approach: start with all candidates, then try to remove clues one by one
    # Start with enough clues to guarantee unique solution, then prune
    current_clues = list(candidate_pool)

    # First verify the full set gives a unique solution
    n_solutions = _count_solutions(n_houses, categories, current_clues,
                                    {cat: list(solution[cat]) for cat in categories}, max_count=2)

    if n_solutions != 1:
        # If even all clues don't give unique solution, add position clues until unique
        for cat in categories:
            for pos in range(n_houses):
                val = solution[cat][pos]
                ordinal = _ordinal(pos + 1)
                c = Clue("position", f"The {cat} {val} is in the {ordinal} house.",
                         {"cat": cat, "val": val, "pos": pos})
                sig = _clue_signature(c)
                if sig not in seen_signatures:
                    current_clues.append(c)
                    seen_signatures.add(sig)
                    n_solutions = _count_solutions(n_houses, categories, current_clues,
                                                    {cat: list(solution[cat]) for cat in categories}, max_count=2)
                    if n_solutions == 1:
                        break
            if n_solutions == 1:
                break

    # Now prune: try removing each clue and check if solution is still unique
    rng.shuffle(current_clues)
    pruned = list(current_clues)

    for clue in current_clues:
        if len(pruned) <= n_houses:  # Don't go below minimum
            break
        test_set = [c for c in pruned if c is not clue]
        n_solutions = _count_solutions(n_houses, categories, test_set,
                                        {cat: list(solution[cat]) for cat in categories}, max_count=2)
        if n_solutions == 1:
            pruned = test_set

    # Shuffle the final clue order for presentation
    rng.shuffle(pruned)
    return pruned


def format_puzzle(puzzle: dict) -> str:
    """Format a puzzle as a human-readable string."""
    lines = []
    lines.append(f"There are {puzzle['n_houses']} houses in a row, numbered 1 to {puzzle['n_houses']} from left to right.")
    lines.append(f"Each house has exactly one value for each of the following {len(puzzle['categories'])} categories:")
    lines.append("")
    for cat in puzzle["categories"]:
        lines.append(f"  {cat.capitalize()}: {', '.join(puzzle['values'][cat])}")
    lines.append("")
    lines.append("Each value appears in exactly one house. Using the following clues, determine which values belong to each house:")
    lines.append("")
    for i, clue in enumerate(puzzle["clues"], 1):
        lines.append(f"  {i}. {clue}")
    lines.append("")
    lines.append("Provide your answer as a JSON object mapping each category to a list of values, where the i-th element is the value for house i.")
    lines.append('For example: {"color": ["Red", "Blue", "Green"], "pet": ["Cat", "Dog", "Fish"]}')
    return "\n".join(lines)


def score_answer(puzzle: dict, answer: dict[str, list[str]]) -> tuple[float, str]:
    """
    Score an answer against the puzzle solution.
    Returns (reward, feedback_message).
    reward is 1.0 for fully correct, 0.0 otherwise.
    """
    solution = puzzle["solution"]

    # Check all categories are present
    missing = set(solution.keys()) - set(answer.keys())
    if missing:
        return 0.0, f"Missing categories in answer: {missing}"

    extra = set(answer.keys()) - set(solution.keys())
    if extra:
        return 0.0, f"Extra categories in answer: {extra}"

    # Check each category
    n_correct = 0
    n_total = 0
    errors = []
    for cat in solution:
        if cat not in answer:
            continue
        ans_vals = answer[cat]
        sol_vals = solution[cat]
        if len(ans_vals) != len(sol_vals):
            errors.append(f"{cat}: expected {len(sol_vals)} values, got {len(ans_vals)}")
            continue
        for i, (a, s) in enumerate(zip(ans_vals, sol_vals)):
            n_total += 1
            if a == s:
                n_correct += 1

    if n_total == 0:
        return 0.0, "No valid assignments found."

    if n_correct == n_total:
        return 1.0, "Correct! All assignments match the solution."
    else:
        return 0.0, f"Incorrect. {n_correct}/{n_total} assignments correct."
