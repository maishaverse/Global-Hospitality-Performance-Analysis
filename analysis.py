"""
Global Luxury Hospitality — Enterprise Performance Analysis
Portfolio Project | Data Analyst

Author: Maisha Khatoon
Tools: Python (pandas, matplotlib), Power BI
Description:
    End-to-end hospitality analytics pipeline — data ingestion, quality audit,
    KPI calculation across 12 dimensions, and chart generation.
    Processes ~689K rows of hotel stay data across 2022-2023.
"""

# HOW TO READ THIS SCRIPT
#
# This script runs in 20 sections in sequence:
#   1.  Load raw data (4 CSV files)
#   2.  Data quality audit — run BEFORE any cleaning
#   3.  Merge reference tables + filter clean rows
#   4.  Reusable KPI aggregation function
#   5-17. Aggregate by 12 dimensions (year, region, channel etc.)
#   18. Export clean CSVs and data quality log
#   19. Export data quality log
#   20. Generate 11 matplotlib charts
#
# Key design decisions:
#   - Left joins used (not inner) to preserve all rows visibly
#   - Zero and negative revenue excluded BEFORE KPI calculation
#   - kpi_agg() function defined once, applied across all dimensions
#   - ADR calculated at aggregated level (weighted), not averaged

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import warnings
warnings.filterwarnings('ignore')


# 0. PATHS
DATA_DIR = 'data/'       # Place raw input files (Stays.csv, Ref_Hotel.csv etc.) here
OUTPUT_DIR = 'outputs/'  # Cleaned CSVs and data quality log saved here
CHARTS_DIR = 'charts/'   # All matplotlib charts saved here


# 1. LOAD RAW DATA
stays   = pd.read_csv(DATA_DIR + 'Stays.csv')
hotels  = pd.read_csv(DATA_DIR + 'Ref_Hotel.csv')
markets = pd.read_csv(DATA_DIR + 'Ref_Market.csv')
channels= pd.read_csv(DATA_DIR + 'Ref_Channel.csv')

print(f"Stays loaded: {stays.shape}")

# 2. DATA QUALITY FLAGS (BEFORE CLEANING)
dq = {}

# 2a. Nulls
dq['null_market_code']    = stays['market_code'].isnull().sum()
dq['null_source_code']    = stays['source_code'].isnull().sum()
dq['null_guest_country']  = stays['guest_country'].isnull().sum()
dq['null_guest_gen']      = stays['guest_generation'].isnull().sum()
dq['null_room_revenue']   = stays['Room_revenue'].isnull().sum()
dq['null_total_revenue']  = stays['Total_revenue'].isnull().sum()
dq['null_room_nights']    = stays['Room_nights'].isnull().sum()

# 2b. Negative revenues
dq['negative_room_rev']   = (stays['Room_revenue'] < 0).sum()
dq['negative_total_rev']  = (stays['Total_revenue'] < 0).sum()

# 2c. Zero revenue rows (possible comps / data issues)
dq['zero_room_rev']       = (stays['Room_revenue'] == 0).sum()

# 2d. Suspicious market codes in reference
bad_market_codes = ['.', '?', '{NULL}', '0', '-100', 'FIXME', 'UNKNOWN', 'NON', 'FUN', 'FUNC', 'FUNS', 'OLD', 'A/R', 'AR']
dq['bad_market_codes_in_ref'] = len(bad_market_codes)

# 2e. Incomplete hotel reference rows
dq['hotel_ref_missing_name']   = hotels['Hotel_short_nm'].isnull().sum()
dq['hotel_ref_missing_status'] = hotels['Status_cd'].isnull().sum()
dq['hotel_ref_missing_type']   = hotels['Property_type_cd'].isnull().sum()

# 2f. Orphan keys — stays referencing hotels not in ref
stays_hotels = set(stays['property_id'].unique())
ref_hotels   = set(hotels['Hotel_cd'].unique())
dq['stays_properties_not_in_ref'] = len(stays_hotels - ref_hotels)
dq['stays_properties_not_in_ref_list'] = list(stays_hotels - ref_hotels)

