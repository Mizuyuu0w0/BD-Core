import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
from plugins.base import BasePlugin

class HeatmapPlugin(BasePlugin):
    """
    Heatmap: Supports 'correlation' (default) and 'expression' modes.
    """
    def validate_data(self):
        self.numeric_cols = self.df.select_dtypes(include=['number']).columns
        if len(self.numeric_cols) < 2:
            raise ValueError("Heatmap requires at least 2 numeric columns.")

    def compute_stats(self):
        # [Sanitization v1.2] Clean Dataframe IMMEDIATELY
        # Strip whitespace/newlines AND internal newlines (e.g. from Excel copy-paste)
        try:
            self.df.index = self.df.index.astype(str).str.replace(r'[\r\n\t]', '', regex=True).str.strip()
            self.df.columns = self.df.columns.astype(str).str.replace(r'[\r\n\t]', '', regex=True).str.strip()
        except Exception:
            pass 

        # 1. Determine columns to use
        if self.config.get('selected_columns'):
            # Also clean the user's requested columns to match the clean DF
            cols_to_use = [str(c).replace('\r','').replace('\n','').replace('\t','').strip() for c in self.config['selected_columns']]
        else:
            # Fallback
            cols_to_use = [c for c in self.numeric_cols if c not in ['x','y']]

        # [Fix] Case-insensitive matching for columns
        clean_cols = [c.lower() for c in self.df.columns]
        self.valid_cols = []
        for user_col in cols_to_use:
            # Try exact match
            if user_col in self.df.columns:
                self.valid_cols.append(user_col)
            # Try lower match
            elif user_col.lower() in clean_cols:
                 idx = clean_cols.index(user_col.lower())
                 self.valid_cols.append(self.df.columns[idx])
        
        # Get subtype (default to correlation if missing)
        self.subtype = self.config.get('subtype', self.config.get('heatmap_mode', 'correlation'))
        # 2. Compute Data based on Subtype
        if self.subtype == 'correlation':
            # Mode A: Correlation Matrix (Values -1 to 1)
            self.heatmap_data = self.df[self.valid_cols].corr()
            
            # [Statistics] Calculate P-values for Correlation
            # We need a dataframe of p-values matching the corr matrix
            import scipy.stats as stats
            df_corr = self.heatmap_data
            p_values = pd.DataFrame(index=df_corr.index, columns=df_corr.columns, dtype=float)
            
            # Efficiently calculate pairwise p-values
            # Note: This is O(N^2), might be slow for huge N, but N=50 is fine.
            data_values = self.df[self.valid_cols].dropna() 
            
            for c1 in df_corr.columns:
                for c2 in df_corr.columns:
                     if c1 == c2:
                         p_values.loc[c1, c2] = 0.0 # Identity
                     else:
                         # Pearsonr returns (r, p)
                         try:
                            _, p = stats.pearsonr(data_values[c1], data_values[c2])
                            p_values.loc[c1, c2] = p
                         except:
                            p_values.loc[c1, c2] = np.nan
                            
            # Store for BasePlugin to save/star
            # We flatten it or keep it as matrix? BasePlugin expects list of dicts or DataFrame.
            # BasePlugin.save_artifacts -> stats_df = pd.DataFrame(self.stats_results)
            # If we pass the P-value matrix, it will be saved as "Hypothesis Test".
            # But the starring logic looks for "p-value" column. 
            # Actually, standard logic expects a table like: Comparison | P-Value
            # For a matrix, maybe we save the matrix itself?
            
            # Let's save the P-Value Matrix as "Hypothesis Test" sheet.
            # But the starring logic in BasePlugin (lines 235+) looks for a SINGLE 'p-value' column.
            # So the starred "Three-Line Table" won't work automatically for a matrix.
            # However, saving the P-values is what the user asked for ("p is gone").
            
            self.stats_results = p_values # This will be saved as Sheet 2.
            
        else:
            # Mode B: Expression Matrix (Raw Values)
            self.heatmap_data = self.df[self.valid_cols]
            # No simple p-value for raw expression without defined groups.
            self.stats_results = {} # Clear previous if any
            
    def plot(self):
        # 3. Configure Plot
        # [Nature Standard]
        # Correlation: Centered at 0, Diverging (RdBu_r), Square
        # Expression: Sequential (Viridis), Rectangular, Z-Score (Optional)
        
        data = self.heatmap_data
        
        if self.subtype == 'correlation':
            cmap = "RdBu_r"
            center = 0
            # Correlation matrix is typically square
            z_score = None 
            metric = 'euclidean'
            method = 'average'
        else: # expression
            cmap = "viridis" 
            center = None
            # [Z-Score Normalization]
            # 0 = Rows (Genes), 1 = Cols (Samples). Default to None.
            z_score = self.config.get('z_score', None) 
            metric = 'euclidean'
            method = 'average'

        # [Clustermap Upgrade]
        # sns.clustermap creates its own Figure/Axes grid.
        # We must attach it to self.fig if possible, or handle the figure object it returns.
        
        # Close the base-class created figure since Clustermap makes a new one
        plt.close(self.fig) 
        
        try:
            # Handle NaN safely (Clustermap crashes on NaN)
            if data.isnull().values.any():
                data = data.fillna(0) # Simple fallback

            # [Clustering Control]
            # Default to True (Nature standard). User can opt-out to preserve order.
            do_cluster = self.config.get('cluster', True)
            
            self.cluster_grid = sns.clustermap(
                data,
                cmap=cmap,
                center=center,
                z_score=z_score,
                metric=metric,
                method=method,
                figsize=(10, 8), # Default size
                dendrogram_ratio=(.1 if do_cluster else 0, .2 if do_cluster else 0),
                cbar_pos=(0.02, 0.8, 0.03, 0.18), # Move colorbar to left
                col_cluster=do_cluster,
                row_cluster=do_cluster
            )
            
            # Re-assign self.fig and self.ax for downstream saving/stamping
            self.fig = self.cluster_grid.fig
            self.ax = self.cluster_grid.ax_heatmap 
            
            # [Clean Up] Remove Axis Labels if too crowded
            if len(data.index) > 50:
                 self.ax.set_yticklabels([])
                 self.ax.set_ylabel("")
            if len(data.columns) > 50:
                 self.ax.set_xticklabels([])
                 self.ax.set_xlabel("")

        except Exception as e:
            # Fallback to standard Heatmap if clustering fails (e.g. single row/col)
            # logger.warning(f"Clustermap failed ({e}), falling back to standard Heatmap.")
            self.fig, self.ax = plt.subplots(figsize=(8, 6))
            
            # Recalculate basic params for fallback
            annot = True if len(data) < 20 else False
            square = True if self.subtype == 'correlation' else False
            
            sns.heatmap(
                data, 
                cmap=cmap, 
                center=center, 
                annot=annot,
                square=square,
                fmt=".2f",
                ax=self.ax
            )