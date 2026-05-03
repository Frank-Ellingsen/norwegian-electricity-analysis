# Power BI Setup Guide: Norwegian Electricity Price Analysis

## Data Structure Overview
Your CSV contains the following columns:
- `zone` (NO1, NO2, NO3, NO4, NO5)
- `timestamp_utc` (hourly data from 2021-2026)
- `price_eur_per_mwh` (spot prices)
- `zone_code`, `zone_name`, `country`, `region`, `description`
- `Mapped_City`, `Latitude`, `Longitude`

## 1. DATA MODEL SETUP

### Step 1: Import and Transform Data

**Power Query Transformations:**
```m
// 1. Convert timestamp to proper datetime
= Table.TransformColumnTypes(Source,{{"timestamp_utc", type datetimezone}})

// 2. Add date/time columns
= Table.AddColumn(#"Changed Type", "Date", each Date.From([timestamp_utc]))
= Table.AddColumn(#"Added Date", "Year", each Date.Year([Date]))
= Table.AddColumn(#"Added Year", "Month", each Date.Month([Date]))
= Table.AddColumn(#"Added Month", "Hour", each Time.Hour([timestamp_utc]))
= Table.AddColumn(#"Added Hour", "Weekday", each Date.DayOfWeek([Date]))
= Table.AddColumn(#"Added Weekday", "IsWeekend", each [Weekday] >= 5)

// 3. Add regional grouping
= Table.AddColumn(#"Added IsWeekend", "Region_Group", 
    each if List.Contains({"NO3", "NO4"}, [zone]) then "North" else "South")

// 4. Add season column
= Table.AddColumn(#"Added Region_Group", "Season", 
    each if List.Contains({12, 1, 2}, [Month]) then "Winter"
    else if List.Contains({3, 4, 5}, [Month]) then "Spring"
    else if List.Contains({6, 7, 8}, [Month]) then "Summer"
    else "Autumn")
```

### Step 2: Create Date Table

Create a separate date table for better time intelligence:

```m
let
    StartDate = #date(2021, 1, 1),
    EndDate = #date(2026, 12, 31),
    DateList = List.Dates(StartDate, Duration.Days(EndDate - StartDate) + 1, #duration(1, 0, 0, 0)),
    #"Converted to Table" = Table.FromList(DateList, Splitter.SplitByNothing(), {"Date"}),
    #"Added Year" = Table.AddColumn(#"Converted to Table", "Year", each Date.Year([Date])),
    #"Added Month" = Table.AddColumn(#"Added Year", "Month", each Date.Month([Date])),
    #"Added Month Name" = Table.AddColumn(#"Added Month", "Month Name", each Date.MonthName([Date])),
    #"Added Quarter" = Table.AddColumn(#"Added Month Name", "Quarter", each Date.QuarterOfYear([Date])),
    #"Added Weekday" = Table.AddColumn(#"Added Quarter", "Weekday", each Date.DayOfWeek([Date])),
    #"Added IsWeekend" = Table.AddColumn(#"Added Weekday", "IsWeekend", each [Weekday] >= 5),
    #"Added Season" = Table.AddColumn(#"Added IsWeekend", "Season", 
        each if List.Contains({12, 1, 2}, [Month]) then "Winter"
        else if List.Contains({3, 4, 5}, [Month]) then "Spring"
        else if List.Contains({6, 7, 8}, [Month]) then "Summer"
        else "Autumn")
in
    #"Added Season"
```

### Step 3: Create Zone Lookup Table

```m
let
    Source = Table.FromRows({
        {"NO1", "Eastern (Oslo)", "South", "Oslo", 59.9127, 10.7461},
        {"NO2", "Southern (Kristiansand)", "South", "Kristiansand", 58.1467, 7.9956},
        {"NO3", "Central (Trondheim)", "North", "Trondheim", 63.4305, 10.3951},
        {"NO4", "Northern (Tromsø)", "North", "Tromsø", 69.6492, 18.9553},
        {"NO5", "Western (Bergen)", "South", "Bergen", 60.3913, 5.3221}
    }, {"zone_code", "zone_name", "region_group", "city", "latitude", "longitude"})
in
    Source
```

### Step 4: Establish Relationships

1. **Fact Table**: `spot_prices_mwh_eur` (main data)
2. **Date Table**: Related via `Date` field (one-to-many)
3. **Zone Table**: Related via `zone` field (many-to-one)

## 2. CALCULATED COLUMNS

Add these calculated columns to your main fact table:

### Time-based Columns
```dax
// Time Period Classification
Time_Period = 
SWITCH(
    TRUE(),
    spot_prices_mwh_eur[Hour] >= 6 && spot_prices_mwh_eur[Hour] <= 9, "Morning Peak",
    spot_prices_mwh_eur[Hour] >= 17 && spot_prices_mwh_eur[Hour] <= 20, "Evening Peak",
    spot_prices_mwh_eur[Hour] >= 22 || spot_prices_mwh_eur[Hour] <= 5, "Night",
    "Off-Peak"
)

// Day Type
Day_Type = 
IF(
    spot_prices_mwh_eur[IsWeekend],
    "Weekend",
    "Weekday"
)
```

