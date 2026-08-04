# Global Luxury Hospitality — Enterprise Performance Analysis

A personal analytics project exploring how luxury hospitality 
portfolios can use data to drive enterprise performance decisions. 
Built to demonstrate end-to-end data analyst capabilities across 
Python, Power BI, and business intelligence.

---

## Project Overview

| Item | Detail |
|---|---|
| **Domain** | Luxury Hospitality |
| **Dataset** | ~689K hotel stay records (2022–2023) |
| **Tools** | Python, Power BI, DAX, Power Query M |
| **Libraries** | pandas, numpy, matplotlib |
| **Output** | Cleaned dataset, 12 aggregated CSVs, data quality log, 11 charts, Power BI dashboard |

---

## Business Problem

Design an enterprise performance reporting framework that answers different questions for different leadership audiences:

- **C-Suite** → Is the portfolio growing? Where is the rate going?
- **Regional VPs** → Which regions and subregions are driving or dragging performance?
- **General Managers** → How is my property performing and who are my guests?

---

## Project Structure

```
├── analysis.py              # Main Python analysis pipeline
├── README.md                # This file
├── requirements.txt         # Python dependencies
├── .gitignore               # Files to exclude from GitHub
│
├── data/                    # Raw input files (not included — see Data section)
│   ├── Stays.csv
│   ├── Ref_Hotel.csv
│   ├── Ref_Market.csv
│   └── Ref_Channel.csv
│
├── outputs/                 # Generated outputs
│   ├── data_quality_log.csv     # Governance log — 7 issues flagged
│   ├── agg_monthly.csv          # Monthly KPI summary
│   ├── agg_regional.csv         # Regional KPI summary
│   ├── agg_property.csv         # Property-level KPI summary
│   ├── agg_channel.csv          # Channel mix summary
│   └── agg_market_category.csv  # Market category summary
│
├── charts/                  # Generated matplotlib charts
│   ├── chart_kpi_scorecard.png
│   ├── chart_monthly_revenue.png
│   ├── chart_regional_revenue.png
│   ├── chart_adr_regional.png
│   ├── chart_market_mix.png
│   ├── chart_top10_properties.png
│   ├── chart_channel_adr.png
│   ├── chart_travel_purpose.png
│   ├── chart_guest_generation.png
│   ├── chart_property_type.png
│   └── chart_seasonality.png
│
└── dashboard_screenshots/   # Power BI dashboard screenshots
    ├── executive_summary.png
    ├── regional_insights.png
    └── property_overview.png
```

---

## How to Run

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/hospitality-performance-analysis.git
cd hospitality-performance-analysis
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Add raw data files
Place the following files in the `data/` folder:
- `Stays.csv` — hotel stay transaction records
- `Ref_Hotel.csv` — hotel reference table
- `Ref_Market.csv` — market segment reference table
- `Ref_Channel.csv` — booking channel reference table

> **Note:** Raw data files are not included in this repository as they contain proprietary hospitality data.

### 4. Run the analysis
```bash
python analysis.py
```

All outputs (cleaned CSV, aggregated tables, data quality log, charts) will be saved to the `outputs/` and `charts/` folders.

---

## Key Findings

| KPI | 2022 | 2023 | Change |
|---|---|---|---|
| Room Revenue | $1.69B | $1.89B | ▲ +12.0% |
| Total Revenue | $2.15B | $2.40B | ▲ +11.7% |
| Room Nights | 2.25M | 2.60M | ▲ +15.6% |
| ADR | $751 | $727 | ▼ -3.1% |

**Core Insight:** Revenue growth was volume-driven, not rate-driven. The portfolio filled 15.6% more rooms in 2023 but at a 3.1% lower average rate — signalling a pricing gap or mix shift that leadership needs to investigate.

### Regional Picture (2023)
- **Americas** — $987M | 52% of portfolio | ADR $895
- **EMEA** — $572M | 30% of portfolio | ADR $760
- **APAC** — $332M | 18% of portfolio | ADR $446

### Channel Opportunity
- Direct channels (Brand Website, Direct reservations channel) command **3× the ADR** of the Sales Office ($1,069 vs $380)
- Shifting existing bookings from indirect to direct channels is the single biggest rate optimization lever

---

## Data Quality

Of 689,300 raw rows, **80,718 were excluded (11.7%)** before any KPI was calculated.

| Severity | Issue | Rows |
|---|---|---|
| HIGH | Null Room Revenue | 19,255 |
| HIGH | Negative Revenue | 2,836 |
| HIGH | Zero Revenue (comp stays) | 53,431 |
| MEDIUM | Undocumented Status Code 'U' | 8 hotels |
| MEDIUM | Incomplete Hotel Reference | 3 hotels |
| MEDIUM | Null Guest Country | 38,513 |
| MEDIUM | Suspicious Market Codes | 14 codes |

> All quality issues were flagged **before** any KPI was computed — documented in `outputs/data_quality_log.csv`

---

## KPI Definitions

| KPI | Formula | Notes |
|---|---|---|
| **ADR** | Room Revenue ÷ Room Nights | Zero/negative revenue excluded from both |
| **TrevPOR** | Total Revenue ÷ Room Nights | Total Revenue Per Occupied Room |
| **Attach Rate** | Total Revenue ÷ Room Revenue | Multiplier — 1.27× means $1.27 total per $1 room |
| **ALOS** | Room Nights ÷ Stays Count | Average Length of Stay |
| **YoY%** | (Current - Prior) ÷ Prior × 100 | Active hotels only |

> **Note:** RevPAR and Occupancy Rate could not be calculated — total available room inventory was not present in the dataset.

---

## Power BI Dashboard

The dashboard has 3 audience-specific pages:

| Page | Audience | Key Visuals |
|---|---|---|
| Executive Summary | C-Suite | KPI cards, monthly trend, regional revenue, market mix |
| Regional Insights | Regional VPs | Subregion bar, ADR comparison, channel ADR, YoY matrix |
| Property Overview | General Managers | Top 10 properties, guest generation, travel purpose, room mix |

Screenshots available in `dashboard_screenshots/` folder.

> **Data Notice:** Data used in this project is anonymised hospitality stay data. All figures shown are aggregated KPIs — no individual guest or transaction data is included.

---

## Technologies Used

| Tool | Purpose |
|---|---|
| **Python / pandas** | Data ingestion, cleaning, merging, aggregation |
| **matplotlib** | Chart generation and validation |
| **Power BI Desktop** | Dashboard design and DAX measures |
| **Power Query M** | Calendar table creation |
| **DAX** | KPI measures — ADR, TrevPOR, YoY%, SAMEPERIODLASTYEAR |

---

## Author

**Maisha Khatoon**
Data Analyst | Python · Power BI · SQL · DAX


[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue)](https://linkedin.com/in/maisha-khatoon)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-black)](https://github.com/maishaverse)