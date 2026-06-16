# Rescue Win-Back — Experiment Design (A/B with untreated control)

**Goal.** Measure the *incremental* effect of a one-time personalised reactivation
offer on high-value, lapsing, at-risk members ("Rescue", N=250).

**Hypothesis.** A personalised one-time offer (tailored to each member's usual
SKUs/categories) increases the 90-day return rate vs. no contact.

**Design.** Randomise the 250 members 50/50 into:
- **Treatment** (125): personalised one-time offer (A/B sub-test on discount depth,
  e.g. 30% vs a lighter personalised offer).
- **Control (untreated)** (125): no contact. *This is the non-negotiable arm* — it
  is the only way to separate "the offer worked" from "they'd have returned anyway."

**Primary metric.** 90-day return rate (% who make a purchase). **Secondary.**
incremental revenue / margin per member, and net of offer cost.

**Decision rule.** One-sided two-proportion test, alpha=0.05. Treatment wins if the
return-rate lift is significant *and* incremental margin (returns x margin - offer cost)
is positive.

## Power analysis (the crux — N is small)
Assumed organic control return rate p0 = 15%; target power = 80%; alpha = 0.05.

**Required sample per arm to detect, at 80% power:**
- +10pp (15%->25%): **195 per arm**
- +15pp (15%->30%): **93 per arm**
- +25pp (15%->40%): **38 per arm**

**Power actually achieved at our 125/arm for a true uplift of:**
- +10pp (15%->25%): power **0.64**
- +15pp (15%->30%): power **0.89**
- +25pp (15%->40%): power **1.0**
- +35pp (15%->50%): power **1.0**

**Minimum detectable effect at 125/arm, 80% power: ~+13pp** (i.e. p0 15% -> ~28%).

**Honest read.** At N=250 (=125/arm) the test is only powered to detect a
*large* uplift (~+13pp). Implications and options:
1. Treat the result as **directional**, not precise, if the true effect is modest.
2. **Expand the population** using the churn model: pool all high-value members with high
   predicted churn (not just the 250 cluster members) to raise N and power.
3. Run a **longer window** or sequential test to accumulate more outcomes.

## Link to the model
Members are prioritised by `churn_prob_pred` (Analysis 2b, AUC ~0.79). The win-back is
targeted at the highest-risk high-value members *before* they fully lapse — the model
provides the ranking, the experiment proves the lift.
