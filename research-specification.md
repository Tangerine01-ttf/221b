# 221B Research Specification

**Status:** Draft v0.3  
**Purpose:** Define the first controlled experiment before game or model implementation. The primary evaluation measure has been selected; other experiment details remain open.

## Research question

Can a Transformer trained to predict an opponent’s next move from situations, clues, and previous moves develop internal patterns that let a separate probe estimate the opponent’s hidden, occasionally changing strategy? How close are the probe’s strategy estimates to those of a Bayesian model that knows the game’s rules?

## In plain language

We will create a detective game with an opponent whose behavior follows one of four hidden strategies. The Transformer learns to predict the opponent’s next move from the situations, clues, and moves it has observed. After training, a separate probe will check whether the Transformer’s internal patterns contain information about which strategy is active. The probe’s estimates will be compared with the known truth and with a Bayesian model that knows the game’s rules.

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

Before each move, the Transformer receives the current situation and clue, along with the situations, clues, and revealed moves from previous rounds. It predicts probabilities for the two possible moves, A and B.

The current move is not included in the input. Once revealed, it becomes part of the history for later predictions. In this baseline, the Transformer does not directly output probabilities for the hidden strategy. After training, a separate probe will examine the frozen Transformer’s internal patterns and estimate the active strategy. The later sections describe this probe.

## Comparison models

We will evaluate the Transformer’s next-move predictions and, separately, the strategy estimates produced by the post-training probe.

We will compare the probe’s strategy estimates with a Bayesian oracle. The oracle knows the game-generation rules and updates its estimates as situations, clues, and moves arrive. It serves as a reference for this designed environment, not as a claim of perfect reasoning in every detective story or in real life.

We will also use a simple next-move predictor that does not track the full within-case history. Its exact form will be specified before final evaluation.

## Practical closeness criterion

We set the practical closeness margin at 0.05 log-loss units per round. For each training size, we will compare the post-training probe’s strategy probabilities with the Bayesian oracle’s probabilities, scoring both against the strategy that was actually active. We define Δ = probe strategy log loss − Bayesian-oracle strategy log loss. We will call the probe’s estimates sufficiently close at that training size only if the upper bound of the 95% uncertainty interval for Δ is below 0.05. If the interval crosses 0.05, the result is inconclusive relative to this margin.

This criterion applies to strategy estimates read from the Transformer’s frozen internal patterns in this synthetic game. It does not mean the Transformer was trained to output strategy beliefs, or that it reasons like a person.

## Data and splits

Each case contains 16 rounds. We will keep all rounds from a case together so that one case cannot appear in both training and evaluation.

The training sets will be nested:

- 1,000 cases
- 10,000 cases, including the 1,000-case set
- 50,000 cases, including the 10,000-case set

We will also create separate sets of 5,000 validation cases and 10,000 test cases. The validation and test cases will not appear in training.

This gives us 65,000 unique cases in total, or 1,040,000 rounds. We will train five independently initialized Transformer runs at each training size: 15 runs altogether. We will use the same validation and test cases for every run. Model choices will use the validation set; the test set will remain untouched until final evaluation.

## Primary success measure

The primary measure is strategy-probability log loss from the post-training probe. The probe produces probabilities for each of the four possible active strategies on each test round. We score those probabilities against the strategy that was actually active. Lower loss is better.

We compare the probe with the Bayesian oracle on the same test cases. The detailed scoring procedure and the definition of Δ appear below under “Primary strategy-belief measure.” The Transformer’s direct next-move predictions are reported separately as other measures.

## Other measures

We will also report:

*Transformer next-move log loss and Brier score.

*Transformer move prediction accuracy.

*Probe strategy top-choice accuracy.

*Calibration plots for the Transformer’s move probabilities and the probe’s strategy probabilities. These plots compare stated confidence with how often the corresponding predictions are correct.



## Comparing results and estimating uncertainty

For each training run, we will calculate the probe’s paired difference in strategy log loss from the Bayesian oracle on each test case. We will estimate a 95% uncertainty interval by repeatedly sampling complete test cases with replacement and recalculating the average difference. Each sample will keep all 16 rounds of a case together, and the same sampled cases will be used for both the probe and oracle.

We will use 10,000 bootstrap resamples. Using a complete case as the resampling unit is our design choice because rounds within a case share a history and hidden strategy. Koehn, 2004.

We will report the five training runs separately, as well as their average and variation. The case-resampling interval describes uncertainty across test cases for these trained runs; the variation across runs shows sensitivity to training randomness. An interval that includes zero does not by itself prove that the Transformer and oracle are equivalent.

## Human-facing game and stories

The player may predict or watch in spectator mode. The post-case debrief will show a plain-language explanation, a simple chart of clues, moves, and player score, and a Bayesian belief chart. Whether the belief chart is shown during play or only in the debrief remains to be decided, because seeing it during play could affect the player’s predictions.

Cases should be mostly original, with any public-domain Holmes inspirations credited. Stories should give players a chain of evidence to assess rather than imply that one clue alone proves guilt. The social-theory literature review can guide how we present clues, roles, and interpretations; it will not be used to claim that simulated strategies represent real people’s motives.

## Per-round model input and labels

At round *t*, the Transformer receives the completed rounds so far and the current situation and clue. It does not receive information from future rounds.

Each completed round is encoded as:

`<ROUND_START> <SIT_i> <CLUE_j> <MOVE_A or MOVE_B>`

The current, not-yet-completed round is encoded as:

`<ROUND_START> <SIT_i> <CLUE_j> <PREDICT>`

### Transformer training

The Transformer is trained to predict the current move, `MOVE_A` or `MOVE_B`. Its output is a probability for A and a probability for B.

The current move is used as the training answer, but it is not part of the input for that prediction. After the move is revealed, it becomes part of the history for the next round.

The Transformer is not trained on the hidden strategy or the Bayesian posterior. It has no strategy-prediction output head in this baseline.

### Evaluation-only information and probing

A separate evaluation record stores the actual active strategy and the Bayesian oracle’s posterior for each round. These are not included in the Transformer’s training input or training loss.

After the Transformer has been trained, it is frozen. A separate probe may then use its internal activations and active-strategy labels from the validation cases to estimate the active strategy. The probe does not update the Transformer. The test cases remain untouched until final evaluation.

## Primary strategy-belief measure

We will compare the probe’s four strategy probabilities with the Bayesian oracle’s probabilities by scoring both against the actual active strategy on the same held-out test rounds. The primary score is strategy log loss; lower is better.

Let Δ equal the probe’s log loss minus the oracle’s log loss. Our practical closeness margin remains 0.05 log-loss units per round. We will call the probe’s strategy estimates sufficiently close only if the upper bound of the 95% uncertainty interval for Δ is below 0.05.

This tests whether strategy information can be read from the Transformer’s frozen internal representations. It does not mean the Transformer was trained to output strategy beliefs.
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
