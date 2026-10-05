# 221B Research Specification

**Status:** Draft v0.3  
**Purpose:** Define the first controlled experiment before game or model implementation. The primary evaluation measure has been selected; other experiment details remain open.

## Research question

Can a Transformer infer an opponent’s hidden, occasionally changing strategy from situations, noisy clues, and moves—and express its uncertainty accurately compared with a Bayesian model?

## In plain language

We will create a detective game with an opponent whose behavior follows one of four hidden strategies. The player and model see situations, clues, and moves, then try to work out which strategy is active and predict what the opponent will do next.

Because we control how the opponent is generated, we know the hidden strategy. That lets us compare the Transformer’s predictions with the truth and with a Bayesian model that knows the game’s rules.

## Scope and terminology

In this project, a **strategy** is a rule programmed into the game. A model’s **belief** is its probability estimate about which programmed strategy is active. These terms describe the simulation; they are not claims about real people’s thoughts or motives.

The first experiment tests performance in this controlled game. Results will not automatically generalize to real people or investigations.

## Confirmed game baseline

| Setting | First version |
|---|---|
| Situations | Four; each is sampled with equal probability each round |
| Hidden strategies | Four; each favors a different situation |
| Starting strategy | Sampled uniformly at the start of each case |
| Moves | A or B |
| Move rule | The chance of A is 65% in the active strategy’s favored situation and 35% in the other situations; B is the complement |
| Case length | 16 rounds |
| Strategy changes | After a round that has a following round, there is a 5% chance of switching. A new strategy is selected uniformly from the other three. |
| Noisy clue | One of four clue types appears before the move |
| Clue rule | The clue matches the active strategy 40% of the time; each other clue type appears 20% of the time |
| Human role | The player may predict or watch in spectator mode. Human predictions do not affect the opponent’s behavior. |

These are the intermediate-level baseline settings. The proposed easy-to-advanced settings still need to be confirmed before they are used in an experiment.

## What happens each round

The game samples a situation and shows a clue. The opponent then chooses A or B according to the active strategy and that situation. The strategy may change between rounds according to the 5% rule.

The player and model see the situation and clue before the move. After the move is revealed, it becomes part of the history available for later predictions.

## What the model sees and predicts

Before each move, the model receives:

- The current situation and clue.
- The situations, clues, and observed moves from previous rounds.

It predicts:

1. The probability of move A or B on this round.
2. Its probability estimate for each of the four strategies.

The model does not receive the hidden strategy or the unrevealed move as input. During training, the known strategy and move may be used as answer labels.

## Comparison models

We will compare the Transformer with:

- **A Bayesian oracle:** a probability calculator that knows the game-generation rules and updates its strategy estimates as clues and moves arrive.
- **A simple baseline:** a predictor that does not use the full within-case history to track strategy. Its exact form will be specified before final evaluation.

The Bayesian oracle is a reference for this designed environment. It does not represent perfect reasoning in every detective story or real-world situation.

## Practical closeness criterion

We set the practical closeness margin at 0.05 log-loss units per round. For each training size, we will compare the Transformer with the Bayesian oracle using Δ = Transformer log loss − Bayesian-oracle log loss. We will call the Transformer sufficiently close at that training size only if the upper bound of the 95% uncertainty interval for Δ is below 0.05. If the interval crosses 0.05, the result is inconclusive relative to this margin.

This criterion applies to the specified synthetic game and primary strategy-prediction measure. It does not establish that the Transformer reasons like a person.

## Data and splits

Each case contains 16 rounds. We will keep all rounds from a case together so that one case cannot appear in both training and evaluation.

The training sets will be nested:

- 1,000 cases
- 10,000 cases, including the 1,000-case set
- 50,000 cases, including the 10,000-case set

We will also create separate sets of 5,000 validation cases and 10,000 test cases. The validation and test cases will not appear in training.

This gives us 65,000 unique cases in total, or 1,040,000 rounds. We will train five independently initialized Transformer runs at each training size: 15 runs altogether. We will use the same validation and test cases for every run. Model choices will use the validation set; the test set will remain untouched until final evaluation.

## Primary success measure

The primary measure is **strategy-probability log loss**.

Before each move, after seeing the current situation and clue, the Transformer predicts probabilities for the four possible active strategies. For each round, we score how much probability it assigned to the strategy that was actually active. We average the 16 round scores within each case, then average across the 10,000 test cases. Lower loss is better.

We will compare the Transformer and Bayesian oracle on the same test cases. The Bayesian oracle knows the game’s generating rules, so it is our reference for how well strategy uncertainty can be estimated in this setting. The main result will be the difference:

