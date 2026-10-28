from __future__ import annotations

import secrets

import streamlit as st

from game221b.oracle import predict_before_move
from game221b.simulator import DIFFICULTIES, ROUNDS_PER_CASE, generate_case


SITUATIONS = (
    "A bell rings after dark",
    "An oil lamp suddenly goes out",
    "Rain sweeps across the courtyard",
    "An unexpected visitor arrives",
)

# During play, show the marks only. Their meanings appear in the debrief.
SEAL_MARKS = ("C|||", "/\\.", "~|~", "o o<")
SEAL_NAMES = ("Echo", "Ember", "River", "Footstep")
SEAL_MEANINGS = (
    "a broken ring with three short rays; linked to the bell",
    "a small flame with a missing stroke; linked to the lamp",
    "three waves with one broken line; linked to the rain",
    "two prints, one turned backwards; linked to the visitor",
)

ROUTE_NAMES = {"A": "North Path", "B": "South Path"}
DIFFICULTY_BY_NAME = {
    setting.name: setting for setting in DIFFICULTIES.values()
}


def start_case(mode: str, difficulty_name: str) -> None:
    difficulty = DIFFICULTY_BY_NAME[difficulty_name]
    case = generate_case(secrets.randbits(32), difficulty)
    oracle_predictions = [
        predict_before_move(example.model_input, difficulty)
        for example in case.training_examples
    ]

    st.session_state["game"] = {
        "case": case,
        "difficulty": difficulty,
        "oracle_predictions": oracle_predictions,
        "mode": mode,
        "round_index": 0,
        "guesses": [],
        "score": 0,
        "revealed": False,
        "stage": "play",
    }


def record_guess(guess: str | None) -> None:
    game = st.session_state["game"]
    index = game["round_index"]
    example = game["case"].training_examples[index]

    game["guesses"].append(guess)
    game["revealed"] = True

    if guess == example.move_target:
        game["score"] += 1


def advance_round() -> None:
    game = st.session_state["game"]

    if game["round_index"] + 1 >= ROUNDS_PER_CASE:
        game["stage"] = "debrief"
    else:
        game["round_index"] += 1
        game["revealed"] = False


def show_debrief(game: dict) -> None:
    case = game["case"]
    difficulty = game["difficulty"]

    st.header("Case debrief")
    st.write(
        "Before sunrise, the messenger reaches the Nalanda courtyard. "
        "The manuscript is now in your hands. Let’s decode the dispatches."
    )

    if game["mode"] == "predict":
        st.metric("Your route predictions", f"{game['score']} / {ROUNDS_PER_CASE}")
    else:
        st.info("Spectator mode: no predictions were scored.")

    other_clue_probability = (
        1 - difficulty.clue_match_probability
    ) / 3

    st.subheader("What the hidden pattern meant")
    st.write(
        f"Difficulty: **{difficulty.name}**. The seal matching the active "
        f"playbook appeared {difficulty.clue_match_probability:.0%} of the time; "
        f"each other seal appeared {other_clue_probability:.0%} of the time."
    )
    st.write(
        f"North was chosen {difficulty.p_a_in_favored_situation:.0%} of the time "
        "in the favored situation, and "
        f"{1 - difficulty.p_a_in_favored_situation:.0%} in the other situations. "
        f"Before each later round, the playbook had a "
        f"{difficulty.strategy_switch_probability:.0%} chance to switch."
    )

    st.markdown("**Situation key**")
    for number, situation in enumerate(SITUATIONS, start=1):
        st.write(f"{number}. {situation}")

    st.markdown("**Four-seal key**")
    for mark, name, meaning in zip(SEAL_MARKS, SEAL_NAMES, SEAL_MEANINGS):
        st.write(f"- `{mark}` — **{name}:** {meaning}.")

    st.subheader("Dispatches, routes, and revealed playbooks")
    rows = []

    for index, (example, label, guess) in enumerate(
        zip(case.training_examples, case.evaluation_labels, game["guesses"]),
        start=1,
    ):
        strategy_number = label.active_strategy + 1

        if guess is None:
            result = "—"
            guess_text = "—"
        else:
            result = "Correct" if guess == example.move_target else "Miss"
            guess_text = f"{ROUTE_NAMES[guess]} ({guess})"

        rows.append(
            {
                "Round": index,
                "Situation": SITUATIONS[example.model_input.situation],
                "Seal": SEAL_MARKS[example.model_input.clue],
                "Messenger's route": (
                    f"{ROUTE_NAMES[example.move_target]} "
                    f"({example.move_target})"
                ),
                "Your prediction": guess_text,
                "Result": result,
                "Hidden playbook": (
                    f"{strategy_number} "
                    f"(favors Situation {strategy_number})"
                ),
            }
        )

    st.dataframe(rows, hide_index=True)

    st.subheader("Bayesian belief chart")
    st.caption(
        "Each line shows the oracle’s belief in a playbook before that "
        "round’s route was revealed."
    )

    chart_data = {
        "Round": list(range(1, ROUNDS_PER_CASE + 1)),
    }
    for strategy in range(4):
        chart_data[f"Playbook {strategy + 1}"] = [
            prediction.strategy_probabilities[strategy]
            for prediction in game["oracle_predictions"]
        ]

    st.line_chart(
        chart_data,
        x="Round",
        y=[f"Playbook {strategy + 1}" for strategy in range(4)],
    )


