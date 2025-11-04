# 🏈 Gang of Gridiron Gurus - Fantasy Football Analysis Report

> **Analysis Date:** November 04, 2025 | **Weeks Analyzed:** 9 completed weeks

---

## � Table of Contents
- [Executive Summary](#-executive-summary)
- [Luck Rankings](#-luck-rankings) 
- [Weekly Scoring Trends](#-weekly-scoring-trends)
- [Performance Analysis](#-performance-analysis)
- [Methodology](#-methodology)

---

## 📊 Executive Summary

This comprehensive analysis examines team performance across **9 weeks** of fantasy football action. We analyze both **luck factors** (schedule strength and opponent matchups) and **scoring trends** (momentum and consistency) to provide actionable insights for your league.

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
| 1 | Bye Week All-Stars 💀 | -191.8 | 2-7 | 4-5 | -2 |
| 2 | The chain gang 💀 | -162.7 | 3-6 | 5-4 | -2 |
| 3 | Where Shaquon at? 💀 | -122.7 | 5-4 | 6-3 | -1 |
| 4 | MarlBurrow Men 💀 | -70.0 | 3-6 | 4-5 | -1 |
| 5 | Stèrby FFC 💀 | -28.2 | 3-6 | 3-6 | +0 |
| 6 | Little Kittle Lover 💀 | -11.8 | 5-4 | 5-4 | +0 |
| 7 | The Hurt Locker 🍀 | +30.0 | 4-5 | 4-5 | +0 |
| 8 | Josh & Junk 🍀 | +53.6 | 5-4 | 4-5 | +1 |
| 9 | Let Him Cook 🍀 | +55.5 | 6-3 | 5-4 | +1 |
| 10 | Go On Jalen! 🍀 | +91.8 | 5-4 | 4-5 | +1 |
| 11 | Last Second Kicker 🍀 | +115.5 | 6-3 | 5-4 | +1 |
| 12 | Shot of Jameson 🍀 | +240.9 | 7-2 | 5-4 | +2 |


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
- **Luckiest:** The chain gang Week 7 - 115.7 vs 109.4 (**WIN**)


---

## 📈 Weekly Scoring Trends

*Track team momentum, consistency, and recent form to predict future performance*

![Scoring Trends](charts/scoring_trends.png)

This **heatmap visualization** displays each team's weekly scoring performance with color-coded intensity. Darker blue cells indicate higher scores, while lighter/white cells show lower performances. The **sparklines** on the right reveal each team's trajectory: ↗ rising trends (green), → stable performance (gray), and ↘ declining trends (red). Teams are sorted by average scoring to easily identify the strongest performers.

### 🔥 Momentum Analysis

*Teams sorted by recent form (last 3 weeks average)*

| Team | Avg Score | Recent Form | Trend | Volatility |
|------|-----------|-------------|-------|------------|
| Let Him Cook | 114.2 | 126.0 | ⬆️ +2.1/wk | 14% |
| Little Kittle Lover | 110.6 | 116.9 | ⬆️ +1.2/wk | 14% |
| Josh & Junk | 106.4 | 116.2 | ⬆️ +2.2/wk | 15% |
| Bye Week All-Stars | 100.5 | 110.3 | ⬆️ +3.2/wk | 22% |
| The chain gang | 109.9 | 107.2 | ➡️ -0.4/wk | 23% |
| MarlBurrow Men | 101.2 | 106.2 | ⬆️ +1.7/wk | 19% |
| Last Second Kicker | 108.2 | 106.0 | ➡️ +0.5/wk | 15% |
| The Hurt Locker | 100.3 | 105.5 | ⬆️ +3.2/wk | 26% |
| Stèrby FFC | 99.4 | 102.1 | ➡️ -0.0/wk | 9% |
| Where Shaquon at? | 115.0 | 99.2 | ⬇️ -2.5/wk | 19% |
| Go On Jalen! | 104.8 | 96.8 | ⬇️ -4.2/wk | 20% |
| Shot of Jameson | 108.4 | 91.0 | ⬇️ -2.6/wk | 21% |


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

*Analysis Date: November 04, 2025*

*Unlock the patterns behind your fantasy success*

</div>
