
import pandas as pd
import numpy as np
import os
from plugins.heatmap import HeatmapPlugin
from core.artifact_manager import ArtifactManager

# Mock AM
class MockAM(ArtifactManager):
    def __init__(self):
        self.run_id = "TEST_DIRTY"
        self.timestamp = "2026-02-08"
        self.sandbox_dir = "test_output_v1_2"
        os.makedirs(self.sandbox_dir, exist_ok=True)
    def save_figure(self, fig, name):
        pass
    def save_data(self, data, name):
        pass

am = MockAM()

# Create Dirty Data (Newlines in Gene Names and Sample Names)
df = pd.DataFrame(
    np.random.rand(5, 3),
    columns=[" S1 \n", "S2\n", "\tS3"],  # Dirty Columns
    index=["Gene A\n", "Gene\nB", " Gene C ", "Gene D\t", " Gene E "] # Dirty Index (Matches 5 rows)
)

print("Original Columns:", df.columns.tolist())
print("Original Index:", df.index.tolist())

# Config
config = {'graph': 'Heatmap', 'heatmap_mode': 'expression', 'subtype': 'expression', 'z_score': 0, 'cluster': False, 'selected_columns': [" S1 \n", "S2\n", "\tS3"]}

# Run Plugin
plugin = HeatmapPlugin(am, config, df)
plugin.run()

# Verify Sanitization
print("\n[Verification] Checking internal data...")
cleaned_index = plugin.heatmap_data.index.tolist()
cleaned_cols = plugin.heatmap_data.columns.tolist()

print("Cleaned Index:", cleaned_index)
print("Cleaned Columns:", cleaned_cols)

errors = []
for i in cleaned_index:
    if '\n' in i or i.startswith(' ') or i.endswith(' '):
        errors.append(f"Index '{i}' not clean")
for c in cleaned_cols:
    if '\n' in c or c.startswith(' ') or c.endswith(' '):
        errors.append(f"Column '{c}' not clean")

if not errors:
    print("\nSUCCESS: All newlines and whitespace stripped!")
    # Detailed check
    if "Gene\nB" in cleaned_index:
        print("FAILURE: Internal newline not removed in Gene\\nB")
    elif "GeneB" in cleaned_index:
        print("SUCCESS: Internal newline removed: Gene\\nB -> GeneB")
else:
    print("\nFAILURE: Found dirty data:")
    for e in errors: print(e)
