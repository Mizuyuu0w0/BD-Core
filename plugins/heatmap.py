import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
from plugins.base import BasePlugin

class HeatmapPlugin(BasePlugin):
    """
    Heatmap: Defaults to Correlation Matrix if no specific mapping is found.
    """
    def validate_data(self):
        # 只需要有数值列即可
        self.numeric_cols = self.df.select_dtypes(include=['number']).columns
        if len(self.numeric_cols) <2:
            raise ValueError("Heatmap requires at least 2 numeric columns for correlation.")

    def compute_stats(self):
        # [HYGIENE] Exclude x/y from correlation matrix
        # We only want biological variables, not the coordinates
        cols_to_use = [c for c in self.numeric_cols if c not in ['x','y']]  

        # Calculate Pearson Correlation
        self.corr_matrix = self.df[cols_to_use].corr()

    def plot(self):
        # [Visual Logic] 1. Truncate Long Labels
        # Prevent layout breakage (max 15 chars)
        trunc = lambda x: (x[:12] + '...') if isinstance(x, str) and len(x)>15 else x

        # Apply truncation to index/columns for display only
        df_display = self.df.copy()
        df_display.index = [trunc(x) for x in df_display.index]
        df_display.columns = [trunc(x) for x in df_display.columns]

        # [Visual Logic] 2. High Contrast Colormap
        # RdBu_r: Red=High, Blue=Low, White=Zero. Visually distinct.
        sns.heatmap(
            self.corr_matrix,
            annot=True, fmt=".2f",
            annot_kws={"size":6},
            cmap="RdBu_r",center=0,# Crucial for correlation
            square=True,# Enforce 1:1 aspect ratio
            cbar_kws={"shrink":.5, "label": self.config.get('legend_name', '')},
            ax=self.ax
        )

        # [Visual Logic] 3. Alignment
        # Rotate X labels for readability
        plt.setp(self.ax.get_xticklabels(), rotation=45, ha='right', rotation_mode='anchor')