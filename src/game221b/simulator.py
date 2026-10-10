from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Literal

Move = Literal["A", "B"]

NUM_CATEGORIES = 4
ROUNDS_PER_CASE = 16


@dataclass(frozen=True)
class DifficultySettings:
    """Probability settings that define one case difficulty."""

    name: str
    p_a_in_favored_situation: float
    clue_match_probability: float
    strategy_switch_probability: float


DIFFICULTIES = {
    "1": DifficultySettings("Easy", 0.85, 0.70, 0.01),
    "2": DifficultySettings("Moderate", 0.75, 0.55, 0.02),
    "3": DifficultySettings("Intermediate", 0.65, 0.40, 0.05),
    "4": DifficultySettings("Hard", 0.60, 0.32, 0.10),
    "5": DifficultySettings("Advanced", 0.55, 0.27, 0.15),
}

DEFAULT_DIFFICULTY = DIFFICULTIES["3"]

# Keep the existing game behavior at Intermediate until we connect the menu.
STRATEGY_SWITCH_PROBABILITY = DEFAULT_DIFFICULTY.strategy_switch_probability
CLUE_MATCH_PROBABILITY = DEFAULT_DIFFICULTY.clue_match_probability
P_A_IN_FAVORED_SITUATION = DEFAULT_DIFFICULTY.p_a_in_favored_situation


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


def generate_case(
    seed: int,
    difficulty: DifficultySettings = DEFAULT_DIFFICULTY,
) -> GeneratedCase:
    """Generate one reproducible 16-round case."""

    rng = random.Random(seed)
    active_strategy = rng.randrange(NUM_CATEGORIES)
    history: list[ObservedRound] = []
    examples: list[TrainingExample] = []
    evaluation: list[EvaluationLabel] = []

    for round_index in range(ROUNDS_PER_CASE):
        # A strategy can switch between rounds, but never after the final round.
        if round_index > 0 and rng.random() < difficulty.strategy_switch_probability:
            alternatives = [
                strategy
                for strategy in range(NUM_CATEGORIES)
                if strategy != active_strategy
            ]
            active_strategy = rng.choice(alternatives)

        situation = rng.randrange(NUM_CATEGORIES)

        # The active strategy's clue appears 40% of the time.
        # Each of the other three clues therefore appears 20% of the time.
        if rng.random() < difficulty.clue_match_probability:
            clue = active_strategy
        else:
            other_clues = [
                clue_type
                for clue_type in range(NUM_CATEGORIES)
                if clue_type != active_strategy
            ]
            clue = rng.choice(other_clues)

        probability_of_a = (
            difficulty.p_a_in_favored_situation
            if situation == active_strategy
            else 1 - difficulty.p_a_in_favored_situation
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