# 2g. Inactive hotels with stays
inactive_hotels = hotels[hotels['Status_cd'] == 'I']['Hotel_cd'].tolist()
dq['inactive_hotels_with_stays'] = stays[stays['property_id'].isin(inactive_hotels)]['property_id'].nunique()
dq['room_nights_from_inactive']  = stays[stays['property_id'].isin(inactive_hotels)]['Room_nights'].sum()

print("\n=== DATA QUALITY SUMMARY ===")
for k, v in dq.items():
    if k != 'stays_properties_not_in_ref_list':
        print(f"  {k}: {v:,}" if isinstance(v, (int, float)) else f"  {k}: {v}")


# 3. CLEANING / ENRICHMENT

# 3a. Merge reference tables
df = stays.merge(hotels, left_on='property_id', right_on='Hotel_cd', how='left')
df = df.merge(markets, left_on='market_code', right_on='market_cd', how='left')
df = df.merge(channels, left_on='source_code', right_on='minor_source_cd', how='left')

# 3b. Flag and exclude zero/negative revenue rows for KPI calc
# Keep original for data quality reporting; create clean version for KPIs
df_clean = df[
    (df['Room_revenue'] > 0) &
    (df['Total_revenue'] > 0) &
    (df['Room_nights'] > 0) &
    (df['Status_cd'] == 'A')   # active hotels only
].copy()

print(f"\nClean dataset (positive rev, active hotels): {df_clean.shape}")
print(f"Rows excluded: {len(df) - len(df_clean):,}")

# 3c. Date fields
df_clean['year_month'] = pd.to_datetime(
    df_clean['stay_year'].astype(str) + '-' + df_clean['stay_month'].astype(str).str.zfill(2) + '-01'
)

# 3d. ADR at record level (used for weighted aggregation)
df_clean['ADR_record'] = df_clean['Room_revenue'] / df_clean['Room_nights']


# 4. KPI AGGREGATION FUNCTIONS


def kpi_agg(grp):
    """Aggregate stays/nights/revenue and compute KPIs."""
    agg = grp.agg(
        stays_count  = ('stays', 'sum'),
        room_nights  = ('Room_nights', 'sum'),
        room_revenue = ('Room_revenue', 'sum'),
        total_revenue= ('Total_revenue', 'sum'),
    ).reset_index()
    agg['ADR']            = agg['room_revenue'] / agg['room_nights']
    agg['revenue_per_stay']= agg['room_revenue'] / agg['stays_count']
    agg['TrevPOR']        = agg['total_revenue'] / agg['room_nights']   # Total Rev per Occ Room
    agg['attach_rate']    = agg['total_revenue'] / agg['room_revenue']  # Total / Room revenue ratio
    return agg


# 5. ANNUAL SUMMARY (YoY)

annual = kpi_agg(df_clean.groupby('stay_year'))
annual_pivot = annual.set_index('stay_year')

yoy = {}
for col in ['stays_count','room_nights','room_revenue','total_revenue','ADR']:
    try:
        yoy[col] = (annual_pivot.loc[2023, col] - annual_pivot.loc[2022, col]) / annual_pivot.loc[2022, col] * 100
    except:
        yoy[col] = np.nan

print("\n=== ANNUAL KPIs ===")
print(annual[['stay_year','stays_count','room_nights','room_revenue','total_revenue','ADR']].to_string(index=False))
print("\nYoY Growth %:")
for k, v in yoy.items():
    print(f"  {k}: {v:.1f}%")

# 6. MONTHLY TREND

monthly = kpi_agg(df_clean.groupby(['stay_year','stay_month','year_month']))
monthly = monthly.sort_values('year_month')


# 7. REGIONAL ANALYSIS

regional = kpi_agg(df_clean.groupby(['stay_year','Hotel_region']))
regional_22 = regional[regional['stay_year']==2022].set_index('Hotel_region')
regional_23 = regional[regional['stay_year']==2023].set_index('Hotel_region')

print("\n=== REGIONAL KPIs 2023 ===")
print(regional_23[['room_revenue','room_nights','ADR','total_revenue']].sort_values('room_revenue', ascending=False).to_string())


