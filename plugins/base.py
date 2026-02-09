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
             subtype = self.config.get('subtype', self.config.get('heatmap_mode', 'correlation'))
             desc = "Expression Heatmap" if subtype == 'expression' else "Correlation Matrix"
             name = f"{g_type} Graph ({desc})"
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
        # Sheet 2: Hypothesis Testing (P-value etc.)
        # [Fix] Handle if stats_results is a DataFrame (Matrix) or Dict
        has_stats = False
        import pandas as pd # Import before use
        
        if isinstance(self.stats_results, pd.DataFrame):
             has_stats = not self.stats_results.empty
        else:
             has_stats = bool(self.stats_results)

        if has_stats:
            if isinstance(self.stats_results, list):
                stats_df = pd.DataFrame(self.stats_results)
            elif isinstance(self.stats_results, pd.DataFrame):
                 stats_df = self.stats_results
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
                # Global Stats
                # If 'x'/'y' exist (Scatter/Volcano), prioritize them.
                # If not (Heatmap), describe ALL numeric columns.
                cols = [c for c in self.df.columns if c in ['x', 'y', 'value']]
                if not cols: 
                    # Fallback for Heatmap or other multivariate plots
                    # Select only numeric columns to avoid errors
                    numeric_df = self.df.select_dtypes(include=['number'])
                    if not numeric_df.empty:
                        desc = numeric_df.describe().T
                        desc.index.name = "Variable"
                        data_packet["Descriptive Stats"] = round_floats(desc.reset_index(), 3)
                else:
                    # Standard X/Y Stats
                    desc = self.df[cols].describe().T
                    desc.index.name = "Variable"
                    # Transpose makes x,y the rows.
                    data_packet["Descriptive Stats"] = round_floats(desc.reset_index(), 3)
                    
            if stats_obj is not None:
                data_packet["Descriptive Stats"] = round_floats(stats_obj, 3)

            # [Publication Engine] Three-Line Table (Mean ± SEM)
            # We derive this from the descriptive stats we just calculated.
            if "Descriptive Stats" in data_packet:
                 ds = data_packet["Descriptive Stats"].copy()
                 
                 # Ensure we have mean, std, count (sometimes 'count' is 'N')
                 # Describe (pandas) produces: count, mean, std...
                 # We need to check columns. If grouped, index might be involved.
                 
                 # Normalizing column names to lowercase for checking
                 ds.columns = [c.lower() if isinstance(c, str) else c for c in ds.columns]
                 
                 # Calculate SEM = std / sqrt(count)
                 if 'std' in ds.columns and 'count' in ds.columns:
                     try:
                        import numpy as np
                        ds['sem'] = ds['std'] / np.sqrt(ds['count'])
                        
                        # Format "Mean ± SEM"
                        # Use .apply for row-wise formatting
                        def fmt_mean_sem(row):
                            m = row.get('mean', 0)
                            s = row.get('sem', 0)
                            return f"{m:.2f} ± {s:.2f}"
                        
                        ds['Mean ± SEM'] = ds.apply(fmt_mean_sem, axis=1)
                        
                        # Clean up for report
                        # Keep Index/Group columns and the new formatted column
                        keep_cols = [xlabel] if xlabel and xlabel.lower() in ds.columns else []
                        if 'x' in ds.columns: keep_cols.append('x')
                        if 'index' in ds.columns: keep_cols.append('index')
                        
                        keep_cols.append('Mean ± SEM')
                        keep_cols.extend(['count', 'mean', 'std', 'sem']) # Keep raw for validation
                        
                        # Filter existing keys
                        final_cols = [c for c in keep_cols if c in ds.columns]
                        report_df = ds[final_cols].copy()
                        
                        # [P-Value Starring]
                        # If Hypothesis Test exists, try to merge or list p-values
                        if "Hypothesis Test" in data_packet:
                            ht = data_packet["Hypothesis Test"]
                            
                            # Case A: Matrix (Correlation P-values)
                            # Check if index and columns match and are symmetric-ish
                            if ht.shape[0] == ht.shape[1] and ht.shape[0] > 1:
                                # Start logic for Matrix
                                def get_stars(p):
                                    if pd.isna(p): return ""
                                    if p < 0.001: return "***"
                                    if p < 0.01: return "**"
                                    if p < 0.05: return "*"
                                    return "ns"
                                
                                # Apply to entire dataframe
                                star_matrix = ht.map(get_stars)
                                # Save as separate sheet or append? 
                                # Let's save a new sheet "Significance Matrix"
                                data_packet["Significance Matrix"] = star_matrix
                            
                            # Case B: Table (Comparison | P-Value)
                            else:
                                # Naive check: look for 'p-value' or 'p_value' column
                                p_col = next((c for c in ht.columns if 'p' in c.lower() and 'val' in c.lower()), None)
                                if p_col:
                                    # Start logic
                                    def get_stars_row(p):
                                        if pd.isna(p): return "ns"
                                        if p < 0.001: return "***"
                                        if p < 0.01: return "**"
                                        if p < 0.05: return "*"
                                        return "ns"
                                    
                                    # Add stars column to Hypothesis Test DataFrame for reference
                                    ht['Significance'] = ht[p_col].apply(get_stars_row)
                                    data_packet["Hypothesis Test"] = ht # Update packet
                        
                        data_packet["Publication Report"] = report_df
                     except Exception as e:
                        logger.warning(f"Failed to generate Three-Line Table: {e}")

        except Exception as e:
            logger.warning(f"Descriptive stats calculation failed: {e}")
            
        # Save Bundle
        self.am.save_data(data_packet, f"{name} Data")

    def _stamp_audit(self):
        """
        Internal: Save RunID and Metadata to summary.txt instead of Watermark.
        [Nature-Standard Hygiene] No text on image.
        """
        try:
             # Create summary.txt content
             lines = [
                 "========================================",
                 f" BioData Analysis Report (v1.2)",
                 "========================================",
                 f"Run ID       : {self.am.run_id}",
                 f"Graph Type   : {self.config.get('graph', 'Unknown')}",
                 f"Subtype      : {self.config.get('subtype', 'Default')}",
                 f"Timestamp    : {self.am.timestamp}",
                 "----------------------------------------",
                 "Configuration Snapshot:",
                 str(self.config),
                 "----------------------------------------",
                 "Generated by BD-Core (github.com/Mizuyuu0w0/BD-Core)"
             ]
             
             # Save to sandbox using ArtifactManager
             # We reuse save_data logic or just write file directly if AM exposes path
             # AM.save_data typically saves structured data (Excel/CSV/JSON)
             # We'll use a raw write via the sandbox path if available, or ask AM to do it.
             # Since AM constructs paths, let's create a simple text artifact.
             
             # Using a small hack: pass a dict to save_data? No, save_data handles dicts as JSON/Excel.
             # Let's inspect AM later. For now, we can try to save it as a text file if AM supports checks.
             
             # Actually, let's just write to the sandbox root.
             # self.am.sandbox_dir should be available.
             import os
             summary_path = os.path.join(self.am.sandbox_dir, "summary.txt")
             with open(summary_path, "w", encoding='utf-8') as f:
                 f.write("\n".join(lines))
                 
             logger.info(f"Metadata saved to {summary_path}")
                 
        except Exception as e:
            logger.warning(f"Failed to save summary.txt: {e}")

        # [Restored] Visual Watermark (User Request)
        # We keep the summary.txt for detailed info, but put back the RunID on the plot.
        # Make it small and unobtrusive.
        run_id = self.am.run_id
        github_url = "github.com/Mizuyuu0w0/BD-Core"
        text = f"RunID: {run_id} | BD-Core v1.2\n{github_url}"
        
        # Smart Placement: Figure Bottom-Right (Global)
        # 1. Reserve footer space (Shift plots up)
        # This ensures the `0.01` y-coordinate is in empty white space, not over axes/labels.
        try:
            self.fig.subplots_adjust(bottom=0.15)
        except Exception:
            # Clustermap or complex layouts might ignore this or warn.
            # For Clustermap, we might need to rely on its internal layout or accept strict borders.
            # But usually fig.subplots_adjust works on the global figure figure.
            pass

        # 2. Place Text in the reserved footer
        self.fig.text(0.99, 0.01, text, 
                     ha='right', va='bottom', 
                     fontsize=5, color='grey', alpha=0.6)
        

    def _apply_mapping(self):
        """
        [DSL Feature]
        Apply column mapping from config.
        Example: Independent Variable: {Time} -> Rename 'Time' to 'x'
        """
        mapping = self.config.get('_mapping', {})
        
        # [Fix] Do NOT return early if mapping is empty. 
        # We need to fall back to xlabel/ylabel logic below.

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
        target_x = mapping.get('independent_variable')
        if not target_x:
            # Fallback: Check 'xlabel'
            target_x = self.config.get('xlabel')
        
        if target_x:
            found = find_col(target_x)
            if found:
                logger.info(f"Mapping column '{found}' (target: {target_x}) -> 'x'")
                self.df.rename(columns={found: 'x'}, inplace=True)
            else:
                 logger.warning(f"Mapping Failed: Column '{target_x}' not found for X-axis.")
        
        # 2. Map Dependent Variable -> y
        target_y = mapping.get('dependent_variable')
        if not target_y:
            # Fallback: Check 'ylabel'
            target_y = self.config.get('ylabel')

        if target_y:
            found = find_col(target_y)
            if found:
                logger.info(f"Mapping column '{found}' (target: {target_y}) -> 'y'")
                self.df.rename(columns={found: 'y'}, inplace=True)
            else:
                 logger.warning(f"Mapping Failed: Column '{target_y}' not found for Y-axis.")
            