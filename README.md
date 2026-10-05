# 221b
Investigating how neural models infer, represent, and use hidden beliefs from observable behavior.

221B
Investigating Hidden Beliefs in Neural Models

Overview

221B investigates whether a small autoregressive Transformer,
trained only on observable trajectories in an imperfect-information
game, develops internal representations corresponding to Bayesian
beliefs about hidden opponent strategies.

The model never receives the true hidden strategy or Bayesian
posterior during training.

Instead, an exact Bayesian oracle is used only as an evaluation
reference.

Research Questions

1. Can the model predict behavior from observable trajectories?
2. Do its internal representations encode Bayesian beliefs?
3. Do these representations emerge at specific layers?
4. Do representations respond appropriately to counterfactual evidence?
5. Does manipulating these representations causally alter behavior?

Method

Observable Game Trajectory
          ↓
Small Autoregressive Transformer
          ↓
Hidden Representations
          ↓
 ┌────────┴────────┐
 ↓                 ↓
Probing       Counterfactuals
 ↓                 ↓
Bayesian       Representation
Beliefs          Changes
        \         /
         \       /
       Activation
       Intervention
             ↓
       Causal Evidence
