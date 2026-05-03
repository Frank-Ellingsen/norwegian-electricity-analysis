# Power BI Dashboard Templates for Norwegian Electricity Analysis

## Dashboard 1: Executive Summary

### Layout: 4x3 Grid

**Row 1: Key Performance Indicators**
```
[KPI Card]          [KPI Card]          [KPI Card]          [KPI Card]
North Avg Price     South Avg Price     NS Difference       Convergence Rate
79.91 EUR/MWh      90.09 EUR/MWh       58.75 EUR/MWh       7.9%
```

**Row 2: Main Trend Analysis**
```
[Line Chart - Full Width Spanning 4 Columns]
Title: "North vs South Daily Average Prices"
- X-axis: Date (2021-2026)
- Y-axis: Price (EUR/MWh)
- Series 1: North Average (Blue)
- Series 2: South Average (Red)
- Series 3: Convergence Threshold ±5 EUR (Gray dashed lines)
```

**Row 3: Supporting Visuals**
```
[Area Chart]              [Heatmap]                [Map Visual]
NS Price Difference       Convergence by Season    Geographic Price Distribution
- Shows convergence       - Rows: Seasons          - Bubble size: Avg Price
  periods in green        - Columns: Years         - Color: Price level
- Divergence in red       - Values: Conv. Rate %   - Coordinates: Lat/Long
```

### Filters Panel (Right Side):
- Date Range Slicer
- Zone Multi-Select
- Season Dropdown
- Convergence Status Toggle

---

## Dashboard 2: Convergence Deep Dive

### Layout: 3x4 Grid

**Row 1: Convergence Overview**
```
[Gauge Chart]           [Donut Chart]           [Card Visual]
Current Conv. Rate      Conv. Distribution      Longest Streak
7.9%                   Convergent: 7.9%        6 days
Target: 15%            Divergent: 92.1%        (Feb 2021)
```

**Row 2: Convergence Patterns**
```
[Scatter Plot - Full Width]
Title: "Daily North vs South Price Correlation"
- X-axis: North Price (EUR/MWh)
- Y-axis: South Price (EUR/MWh)
- Diagonal line: Perfect convergence
- Color: Convergence status
- Size: Absolute difference
```

**Row 3: Temporal Analysis**
```
[Matrix Visual]              [Column Chart]           [Line Chart]
Convergence by Time          Monthly Conv. Rate       Convergence Streaks
Rows: Hour of Day           X: Month-Year            X: Date
Cols: Day of Week           Y: Convergence %         Y: Streak Length
Values: Conv. Rate %        Color: Season            Threshold: 3+ days
```

**Row 4: Drivers Analysis**
```
[Waterfall Chart]           [Bar Chart]             [Combo Chart]
Conv. Rate Factors          Weekend vs Weekday      Price Level Impact
- Base Rate                 Weekend: 10.9%          Line: Avg Price
- Weekend Effect: +4.3%     Weekday: 6.6%          Bars: Conv. Rate
- Season Effect: varies     Difference: +4.3%       by Price Category
- Final Rate: 7.9%
```

---

## Dashboard 3: Zone Analysis

### Layout: 4x3 Grid

**Row 1: Zone Performance Cards**
```
[Card] NO1    [Card] NO2    [Card] NO3    [Card] NO4    [Card] NO5
79.91         88.26         36.96         22.96         74.84
EUR/MWh       EUR/MWh       EUR/MWh       EUR/MWh       EUR/MWh
Eastern       Southern      Central       Northern      Western
```

**Row 2: Zone Comparison**
```
[Box Plot - Full Width]
Title: "Price Distribution by Zone (2021-2026)"
- X-axis: Zone (NO4, NO3, NO5, NO1, NO2) - North to South order
- Y-axis: Price (EUR/MWh)
- Show: Median, Quartiles, Outliers
- Color coding: North (Blue), South (Red)
```

**Row 3: Detailed Analysis**
```
[Line Chart]              [Heatmap]                [Table Visual]
All Zones Trend           Zone vs Season Matrix    Zone Statistics
- 5 lines for zones       Rows: Zones              Columns: Zone, Avg, Min,
- Different colors        Cols: Seasons            Max, StdDev, Spikes,
- Same Y-axis scale       Values: Avg Price        Ranking
- Legend: Zone names      Color: Price intensity
```

---

## Dashboard 4: Price Spikes & Volatility

### Layout: 3x4 Grid

**Row 1: Spike Overview**
```
[KPI Card]              [KPI Card]              [KPI Card]
Total Spikes >200       Highest Price           Most Volatile Zone
1,247 events           898.25 EUR/MWh          NO2 (Southern)
                       Dec 12, 2024            σ = 70.01
```

**Row 2: Spike Analysis**
```
[Column Chart]                    [Scatter Plot]
Monthly Spike Count               Price vs Volatility
- X: Month-Year                   - X: Average Price
- Y: Number of spikes >200        - Y: Standard Deviation
- Color: Zone                     - Size: Spike count
- Stacked by zone                 - Color: Zone
```