# 8. SUBREGION ANALYSIS

subregion = kpi_agg(df_clean.groupby(['stay_year','Hotel_region','Hotel_subregion']))


# 9. PROPERTY TYPE (Urban vs Resort)

prop_type = kpi_agg(df_clean.groupby(['stay_year','Property_type_cd']))
print("\n=== PROPERTY TYPE KPIs ===")
print(prop_type.to_string(index=False))


# 10. MARKET CATEGORY MIX

market_cat = kpi_agg(df_clean.groupby(['stay_year','major_market_cat']))
market_cat_23 = market_cat[market_cat['stay_year']==2023].sort_values('room_revenue', ascending=False)
print("\n=== MARKET CATEGORY 2023 ===")
print(market_cat_23[['major_market_cat','room_revenue','room_nights','ADR']].to_string(index=False))


# 11. CHANNEL MIX

channel_mix = kpi_agg(df_clean.groupby(['stay_year','major_source_nm']))
channel_23 = channel_mix[channel_mix['stay_year']==2023].sort_values('room_revenue', ascending=False).head(10)
print("\n=== TOP CHANNELS 2023 ===")
print(channel_23[['major_source_nm','room_revenue','room_nights','ADR']].to_string(index=False))

# Minor channel (more granular)
minor_channel = kpi_agg(df_clean.groupby(['stay_year','minor_channel_nm']))


# 12. TRAVEL PURPOSE

purpose = kpi_agg(df_clean.groupby(['stay_year','travel_purpose']))
purpose_23 = purpose[purpose['stay_year']==2023].sort_values('room_revenue', ascending=False)


# 13. GUEST GENERATION

gen_mix = kpi_agg(df_clean.groupby(['stay_year','guest_generation']))
gen_23 = gen_mix[gen_mix['stay_year']==2023].sort_values('room_revenue', ascending=False)


# 14. ROOM CATEGORY

room_cat = kpi_agg(df_clean.groupby(['stay_year','room_category_booked']))
room_cat_23 = room_cat[room_cat['stay_year']==2023].sort_values('room_revenue', ascending=False)


# 15. TOP PROPERTIES

prop_perf = kpi_agg(df_clean.groupby(['stay_year','property_id','Hotel_short_nm','Hotel_region']))
prop_23 = prop_perf[prop_perf['stay_year']==2023].sort_values('room_revenue', ascending=False)
print("\n=== TOP 10 PROPERTIES 2023 by Room Revenue ===")
print(prop_23[['Hotel_short_nm','Hotel_region','room_revenue','room_nights','ADR']].head(10).to_string(index=False))


# 16. SEASONALITY — monthly index (2023)

monthly_23 = monthly[monthly['stay_year']==2023].copy()
mean_rev = monthly_23['room_revenue'].mean()
monthly_23['seasonality_index'] = monthly_23['room_revenue'] / mean_rev * 100

# 17. BUSINESS UNIT MIX
biz_unit = kpi_agg(df_clean.groupby(['stay_year','business_unit_nm']))
print("\n=== BUSINESS UNIT MIX ===")
print(biz_unit.to_string(index=False))


# 18. EXPORT CLEAN DATA FOR POWER BI
# Full enriched clean dataset
df_clean.to_csv(OUTPUT_DIR + 'stays_clean_enriched.csv', index=False)

# Pre-aggregated tables
monthly.to_csv(OUTPUT_DIR + 'agg_monthly.csv', index=False)
regional.to_csv(OUTPUT_DIR + 'agg_regional.csv', index=False)
subregion.to_csv(OUTPUT_DIR + 'agg_subregion.csv', index=False)
prop_type.to_csv(OUTPUT_DIR + 'agg_property_type.csv', index=False)
market_cat.to_csv(OUTPUT_DIR + 'agg_market_category.csv', index=False)
channel_mix.to_csv(OUTPUT_DIR + 'agg_channel.csv', index=False)
minor_channel.to_csv(OUTPUT_DIR + 'agg_minor_channel.csv', index=False)
purpose.to_csv(OUTPUT_DIR + 'agg_travel_purpose.csv', index=False)
gen_mix.to_csv(OUTPUT_DIR + 'agg_generation.csv', index=False)
room_cat.to_csv(OUTPUT_DIR + 'agg_room_category.csv', index=False)
prop_perf.to_csv(OUTPUT_DIR + 'agg_property.csv', index=False)
biz_unit.to_csv(OUTPUT_DIR + 'agg_business_unit.csv', index=False)