st.set_page_config(
    page_title="221B — The Manuscript Meant for You",
    page_icon="🔎",
    layout="wide",
)

st.title("221B: The Manuscript Meant for You")
st.caption("A 16-round mystery set in fictional historical Nalanda.")

st.markdown(
    "At Nalanda, a sealed manuscript arrives bearing your name—and yours "
    "alone. A trusted messenger is bringing it before sunrise. Its warning "
    "could put people in danger if it falls into the wrong hands. Someone "
    "else may be searching for the messenger, who can take the North Path "
    "or the South Path."
)
st.caption(
    "You will see a situation and a strange seal in each dispatch. "
    "Study the pattern and predict the messenger’s route."
)
st.info(
    "This is an original fictional story. Its characters, seals, and events "
    "are invented for the game."
)

if "game" not in st.session_state:
    st.subheader("Prepare your investigation")

    mode_label = st.radio(
        "Choose how to play",
        ("Predict the route", "Spectator mode"),
        horizontal=True,
    )
    difficulty_name = st.selectbox(
        "Choose a difficulty",
        tuple(DIFFICULTY_BY_NAME),
        index=2,
    )

    mode = "predict" if mode_label == "Predict the route" else "spectate"

    if st.button("Begin the case", type="primary"):
        start_case(mode, difficulty_name)
        st.rerun()

    st.stop()


game = st.session_state["game"]

if game["stage"] == "debrief":
    show_debrief(game)

    if st.button("Start a new case", type="primary"):
        del st.session_state["game"]
        st.rerun()

    st.stop()


index = game["round_index"]
example = game["case"].training_examples[index]
model_input = example.model_input

st.caption(
    f"Difficulty: {game['difficulty'].name} · "
    f"Round {index + 1} of {ROUNDS_PER_CASE}"
)
st.progress((index + 1) / ROUNDS_PER_CASE)

left, right = st.columns(2)
with left:
    st.markdown("**Situation**")
    st.write(SITUATIONS[model_input.situation])
with right:
    st.markdown("**Seal mark**")
    st.code(SEAL_MARKS[model_input.clue])

if not game["revealed"]:
    if game["mode"] == "predict":
        st.markdown("### Which route will the messenger take?")
        north_column, south_column = st.columns(2)

        with north_column:
            st.button(
                "Predict North Path (A)",
                key=f"north-{index}",
                on_click=record_guess,
                args=("A",),
                use_container_width=True,
            )

        with south_column:
            st.button(
                "Predict South Path (B)",
                key=f"south-{index}",
                on_click=record_guess,
                args=("B",),
                use_container_width=True,
            )
    else:
        st.button(
            "Reveal the messenger’s route",
            key=f"reveal-{index}",
            on_click=record_guess,
            args=(None,),
            type="primary",
        )


if game["revealed"]:
    route = example.move_target
    st.markdown(f"### The messenger took the **{ROUTE_NAMES[route]} ({route})**.")

    guess = game["guesses"][index]
    if guess is None:
        st.info("Keep watching the clues. The debrief will reveal the pattern.")
    elif guess == route:
        st.success("Correct prediction!")
    else:
        st.warning("That route prediction was incorrect.")

    button_label = (
        "Open the debrief"
        if index + 1 == ROUNDS_PER_CASE
        else "Continue to the next dispatch"
    )
    st.button(
        button_label,
        key=f"continue-{index}",
        type="primary",
        on_click=advance_round,
    )