**Row 3: Volatility Patterns**
```
[Heatmap]                        [Line Chart]
Hourly Volatility Matrix         Rolling Volatility
- Rows: Hour (0-23)              - X: Date
- Cols: Day of Week              - Y: 30-day rolling StdDev
- Values: Avg volatility         - Multiple lines for zones
- Color: Intensity scale         - Highlight extreme periods
```

**Row 4: Risk Metrics**
```
[Gauge Chart]           [Waterfall Chart]       [Table]
VaR 95%                Price Jump Analysis      Risk Summary
Current: 156.2         - Base price            - Zone
Target: <100           - Jump magnitude        - VaR 95%
Status: High Risk      - Final price           - Expected Shortfall
                       - Jump frequency        - Max Drawdown
```

---

## Dashboard 5: Temporal Patterns

### Layout: 4x3 Grid

**Row 1: Time-based KPIs**
```
[Card]              [Card]              [Card]              [Card]
Peak Hour Price     Off-Peak Price      Weekend Effect      Seasonal Range
127.3 EUR/MWh      45.8 EUR/MWh        -8.8 EUR/MWh       45.2 EUR/MWh
(17:00-20:00)      (23:00-06:00)       (Lower weekends)    (Winter-Summer)
```

**Row 2: Daily Patterns**
```
[Line Chart - Full Width]
Title: "Average Hourly Price Patterns by Zone"
- X-axis: Hour (0-23)
- Y-axis: Price (EUR/MWh)
- Multiple lines: One per zone
- Peak highlighting: Morning (6-9), Evening (17-20)
```

**Row 3: Calendar Analysis**
```
[Calendar Heatmap]         [Column Chart]          [Line Chart]
Daily Price Calendar       Seasonal Comparison     Weekend vs Weekday
- Dates as calendar        - X: Season             - X: Hour
- Color: Price level       - Y: Avg Price          - Y: Price
- Hover: Exact values      - Series: North/South   - Two lines: Wknd/Wkdy
- Year selector            - Error bars: StdDev    - Highlight differences
```

---

## Dashboard 6: Market Efficiency & Grid Analysis

### Layout: 3x4 Grid

**Row 1: Efficiency Metrics**
```
[Gauge]                 [KPI Card]              [KPI Card]
Market Efficiency       Grid Stress Level       Bottleneck Score
Score: 0.73            Medium Stress           2.3x
Target: >0.80          (50-100 EUR spread)     (vs historical median)
```

**Row 2: Grid Stress Analysis**
```
[Area Chart - Full Width]
Title: "Grid Stress Indicator Over Time"
- X-axis: Date
- Y-axis: Max Zone Spread (EUR/MWh)
- Areas: Normal (<20), Low Stress (20-50), Medium (50-100), High (>100)
- Line: Actual spread
```

**Row 3: Interconnector Impact**
```
[Scatter Plot]              [Bar Chart]             [Line Chart]
NO2 vs Other South         Interconnector Effect   Transmission Capacity
- X: NO1+NO5 Avg           - X: Zone               - X: Date
- Y: NO2 Price             - Y: Premium vs North   - Y: NS Difference
- Color: Time period       - Highlight NO2 stress  - Trend line
- Size: Volatility         - Reference line: 0     - Capacity improvements
```

**Row 4: Efficiency Trends**
```
[Combo Chart]              [Matrix]                [Funnel Chart]
Efficiency Over Time       Efficiency by Factors   Convergence Funnel
- Line: Efficiency score   Rows: Season, DayType   - All periods: 100%
- Bars: Price spread       Cols: Efficiency bins   - Low spread: 45%
- Secondary axis           Values: Count/Avg       - Convergent: 7.9%
- Trend analysis           Color coding            - Perfect: 0.8%
```

---

## Interactive Features & Drill-Through

### Cross-Dashboard Navigation
```
Dashboard 1 (Executive) → Dashboard 2 (Convergence) → Dashboard 3 (Zones)
     ↓                         ↓                         ↓
Dashboard 6 (Efficiency) ← Dashboard 5 (Temporal) ← Dashboard 4 (Spikes)
```

### Drill-Through Pages

**1. Zone Detail Page**
- Triggered from: Any zone visual
- Content: Detailed zone analysis, hourly patterns, comparison with neighbors
- Filters: Automatically set to selected zone

**2. Date Detail Page**
- Triggered from: Any date-based visual
- Content: Hourly breakdown, all zones, weather correlation (if available)
- Filters: Automatically set to selected date range

**3. Spike Investigation Page**
- Triggered from: Price spike visuals
- Content: Spike details, duration, affected zones, potential causes
- Filters: Automatically set to spike periods

### Bookmarks for Quick Views
1. **"Normal Operations"** - Filter to convergent periods only
2. **"Crisis Periods"** - Filter to extreme price events
3. **"Seasonal View"** - Group by seasons, show patterns
4. **"Zone Comparison"** - Side-by-side zone analysis
5. **"Recent Trends"** - Last 90 days detailed view

### Tooltip Pages
- **Zone Tooltip**: Mini-dashboard showing zone stats
- **Date Tooltip**: Daily summary with key metrics
- **Price Tooltip**: Price context with percentiles and trends

This comprehensive dashboard setup provides multiple perspectives on the Norwegian electricity market, enabling users to explore the data from executive summary level down to detailed operational insights.