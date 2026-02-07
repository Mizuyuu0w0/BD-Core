import seaborn as sns 
import matplotlib.pyplot as plt
from scipy import stats
import pandas as pd
import textwrap
from plugins.base import BasePlugin
import logging

logger = logging.getLogger(__name__)

class BoxplotPlugin(BasePlugin):
    """
    MVP Plugin: Boxplot + Stripplot with Auto-Stats.
    """

    def validate_data(self):
        """Ensure 'x' (Group) and 'y' (Value) columns exist."""
        # BasePlugin._apply_mapping has already renamed columns to x/y
        if 'x' not in self.df.columns or 'y' not in self.df.columns:
             # Legacy fallback: try to find group/value and rename
             if 'group' in self.df.columns: self.df.rename(columns={'group':'x'}, inplace=True)
             if 'value' in self.df.columns: self.df.rename(columns={'value':'y'}, inplace=True)
        
        if 'x' not in self.df.columns:
             # Auto-assign default group if missing
             self.df['x'] = 'Default'
             logger.info("Auto-assigned 'Default' group to 'x'.")

        if 'y' not in self.df.columns:
            raise ValueError("Boxplot requires a dependent variable (Y-axis/Value).")

        # Remove NaNs
        self.df = self.df.dropna(subset=['y'])
        logger.info(f"Data Validated. Rows: {len(self.df)}")

    def compute_stats(self):
        """
        [LOGIC PATCH] One-vs-Rest (Control)
        Compare every group against a specific Reference Group.
        """
        import pandas as pd
        from scipy import stats

        if 'x' not in self.df.columns or 'y' not in self.df.columns:
            return

        # 1. Identify Control Group
        groups = self.df['x'].unique()
        # sort alphabetically first to be deterministic
        groups = sorted(groups, key=lambda s: str(s))
        ref_group = groups[0] # Default: First one

        # Priority Search for "Control" or similar
        img_keywords = ['control','wt','placebo','0','mock','ctrl']
        for g in groups:
            if str(g).lower() in img_keywords:
                ref_group = g
                break

        logger.info(f"Hypothesis Test: Reference Group = '{ref_group}'")

        # 2. Reorder groups list so Ref is first (Visual)
        # Remove ref, then prepend it
        others = [g for g in groups if g != ref_group]
        self.order = [ref_group] + others

        # [HYGIENE] Enforce Data Sorting (Control First)
        # Convert to categorical to ensure groupby/export respects this order
        self.df['x'] = pd.Categorical(self.df['x'], categories=self.order, ordered=True)
        self.df = self.df.sort_values('x')

        # 3. Pairwise Tests (Treatment vs Control)
        control_data = self.df[self.df['x'] == ref_group]['y']
        
        results_list = []
        for test_group in others:
            test_data = self.df[self.df['x'] == test_group]['y']
            
            # Normality Check (Simplified)
            try:
                if len(control_data) >= 3 and len(test_data) >= 3:
                     _, p1 = stats.shapiro(control_data)
                     _, p2 = stats.shapiro(test_data)
                     is_normal = (p1 > 0.05) and (p2 > 0.05)
                else:
                     is_normal = False # Fallback for small N
            except:
                is_normal = False
                
            if is_normal:
                stat, p_val = stats.ttest_ind(test_data, control_data)
                method = "T-test"
            else:
                stat, p_val = stats.mannwhitneyu(test_data, control_data,)
                method = "Mann-Whitney"
                
            results_list.append({
                "Comparison": f"{test_group} vs {ref_group}",
                "Method": method,
                "P-Value": p_val,
                "Control_N": len(control_data),
                "Test_N": len(test_data)
            })
            
        logger.info(f"Completed {len(results_list)} pairwise comparisons against {ref_group}")
        
        # Store as list (BasePlugin expects a dictionary, but we hack it to handle lists or we just take the first one for plot label)
        # Actually, BasePlugin's save_artifacts wraps stats_results in a DataFrame. 
        # If stats_results is a list of dicts, pd.DataFrame(self.stats_results) works perfectly!
        self.stats_results = results_list

    def plot(self):
        """
        [Visual Logic] 1. Logic Sorting
        Bio-readers expect Control/WT on the left.
        Check unique groups and sort them strictly.
        """
        # [Fix] Smart Wrap helper
        def smart_wrap(text, width=20):
            return "\n".join(textwrap.wrap(str(text), width=width))

        # 1. Prepare Data Labels (Wrap text to avoid overflow)
        # We must modify the dataframe itself so Seaborn picks up the wrapped labels
        self.df['x'] = self.df['x'].apply(lambda x: smart_wrap(x, width=15))
        
        # Re-sort groups based on the wrapped text (preserving logic order)
        # Note: compute_stats already set 'x' as Categorical with specific order.
        # We need to map the original order to the new wrapped values.
        
        # If 'order' was set in compute_stats, map it to wrapped version
        plot_order = None
        if hasattr(self, 'order') and self.order:
             plot_order = [smart_wrap(g, 15) for g in self.order]
        else:
             # Fallback sorting
             unique_groups = sorted(self.df['x'].unique(), key=lambda x: str(x).lower())
             priority = ['0','control','wt','mock']
             # Check if wrapped strings match priority (fuzzy check not needed if we trust the loop)
             plot_order = sorted(unique_groups, key=lambda x: (str(x).lower() not in priority, x))

        # 2. Main Plot
        sns.boxplot(
            data=self.df, x='x', y='y', order=plot_order,
            hue='x', dodge=False,
            boxprops=dict(facecolor="none",edgecolor="black"), # Skeleton style
            whiskerprops=dict(color="black"),
            capprops=dict(color="black"),
            medianprops=dict(color="red"),
            ax=self.ax
        )

        #Stripplot (The raw points)
        sns.stripplot(
            data=self.df, x="x", y="y",
            color="black", size=3, alpha=0.6, jitter=0.2,
            zorder=2,
            ax=self.ax
        )

        # [Title & Legend Fix]
        # 1. Title
        title = self.config.get('title')
        if title:
             wrapped_title = "\n".join(textwrap.wrap(title, width=50))
             self.ax.set_title(wrapped_title, fontsize=12, pad=15)
        
        # 2. Legend
        # If the user specifically requested a legend (common for multi-group)
        # The 'boxplot' above uses hue='x', so a legend is created by default.
        # We need to decide whether to keep it or customize it.
        show_legend = self.config.get('legend', False) # Default False for boxplot (redundant with X-axis)
        
        # [Fix] Capture seaborn's auto-generated legend handles/labels
        handles, labels = [], []
        if self.ax.get_legend():
             handles = self.ax.get_legend().legend_handles
             labels = [t.get_text() for t in self.ax.get_legend().texts]
             # If handles list is empty but legend exists, try get_legend_handles_labels on ax
             if not handles:
                 handles, labels = self.ax.get_legend_handles_labels()
        
        if show_legend and handles:
             legend_title = self.config.get('legend_name') or self.config.get('xlabel') or "Group"
             # [Smart Wrap] Wrap legend title
             wrapped_leg_title = "\n".join(textwrap.wrap(legend_title, width=20))
             
             # Move legend outside to prevent covering data
             self.ax.legend(handles=handles, labels=labels, title=wrapped_leg_title, 
                            bbox_to_anchor=(1.05, 1), loc='upper left', 
                            borderaxespad=0., prop={'size': 8})
        else:
             # Remove default legend if not requested
             if self.ax.get_legend():
                 self.ax.get_legend().remove()

        # 3. Labeling
        xlabel = self.config.get('xlabel', 'Group')
        ylabel = self.config.get('ylabel', 'Value')
        self.ax.set_xlabel(xlabel) 
        self.ax.set_ylabel(ylabel)

        # Add P-value annotation if exists
        # Handle both list (One-vs-Rest) and dict (Legacy)
        p_v = None
        method = ""
        
        if isinstance(self.stats_results, list) and len(self.stats_results) > 0:
             # Take the first comparison (usually the main treatment vs control)
             res = self.stats_results[0]
             p_v = res.get("P-Value")
             method = res.get("Method", "Test")
        elif isinstance(self.stats_results, dict) and "P-Value" in self.stats_results:
             p_v = self.stats_results["P-Value"]
             method = self.stats_results["Method"]

        if p_v is not None:
            if p_v < 0.001:
                p_str = "p < 0.001"
            elif p_v < 0.05:  
                p_str = "p < 0.05"
            else:
                p_str = f"p = {p_v:.4f}"

            label = f"{method}\n{p_str}"

            self.ax.text(0.05, 0.95, label, transform=self.ax.transAxes,
                        verticalalignment='top',fontsize=6)