### Price Classification Columns
```dax
// Price Level Category
Price_Category = 
SWITCH(
    TRUE(),
    spot_prices_mwh_eur[price_eur_per_mwh] < 0, "Negative",
    spot_prices_mwh_eur[price_eur_per_mwh] <= 50, "Low",
    spot_prices_mwh_eur[price_eur_per_mwh] <= 100, "Medium",
    spot_prices_mwh_eur[price_eur_per_mwh] <= 200, "High",
    "Extreme"
)

// Price Spike Indicator
Is_Price_Spike = spot_prices_mwh_eur[price_eur_per_mwh] > 200
```

## 3. KEY DAX MEASURES

### Basic Price Measures
```dax
// Average Price
Avg_Price = AVERAGE(spot_prices_mwh_eur[price_eur_per_mwh])

// Median Price
Median_Price = MEDIAN(spot_prices_mwh_eur[price_eur_per_mwh])

// Price Volatility (Standard Deviation)
Price_Volatility = STDEV.P(spot_prices_mwh_eur[price_eur_per_mwh])

// Min/Max Prices
Min_Price = MIN(spot_prices_mwh_eur[price_eur_per_mwh])
Max_Price = MAX(spot_prices_mwh_eur[price_eur_per_mwh])
```

### Regional Analysis Measures
```dax
// North Average Price
North_Avg_Price = 
CALCULATE(
    [Avg_Price],
    spot_prices_mwh_eur[Region_Group] = "North"
)

// South Average Price
South_Avg_Price = 
CALCULATE(
    [Avg_Price],
    spot_prices_mwh_eur[Region_Group] = "South"
)

// North-South Price Difference
NS_Price_Difference = [South_Avg_Price] - [North_Avg_Price]

// Absolute North-South Difference
NS_Abs_Difference = ABS([NS_Price_Difference])

// North-South Price Ratio
NS_Price_Ratio = 
DIVIDE(
    [South_Avg_Price],
    [North_Avg_Price],
    BLANK()
)
```

### Convergence Analysis Measures
```dax
// Price Convergence Indicator (difference < 5 EUR/MWh)
Is_Convergent = [NS_Abs_Difference] < 5

// Convergence Rate (% of time periods with convergence)
Convergence_Rate = 
VAR ConvergentPeriods = 
    SUMX(
        VALUES(spot_prices_mwh_eur[Date]),
        IF(
            CALCULATE([NS_Abs_Difference]) < 5,
            1,
            0
        )
    )
VAR TotalPeriods = DISTINCTCOUNT(spot_prices_mwh_eur[Date])
RETURN
    DIVIDE(ConvergentPeriods, TotalPeriods, 0) * 100

// Daily Price Convergence
Daily_Convergence = 
CALCULATE(
    IF([NS_Abs_Difference] < 5, "Convergent", "Divergent"),
    VALUES(spot_prices_mwh_eur[Date])
)
```

### Zone-Specific Measures
```dax
// Individual Zone Prices
NO1_Price = CALCULATE([Avg_Price], spot_prices_mwh_eur[zone] = "NO1")
NO2_Price = CALCULATE([Avg_Price], spot_prices_mwh_eur[zone] = "NO2")
NO3_Price = CALCULATE([Avg_Price], spot_prices_mwh_eur[zone] = "NO3")
NO4_Price = CALCULATE([Avg_Price], spot_prices_mwh_eur[zone] = "NO4")
NO5_Price = CALCULATE([Avg_Price], spot_prices_mwh_eur[zone] = "NO5")

// Zone with Highest Price
Highest_Price_Zone = 
VAR MaxPrice = 
    MAXX(
        VALUES(spot_prices_mwh_eur[zone]),
        CALCULATE([Avg_Price])
    )
RETURN
    MAXX(
        FILTER(
            VALUES(spot_prices_mwh_eur[zone]),
            CALCULATE([Avg_Price]) = MaxPrice
        ),
        spot_prices_mwh_eur[zone]
    )
```

### Time Intelligence Measures
```dax
// Previous Period Comparison
Price_vs_Previous_Month = 
VAR CurrentPrice = [Avg_Price]
VAR PreviousPrice = 
    CALCULATE(
        [Avg_Price],
        DATEADD('Date'[Date], -1, MONTH)
    )
RETURN
    CurrentPrice - PreviousPrice

// Year-over-Year Change
Price_YoY_Change = 
VAR CurrentPrice = [Avg_Price]
VAR PreviousYearPrice = 
    CALCULATE(
        [Avg_Price],
        SAMEPERIODLASTYEAR('Date'[Date])
    )
RETURN
    DIVIDE(CurrentPrice - PreviousYearPrice, PreviousYearPrice, 0) * 100

// Moving Average (30-day)
Price_30Day_MA = 
CALCULATE(
    [Avg_Price],
    DATESINPERIOD(
        'Date'[Date],
        MAX('Date'[Date]),
        -30,
        DAY
    )
)
```