print("\n All aggregated CSVs exported.")


# 19. DATA QUALITY EXPORT
dq_rows = []
dq_data = {
    'Null: market_code':         (dq['null_market_code'],   'Low',    'Impute to UNKNOWN or investigate upstream'),
    'Null: source_code':         (dq['null_source_code'],   'Low',    'Flag as Admin/Other; validate with IT'),
    'Null: guest_country':       (dq['null_guest_country'], 'Medium', '5.6% of rows; may affect geographic reporting'),
    'Null: guest_generation':    (dq['null_guest_gen'],     'Low',    '1% missing; impute as Unknown'),
    'Null: Room_revenue':        (dq['null_room_revenue'],  'High',   '19K rows with no revenue — exclude from KPIs'),
    'Negative Room_revenue':     (dq['negative_room_rev'],  'High',   'Likely adjustments/cancellations; separate in reporting'),
    'Zero Room_revenue':         (dq['zero_room_rev'],      'High',   'Complimentary stays inflate room nights; exclude from ADR'),
    'Hotel ref: missing name':   (dq['hotel_ref_missing_name'], 'Medium', 'MAD, MKN, CIB incomplete — validate before publish'),
    'Hotel ref: missing type':   (dq['hotel_ref_missing_type'], 'Medium', 'U/R flag missing; affects Urban vs Resort split'),
    'Inactive hotels with stays':(dq['inactive_hotels_with_stays'], 'Medium', 'Stays recorded against closed properties'),
    'Suspicious market codes':   (dq['bad_market_codes_in_ref'], 'Medium', 'Codes like ., ?, {NULL}, FIXME present in ref table'),
}

dq_export = pd.DataFrame([
    {'Issue': k, 'Record Count': v[0], 'Severity': v[1], 'Recommendation': v[2]}
    for k, v in dq_data.items()
])
dq_export.to_csv(OUTPUT_DIR + 'data_quality_log.csv', index=False)
print(" Data quality log exported.")


# 20. CHARTS

# Colour palette — luxury brand feel
C22 = '#B8A88A'   # warm gold — 2022
C23 = '#2C3E50'   # deep navy — 2023
ACCENT = '#C0392B'
LIGHT_BG = '#F8F6F3'
FONT = 'DejaVu Sans'

def fmt_m(x, pos=None):
    if x >= 1e9: return f'${x/1e9:.1f}B'
    if x >= 1e6: return f'${x/1e6:.0f}M'
    return f'${x:,.0f}'

def save(fig, name):
    fig.savefig(CHARTS_DIR + name, dpi=150, bbox_inches='tight', facecolor=LIGHT_BG)
    plt.close(fig)
    print(f"  Saved: {name}")

print("\n Generating charts...")

# Chart 1: Monthly Room Revenue 2022 vs 2023 
fig, ax = plt.subplots(figsize=(12, 5), facecolor=LIGHT_BG)
ax.set_facecolor(LIGHT_BG)
months = range(1, 13)
month_labels = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

rev_22 = monthly[monthly['stay_year']==2022].sort_values('stay_month')['room_revenue'].values
rev_23 = monthly[monthly['stay_year']==2023].sort_values('stay_month')['room_revenue'].values

ax.plot(months, rev_22/1e6, marker='o', color=C22, linewidth=2.5, label='2022', markersize=6)
ax.plot(months, rev_23/1e6, marker='o', color=C23, linewidth=2.5, label='2023', markersize=6)
ax.fill_between(months, rev_22/1e6, rev_23/1e6, alpha=0.08, color=C23)
ax.set_xticks(list(months)); ax.set_xticklabels(month_labels)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,p: f'${x:.0f}M'))
ax.set_title('Monthly Room Revenue — 2022 vs 2023', fontsize=14, fontweight='bold', pad=12)
ax.legend(fontsize=11); ax.grid(axis='y', alpha=0.3); ax.spines[['top','right']].set_visible(False)
save(fig, 'chart_monthly_revenue.png')

