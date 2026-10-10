from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from .simulator import (
    DEFAULT_DIFFICULTY,
    DifficultySettings,
    NUM_CATEGORIES,
    ModelInput,
)


@dataclass(frozen=True)
class OraclePrediction:
    """Oracle probabilities, in strategy order 0–3 and move order A, B."""

    strategy_probabilities: tuple[float, ...]
    move_probabilities: tuple[float, float]


def _check_category(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer from 0 to 3.")
    if not 0 <= value < NUM_CATEGORIES:
        raise ValueError(f"{name} must be an integer from 0 to 3.")


def _normalize(weights: list[float]) -> tuple[float, ...]:
    total = sum(weights)
    if not isfinite(total) or total <= 0:
        raise ValueError("Cannot turn these weights into probabilities.")
    return tuple(weight / total for weight in weights)


def _transition(
    belief: tuple[float, ...],
    difficulty: DifficultySettings,
) -> tuple[float, ...]:
    """Apply the selected difficulty's playbook-switch chance."""

    switch_to_each_other = (
        difficulty.strategy_switch_probability / (NUM_CATEGORIES - 1)
    )

    new_belief = []
    for next_strategy in range(NUM_CATEGORIES):
        probability = belief[next_strategy] * (
            1 - difficulty.strategy_switch_probability
        )
        probability += sum(
            belief[old_strategy] * switch_to_each_other
            for old_strategy in range(NUM_CATEGORIES)
            if old_strategy != next_strategy
        )
        new_belief.append(probability)

    return _normalize(new_belief)


def _clue_likelihood(
    clue: int,
    strategy: int,
    difficulty: DifficultySettings,
) -> float:
    """Probability of seeing this clue if this strategy is active."""

    if clue == strategy:
        return difficulty.clue_match_probability
    return (1 - difficulty.clue_match_probability) / (NUM_CATEGORIES - 1)


def _move_likelihood(
    move: str,
    situation: int,
    strategy: int,
    difficulty: DifficultySettings,
) -> float:
    """Probability of seeing this move under the situation and strategy."""

    probability_of_a = (
        difficulty.p_a_in_favored_situation
        if situation == strategy
        else 1 - difficulty.p_a_in_favored_situation
    )

    if move == "A":
        return probability_of_a
    if move == "B":
        return 1 - probability_of_a
    raise ValueError("Move must be 'A' or 'B'.")


def strategy_posterior_before_move(
    model_input: ModelInput,
    difficulty: DifficultySettings = DEFAULT_DIFFICULTY,
) -> tuple[float, ...]:
    """Estimate the active strategy after the current clue, before the move."""

    belief = tuple(1 / NUM_CATEGORIES for _ in range(NUM_CATEGORIES))

    # Replay completed rounds. Before each later round, allow the strategy to
    # switch; then use that round's clue and revealed move as evidence.
    for round_index, past_round in enumerate(model_input.history):
        if round_index > 0:
            belief = _transition(belief, difficulty)

        _check_category(past_round.situation, "Past situation")
        _check_category(past_round.clue, "Past clue")

        belief = _normalize([
            belief[strategy]
            * _clue_likelihood(past_round.clue, strategy, difficulty)
            for strategy in range(NUM_CATEGORIES)
        ])
        belief = _normalize([
            belief[strategy]
            * _move_likelihood(
                past_round.move,
                past_round.situation,
                strategy,
                difficulty,
            )
            for strategy in range(NUM_CATEGORIES)
        ])

    # Move from the last completed round's strategy to the current round.
    if model_input.history:
        belief = _transition(belief, difficulty)

    _check_category(model_input.situation, "Current situation")
    _check_category(model_input.clue, "Current clue")

    # The current situation is sampled independently of strategy, so it
    # provides no evidence about strategy. The current clue does.
    return _normalize([
        belief[strategy]
        * _clue_likelihood(model_input.clue, strategy, difficulty)
        for strategy in range(NUM_CATEGORIES)
    ])

def predict_before_move(
    model_input: ModelInput,
    difficulty: DifficultySettings = DEFAULT_DIFFICULTY,
) -> OraclePrediction:
    """Return strategy and A/B probabilities using only visible information."""

    strategy_probabilities = strategy_posterior_before_move(
        model_input,
        difficulty,
    )

    probability_of_a = sum(
        strategy_probabilities[strategy]
        * (
            difficulty.p_a_in_favored_situation
            if model_input.situation == strategy
            else 1 - difficulty.p_a_in_favored_situation
        )
        for strategy in range(NUM_CATEGORIES)
    )

    return OraclePrediction(
        strategy_probabilities=strategy_probabilities,
        move_probabilities=(probability_of_a, 1 - probability_of_a),
    )