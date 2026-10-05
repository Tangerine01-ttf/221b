from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Literal

Move = Literal["A", "B"]

NUM_CATEGORIES = 4
ROUNDS_PER_CASE = 16

STRATEGY_SWITCH_PROBABILITY = 0.05
CLUE_MATCH_PROBABILITY = 0.40
P_A_IN_FAVORED_SITUATION = 0.65


@dataclass(frozen=True)
class ObservedRound:
    """A completed round that may appear in the next model input."""

    situation: int
    clue: int
    move: Move


@dataclass(frozen=True)
class ModelInput:
    """Information visible to the model before the current move."""

    history: tuple[ObservedRound, ...]
    situation: int
    clue: int


@dataclass(frozen=True)
class TrainingExample:
    """The visible input and its move answer label."""

    model_input: ModelInput
    move_target: Move


@dataclass(frozen=True)
class EvaluationLabel:
    """Answer-key information for evaluation, not a model input."""

    active_strategy: int


@dataclass(frozen=True)
class GeneratedCase:
    """One case, with model examples and evaluation labels kept separate."""

    training_examples: tuple[TrainingExample, ...]
    evaluation_labels: tuple[EvaluationLabel, ...]
    seed: int


def generate_case(seed: int) -> GeneratedCase:
    """Generate one reproducible 16-round case."""

    rng = random.Random(seed)
    active_strategy = rng.randrange(NUM_CATEGORIES)
    history: list[ObservedRound] = []
    examples: list[TrainingExample] = []
    evaluation: list[EvaluationLabel] = []

    for round_index in range(ROUNDS_PER_CASE):
        # A strategy can switch between rounds, but never after the final round.
        if round_index > 0 and rng.random() < STRATEGY_SWITCH_PROBABILITY:
            alternatives = [
                strategy
                for strategy in range(NUM_CATEGORIES)
                if strategy != active_strategy
            ]
            active_strategy = rng.choice(alternatives)

        situation = rng.randrange(NUM_CATEGORIES)

        # The active strategy's clue appears 40% of the time.
        # Each of the other three clues therefore appears 20% of the time.
        if rng.random() < CLUE_MATCH_PROBABILITY:
            clue = active_strategy
        else:
            other_clues = [
                clue_type
                for clue_type in range(NUM_CATEGORIES)
                if clue_type != active_strategy
            ]
            clue = rng.choice(other_clues)

        probability_of_a = (
            P_A_IN_FAVORED_SITUATION
            if situation == active_strategy
            else 1 - P_A_IN_FAVORED_SITUATION
        )
        move: Move = "A" if rng.random() < probability_of_a else "B"

        # The current move is a training answer, not part of this round's input.
        examples.append(
            TrainingExample(
                model_input=ModelInput(
                    history=tuple(history),
                    situation=situation,
                    clue=clue,
                ),
                move_target=move,
            )
        )

        # Keep the hidden strategy in the evaluation answer key only.
        evaluation.append(EvaluationLabel(active_strategy=active_strategy))

        # Once revealed, this round becomes visible history for later rounds.
        history.append(ObservedRound(situation, clue, move))

    return GeneratedCase(
        training_examples=tuple(examples),
        evaluation_labels=tuple(evaluation),
        seed=seed,
    )
