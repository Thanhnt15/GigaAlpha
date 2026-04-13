import pandas as pd
import os
import logging
from typing import List

logger = logging.getLogger(__name__)


def plot_sharpe_surface(df: pd.DataFrame, title: str, target_cols: List[str],
                        colors: List[str], output_path: str) -> None:
    """Vẽ Sharpe Surface 3D và lưu ra file HTML."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    z_col, x_col, y_col = target_cols

    df_plot = df.copy()
    df_plot[z_col] = pd.to_numeric(df_plot[z_col], errors='coerce')
    df_plot = df_plot.dropna(subset=[z_col, x_col, y_col])

    pivot_df = df_plot.pivot_table(index=y_col, columns=x_col, values=z_col, aggfunc='mean')

    custom_colorscale = [
        [0.0, colors[0]], [0.25, colors[1]], [0.5, colors[2]], [0.75, colors[3]], [1.0, colors[4]]
    ]

    total = len(df_plot)
    get_val = lambda v: f"{(len(df_plot[df_plot[z_col] > v]) / total * 100):.2f}"

    metrics_values = [
        ['Total Configurations', f"{total}"],
        [f'{z_col} > 0 (%)', get_val(0)],
        [f'{z_col} > 1 (%)', get_val(1)],
        [f'{z_col} > 2 (%)', get_val(2)],
        [f'{z_col} > 3 (%)', get_val(3)],
        ['Avg TVR', f"{df_plot['tvr'].mean():.2f}"]
    ]

    fig = make_subplots(
        rows=2, cols=2,
        column_widths=[0.7, 0.3],
        row_heights=[0.4, 0.6],
        specs=[[{"type": "scene", "rowspan": 2}, {"type": "table"}],
                [None, {"type": "table"}]],
        horizontal_spacing=0.05, vertical_spacing=0.05
    )

    fig.add_trace(
        go.Surface(
            z=pivot_df.values, x=pivot_df.columns, y=pivot_df.index,
            colorscale=custom_colorscale,
            colorbar=dict(title=z_col.upper(), x=0.62, thickness=20),
            hovertemplate=(
                f"<b>{x_col}</b>: %{{x}}<br>" +
                f"<b>{y_col}</b>: %{{y}}<br>" +
                f"<b>{z_col}</b>: %{{z:.3f}}<extra></extra>"
            ),
            contours={
                "x": {"highlight": True, "highlightcolor": "#00e5ff", "width": 4},
                "y": {"highlight": True, "highlightcolor": "#ff007f", "width": 4},
                "z": {"highlight": True, "highlightcolor": "#ffff00", "width": 4}
            }
        ),
        row=1, col=1
    )

    legend_labels = [f'{z_col} > 3.0', f'2.0 < {z_col} < 3.0', f'1.0 < {z_col} < 2.0', f'0.0 < {z_col} < 1.0', 'Negative < 0.0']
    legend_colors = [colors[4], colors[3], colors[2], colors[1], colors[0]]

    fig.add_trace(
        go.Table(
            header=dict(values=['<b>Legend</b>', '<b>Color</b>'], fill_color='#1a1c24', align='left', font=dict(color='white', size=14)),
            cells=dict(values=[legend_labels, [''] * 5], fill_color=[['#1a1c24'] * 5, legend_colors], align='left', height=30)
        ),
        row=1, col=2
    )

    fig.add_trace(
        go.Table(
            header=dict(values=['<b>Metric</b>', '<b>Value</b>'], fill_color='#1a1c24', align='left', font=dict(color='white', size=14)),
            cells=dict(values=list(zip(*metrics_values)), fill_color='#1a1c24', align='left', font=dict(color='white', size=13), height=35)
        ),
        row=2, col=2
    )

    fig.update_layout(
        title=title,
        template="plotly_dark",
        paper_bgcolor='#0a0f1e', plot_bgcolor='#0a0f1e',
        width=1500, height=850,
        scene=dict(
            xaxis_title=x_col, yaxis_title=y_col, zaxis_title=z_col,
            xaxis=dict(showspikes=True, spikecolor="#00e5ff", spikethickness=6, spikesides=True),
            yaxis=dict(showspikes=True, spikecolor="#ff007f", spikethickness=6, spikesides=True),
            zaxis=dict(showspikes=True, spikecolor="#ffff00", spikethickness=6, spikesides=True),
            camera=dict(eye=dict(x=1.6, y=1.6, z=1.0)),
            aspectratio=dict(x=1, y=1, z=0.6)
        ),
        margin=dict(l=20, r=20, b=20, t=60)
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.write_html(output_path)
    logger.info(f"Chart saved: {output_path}")


def plot_pnl_and_mdd(df: pd.DataFrame, col_pnl: str, col_mdd: str, title: str, output_path: str):
    pass

    