# Chart 2: Room Revenue by Region (stacked bar) 
fig, ax = plt.subplots(figsize=(11, 5), facecolor=LIGHT_BG)
ax.set_facecolor(LIGHT_BG)
regions = regional_23.index.tolist()
rev_23_r = [regional_23.loc[r, 'room_revenue']/1e6 for r in regions]
rev_22_r = [regional_22.loc[r, 'room_revenue']/1e6 if r in regional_22.index else 0 for r in regions]

x = np.arange(len(regions))
w = 0.35
bars22 = ax.bar(x - w/2, rev_22_r, w, color=C22, label='2022')
bars23 = ax.bar(x + w/2, rev_23_r, w, color=C23, label='2023')
ax.set_xticks(x); ax.set_xticklabels(regions, fontsize=11)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,p: f'${x:.0f}M'))
ax.set_title('Room Revenue by Region — 2022 vs 2023', fontsize=14, fontweight='bold', pad=12)
ax.legend(fontsize=11); ax.grid(axis='y', alpha=0.3); ax.spines[['top','right']].set_visible(False)
save(fig, 'chart_regional_revenue.png')

# Chart 3: ADR by Region 
fig, ax = plt.subplots(figsize=(10, 5), facecolor=LIGHT_BG)
ax.set_facecolor(LIGHT_BG)
adr_22_r = [regional_22.loc[r,'ADR'] if r in regional_22.index else 0 for r in regions]
adr_23_r = [regional_23.loc[r,'ADR'] for r in regions]
ax.bar(x - w/2, adr_22_r, w, color=C22, label='2022')
ax.bar(x + w/2, adr_23_r, w, color=C23, label='2023')
ax.set_xticks(x); ax.set_xticklabels(regions)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,p: f'${x:,.0f}'))
ax.set_title('Average Daily Rate (ADR) by Region — 2022 vs 2023', fontsize=14, fontweight='bold', pad=12)
ax.legend(fontsize=11); ax.grid(axis='y', alpha=0.3); ax.spines[['top','right']].set_visible(False)
save(fig, 'chart_adr_regional.png')

# Chart 4: Market Category Mix (2023 room revenue pie) 
fig, ax = plt.subplots(figsize=(8, 6), facecolor=LIGHT_BG)
ax.set_facecolor(LIGHT_BG)
mcat = market_cat_23[market_cat_23['room_revenue'] > 0].sort_values('room_revenue', ascending=False)
# Collapse small categories
threshold = mcat['room_revenue'].sum() * 0.02
mcat_plot = mcat[mcat['room_revenue'] >= threshold].copy()
other_val = mcat[mcat['room_revenue'] < threshold]['room_revenue'].sum()
if other_val > 0:
    mcat_plot = pd.concat([mcat_plot, pd.DataFrame({'major_market_cat': ['Other'], 'room_revenue': [other_val]})])
colors_pie = ['#2C3E50','#B8A88A','#5D6D7E','#85929E','#AEB6BF','#D5D8DC','#784212','#E8DAEF']
wedges, texts, autotexts = ax.pie(
    mcat_plot['room_revenue'], labels=mcat_plot['major_market_cat'],
    autopct='%1.1f%%', startangle=140, colors=colors_pie[:len(mcat_plot)],
    pctdistance=0.75, labeldistance=1.1
)
for t in autotexts: t.set_fontsize(9)
ax.set_title('Room Revenue by Market Category — 2023', fontsize=13, fontweight='bold')
save(fig, 'chart_market_mix.png')

