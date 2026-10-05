from __future__ import annotations

import secrets

from .oracle import OraclePrediction, predict_before_move
from .simulator import GeneratedCase, TrainingExample, generate_case


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


def _choose_move() -> str:
    while True:
        move = input("Your prediction, A or B: ").strip().upper()
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
) -> None:
    print("\n" + "=" * 72)
    print("CASE DEBRIEF")
    print("=" * 72)

    if mode == "predict":
        print(f"Your score: {score}/{len(case.training_examples)}")
    else:
        print("Spectator mode: no predictions were scored.")

    print("\nClues, moves, predictions, and revealed strategies")
    print("Rnd | Situation | Clue | Move | Guess | Result | Active strategy")
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
            f"Strategy {strategy} (favors Situation {strategy})"
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


def _play_case(mode: str) -> None:
    seed = secrets.randbits(32)
    case = generate_case(seed)
    guesses: list[str | None] = []
    oracle_predictions: list[OraclePrediction] = []
    score = 0

    print("\nNew 16-round case")
    print("Strategies and Bayesian beliefs stay hidden until the debrief.")

    for index, example in enumerate(case.training_examples):
        model_input = example.model_input
        oracle_prediction = predict_before_move(model_input)
        oracle_predictions.append(oracle_prediction)

        print(f"\nRound {index + 1}/16")
        print(f"Situation: {model_input.situation + 1}")
        print(f"Clue:      {model_input.clue + 1}")

        if mode == "predict":
            guess = _choose_move()
        else:
            input("Press Enter to reveal the opponent's move: ")
            guess = None

        guesses.append(guess)
        print(f"Opponent chose: {example.move_target}")

        if guess is not None:
            if guess == example.move_target:
                score += 1
                print("Correct — 1 point.")
            else:
                print("Not this time.")

        if index + 1 < len(case.training_examples):
            input("Press Enter for the next round...")

    _show_debrief(case, guesses, oracle_predictions, score, mode)


def main() -> None:
    while True:
        mode = _choose_mode()
        _play_case(mode)

        again = input("\nPlay another case? (y/N): ").strip().lower()
        if again not in {"y", "yes"}:
            break


if __name__ == "__main__":
    main()