**Δ = Transformer log loss − Bayesian-oracle log loss**

A positive Δ means the Transformer had higher loss on the test set. A negative Δ means it had lower observed loss on that finite test set; it does not by itself show that the Transformer is better in expectation than an oracle that knows the correct rules.

## Other measures

We will also report:

- Log loss and Brier score for next-move predictions.
- Strategy top-choice accuracy.
- Move prediction accuracy.
- Calibration plots, which compare stated confidence with how often predictions are correct.

## Comparing results and estimating uncertainty

For each Transformer run, we will calculate the paired difference in log loss from the Bayesian oracle on each test case. We will estimate a 95% uncertainty interval by repeatedly sampling complete test cases with replacement and recalculating the average difference. Each sample will keep all 16 rounds of a case together. We will use the same sampled cases for both models.

We will use 10,000 bootstrap resamples. This applies a paired bootstrap approach used in model evaluation; using a complete case as the resampling unit is our design choice because rounds within a case share a history and hidden strategy. [Koehn, 2004](https://aclanthology.org/W04-3250/)

We will report the five training runs separately as well as their average and variation. The case-resampling interval describes uncertainty across test cases for these runs; the variation across runs shows sensitivity to training randomness. An interval that includes zero will not, by itself, count as proof that the Transformer and oracle are equivalent. Any “close enough” threshold must be chosen before the final test.

## Human-facing game and stories

The player may predict or watch in spectator mode. The post-case debrief will show a plain-language explanation, a simple chart of clues, moves, and player score, and a Bayesian belief chart. Whether the belief chart is shown during play or only in the debrief remains to be decided, because seeing it during play could affect the player’s predictions.

Cases should be mostly original, with any public-domain Holmes inspirations credited. Stories should give players a chain of evidence to assess rather than imply that one clue alone proves guilt. The social-theory literature review can guide how we present clues, roles, and interpretations; it will not be used to claim that simulated strategies represent real people’s motives.

## Per-round model input and answer labels

### What the model receives

For each prediction, the input contains the observed history and the current round’s situation and clue. It does not contain anything from future rounds.

Each completed round is encoded as four structured symbols:

`<ROUND_START> <SIT_i> <CLUE_j> <MOVE_A or MOVE_B>`

The current, not-yet-completed round is encoded as:

`<ROUND_START> <SIT_i> <CLUE_j> <PREDICT>`

For example:

`<ROUND_START> <SIT_2> <CLUE_1> <MOVE_B> <ROUND_START> <SIT_4> <CLUE_3> <PREDICT>`

Here, the first round is already complete, while the model is being asked to predict the move and active strategy in the second round. At round 16, the sequence contains at most 64 symbols: four for each round.

### What the model predicts

For each round, the model produces two probability distributions:

- **Active-strategy probabilities:** one probability for each of the four strategies.
- **Move probabilities:** one probability for A and one for B.

### Answer labels used for training and scoring

Each prediction example has two answer labels stored separately from its input:

| Label | What it records |
|---|---|
| `active_strategy` | The strategy actually active in this round: one of `STRAT_1` through `STRAT_4` |
| `move` | The move actually chosen this round: `MOVE_A` or `MOVE_B` |

The strategy label is used to train and score the strategy-prediction output. The move label is used to train and score the move-prediction output. Neither label is included in the model input for that same round.

### When a move becomes visible

The move for the current round is hidden while the model predicts. After it is revealed, it is added to the observed history as `MOVE_A` or `MOVE_B` for the next round’s prediction.

Training examples will be made from the observed prefix at each round. We will split data by complete case **before** creating these per-round examples, so rounds from one case cannot appear in different data splits.

### Information excluded from the first experiment

The Transformer input will not include:

- The hidden active-strategy label.
- The current or any future move before it is revealed.
- Future-round situations or clues.
- Case IDs, random seeds, or other bookkeeping information.
- Story text, player scores, human predictions, explanations, or the Bayesian belief chart.

The Bayesian oracle receives the same observable history, situation, and clue as the Transformer, plus the known game-generation rules. Its probability estimates are used for comparison; they are not Transformer inputs.

Story text remains reserved for a separate experiment after the structured-symbol baseline has been evaluated.

## Limits and safeguards

- The first dataset is synthetic.
- The four strategies are programmed rules, not personality types or demographic categories.
- Human predictions do not control the opponent’s moves.
- Any later study involving human participants will need its own plan for consent and privacy.
- Difficulty settings, the player’s final strategy-guess bonus, model size, and dataset size remain open decisions.