# Chart 5: Top 10 Properties by Room Revenue (2023) 
fig, ax = plt.subplots(figsize=(11, 6), facecolor=LIGHT_BG)
ax.set_facecolor(LIGHT_BG)
top10 = prop_23.head(10)
bars = ax.barh(top10['Hotel_short_nm'][::-1], top10['room_revenue'][::-1]/1e6, color=C23)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x,p: f'${x:.0f}M'))
ax.set_title('Top 10 Properties by Room Revenue — 2023', fontsize=14, fontweight='bold', pad=12)
ax.grid(axis='x', alpha=0.3); ax.spines[['top','right']].set_visible(False)
for bar, val in zip(bars, top10['room_revenue'][::-1]/1e6):
    ax.text(val + 0.3, bar.get_y() + bar.get_height()/2,
            f'${val:.1f}M', va='center', fontsize=9, color='#444')
save(fig, 'chart_top10_properties.png')

# Chart 6: Channel Mix — ADR comparison 
fig, ax = plt.subplots(figsize=(12, 5), facecolor=LIGHT_BG)
ax.set_facecolor(LIGHT_BG)
ch_23 = minor_channel[minor_channel['stay_year']==2023].dropna(subset=['minor_channel_nm'])
ch_23 = ch_23[ch_23['room_revenue'] > 1e5].sort_values('ADR', ascending=False).head(12)
ax.barh(ch_23['minor_channel_nm'][::-1], ch_23['ADR'][::-1], color=C23)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x,p: f'${x:,.0f}'))
ax.set_title('Average Daily Rate by Booking Channel — 2023', fontsize=13, fontweight='bold', pad=12)
ax.grid(axis='x', alpha=0.3); ax.spines[['top','right']].set_visible(False)
save(fig, 'chart_channel_adr.png')

# Chart 7: Travel Purpose mix 
fig, axes = plt.subplots(1, 2, figsize=(12, 5), facecolor=LIGHT_BG)
for i, (yr, ax) in enumerate(zip([2022, 2023], axes)):
    ax.set_facecolor(LIGHT_BG)
    pur = purpose[purpose['stay_year']==yr].sort_values('room_revenue', ascending=False)
    pur = pur[pur['travel_purpose'] != 'Unknown']
    ax.bar(pur['travel_purpose'], pur['room_revenue']/1e6, color=[C22, C23, ACCENT][:len(pur)])
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,p: f'${x:.0f}M'))
    ax.set_title(f'Room Revenue by Travel Purpose — {yr}', fontsize=12, fontweight='bold')
    ax.grid(axis='y', alpha=0.3); ax.spines[['top','right']].set_visible(False)
plt.tight_layout()
save(fig, 'chart_travel_purpose.png')

# Chart 8: Guest Generation Mix (2023 room rev) 
fig, ax = plt.subplots(figsize=(8, 5), facecolor=LIGHT_BG)
ax.set_facecolor(LIGHT_BG)
gen = gen_23[gen_23['guest_generation'].notna()].sort_values('room_revenue', ascending=False)
gen_colors = ['#2C3E50','#B8A88A','#5D6D7E','#85929E','#AEB6BF']
ax.bar(gen['guest_generation'], gen['room_revenue']/1e6, color=gen_colors[:len(gen)])
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,p: f'${x:.0f}M'))
ax.set_title('Room Revenue by Guest Generation — 2023', fontsize=13, fontweight='bold', pad=12)
ax.grid(axis='y', alpha=0.3); ax.spines[['top','right']].set_visible(False)
save(fig, 'chart_guest_generation.png')

# Chart 9: Urban vs Resort 
fig, axes = plt.subplots(1, 2, figsize=(12, 5), facecolor=LIGHT_BG)
pt = prop_type.copy()
pt['type_label'] = pt['Property_type_cd'].map({'U':'Urban','R':'Resort'})

for i, metric in enumerate(['room_revenue', 'ADR']):
    ax = axes[i]; ax.set_facecolor(LIGHT_BG)
    for yr, color in [(2022, C22), (2023, C23)]:
        sub = pt[pt['stay_year']==yr].dropna(subset=['type_label'])
        ax.bar([f"{t}\n{yr}" for t in sub['type_label']], 
               sub[metric]/(1e6 if metric=='room_revenue' else 1), color=color, alpha=0.85)
    if metric == 'room_revenue':
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,p: f'${x:.0f}M'))
        ax.set_title('Room Revenue: Urban vs Resort', fontsize=12, fontweight='bold')
    else:
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,p: f'${x:,.0f}'))
        ax.set_title('ADR: Urban vs Resort', fontsize=12, fontweight='bold')
    ax.grid(axis='y', alpha=0.3); ax.spines[['top','right']].set_visible(False)
