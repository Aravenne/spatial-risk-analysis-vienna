# Spatial Data Pipeline for Environmental Risk Analysis

### Project Overview
This project performs a spatial risk analysis to evaluate the impact of acoustic traffic signals on urban wildlife mortality. By fusing 6 Open Government Datasets from the City of Vienna, including biological records; infrastructure data; and topological layers, this pipeline models whether acoustic signals deter wildlife or correlate with higher roadkill rates.

### Key Findings
* **Hypothesis:** Acoustic signals act as a "Sonic Shield," reducing roadkill rates.
* **Result:** Negative correlation. Acoustic signals showed a consistently higher mortality rate (~45-50 deaths/1,000 lights) compared to silent signals (~30-36 deaths/1,000 lights) across all spatial sensitivities.
* **Statistical Verdict:** While the trend is visually consistent, the p-value (>0.05) indicates statistical insignificance due to the limited sample size of "silent" lights in valid habitat zones.

![Robustness Chart](robustness_chart.png)

### Technical Implementation
* **Language:** Python 3.9+
* **Spatial Indexing:** Implemented `scipy.spatial.cKDTree` for high-performance nearest-neighbor queries (processing ~140,000 water/habitat points against ~1,200 infrastructure nodes).
* **Data Engineering:** Integrated disparate CSV datasets with regex coordinate parsing and custom spatial filtering.
* **Sensitivity Analysis:** Developed a "Robustness Loop" to test validity across varying spatial buffers (50m – 250m).

### Dataset Sources
This project utilizes public data from **Vienna Open Government Data (OGD)** and **Project Roadkill (GBIF)**.
To reproduce this analysis, download the following datasets and place them in the root directory:
1.  **Project Roadkill:** [GBIF Occurrence Data](https://www.gbif.org/)
2.  **Vienna Infrastructure:**
    * Traffic lights without acoustic indicators - locations in Vienna
    * Traffic lights with acoustic indicators - locations in Vienna
3.  **Vienna Environments:**
    * Standing waters Vienna
    * Nature reserves Vienna
    * Vienna Green Belt
    * Residential streets in Vienna

### Usage
```bash
# Install dependencies
pip install pandas scipy numpy matplotlib

# Run the spatial analysis pipeline

python final_analysis.py