### Advanced Analytics Measures
```dax
// Price Spike Count
Price_Spike_Count = 
SUMX(
    spot_prices_mwh_eur,
    IF(spot_prices_mwh_eur[price_eur_per_mwh] > 200, 1, 0)
)

// Negative Price Hours
Negative_Price_Hours = 
SUMX(
    spot_prices_mwh_eur,
    IF(spot_prices_mwh_eur[price_eur_per_mwh] < 0, 1, 0)
)

// Price Range (Max - Min)
Price_Range = [Max_Price] - [Min_Price]

// Coefficient of Variation (Volatility relative to mean)
Price_CV = 
DIVIDE(
    [Price_Volatility],
    [Avg_Price],
    BLANK()
) * 100

// Seasonal Price Premium
Seasonal_Premium = 
VAR WinterPrice = 
    CALCULATE(
        [Avg_Price],
        spot_prices_mwh_eur[Season] = "Winter"
    )
VAR SummerPrice = 
    CALCULATE(
        [Avg_Price],
        spot_prices_mwh_eur[Season] = "Summer"
    )
RETURN
    WinterPrice - SummerPrice
```

### Ranking and Percentile Measures
```dax
// Zone Price Ranking
Zone_Price_Rank = 
RANKX(
    ALL(spot_prices_mwh_eur[zone]),
    [Avg_Price],
    ,
    DESC
)

// Price Percentile
Price_Percentile = 
PERCENTRANK.INC(
    ALL(spot_prices_mwh_eur[price_eur_per_mwh]),
    [Avg_Price]
) * 100

// Top 10% Price Threshold
Top_10_Percent_Threshold = 
PERCENTILE.INC(
    spot_prices_mwh_eur[price_eur_per_mwh],
    0.9
)
```

## 4. RECOMMENDED VISUALIZATIONS

### Dashboard 1: Overview
1. **KPI Cards**: North Avg Price, South Avg Price, NS Difference, Convergence Rate
2. **Line Chart**: Daily North vs South prices over time
3. **Area Chart**: Price difference over time with convergence threshold
4. **Map Visual**: Average prices by zone with geographic coordinates

### Dashboard 2: Convergence Analysis
1. **Scatter Plot**: North vs South daily prices (convergence = diagonal line)
2. **Heatmap**: Convergence rate by month and year
3. **Bar Chart**: Convergence rate by season and day type
4. **Histogram**: Distribution of price differences

### Dashboard 3: Zone Comparison
1. **Box Plot**: Price distribution by zone
2. **Line Chart**: All 5 zones price trends
3. **Matrix**: Zone statistics (avg, min, max, volatility)
4. **Waterfall Chart**: Price differences between consecutive zones

### Dashboard 4: Time Patterns
1. **Heatmap**: Average prices by hour and day of week
2. **Line Chart**: Seasonal price patterns
3. **Column Chart**: Price spikes by month
4. **Gauge**: Current vs historical price levels

## 5. FILTERS AND SLICERS

### Recommended Slicers:
- **Date Range Slicer**: For time period selection
- **Zone Multi-Select**: For zone comparison
- **Season Slicer**: For seasonal analysis
- **Day Type**: Weekend vs Weekday
- **Price Category**: Low/Medium/High/Extreme
- **Convergence Status**: Convergent vs Divergent periods

### Filter Hierarchy:
1. Year → Quarter → Month → Date
2. Region Group → Zone → City
3. Season → Month → Day Type

## 6. PERFORMANCE OPTIMIZATION

### Aggregation Tables:
Create aggregated tables for better performance:

```dax
// Daily Aggregation Table
Daily_Prices = 
SUMMARIZE(
    spot_prices_mwh_eur,
    spot_prices_mwh_eur[Date],
    spot_prices_mwh_eur[zone],
    "Avg_Price", AVERAGE(spot_prices_mwh_eur[price_eur_per_mwh]),
    "Min_Price", MIN(spot_prices_mwh_eur[price_eur_per_mwh]),
    "Max_Price", MAX(spot_prices_mwh_eur[price_eur_per_mwh]),
    "Price_Volatility", STDEV.P(spot_prices_mwh_eur[price_eur_per_mwh])
)

// Monthly Aggregation Table
Monthly_Prices = 
SUMMARIZE(
    spot_prices_mwh_eur,
    spot_prices_mwh_eur[Year],
    spot_prices_mwh_eur[Month],
    spot_prices_mwh_eur[zone],
    "Avg_Price", AVERAGE(spot_prices_mwh_eur[price_eur_per_mwh]),
    "Price_Volatility", STDEV.P(spot_prices_mwh_eur[price_eur_per_mwh]),
    "Spike_Count", SUMX(spot_prices_mwh_eur, IF(spot_prices_mwh_eur[price_eur_per_mwh] > 200, 1, 0))
)
```

This comprehensive setup will allow you to recreate all the insights from our Python analysis in Power BI, with interactive dashboards for exploring the Norwegian electricity market's North-South price divide and convergence patterns.