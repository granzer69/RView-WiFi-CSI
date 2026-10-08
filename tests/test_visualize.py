from pathlib import Path

import numpy as np

from csi.visualize import save_amplitude_plot, save_heatmap
from ingestion.schema import CsiWindow


def test_plots_are_written(tmp_path: Path):
    window = CsiWindow(
        amplitude=np.arange(40, dtype=np.float64).reshape(10, 4),
        phase=None,
        sample_rate_hz=None,
        timestamp=None,
        subcarriers=4,
        antennas=None,
        metadata={"session_id": "1-1-1-1", "normalized_label": "running"},
    )
    amplitude = tmp_path / "amplitude.png"
    heatmap = tmp_path / "heatmap.png"
    save_amplitude_plot(window, amplitude)
    save_heatmap(window, heatmap)
    assert amplitude.stat().st_size > 0
    assert heatmap.stat().st_size > 0
