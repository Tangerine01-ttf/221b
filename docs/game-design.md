# 221B Game Design Baseline

**Status:** Design baseline v0.1  
**Project:** Investigating hidden beliefs in neural models

## Goal

Build a small detective game that lets a person and a Transformer predict an opponent’s next move from situations, clues, and previous moves.

The first version is an **observer game**: the player’s prediction does not affect the opponent’s move. The hidden strategies are simulated game states, not claims about real people’s personalities or motives.

## Core game

- Each case has 16 rounds.
- There are four situations, selected randomly with equal probability each round. Situations can repeat.
- There are four hidden strategies, equally likely at the start of a case.
- Each strategy favors one of the four situations.
- The opponent chooses between move A and move B.
- The mapping is one-to-one: exactly one strategy favors each situation. At the start of each case, the strategy is sampled uniformly. Case 1 has no final strategy-identification bonus guess; the score counts route predictions only.

## Intermediate baseline probabilities

If the current situation is the one favored by the active strategy, the opponent chooses A with 65% probability and B with 35% probability.

In any other situation, the opponent chooses A with 35% probability and B with 65% probability.

There are four clue types. The clue associated with the active strategy appears 40% of the time; each other clue appears 20% of the time.

The clue and move are generated separately. The clue does not cause or change the opponent’s move in this baseline.

After a round, the strategy has a 5% chance of switching before the next round. If it switches, it changes uniformly to one of the other three strategies. The strategy active during round 16 is the final strategy for scoring.

## Round sequence

1. Select a situation.
2. Show the clue.
3. Let the human predict A or B, or let them spectate.
4. Reveal the opponent’s move.
5. Award one point for a correct move prediction.
6. Apply the possible strategy switch before the next round.

## Human play and debrief

Prediction mode gives one point for each correct route prediction, for a score out of 16. In Case 1, the score is feedback only. The debrief reveals the messenger’s hidden strategy after the case; identifying the strategy is not scored in this first story version.

Spectator mode shows the same game without requiring predictions.

After round 16, show a plain-language explanation, a chart of situations, clues, moves, predictions, and score, and a research chart of the Bayesian oracle’s estimated probabilities for the four strategies. These charts are for the human debrief, not Transformer training inputs.

## Bayesian oracle

The oracle keeps a probability for each possible strategy.

Before a round, it updates its probabilities to account for the possible strategy switch. After seeing the round’s clue, it updates those probabilities using the clue likelihood. It uses the updated probabilities to predict A or B. After the move is revealed, it updates again using the move likelihood.

The oracle is an evaluation reference. The baseline Transformer is trained to predict observed moves; it does not receive hidden strategy labels or oracle probabilities as training targets.

## Proposed difficulty levels

These settings are starting proposals for playtesting. Intermediate is the research baseline.

| Level | Chance of A in favored / other situations | Matching clue chance | Switch chance |
|---|---:|---:|---:|
| Easy | 85% / 15% | 70% | 1% |
| Moderate | 75% / 25% | 55% | 2% |
| Intermediate | 65% / 35% | 40% | 5% |
| Hard | 60% / 40% | 32% | 10% |
| Advanced | 55% / 45% | 27% | 15% |

For each level, the remaining clue probability is divided equally among the other three clue types. Human playtesting may lead us to revise these settings.

## Case 1: The Manuscript Meant for You

**Setting:** Fictional historical Nalanda; the exact year is unspecified. The messenger, recipient, manuscript, paths, events, and cipher are invented for the game.

**Opening narration:**

At Nalanda, a sealed manuscript arrives bearing your name—and yours alone. A trusted messenger is bringing it before sunrise. Its warning could put people in danger if it falls into the wrong hands. Someone else may be searching for the messenger, who can take the North Path or the South Path.

You have sixteen coded dispatches. Each records one event and carries a strange mark. Some marks may mislead you. Study the pattern and predict each route so you can be the first to receive the manuscript.

**Routes:** A is the North Path; B is the South Path.

**Situations:**

1. A bell rings after dark.
2. An oil lamp suddenly goes out.
3. Rain sweeps across the courtyard.
4. An unexpected visitor arrives.

**The Four Seals:** Show the marks without their names or meanings during play. Reveal their key in the debrief.

- Echo: a broken ring with three short rays; linked to the bell.
- Ember: a small flame with a missing stroke; linked to the lamp.
- River: three waves with one broken line; linked to the rain.
- Footstep: two prints, one turned backwards; linked to the visitor.

These are original fictional marks, not historical Nalanda writing or religious symbols.

**Round flow:** Show the situation and its seal, ask the player to predict North or South, then reveal the messenger’s route. Repeat for 16 rounds. The seal is a clue about the hidden strategy; it does not determine the route.

**Scoring:** Give one point per correct route prediction, for a score out of 16. In this first case, the score is feedback only; it does not decide whether the manuscript reaches its intended recipient.

**Debrief:** Reveal the seal key and the hidden strategy used in each round, including any switches. Explain that the matching seal appears 40% of the time and each other seal 20% of the time. In the favored situation, North is chosen 65% of the time; in the other situations, 35%. Show the route-and-score chart and the Bayesian belief chart.

**Research separation:** This story is for the player-facing game. Keep the first Transformer experiment’s structured-symbol inputs unchanged; test story text separately later.

## Social and ethical design notes

- Call the four hidden strategies simulated **playbooks**, not personality types.
- Do not associate a playbook with a character’s demographic identity.
- Treat clues as information generated by the game, not as proof of intent or morality.
- Clearly distinguish observed moves, the oracle’s estimates, and the Transformer’s predictions.
- If player data is collected for research, explain what is collected and minimize personal data.

## Later experiments

Keep the baseline separate from future variants, such as clues that affect the opponent’s move or signals whose meanings change through interaction. This lets us measure what each change contributes.

## Next development milestone

Implement Case 1’s story labels and debrief in the Python CLI while keeping the simulator probabilities and structured Transformer inputs unchanged.