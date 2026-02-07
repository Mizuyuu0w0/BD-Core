import seaborn as sns
import matplotlib.pyplot as plt 
from scipy import stats
from plugins.base import BasePlugin
import logging
import pandas as pd
import textwrap

logger = logging.getLogger(__name__)

class ScatterPlugin(BasePlugin):
    """
    MVP Plugin: Scatter Plot with Linear Regression.
    """

    def validate_data(self):
        """Ensure 'x' and 'y' columns exist."""
        required = ['x','y'] 
        missing = [col for col in required if col not in self.df.columns]
        if missing:
            raise ValueError(f"Scatter requires columns: {missing}")

        # Enforce numeric types (coerce strings like '48h', 'ND' to NaN)
        self.df['x'] = pd.to_numeric(self.df['x'], errors='coerce')
        self.df['y'] = pd.to_numeric(self.df['y'], errors='coerce')

        self.df = self.df.dropna(subset=['x','y'])
        logger.info(f"Data Validated. Rows: {len(self.df)}")

    def compute_stats(self):
        """
        Pearson Correlation + Linear Regression Stats
        """
        x = self.df['x']
        y = self.df['y']

        if len(x) < 2:
            return

        # Pearson Correlation
        r, p_val = stats.pearsonr(x, y)
        r_squared = r ** 2

        logger.info(f"Correlation: R^2={r_squared:.4f}, p={p_val:.4e}")

        self.stats_results = {
            "Pearson_r": r,
            "R_Squared": r_squared,
            "P-Value": p_val,
            "N": len(x)
        }

    def plot(self):
        """
        Visual: Points + Regression Line + 95% CI
        """
        # [Fix] Smart Title Wrap
        title = self.config.get('title')
        if title:
             wrapped_title = "\n".join(textwrap.wrap(title, width=50))
             self.ax.set_title(wrapped_title, fontsize=12, pad=15)
        
        # Main Plot
        sns.regplot(
            data=self.df, x='x', y='y',
            color='black', # Points color
            scatter_kws={'s': 10, 'alpha': 0.6},
            line_kws={'color':'red','linewidth':1},
            ci=95, # 95% Confidence Interval (Shaded)
            ax=self.ax,
            label="Data" # Default label
        )

        # [Support Legend]
        if self.config.get('legend', False):
             self.ax.legend()
        else:
             if self.ax.get_legend():
                 self.ax.get_legend().remove()

        # [Visual Logic] Smart Stats Positioning
        # Avoid overlapping the regression line.
        # If r > 0 (Upward), line takes Bottom-Left to Top-Right. Top-Left is safe.
        # If r < 0 (Downward), line takes Top-Left to Bottom-Right. Top-Right is safe.
        r_val = self.stats_results.get('Pearson_r', 0)
        if r_val > 0:
            pos_x,pos_y,halign =0.05,0.95,'left' # Top-Left
        else:
            pos_x,pos_y,halign=0.95,0.05,'right' # Top-Right

        # Cleanup Labels
        self.ax.set_xlabel(self.config.get('xlabel', 'X-Axis'))
        self.ax.set_ylabel(self.config.get('ylabel', 'Y-Axis'))

        if "R_Squared" in self.stats_results:
            r2 = self.stats_results['R_Squared']
            p_v = self.stats_results["P-Value"]

            # Smart P-value Formatting
            if p_v < 0.001:
                p_str = "p < 0.001"
            elif p_v < 0.005: 
                p_str = "p < 0.005"
            else:
                p_str = f"p = {p_v:.4f}"
            
            label = f"$R^2$ = {r2:.3f}\n{p_str}"

            self.ax.text(pos_x,pos_y,label,transform=self.ax.transAxes,ha=halign,va='top',fontsize=6)
