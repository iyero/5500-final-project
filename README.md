# High Tide Ahead

**Flood Risk and Population Exposure on Oahu, Hawaii**

🌐 **[View the Project Website](https://iyero.github.io/5500-final-project/)**

---

## Overview

This project develops a composite flood risk model for Oahu, Hawaii, combining elevation data and proximity to inland waterways to identify flood-prone areas and estimate population exposure across approximately 887,000 residents.

## Key Findings (Oahu Only)

- **86,462 residents** (9.7%) live in high flood risk areas
- **142,190 residents** (16.0%) live in moderate flood risk areas
- **632,045 residents** (71.3%) live in low flood risk areas
- High-risk areas concentrate along the southern coastal plain and windward valley floors

## Repository Contents

```
├── script/                    # Analysis notebooks
│   ├── 01_data_preprocessing.ipynb
│   ├── 02_flood_risk_modeling.ipynb
│   ├── 03_population_exposure.ipynb
│   └── 04_visualization.ipynb
├── outputs/
│   ├── figures/               # Static visualizations
│   └── data/                  # Output spreadsheets (CSV)
│       ├── population_exposure.csv
│       ├── exposure_summary.csv
│       └── summary_statistics.json
├── docs/                      # Quarto website (GitHub Pages)
├── *.qmd                      # Quarto source files
├── _quarto.yml                # Quarto configuration
└── styles.css                 # Custom styling
```

## Data Note

**Raw and processed geospatial data are not included in this repository due to GitHub file size limits.** The DEM file alone exceeds 4 GB. However, all data is freely available and easily reproducible.

### Oahu vs. Honolulu County

Honolulu County includes the Northwestern Hawaiian Islands in addition to Oahu. The CSV files in `outputs/data/` contain data for **all of Honolulu County** (773 block groups, 979,682 residents). The visualizations and figures on the website are **subsetted to Oahu only** (703 block groups, 886,849 residents) to focus on the main populated island.

### Data Sources & Downloads

| Dataset | Source | Download |
|---------|--------|----------|
| Digital Elevation Model | USGS 3DEP | [National Map Downloader](https://apps.nationalmap.gov/downloader/) |
| Streams & Rivers | USGS NHD | [National Map Downloader](https://apps.nationalmap.gov/downloader/) |
| Coastline | USGS NHD | [National Map Downloader](https://apps.nationalmap.gov/downloader/) |
| Census Block Groups | Census TIGER/Line | [Census Bureau](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html) |
| Population Data | ACS 2020 5-Year | [Census API](https://www.census.gov/data/developers/data-sets/acs-5year.html) |

### Reproducing the Data

1. Download raw data from the sources above
2. Place files in `data/raw/`
3. Run `script/01_data_preprocessing.ipynb` to generate processed files
4. Run notebooks 02-04 in sequence

## Methodology

| Component | Description |
|-----------|-------------|
| **Elevation Risk (70%)** | High: <3m, Moderate: 3-8m, Low: >8m |
| **Proximity Risk (30%)** | High: <100m from waterway, Moderate: 100-500m, Low: >500m |
| **Resolution** | 10m grid cells |
| **Study Area** | Oahu (703 census block groups) |

## Output Spreadsheets

| File | Description |
|------|-------------|
| `population_exposure.csv` | Block group-level flood risk metrics and population exposure (all Honolulu County) |
| `exposure_summary.csv` | Aggregate statistics by risk category (all Honolulu County) |
| `summary_statistics.json` | Key findings in JSON format (all Honolulu County) |

## Author

**Oliver Iyer**  
Master of Public Administration in Quantitative Policy Analysis Candidate  
University of Pennsylvania, Fels Institute of Government

[LinkedIn](https://www.linkedin.com/in/oliver-iyer24/)

---

*MUSA 5500: Geospatial Data Science in Python | December 2025*
