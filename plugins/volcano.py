import pandas as pd
import numpy as np
import seaborn as sns 
import matplotlib.pyplot as plt 
from plugins.base import BasePlugin

class VolcanoPlugin(BasePlugin):
    """
    Volcano Plot: Visualize Differential Expression (X=FoldChange, Y=P-value)
    Auto-transform Y to -log10(P) if raw P-values are detected.
    """
    def validate_data(self):
        # 火山图至少需要两列数据：x (FC), y (P)
        # BasePlugin 的 _apply_mapping 已经把它们重命名为 'x' 和 'y' 了
        if 'x' not in self.df.columns or 'y' not in self.df.columns:
            raise ValueError("Volcano Plot reuires 'Independent Variable (FC)' and 'Dependent Variable (P-value)'.")

    def compute_stats(self):
        # 智能预处理：如果 Y 轴看起来像 P-value (0~1之间)，自动转为 -log10
        y_max =  self.df['y'].max()
        if y_max <= 1.0:
            print("Auto-transforming Y-axis to -log10(P-value)...")
            self.df['y'] = -np.log10(self.df['y'])
            # [UX] 如果没改过 Label，帮用户改一下
            if self.config.get('ylabel') == 'P-value':
                self.config['ylabel'] = '-Log10(P-value)'
    
    def plot(self):
        # [Visual Logic] 1. Define Thresholds
        p_threshold = 1.3 # -log10(0.05)
        fc_threshold = 1.0 # log2(2)

        # [Visual Logic] 2. Semantic Classification
        # Create a temporary 'Status' column for coloring
        conditions = [
            (self.df['x'] > fc_threshold) & (self.df['y'] > p_threshold), # Up
            (self.df['x'] < -fc_threshold) & (self.df['y'] > p_threshold) # Down
        ]
        choices = ['Up','Down']
        self.df['Status'] = np.select(conditions, choices, default='NS')

        # [Visual Logic] 3. Nature Color Palette
        palette = {
            'Up': '#E64B35', # Nature Red
            'Down': '#3C5488', # Nature Blue
            'NS': '#B09C85'    # Muted Grey/Beige
        }

        # [Visual Logic] 4. Layering
        # Plot NS first (bottom layer), then Significant points (top layer)
        sns.scatterplot(
            data=self.df.sort_values('Status',key = lambda x: x== 'NS'), # Put NS first
            x='x',y='y',
            hue='Status',palette=palette,
            style='Status',markers={'Up':'o', 'Down':'o', 'NS':'o'}, # Uniform marker
            alpha=0.8,s=15,edgecolor=None,
            legend=False, # Legend is self-explanatory via color
            ax=self.ax
        )

        # [Visual Logic] 5. Threshold Lines (Guides)
        self.ax.axhline(p_threshold, color='black', linestyle='--', linewidth=0.5, alpha=0.5)
        self.ax.axvline(fc_threshold, color='black', linestyle='--', linewidth=0.5, alpha=0.5)
        self.ax.axvline(-fc_threshold, color='black', linestyle='--', linewidth=0.5, alpha=0.5)

        # Labels & Title... (keep existing)
        self.ax.set_xlabel(self.config.get('xlabel','Log2 Fold Change'))
        self.ax.set_ylabel(self.config.get('ylabel','-Log10 P-value'))
        if self.config.get('title'): self.ax.set_title(self.config['title'])