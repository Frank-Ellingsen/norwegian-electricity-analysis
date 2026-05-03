# Power BI Transmission Bottleneck Analysis Dashboard

## Overview
This specialized dashboard analyzes transmission bottlenecks between Norwegian electricity zones and their impact on price convergence, featuring congestion heat maps, flow direction analysis, and capacity utilization metrics.

## Data Model Extensions

### Additional Calculated Columns for Transmission Analysis

```dax
// Transmission Corridor Classification
Transmission_Corridor = 
SWITCH(
    TRUE(),
    spot_prices_mwh_eur[zone] IN {"NO1", "NO2"}, "South-South",
    spot_prices_mwh_eur[zone] IN {"NO3", "NO4"}, "North-North", 
    spot_prices_mwh_eur[zone] IN {"NO1", "NO5"}, "East-West",
    "North-South"
)

// Price Gradient Indicator
Price_Gradient = 
VAR CurrentZone = spot_prices_mwh_eur[zone]
VAR CurrentPrice = spot_prices_mwh_eur[price_eur_per_mwh]
VAR AdjacentZones = 
    SWITCH(
        CurrentZone,
        "NO1", {"NO2", "NO5"},  // Oslo connects to South and West
        "NO2", {"NO1", "NO5"},  // South connects to East and West
        "NO3", {"NO4", "NO1"},  // Central connects to North and East
        "NO4", {"NO3"},         // North connects to Central
        "NO5", {"NO1", "NO2"},  // West connects to East and South
        {}
    )
RETURN
    "Calculated in measures"

// Congestion Risk Level
Congestion_Risk = 
VAR ZonePriceSpread = 
    CALCULATE(
        MAX(spot_prices_mwh_eur[price_eur_per_mwh]) - MIN(spot_prices_mwh_eur[price_eur_per_mwh]),
        ALLEXCEPT(spot_prices_mwh_eur, spot_prices_mwh_eur[timestamp_utc])
    )
RETURN
    SWITCH(
        TRUE(),
        ZonePriceSpread > 100, "Severe Congestion",
        ZonePriceSpread > 50, "High Congestion",
        ZonePriceSpread > 20, "Moderate Congestion",
        ZonePriceSpread > 5, "Low Congestion",
        "No Congestion"
    )
```

## Advanced DAX Measures for Transmission Analysis

### 1. Congestion Detection Measures

```dax
// Transmission Bottleneck Severity
Bottleneck_Severity = 
VAR MaxZonePrice = 
    CALCULATE(
        MAX(spot_prices_mwh_eur[price_eur_per_mwh]),
        ALLEXCEPT(spot_prices_mwh_eur, spot_prices_mwh_eur[timestamp_utc])
    )
VAR MinZonePrice = 
    CALCULATE(
        MIN(spot_prices_mwh_eur[price_eur_per_mwh]),
        ALLEXCEPT(spot_prices_mwh_eur, spot_prices_mwh_eur[timestamp_utc])
    )
VAR PriceSpread = MaxZonePrice - MinZonePrice
VAR AvgPrice = 
    CALCULATE(
        AVERAGE(spot_prices_mwh_eur[price_eur_per_mwh]),
        ALLEXCEPT(spot_prices_mwh_eur, spot_prices_mwh_eur[timestamp_utc])
    )
RETURN
    DIVIDE(PriceSpread, AvgPrice, 0) * 100

// Congestion Duration (Hours per Day)
Daily_Congestion_Hours = 
VAR CongestionThreshold = 20 // EUR/MWh spread threshold
VAR DailyHours = 
    CALCULATE(
        SUMX(
            VALUES(spot_prices_mwh_eur[Hour]),
            VAR HourlySpread = 
                CALCULATE(
                    MAX(spot_prices_mwh_eur[price_eur_per_mwh]) - MIN(spot_prices_mwh_eur[price_eur_per_mwh])
                )
            RETURN
                IF(HourlySpread > CongestionThreshold, 1, 0)
        )
    )
RETURN
    DailyHours

// Congestion Frequency (% of Time)
Congestion_Frequency = 
VAR TotalHours = 24
VAR CongestedHours = [Daily_Congestion_Hours]
RETURN
    DIVIDE(CongestedHours, TotalHours, 0) * 100
```

### 2. Flow Direction Analysis

```dax
// Implied Power Flow Direction (North to South)
NS_Flow_Direction = 
VAR NorthPrice = 
    CALCULATE(
        AVERAGE(spot_prices_mwh_eur[price_eur_per_mwh]),
        spot_prices_mwh_eur[Region_Group] = "North"
    )
VAR SouthPrice = 
    CALCULATE(
        AVERAGE(spot_prices_mwh_eur[price_eur_per_mwh]),
        spot_prices_mwh_eur[Region_Group] = "South"
    )
RETURN
    SWITCH(
        TRUE(),
        SouthPrice > NorthPrice + 5, "Strong North→South",
        SouthPrice > NorthPrice, "North→South",
        NorthPrice > SouthPrice + 5, "Strong South→North",
        NorthPrice > SouthPrice, "South→North",
        "Balanced"
    )

// Flow Intensity Score
Flow_Intensity = 
VAR PriceDiff = [NS_Price_Difference]
VAR MaxHistoricalDiff = 
    CALCULATE(
        MAX([NS_Abs_Difference]),
        ALL(spot_prices_mwh_eur)
    )
RETURN
    DIVIDE(ABS(PriceDiff), MaxHistoricalDiff, 0) * 100

// Corridor Utilization Proxy
Corridor_Utilization = 
VAR CurrentSpread = [NS_Abs_Difference]
VAR HistoricalMax = 
    CALCULATE(
        PERCENTILE.INC([NS_Abs_Difference], 0.95),
        ALL(spot_prices_mwh_eur)
    )
RETURN
    DIVIDE(CurrentSpread, HistoricalMax, 0) * 100
```

