# 🏈 Gang of Gridiron Gurus - Fantasy Football Analysis Report

> **Analysis Date:** October 28, 2025 | **Weeks Analyzed:** 8 completed weeks

---

## � Table of Contents
- [Executive Summary](#-executive-summary)
- [Luck Rankings](#-luck-rankings) 
- [Weekly Scoring Trends](#-weekly-scoring-trends)
- [Performance Analysis](#-performance-analysis)
- [Methodology](#-methodology)

---

## 📊 Executive Summary

This comprehensive analysis examines team performance across **8 weeks** of fantasy football action. We analyze both **luck factors** (schedule strength and opponent matchups) and **scoring trends** (momentum and consistency) to provide actionable insights for your league.

### Key Findings:
- **Most Lucky Team:** Teams with positive luck scores are winning more than their scoring suggests
- **Most Unlucky Team:** Teams with negative luck scores are underperforming their scoring ability
- **Hottest Team:** Teams with strong upward scoring trends are building momentum
- **Most Consistent:** Teams with low volatility provide reliable weekly production

---

## 🏆 Luck Rankings

*Teams ranked by luck score - negative scores indicate unlucky teams who should have better records*

![Luck Rankings](charts/luck_rankings.png)

| Rank | Team | Luck Score | Record | Should Be | Diff |
|------|------|------------|--------|-----------|------|
| 1 | Bye Week All-Stars 💀 | -176.4 | 2-6 | 4-4 | -2 |
| 2 | MarlBurrow Men 💀 | -140.0 | 2-6 | 3-5 | -1 |
| 3 | Where Shaquon at? 💀 | -118.2 | 5-3 | 6-2 | -1 |
| 4 | Stèrby FFC 💀 | -81.8 | 2-6 | 3-5 | -1 |
| 5 | The chain gang 💀 | -61.8 | 3-5 | 4-4 | -1 |
| 6 | The Hurt Locker 💀 | -7.3 | 3-5 | 3-5 | +0 |
| 7 | Josh & Junk 🍀 | +30.9 | 4-4 | 4-4 | +0 |
| 8 | Little Kittle Lover 🍀 | +36.4 | 5-3 | 5-3 | +0 |
| 9 | Let Him Cook 🍀 | +63.6 | 5-3 | 4-4 | +1 |
| 10 | Last Second Kicker 🍀 | +78.2 | 5-3 | 4-4 | +1 |
| 11 | Go On Jalen! 🍀 | +125.5 | 5-3 | 4-4 | +1 |
| 12 | Shot of Jameson 🍀 | +250.9 | 7-1 | 5-3 | +2 |


##  Performance Analysis

### ⚖️ Wins: Actual vs Expected

*Comparing real records against "should have" records based on scoring performance*

![Wins Comparison](charts/wins_comparison.png)

This analysis reveals which teams have been **schedule beneficiaries** versus **schedule victims**. The orange bars show what each team's record should be based purely on their scoring output, while blue bars show their actual record.

### 🎲 Luck Distribution

![Luck Distribution](charts/luck_distribution.png)

*Distribution of luck scores across the league - most teams cluster around neutral (0)*

This chart shows the distribution of luck scores across all teams. Positive values indicate lucky teams, while negative values show unlucky teams.

### 🎰 Most Extreme Weeks

*The biggest lucky breaks and unlucky losses of the season*

- **Luckiest:** Shot of Jameson Week 1 - 87.3 vs 76.0 (**WIN**)
- **Unluckiest:** Shot of Jameson Week 8 - 73.5 vs 133.7 (**LOSS**)
- **Luckiest:** Bye Week All-Stars Week 6 - 101.0 vs 79.3 (**WIN**)
- **Unluckiest:** Bye Week All-Stars Week 5 - 117.1 vs 118.8 (**LOSS**)
- **Luckiest:** MarlBurrow Men Week 8 - 96.3 vs 64.6 (**WIN**)


---

## 📈 Weekly Scoring Trends

*Track team momentum, consistency, and recent form to predict future performance*

![Scoring Trends](charts/scoring_trends.png)

This **heatmap visualization** displays each team's weekly scoring performance with color-coded intensity. Darker blue cells indicate higher scores, while lighter/white cells show lower performances. The **sparklines** on the right reveal each team's trajectory: ↗ rising trends (green), → stable performance (gray), and ↘ declining trends (red). Teams are sorted by average scoring to easily identify the strongest performers.

### 🔥 Momentum Analysis

*Teams sorted by recent form (last 3 weeks average)*

| Team | Avg Score | Recent Form | Trend | Volatility |
|------|-----------|-------------|-------|------------|
| Where Shaquon at? | 120.3 | 120.3 | ➡️ +1.0/wk | 14% |
| Bye Week All-Stars | 103.3 | 118.0 | ⬆️ +7.1/wk | 21% |
| Little Kittle Lover | 112.1 | 113.4 | ⬆️ +2.9/wk | 14% |
| MarlBurrow Men | 102.6 | 112.0 | ⬆️ +3.6/wk | 19% |
| Josh & Junk | 105.5 | 111.4 | ⬆️ +2.3/wk | 16% |
| Last Second Kicker | 108.4 | 111.2 | ➡️ +0.8/wk | 16% |
| The Hurt Locker | 98.8 | 110.4 | ⬆️ +3.3/wk | 27% |
| Let Him Cook | 109.8 | 109.4 | ➡️ -0.8/wk | 9% |
| Shot of Jameson | 112.5 | 108.7 | ➡️ -0.2/wk | 18% |
| Stèrby FFC | 99.0 | 94.5 | ➡️ -0.4/wk | 9% |
| Go On Jalen! | 107.2 | 90.8 | ⬇️ -4.0/wk | 20% |
| The chain gang | 106.0 | 89.4 | ⬇️ -3.9/wk | 23% |


---

## � Methodology

### Luck Score Calculation
- **Weekly Analysis**: For each week, calculate how many teams you would have beaten with your score
- **Opponent Strength**: Compare your actual opponent's strength to average opponent difficulty
- **Luck Factors**: 
  - ✅ **Positive Luck**: Beating stronger opponents or losing to weaker ones
  - ❌ **Negative Luck**: Losing to stronger opponents or beating weaker ones

### Scoring Trends Analysis
- **Momentum**: Linear regression slope showing points gained/lost per week
- **Recent Form**: Average scoring over last 3 weeks
- **Volatility**: Standard deviation of scoring (consistency measure)
- **Streaks**: Consecutive weeks above/below personal average

### Expected Wins Model
- **Fair Scheduling**: Calculate record based on scoring vs. all possible opponents each week
- **Schedule Strength**: Account for actual opponents faced vs. league average
- **Performance Prediction**: Use trends to project future performance

---

<div align="center">

**📈 Generated by GGG Luck Fantasy Football Analyzer**

*Analysis Date: October 28, 2025*

*Unlock the patterns behind your fantasy success*

</div>
