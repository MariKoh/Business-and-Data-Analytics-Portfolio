"""
Analysis 2c — Rescue win-back experiment design (A/B with untreated control).
Computes the statistical power for the small (N=250) Rescue cohort and writes a
design doc. Answers the JD 'experimentation' requirement.
Run:  python -m src.churn.experiment_design
"""
from pathlib import Path
import pandas as pd
import numpy as np
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"

N_RESCUE = 250
SPLIT = 0.5                # 50/50 treatment/control
P0 = 0.15                  # assumed control (organic) 90-day return rate
ALPHA = 0.05
POWER = 0.80
Z_ALPHA = norm.ppf(1 - ALPHA)        # one-sided

def cohen_h(p1, p0):
    return 2 * (np.arcsin(np.sqrt(p1)) - np.arcsin(np.sqrt(p0)))

def n_for(p1, p0=P0):                 # n per arm for target POWER
    h = cohen_h(p1, p0)
    return 2 * ((Z_ALPHA + norm.ppf(POWER)) / h) ** 2

def power_for(p1, n_per_arm, p0=P0):  # power at given n per arm
    ncp = cohen_h(p1, p0) * np.sqrt(n_per_arm / 2)
    return norm.cdf(ncp - Z_ALPHA)

def main():
    n_arm = int(N_RESCUE * SPLIT)
    # required n/arm to detect various uplifts at 80% power
    req = {f"+{int((p1-P0)*100)}pp ({P0:.0%}->{p1:.0%})": round(n_for(p1)) for p1 in (0.25, 0.30, 0.40)}
    # power achieved at our actual n/arm for various true uplifts
    pw = {f"+{int((p1-P0)*100)}pp ({P0:.0%}->{p1:.0%})": round(power_for(p1, n_arm), 2)
          for p1 in (0.25, 0.30, 0.40, 0.50)}
    # smallest uplift detectable at 80% power with our n/arm
    p1 = P0
    while p1 < 0.95 and power_for(p1, n_arm) < POWER:
        p1 += 0.005
    mde_pp = (p1 - P0) * 100

    doc = f"""# Rescue Win-Back — Experiment Design (A/B with untreated control)

**Goal.** Measure the *incremental* effect of a one-time personalised reactivation
offer on high-value, lapsing, at-risk members ("Rescue", N={N_RESCUE}).

**Hypothesis.** A personalised one-time offer (tailored to each member's usual
SKUs/categories) increases the 90-day return rate vs. no contact.

**Design.** Randomise the {N_RESCUE} members 50/50 into:
- **Treatment** ({n_arm}): personalised one-time offer (A/B sub-test on discount depth,
  e.g. 30% vs a lighter personalised offer).
- **Control (untreated)** ({n_arm}): no contact. *This is the non-negotiable arm* — it
  is the only way to separate "the offer worked" from "they'd have returned anyway."

**Primary metric.** 90-day return rate (% who make a purchase). **Secondary.**
incremental revenue / margin per member, and net of offer cost.

**Decision rule.** One-sided two-proportion test, alpha={ALPHA}. Treatment wins if the
return-rate lift is significant *and* incremental margin (returns x margin - offer cost)
is positive.

## Power analysis (the crux — N is small)
Assumed organic control return rate p0 = {P0:.0%}; target power = {POWER:.0%}; alpha = {ALPHA}.

**Required sample per arm to detect, at 80% power:**
"""
    for k, v in req.items():
        doc += f"- {k}: **{v} per arm**\n"
    doc += f"\n**Power actually achieved at our {n_arm}/arm for a true uplift of:**\n"
    for k, v in pw.items():
        doc += f"- {k}: power **{v}**\n"
    doc += f"""
**Minimum detectable effect at {n_arm}/arm, 80% power: ~+{mde_pp:.0f}pp** (i.e. p0 {P0:.0%} -> ~{P0+mde_pp/100:.0%}).

**Honest read.** At N={N_RESCUE} (={n_arm}/arm) the test is only powered to detect a
*large* uplift (~+{mde_pp:.0f}pp). Implications and options:
1. Treat the result as **directional**, not precise, if the true effect is modest.
2. **Expand the population** using the churn model: pool all high-value members with high
   predicted churn (not just the 250 cluster members) to raise N and power.
3. Run a **longer window** or sequential test to accumulate more outcomes.

## Link to the model
Members are prioritised by `churn_prob_pred` (Analysis 2b, AUC ~0.79). The win-back is
targeted at the highest-risk high-value members *before* they fully lapse — the model
provides the ranking, the experiment proves the lift.
"""
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "experiment_design.md").write_text(doc, encoding="utf-8")
    print("Required n/arm (80% power):", req)
    print("Power at", n_arm, "/arm:", pw)
    print(f"MDE at {n_arm}/arm: ~+{mde_pp:.0f}pp")
    print("saved -> docs/experiment_design.md")

if __name__ == "__main__":
    main()
