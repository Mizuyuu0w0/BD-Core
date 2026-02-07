from abc import ABC, abstractmethod
import matplotlib.pyplot as plt 
import logging
from core.style import NatureStyler

logger = logging.getLogger(__name__)

class BasePlugin(ABC):
    """
    Abstract Base Class representing the Contract for all visualization plugins.
    Follows the Template Method Pattern.
    """

    def __init__(self, artifact_manager, config, df):
        self.am = artifact_manager
        self.config = config
        self.df = df
        self.fig = None
        self.ax = None
        self.stats_results = {}

    def run(self):
        """
        The Template Method. 
        Defines the strict lifecycle of a visualization task.
        Subclasses CANNOT override this, only the steps below.
        """
        logger.info(f"Running Plugin: {self.__class__.__name__}")

        # 1. Prepare
        self._apply_mapping() # [DSL] Rename columns based on config
        self.validate_data()
        
        # 2. Calculate
        self.compute_stats()
        
        # 3. Visualize
        NatureStyler.apply() # Enforce styles globally before plotting
        self.fig, self.ax = plt.subplots(figsize=(8, 6)) # Create canvas (Wider for footer balance)
        self.plot() 

        # 4. Finalize
        self._stamp_audit() # Append RunID hash to image
        self.save_artifacts()

        # 5. Review
        plt.close(self.fig) # Free memory

    @abstractmethod
    def validate_data(self):
        """Step 1: check if data columns match requirements"""
        pass

    @abstractmethod
    def compute_stats(self):
        """Step 2: Scipy/Statsmodels logic"""
        pass

    @abstractmethod
    def plot(self):
        """Step 3: Seaborn/Matplotlib logic"""
        pass

    def save_artifacts(self):
        """Step 4: Save default artifacts (Custom Naming + Multi-Sheet Stats)"""
        # 1. Descriptive Filename
        g_type = self.config.get('graph', 'Graph').capitalize()
        # Fallback logic to get clean labels
        map_cfg = self.config.get('_mapping', {})
        ylabel = self.config.get('ylabel', map_cfg.get('dependent_variable', 'Y'))
        xlabel = self.config.get('xlabel', map_cfg.get('independent_variable', 'X'))
        
        def clean(s): return str(s).replace('/', '_').replace(':', '')
        
        if 'box' in g_type.lower():
             name = f"{g_type} Graph ({clean(ylabel)})"
        elif 'scatter' in g_type.lower():
             name = f"{g_type} Graph ({clean(ylabel)} against {clean(xlabel)})"
        elif 'volcano' in g_type.lower():
             name = f"{g_type} Graph ({clean(ylabel)} vs {clean(xlabel)})"
        elif 'heatmap' in g_type.lower():
             name = f"{g_type} Graph (Correlation Matrix)"
        else:
             name = f"BD Result {self.am.run_id}"

        # 2. Save Figure
        self.am.save_figure(self.fig, name)

        # 3. Save Data (Multi-Sheet)
        # Helper to round floats
        def round_floats(df, decimals=3):
            return df.round(decimals)

        # [HYGIENE PATCH] Restore Headers & Clean Columns
        export_df = self.df.copy()

        # Rename x/y 
        rename_map = {}
        if 'x' in export_df.columns:
            # Special Case: Volcano (Log2FC), Scatter (Indep)
            if 'volcano' in g_type.lower():
                rename_map['x'] = 'Log2_FoldChange'
            else:
                rename_map['x'] = xlabel

        if 'y' in export_df.columns:
            # Special Case: Volcano (Log2FC), Scatter (Dep)
            if 'volcano' in g_type.lower():
                rename_map['y'] = 'P_Value'
            else:
                rename_map['y'] = ylabel

        export_df.rename(columns=rename_map, inplace=True)

        # [Box Plot Specific] Drop technical columns
        if 'box' in g_type.lower():
            # Explicitly drop technical columns if they exist
            drop_cols = ['log2_foldchange', 'p_value', 'expression_x', 'expression_y', 'x', 'y']
            cols_to_drop = [c for c in drop_cols if c in export_df.columns]
            if cols_to_drop:
                export_df.drop(columns=cols_to_drop, inplace=True)

        # [Heatmap Special] Export Matrix
        if 'heatmap' in g_type.lower() and hasattr(self, 'corr_matrix'):
            sheet1_data = round_floats(self.corr_matrix, 3)
        else:
            sheet1_data = round_floats(export_df, 3)

        data_packet = {
            "Data Analysis":sheet1_data
        }
        
        # Sheet 2: Hypothesis Testing (P-value etc.)
        if self.stats_results:
            import pandas as pd
            if isinstance(self.stats_results, list):
                stats_df = pd.DataFrame(self.stats_results)
            else:
                stats_df = pd.DataFrame([self.stats_results])
            
            # [Refined] P-values need more precision. 
            if not stats_df.empty:
                for col in stats_df.columns:
                    if 'p-value' in col.lower():
                        pass # Do not round P signals
                    else:
                        # Safety: check if col is numeric before rounding
                        if pd.api.types.is_numeric_dtype(stats_df[col]):
                            stats_df[col] = round_floats(stats_df[col], 4)
            data_packet["Hypothesis Test"] = stats_df
            
        # Sheet 3: Descriptive Stats (Mean, SD, Median, Quartiles)
        # [Fix] Only group by 'x' if it is a Box Plot (Categorical). 
        # scatter/volcano should be treated as global or customized.
        try:
            # Check for 'x' (Group) and 'y' (Value) - Standardized by BasePlugin
            # [Fix] Only group by 'x' if it is a Box Plot (Categorical). 
            # scatter/volcano should be treated as global or customized.
            is_categorical = 'box' in g_type.lower()
            stats_obj = None
            
            if is_categorical and 'x' in self.df.columns and 'y' in self.df.columns:
                 # Grouped Stats (for Boxplot)
                 # Describe 'y' grouped by 'x'
                 desc = self.df.groupby('x')['y'].describe()
                 desc.index.name = xlabel
                 data_packet["Descriptive Stats"] = round_floats(desc.reset_index(), 3)
            else:
                # Global Stats (for Scatter X/Y)
                cols = [c for c in self.df.columns if c in ['x', 'y', 'value']]
                if cols:
                    desc = self.df[cols].describe()
                    # Rename columns in the result: x->xlabel, y->ylabel
                    trans_map = {'x':xlabel, 'y':ylabel}
                    desc.rename(columns=trans_map,inplace=True)
                    data_packet["Descriptive Stats"] = round_floats(desc.reset_index(), 3)
                    
            if stats_obj is not None:
                data_packet["Descriptive Stats"] = round_floats(stats_obj, 3)

        except Exception as e:
            logger.warning(f"Descriptive stats calculation failed: {e}")
            
        # Save Bundle
        self.am.save_data(data_packet, f"{name} Data")

    def _stamp_audit(self):
        """
        Internal: Add RunID watermark to bottom right.
        Safety/Liability feature.
        """
        run_id = self.am.run_id
        github_url = "github.com/Mizuyuu0w0/BD-Core"
        
        # [Visual Logic] Smart Placement
        # If Title exists -> Footer (Bottom-Right, Below Axis) to avoid top collision.
        # If No Title -> Header (Top-Right, Inside Axis) for better visibility.
        
        has_title = bool(self.config.get('title'))
        
        if has_title:
             # Footer Mode
             # Use \n for two lines as requested
             text = f"RunID: {run_id} | BD-Core v1.0\n{github_url}"
             self.ax.text(1.0, -0.25, text, 
                          transform=self.ax.transAxes,
                          ha='right', va='top', 
                          fontsize=6, color='grey', alpha=0.8)
        else:
             # Header Mode (Original Top-Right)
             text = f"RunID: {run_id} | BD-Core v1.0\n{github_url}"
             props = dict(boxstyle='round', facecolor='white', alpha=0.8, linewidth=0)
             self.ax.text(0.99, 0.99, text, 
                          transform=self.ax.transAxes,
                          ha='right', va='top', 
                          fontsize=6, color='grey', bbox=props)

    def _apply_mapping(self):
        """
        [DSL Feature]
        Apply column mapping from config.
        Example: Independent Variable: {Time} -> Rename 'Time' to 'x'
        """
        mapping = self.config.get('_mapping', {})
        if not mapping:
            return

        # Helper: Try to find column with fuzzy matching (case-insensitive)
        def find_col(target):
            if target in self.df.columns:
                return target
            # Fallback: Look for normalized version (what cleaner.py produces)
            # cleaner logic: strip().lower().replace(' ','_')
            normalized = target.strip().lower().replace(' ','_')
            if normalized in self.df.columns:
                return normalized
            return None

        # 1. Map Independent Variable -> x
        if 'independent_variable' in mapping:
            target = mapping['independent_variable']
            found = find_col(target)
            if found:
                logger.info(f"Mapping column '{found}' (target: {target}) -> 'x'")
                self.df.rename(columns={found: 'x'}, inplace=True)
            else:
                 logger.warning(f"DSL Mapping Failed: Column '{target}' not found.")
        
        # 2. Map Dependent Variable -> y
        if 'dependent_variable' in mapping:
            target = mapping['dependent_variable']
            found = find_col(target)
            if found:
                logger.info(f"Mapping column '{found}' (target: {target}) -> 'y'")
                self.df.rename(columns={found: 'y'}, inplace=True)
            else:
                 logger.warning(f"DSL Mapping Failed: Column '{target}' not found.")
            