### 3. Capacity Constraint Analysis

```dax
// Transmission Capacity Stress
Capacity_Stress_Level = 
VAR CurrentUtilization = [Corridor_Utilization]
RETURN
    SWITCH(
        TRUE(),
        CurrentUtilization > 90, "Critical",
        CurrentUtilization > 75, "High Stress",
        CurrentUtilization > 50, "Moderate Stress",
        CurrentUtilization > 25, "Low Stress",
        "Normal"
    )

// Bottleneck Impact on Convergence
Bottleneck_Impact = 
VAR HighCongestionDays = 
    CALCULATE(
        COUNTROWS(VALUES(spot_prices_mwh_eur[Date])),
        [Bottleneck_Severity] > 20
    )
VAR HighCongestionConvergence = 
    CALCULATE(
        [Convergence_Rate],
        [Bottleneck_Severity] > 20
    )
VAR LowCongestionConvergence = 
    CALCULATE(
        [Convergence_Rate],
        [Bottleneck_Severity] <= 20
    )
RETURN
    LowCongestionConvergence - HighCongestionConvergence

// Grid Efficiency Score
Grid_Efficiency = 
VAR AvgBottleneckSeverity = 
    CALCULATE(
        AVERAGE([Bottleneck_Severity]),
        ALL(spot_prices_mwh_eur)
    )
VAR CurrentSeverity = [Bottleneck_Severity]
RETURN
    MAX(0, 100 - CurrentSeverity)
```

### 4. Temporal Congestion Patterns

```dax
// Peak Congestion Hours
Peak_Congestion_Hours = 
CONCATENATEX(
    TOPN(
        3,
        SUMMARIZE(
            spot_prices_mwh_eur,
            spot_prices_mwh_eur[Hour],
            "AvgSeverity", AVERAGE([Bottleneck_Severity])
        ),
        [AvgSeverity],
        DESC
    ),
    spot_prices_mwh_eur[Hour] & ":00",
    ", "
)

// Seasonal Congestion Pattern
Seasonal_Congestion_Index = 
VAR CurrentSeason = MAX(spot_prices_mwh_eur[Season])
VAR SeasonalAvgSeverity = 
    CALCULATE(
        AVERAGE([Bottleneck_Severity]),
        spot_prices_mwh_eur[Season] = CurrentSeason,
        ALL(spot_prices_mwh_eur[Date])
    )
VAR OverallAvgSeverity = 
    CALCULATE(
        AVERAGE([Bottleneck_Severity]),
        ALL(spot_prices_mwh_eur)
    )
RETURN
    DIVIDE(SeasonalAvgSeverity, OverallAvgSeverity, 1)

// Weekend Congestion Relief
Weekend_Relief_Factor = 
VAR WeekendSeverity = 
    CALCULATE(
        AVERAGE([Bottleneck_Severity]),
        spot_prices_mwh_eur[IsWeekend] = TRUE
    )
VAR WeekdaySeverity = 
    CALCULATE(
        AVERAGE([Bottleneck_Severity]),
        spot_prices_mwh_eur[IsWeekend] = FALSE
    )
RETURN
    DIVIDE(WeekdaySeverity - WeekendSeverity, WeekdaySeverity, 0) * 100
```

### 5. Zone-Specific Transmission Measures

```dax
// Zone Isolation Index
Zone_Isolation_Index = 
VAR CurrentZone = MAX(spot_prices_mwh_eur[zone])
VAR ZonePrice = 
    CALCULATE(
        AVERAGE(spot_prices_mwh_eur[price_eur_per_mwh]),
        spot_prices_mwh_eur[zone] = CurrentZone
    )
VAR OtherZonesAvg = 
    CALCULATE(
        AVERAGE(spot_prices_mwh_eur[price_eur_per_mwh]),
        spot_prices_mwh_eur[zone] <> CurrentZone
    )
RETURN
    ABS(ZonePrice - OtherZonesAvg)

// Interconnection Strength
Interconnection_Strength = 
VAR ZoneIsolation = [Zone_Isolation_Index]
VAR MaxIsolation = 
    CALCULATE(
        MAX([Zone_Isolation_Index]),
        ALL(spot_prices_mwh_eur[zone])
    )
RETURN
    100 - DIVIDE(ZoneIsolation, MaxIsolation, 0) * 100

// Critical Path Indicator
Critical_Path_Zone = 
VAR CurrentZone = MAX(spot_prices_mwh_eur[zone])
VAR ZoneBottleneckFreq = 
    CALCULATE(
        AVERAGE(IF([Bottleneck_Severity] > 30, 1, 0)),
        spot_prices_mwh_eur[zone] = CurrentZone
    )
RETURN
    IF(ZoneBottleneckFreq > 0.3, "Critical Path", "Normal")
```