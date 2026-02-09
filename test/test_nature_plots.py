
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import shutil
from core.artifact_manager import ArtifactManager
from core.style import NatureStyler
from plugins.boxplot import BoxplotPlugin
from plugins.scatter import ScatterPlugin
from plugins.volcano import VolcanoPlugin
from plugins.heatmap import HeatmapPlugin

# Setup
NatureStyler.apply()
os.makedirs("test_output", exist_ok=True)

# Mock ArtifactManager
class MockAM(ArtifactManager):
    def __init__(self):
        self.run_id = "TEST001"
        self.timestamp = "2026-02-08"
        self.sandbox_dir = "test_output"
    def save_figure(self, fig, name):
        # Save as PNG
        path_png = os.path.join(self.sandbox_dir, f"{name}.png")
        fig.savefig(path_png, dpi=300, bbox_inches='tight')
        
        # Save as PDF (Vector Graphics for Nature)
        path_pdf = os.path.join(self.sandbox_dir, f"{name}.pdf")
        fig.savefig(path_pdf, format='pdf', bbox_inches='tight')
        
        print(f"Saved: {path_png} & {path_pdf}")
    def save_data(self, data, name):
        pass # Skip data saving for visual test
    def calculate_input_hash(self, config, df):
        pass
    def close(self):
        pass

am = MockAM()

# 1. Box Plot Data (Long Format)
df_box = pd.DataFrame({
    'Group': ['Ctrl']*10 + ['Treat']*10,
    'Value': np.concatenate([np.random.normal(10, 2, 10), np.random.normal(15, 2, 10)])
})
config_box = {'graph': 'Box', 'xlabel': 'Group', 'ylabel': 'Value', '_mapping': {'independent_variable': 'Group', 'dependent_variable': 'Value'}}
print("Running Box Plot...")
BoxplotPlugin(am, config_box, df_box).run()

# 2. Scatter Plot Data
df_scatter = pd.DataFrame({
    'X': np.random.rand(20) * 10,
    'Y': np.random.rand(20) * 10 + 5
})
config_scatter = {'graph': 'Scatter', 'xlabel': 'X', 'ylabel': 'Y', '_mapping': {'independent_variable': 'X', 'dependent_variable': 'Y'}}
print("Running Scatter Plot...")
ScatterPlugin(am, config_scatter, df_scatter).run()

# 3. Volcano Plot Data
df_volcano = pd.DataFrame({
    'Gene': [f'Gene{i}' for i in range(100)],
    'log2FC': np.random.normal(0, 2, 100),
    'pvalue': np.random.uniform(0, 1, 100)
})
# Start with simple config
config_volcano = {'graph': 'Volcano', 'xlabel': 'log2FC', 'ylabel': 'pvalue', '_mapping': {'independent_variable': 'log2FC', 'dependent_variable': 'pvalue'}, 'p_cutoff': 0.05, 'fc_cutoff': 1.0}
print("Running Volcano Plot...")
VolcanoPlugin(am, config_volcano, df_volcano).run()

# 4. Heatmap Data (Wide)
df_heat = pd.DataFrame(np.random.rand(10, 5), columns=['S1','S2','S3','S4','S5'])
df_heat.index = [f'Gene{i}' for i in range(10)]
# Heatmap plugin expects df to have columns. 
# If index is genes, reset index to make 'Gene' a column? 
# The plugin usually filters numeric columns. If index is not valid, let's reset.
df_heat_reset = df_heat.reset_index().rename(columns={'index':'Gene'})

# 4a. Heatmap Correlation
config_heat_corr = {'graph': 'Heatmap', 'heatmap_mode': 'correlation', 'cluster': True}
print("Running Heatmap (Correlation)...")
HeatmapPlugin(am, config_heat_corr, df_heat_reset).run()

# 4b. Heatmap Expression
config_heat_expr = {'graph': 'Heatmap', 'heatmap_mode': 'expression', 'cluster': True, 'z_score': 0, 'selected_columns': ['S1','S2','S3','S4','S5']}
print("Running Heatmap (Expression)...")
HeatmapPlugin(am, config_heat_expr, df_heat_reset).run()

print("All tests complete. Check 'test_output' folder.")
