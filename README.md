# High Tide Ahead

**Flood Risk and Population Exposure in Honolulu County, Hawaii**

🌐 **[View the Project Website](https://iyero.github.io/5500-final-project/)**

---

## Overview

This project develops a composite flood risk model for Oahu, Hawaii, combining elevation data and proximity to inland waterways to identify flood-prone areas and estimate population exposure across approximately 887,000 residents.

## Key Findings

- **86,462 residents** (9.7%) live in high flood risk areas
- **142,190 residents** (16.0%) live in moderate flood risk areas
- High-risk areas concentrate along the southern coastal plain and windward valley floors

## Repository Contents

```
├── script/                    # Analysis notebooks
│   ├── 01_data_preprocessing.ipynb
│   ├── 02_flood_risk_modeling.ipynb
│   ├── 03_population_exposure.ipynb
│   └── 04_visualization.ipynb
├── outputs/figures/           # Static visualizations
├── docs/                      # Quarto website (GitHub Pages)
├── *.qmd                      # Quarto source files
├── _quarto.yml                # Quarto configuration
└── styles.css                 # Custom styling
```

## Methodology

| Component | Description |
|-----------|-------------|
| **Elevation Risk (70%)** | High: <3m, Moderate: 3-8m, Low: >8m |
| **Proximity Risk (30%)** | High: <100m from waterway, Moderate: 100-500m, Low: >500m |
| **Resolution** | 10m grid cells |
| **Study Area** | Oahu, Honolulu County (703 census block groups) |

## Data Sources

- **Elevation:** USGS 3D Elevation Program (3DEP)
- **Hydrography:** USGS National Hydrography Dataset (NHD)
- **Demographics:** US Census Bureau TIGER/Line & ACS 2020 5-Year Estimates

## Author

**Oliver Iyer**  
Master of Public Administration in Quantitative Policy Analysis Candidate  
University of Pennsylvania, Fels Institute of Government

[LinkedIn](https://www.linkedin.com/in/oliver-iyer24/)

---

*MUSA 5500: Geospatial Data Science in Python | December 2025*