plt.tight_layout()
save(fig, 'chart_property_type.png')

# Chart 10: Seasonality Index (2023)
fig, ax = plt.subplots(figsize=(12, 4), facecolor=LIGHT_BG)
ax.set_facecolor(LIGHT_BG)
si = monthly_23.sort_values('stay_month')
bar_colors = [ACCENT if v < 80 else (C22 if v < 110 else C23) for v in si['seasonality_index']]
ax.bar(si['stay_month'], si['seasonality_index'], color=bar_colors)
ax.axhline(100, color='gray', linewidth=1.2, linestyle='--', label='Baseline (avg=100)')
ax.set_xticks(range(1, 13)); ax.set_xticklabels(month_labels)
ax.set_ylabel('Seasonality Index'); ax.set_ylim(0, 160)
ax.set_title('Seasonality Index — Room Revenue 2023 (100 = monthly average)', fontsize=13, fontweight='bold')
ax.legend(fontsize=10); ax.grid(axis='y', alpha=0.3); ax.spines[['top','right']].set_visible(False)
save(fig, 'chart_seasonality.png')

# Chart 11: YoY KPI summary scorecard
fig, axes = plt.subplots(1, 4, figsize=(14, 4), facecolor=LIGHT_BG)
kpi_items = [
    ('Room Revenue', annual_pivot.loc[2022,'room_revenue']/1e6, annual_pivot.loc[2023,'room_revenue']/1e6, 'M'),
    ('Room Nights',  annual_pivot.loc[2022,'room_nights']/1e3,  annual_pivot.loc[2023,'room_nights']/1e3,  'K'),
    ('ADR',          annual_pivot.loc[2022,'ADR'],              annual_pivot.loc[2023,'ADR'],              ''),
    ('Total Revenue',annual_pivot.loc[2022,'total_revenue']/1e6,annual_pivot.loc[2023,'total_revenue']/1e6,'M'),
]
for ax, (label, v22, v23, suffix) in zip(axes, kpi_items):
    ax.set_facecolor(LIGHT_BG)
    change = (v23 - v22) / v22 * 100
    arrow = '▲' if change > 0 else '▼'
    color = '#27AE60' if change > 0 else ACCENT
    ax.text(0.5, 0.75, f'${v23:,.1f}{suffix}', ha='center', va='center',
            fontsize=20, fontweight='bold', color=C23, transform=ax.transAxes)
    ax.text(0.5, 0.45, label, ha='center', va='center',
            fontsize=11, color='#555', transform=ax.transAxes)
    ax.text(0.5, 0.2, f'{arrow} {abs(change):.1f}% vs 2022', ha='center', va='center',
            fontsize=12, color=color, fontweight='bold', transform=ax.transAxes)
    ax.set_xticks([]); ax.set_yticks([])
    for spine in ax.spines.values(): spine.set_color('#CCC')

fig.suptitle('Enterprise KPI Scorecard — 2023 vs 2022', fontsize=15, fontweight='bold', y=1.02)
save(fig, 'chart_kpi_scorecard.png')

print("\n All charts generated successfully.")
print("\n SUMMARY STATS FOR DECK")
for yr in [2022, 2023]:
    row = annual_pivot.loc[yr]
    print(f"\n{yr}:")
    print(f"  Room Revenue:  ${row['room_revenue']/1e6:,.1f}M")
    print(f"  Total Revenue: ${row['total_revenue']/1e6:,.1f}M")
    print(f"  Room Nights:   {row['room_nights']:,.0f}")
    print(f"  ADR:           ${row['ADR']:,.2f}")
    print(f"  Stays:         {row['stays_count']:,.0f}")