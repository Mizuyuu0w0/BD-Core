import matplotlib.pyplot as plt 
import matplotlib as m 
import logging

logger = logging.getLogger(__name__)

class NatureStyler:
    """
    Nature/Science Publication Style Enforcer.
    
    Philosophy:
    "Zero Configuration."
    Users don't get to choose fonts or sizes. We choose the best defaults for them.
    Reference: Nature Guide to Authors (Final artwork formatting).
    """
    @staticmethod
    def apply():
        """
        Enforces Nature/Science publication standards.
        Strict typography (Arial), thin lines, and minimalist layout.
        """
        logger.info("Applying Nature Publication Style Standards")

        # 1. Font Strategy: Arial is King.
        # Fallback to Helvetica -> sans-serif if Arial is missing.
        plt.rcParams.update({
            # --- 1. Typography (Arial is King) ---
            'font.family': 'sans-serif',
            'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
            'font.size': 8,           # Main text (7-8pt is standard)
            'axes.labelsize': 8,      # X/Y Axis Labels
            'axes.titlesize': 8,      # Subplot Titles (Bold usually)
            'xtick.labelsize': 7,     # Tick numbers
            'ytick.labelsize': 7,
            'legend.fontsize': 6,     # Legend text (smaller)
            
            # --- 2. Lines & Spines (Minimalism) ---
            'axes.linewidth': 0.5,    # Axis lines (thin)
            'grid.linewidth': 0.5,    # Grid lines (very thin, if used)
            'lines.linewidth': 1.0,   # Plot lines
            'lines.markersize': 3,    # Scatter points
            
            # --- 3. Layout (Tufte Style) ---
            'axes.spines.top': False,    # Remove top border (Chartjunk)
            'axes.spines.right': False,  # Remove right border
            'xtick.direction': 'out',    # Ticks point outwards
            'ytick.direction': 'out',
            
            # --- 4. Output Quality ---
            'figure.dpi': 300,           # High Res for Preview
            'savefig.dpi': 300,
            'savefig.bbox': 'tight',     # No whitespace
            'savefig.pad_inches': 0.1,
            'pdf.fonttype': 3            # Type 3 (Standard) to avoid TTF subsetting corruption
        })

        logger.debug("Style constraints applied successfully.")