import pandas as pd
from scipy.spatial import cKDTree
import scipy.stats as stats
import numpy as np
import re


CHECK_DISTANCE_METERS = 50       # 30m gives better results but 50m allows for GPS error.
QUIET_STREET_BUFFER = 50         # Distance to consider a light "On a Quiet Street"
HABITAT_TEST_DISTANCES = [250, 200, 150, 100, 50] # The "Sensitivity Loop"

print("SPATIAL RISK ANALYSIS")

def load_shape_coords(filename, label):
    print(f"Loading {label}.")
    try:
        df = pd.read_csv(filename, sep=',')
        if 'SHAPE' not in df.columns: df = pd.read_csv(filename, sep=';', on_bad_lines='skip')
        
        if 'SHAPE' not in df.columns: return None

        all_lats, all_lons = [], []
        for shape_text in df['SHAPE']:
            coords = re.findall(r"(\d+\.\d+)\s+(\d+\.\d+)", str(shape_text))
            for lon, lat in coords:
                all_lons.append(float(lon))
                all_lats.append(float(lat))
        return np.column_stack((all_lats, all_lons)) if all_lats else None
    except: return None

print("\nStep 1: Loading Environmental Data.")
nature_pts = load_shape_coords('nature.csv', "Nature Reserves")
water_pts  = load_shape_coords('water.csv', "Standing Water")
green1_pts = load_shape_coords('greenbelt1.csv', "Green Belt 1")
green2_pts = load_shape_coords('greenbelt2.csv', "Green Belt 2")
res_pts    = load_shape_coords('residential.csv', "Residential Streets")

# Combining Bio Layers
bio_cloud = []
if nature_pts is not None: bio_cloud.append(nature_pts)
if water_pts is not None:  bio_cloud.append(water_pts)
if green1_pts is not None: bio_cloud.append(green1_pts)
if green2_pts is not None: bio_cloud.append(green2_pts)

# Building Trees
bio_tree = cKDTree(np.vstack(bio_cloud)) if bio_cloud else None
street_tree = cKDTree(res_pts) if res_pts is not None else None

if not bio_tree:
    print("CRITICAL: No habitat data loaded.")
    exit()

# Loading Lights
def load_raw_lights(filename):
    try:
        df = pd.read_csv(filename, sep=',')
        if 'SHAPE' not in df.columns: df = pd.read_csv(filename, sep=';')
        lats, lons = [], []
        for shape_text in df['SHAPE']:
            try:
                coords = re.findall(r"[-+]?\d*\.\d+|\d+", str(shape_text))
                if len(coords) >= 2: lons.append(float(coords[0])); lats.append(float(coords[1]))
                else: lats.append(None); lons.append(None)
            except: lats.append(None); lons.append(None)
        df['lat'] = lats; df['lon'] = lons
        return df.dropna(subset=['lat', 'lon'])
    except: return pd.DataFrame()

acoustic_raw = load_raw_lights('lights_acoustic.csv')
silent_raw   = load_raw_lights('lights_silent.csv')

# Loading Animals
roadkill = pd.read_csv('roadkill.csv', sep='\t', on_bad_lines='skip')
animals = roadkill[
    (roadkill['decimalLatitude'].between(48.12, 48.33)) &
    (roadkill['decimalLongitude'].between(16.18, 16.58))
].dropna(subset=['decimalLatitude', 'decimalLongitude'])

print(f"  -> Animals Loaded: {len(animals)}")


print("\n" + "="*75)
print(f"   RESULTS TABLE: SENSITIVITY ANALYSIS (Check Dist: {CHECK_DISTANCE_METERS}m)")
print("="*75)
print(f"{'HABITAT (m)':<12} | {'ACOUSTIC (Deaths/Lights)':<25} | {'SILENT (Deaths/Lights)':<23} | {'P-VALUE':<10}")
print("-" * 75)

for habitat_dist in HABITAT_TEST_DISTANCES:
    
    # Filtering Lights based on current habitat distance
    def get_valid_lights(df):
        light_coords = df[['lat', 'lon']].values
        keep_mask = np.zeros(len(df), dtype=bool)
        
        # Near Habitat (Variable Distance)
        if bio_tree:
            dists, _ = bio_tree.query(light_coords, k=1)
            keep_mask = keep_mask | ((dists * 111139) < habitat_dist)
            
        # Near Quiet Street (Fixed Distance 50m)
        if street_tree:
            dists, _ = street_tree.query(light_coords, k=1)
            keep_mask = keep_mask | ((dists * 111139) < QUIET_STREET_BUFFER)
            
        return df[keep_mask]

    acoustic_valid = get_valid_lights(acoustic_raw)
    silent_valid   = get_valid_lights(silent_raw)

    # Counting Deaths
    def count_deaths(l_df):
        if len(l_df) == 0: return 0
        t = cKDTree(l_df[['lat', 'lon']].values)
        d, _ = t.query(animals[['decimalLatitude', 'decimalLongitude']].values, k=1)
        return np.sum((d * 111139) < CHECK_DISTANCE_METERS)

    d_a = count_deaths(acoustic_valid)
    d_s = count_deaths(silent_valid)
    
    n_a = len(acoustic_valid)
    n_s = len(silent_valid)

    # Stats
    safe_a = n_a - d_a
    safe_s = n_s - d_s
    
    if n_a > 0 and n_s > 0:
        _, p = stats.fisher_exact([[d_a, safe_a], [d_s, safe_s]])
        rate_a = (d_a / n_a) * 1000
        rate_s = (d_s / n_s) * 1000
    else:
        p = 1.0; rate_a = 0; rate_s = 0

    sig_mark = "*" if p < 0.05 else ""
    print(f"{habitat_dist:<12} | {d_a}/{n_a} ({rate_a:.1f}/1k)      | {d_s}/{n_s} ({rate_s:.1f}/1k)     | {p:.4f} {sig_mark}")

print("-" * 75)
print(" * = Significant (p < 0.05)")
print(f" Note: 'Quiet Street' buffer fixed at {QUIET_STREET_BUFFER}m for all tests.")