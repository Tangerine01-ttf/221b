from __future__ import annotations

import secrets

from .oracle import OraclePrediction, predict_before_move
from .simulator import (
    DEFAULT_DIFFICULTY,
    DIFFICULTIES,
    DifficultySettings,
    GeneratedCase,
    TrainingExample,
    generate_case,
)

SITUATION_TEXT = (
    "A bell rings after dark",
    "An oil lamp suddenly goes out",
    "Rain sweeps across the courtyard",
    "An unexpected visitor arrives",
)

# Temporary text marks for the four seals; their meanings appear in the debrief.
SEAL_MARKS = ("C|||", "/\\.", "~|~", "o o<")
SEAL_NAMES = ("Echo", "Ember", "River", "Footstep")
SEAL_MEANINGS = (
    "a broken ring with three short rays; linked to the bell",
    "a small flame with a missing stroke; linked to the lamp",
    "three waves with one broken line; linked to the rain",
    "two prints, one turned backwards; linked to the visitor",
)

ROUTE_NAMES = {"A": "North Path", "B": "South Path"}

def _choose_mode() -> str:
    print("\nChoose a mode:")
    print("1. Predict the opponent's move")
    print("2. Spectator mode")

    while True:
        choice = input("Enter 1 or 2: ").strip()
        if choice == "1":
            return "predict"
        if choice == "2":
            return "spectate"
        print("Please enter 1 or 2.")

def _choose_difficulty() -> DifficultySettings:
    print("\nChoose a difficulty:")
    for number, difficulty in DIFFICULTIES.items():
        print(f"{number}. {difficulty.name}")

    while True:
        choice = input("Choose 1-5: ").strip()
        if choice in DIFFICULTIES:
            return DIFFICULTIES[choice]
        print("Please enter a number from 1 to 5.")

def _choose_move() -> str:
    while True:
        move = input("Your route prediction: A (North Path) or B (South Path): ").strip().upper()
        if move in {"A", "B"}:
            return move
        print("Please enter A or B.")


def _bar(probability: float, width: int = 10) -> str:
    filled = round(probability * width)
    return "#" * filled + "." * (width - filled)


def _show_debrief(
    case: GeneratedCase,
    guesses: list[str | None],
    oracle_predictions: list[OraclePrediction],
    score: int,
    mode: str,
    difficulty: DifficultySettings,
) -> None:
    print("\n" + "=" * 72)
    print("CASE DEBRIEF")
    print("=" * 72)

    if mode == "predict":
        print(f"Your score: {score}/{len(case.training_examples)}")
    else:
        print("Spectator mode: no predictions were scored.")

    print("\nRoute key: A = North Path; B = South Path")
    print("Situation key:")
    for number, description in enumerate(SITUATION_TEXT, start=1):
        print(f"  Situation {number}: {description}")
    print("Seal key:")
    for number, (name, meaning) in enumerate(
        zip(SEAL_NAMES, SEAL_MEANINGS),
        start=1,
    ):
        print(f"  Clue C{number} ({name}): {meaning}")

    matching_clue_probability = difficulty.clue_match_probability
    other_clue_probability = (
        1 - matching_clue_probability
    ) / (len(SEAL_MARKS) - 1)
    favored_north_probability = difficulty.p_a_in_favored_situation
    other_north_probability = 1 - favored_north_probability
    print(f"\nDifficulty: {difficulty.name}")
    print(
        "The hidden playbook can switch between rounds; the table shows "
        "which situation it favored each round.\n"
        "The seal is a noisy clue about the playbook; it does not choose "
        "the route. "
        f"The matching seal appears {matching_clue_probability:.1%} of the time, "
        f"and each other seal {other_clue_probability:.1%}.\n"
        f"North is chosen {favored_north_probability:.0%} of the time in "
        "the favored situation and "
        f"{other_north_probability:.0%} elsewhere.\n"
        "Before each later round, the playbook has a "
        f"{difficulty.strategy_switch_probability:.0%} chance to switch "
        "to one of the other three."
    )

    print("\nRoutes, seal clues, predictions, and hidden patterns")
    print("Rnd | Situation | Clue | Route | Guess | Result | Active playbook")
    print("-" * 72)

    for index, (example, label, guess) in enumerate(
        zip(case.training_examples, case.evaluation_labels, guesses),
        start=1,
    ):
        situation = example.model_input.situation + 1
        clue = example.model_input.clue + 1
        strategy = label.active_strategy + 1
        guess_text = guess if guess is not None else "-"
        result = (
            "Correct" if guess == example.move_target else "Miss"
        ) if guess is not None else "-"

        print(
            f"{index:>3} | "
            f"Sit. {situation:<2}   | "
            f"C{clue:<3} | "
            f"{example.move_target:<4} | "
            f"{guess_text:<5} | "
            f"{result:<7} | "
            f"Playbook {strategy} (favors Situation {strategy})"
        )

    print("\nBayesian belief chart")
    print("Each bar shows the oracle's belief before that round's move.")
    for index, prediction in enumerate(oracle_predictions, start=1):
        bars = "  ".join(
            f"S{strategy + 1} [{_bar(probability)}] {probability:5.1%}"
            for strategy, probability in enumerate(
                prediction.strategy_probabilities
            )
        )
        print(f"Round {index:02}: {bars}")


def _play_case(
    mode: str,
    difficulty: DifficultySettings,
) -> None:
    seed = secrets.randbits(32)
    case = generate_case(seed, difficulty)
    guesses: list[str | None] = []
    oracle_predictions: list[OraclePrediction] = []
    score = 0

    print("\nCASE 1: The Manuscript Meant for You")
    print("Fictional historical Nalanda; the exact year is unspecified.")
    print(
    "\nAt Nalanda, a sealed manuscript arrives bearing your name—and yours alone. "
    "A trusted messenger is bringing it before sunrise. Its warning could put "
    "people in danger if it falls into the wrong hands. Someone else may be "
    "searching for the messenger, who can take the North Path or the South Path."
)
    print(
    "\nYou have sixteen coded dispatches. Each records one event and carries a "
    "strange mark. Some marks may mislead you. Study the pattern and predict "
    "each route so you can be the first to receive the manuscript."
)
    print("\nThe hidden patterns and Bayesian beliefs stay hidden until the debrief.")


    for index, example in enumerate(case.training_examples):
        model_input = example.model_input
        oracle_prediction = predict_before_move(model_input, difficulty)
        oracle_predictions.append(oracle_prediction)

        print(f"\nRound {index + 1}/16")
        print(f"Situation: {SITUATION_TEXT[model_input.situation]}")
        print(f"Seal:      {SEAL_MARKS[model_input.clue]}")

        if mode == "predict":
            guess = _choose_move()
        else:
            input("Press Enter to reveal the messenger's route: ")
            guess = None

        guesses.append(guess)
        print(
    f"The messenger took the {ROUTE_NAMES[example.move_target]} "
    f"({example.move_target})."
)

        if guess is not None:
            if guess == example.move_target:
                score += 1
                print("Correct — 1 point.")
            else:
                print("Not this time.")

        if index + 1 < len(case.training_examples):
            input("Press Enter for the next round...")

    _show_debrief(case, guesses, oracle_predictions, score, mode, difficulty)


def main() -> None:
    while True:
        mode = _choose_mode()
        difficulty = _choose_difficulty()
        _play_case(mode, difficulty)

        again = input("\nPlay another case? (y/N): ").strip().lower()
        if again not in {"y", "yes"}:
            break

if __name__ == "__main__":
    main()
