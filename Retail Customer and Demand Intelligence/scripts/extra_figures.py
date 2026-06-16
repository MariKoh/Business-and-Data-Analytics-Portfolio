"""Two README figures: (1) a 3x2 segment matrix (value tier x lifecycle),
(2) a before/after value chart with linear-scaling annotation."""
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "reports" / "figures"; TAB = ROOT / "reports" / "tables"; PROC = ROOT / "data" / "processed"
FOREST="#214E34"; GREEN="#2C6E49"; BLUE="#2F6F95"; AMBER="#C77D30"; RED="#B85042"; GREY="#9AA0A6"; CHAR="#2B2B2B"

# ---------- Figure 1: 3x2 segment matrix ----------
p = pd.read_csv(TAB / "segment_profile.csv")
def cell(seg):
    r = p[p["segment"]==seg].iloc[0]
    return r
order = {  # (row, col): (segment, short, priority colour, tag)
 (0,0):("High-value, active","Champions",GREEN,"PROTECT"),
 (0,1):("High-value, lapsing, at-risk","At-risk VIPs",RED,"RESCUE"),
 (1,0):("Mid-value, active, at-risk","Rising regulars",BLUE,"GROW"),
 (1,1):("Mid-value, lapsing, at-risk","Drifting mid-tier",GREY,""),
 (2,0):("Low-value, active","New shoppers",GREY,""),
 (2,1):("Low-value, lapsing","One-and-done",GREY,""),
}
fig, ax = plt.subplots(figsize=(11,7)); ax.set_xlim(0,2); ax.set_ylim(0,3); ax.axis("off")
ax.text(1,3.18,"Customer segments — value tier × lifecycle",ha="center",fontsize=15,fontweight="bold",color=CHAR)
ax.text(0.5,3.02,"ACTIVE",ha="center",fontsize=11,fontweight="bold",color=GREEN)
ax.text(1.5,3.02,"LAPSING / AT-RISK",ha="center",fontsize=11,fontweight="bold",color=RED)
for i,lab in enumerate(["HIGH value","MID value","LOW value"]):
    ax.text(-0.04,2.5-i,lab,ha="right",va="center",fontsize=10,fontweight="bold",color=CHAR,rotation=90)
for (rw,cl),(seg,short,col,tag) in order.items():
    r=cell(seg); x=cl; y=2-rw
    box=FancyBboxPatch((x+0.04,y+0.04),0.92,0.92,boxstyle="round,pad=0.01,rounding_size=0.04",
                       linewidth=2,edgecolor=col,facecolor=col if tag else "#F3F2EE",alpha=0.92 if tag else 1)
    ax.add_patch(box)
    tc = "white" if tag else CHAR
    if tag: ax.text(x+0.5,y+0.80,tag,ha="center",fontsize=10,fontweight="bold",color="white")
    ax.text(x+0.5,y+0.6,short,ha="center",fontsize=12,fontweight="bold",color=tc)
    ax.text(x+0.5,y+0.42,f"{r['members_pct']:.0f}% of members",ha="center",fontsize=9,color=tc)
    ax.text(x+0.5,y+0.28,f"avg £{r['monetary']:,.0f}",ha="center",fontsize=9,color=tc)
    ax.text(x+0.5,y+0.14,f"{r['revenue_pct']:.0f}% of revenue · {r['churn_prob']*100:.0f}% churn risk",ha="center",fontsize=8,color=tc)
fig.tight_layout(); fig.savefig(FIG/"segment_matrix.png",dpi=140,bbox_inches="tight"); print("saved segment_matrix.png")

# ---------- Figure 2: before/after value + scaling ----------
tx = pd.read_parquet(PROC/"model_transactions.parquet")
span=(tx["invoice_date"].max()-tx["invoice_date"].min()).days/365.25
annual_rev=tx["revenue"].sum()/span; margin=0.35
base_gp=annual_rev*margin; uplift=81800; after=base_gp+uplift
fig, ax = plt.subplots(figsize=(9,5.5))
ax.bar(["Today\n(baseline)"],[base_gp],color=GREY,width=0.55,label="Current gross profit (est.)")
ax.bar(["With the\ninitiatives"],[base_gp],color=GREY,width=0.55)
ax.bar(["With the\ninitiatives"],[uplift],bottom=[base_gp],color=GREEN,width=0.55,label="Added profit (projected)")
ax.set_ylabel("Annual gross profit (GBP, illustrative)")
ax.set_title("Projected profit uplift from the four levers",fontweight="bold")
ax.annotate(f"+£{uplift/1000:.0f}k / yr  (+{uplift/base_gp*100:.1f}% of profit)",
            xy=(1,after),xytext=(1.05,after*1.02),fontsize=11,fontweight="bold",color=GREEN)
ax.text(0.5,-0.16*after,
        f"Scales linearly with revenue: ~£{uplift/annual_rev*1e9/1e6:.0f}M/yr at £1B turnover.  "
        "Conservative, sensitivity-tested assumptions.",
        ha="center",fontsize=9,color=CHAR,transform=ax.get_xaxis_transform() if False else ax.transData)
ax.legend(loc="upper left",fontsize=9); ax.set_ylim(0,after*1.15)
fig.tight_layout(); fig.savefig(FIG/"value_before_after.png",dpi=140); print("saved value_before_after.png")
print(f"baseline GP ~£{base_gp/1e6:.2f}M | annual rev ~£{annual_rev/1e6:.2f}M | scaled@1B ~£{uplift/annual_rev*1e9/1e6:.1f}M")
