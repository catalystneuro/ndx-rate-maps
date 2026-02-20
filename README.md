# ndx-rate-maps Extension for NWB

NWB extension for storing rate maps (spatial firing rate maps, tuning curves).

`RateMapTable` is a `DynamicTable` where each row holds a rate map for one unit. It supports both 1D tuning curves (e.g., head direction) and 2D spatial rate maps (e.g., place cells). All maps in a table share the same binning. For multiple conditions, create separate table instances.

## Installation

```bash
pip install ndx-rate-maps
```

For development:

```bash
git clone https://github.com/catalystneuro/ndx-rate-maps.git
cd ndx-rate-maps
pip install -e .
```

## Usage

### 2D spatial rate maps

```python
import numpy as np
from datetime import datetime
from zoneinfo import ZoneInfo
from pynwb import NWBFile, NWBHDF5IO
from pynwb.behavior import Position, SpatialSeries
from hdmf.common import DynamicTableRegion, VectorData
from ndx_rate_maps import RateMapTable

# Create NWBFile and add units
nwbfile = NWBFile(
    session_description="session",
    identifier="id",
    session_start_time=datetime.now(ZoneInfo("UTC")),
)
nwbfile.add_unit_column("location", "brain region")
for i in range(3):
    nwbfile.add_unit(spike_times=np.array([1.0, 2.0, 3.0]) + i, location="CA1")

# Create rate map table
num_units = 3
num_bins_x, num_bins_y = 50, 50

rate_maps = RateMapTable(
    name="place_rate_maps",
    description="2D spatial rate maps, 2cm bins, gaussian-smoothed",
    bin_edges_dim0=np.linspace(0, 100, num_bins_x + 1),  # x bin edges in cm
    bin_edges_dim1=np.linspace(0, 100, num_bins_y + 1),  # y bin edges in cm
    smoothing_kernel="gaussian",
    smoothing_kernel_width=3.0,  # in cm (same units as bin edges)
    units=DynamicTableRegion(
        name="units",
        data=list(range(num_units)),
        description="units for each rate map",
        table=nwbfile.units,
    ),
    rate_map=VectorData(
        name="rate_map",
        description="Rate map values in Hz",
        data=np.random.rand(num_units, num_bins_x, num_bins_y),
    ),
    occupancy_map=VectorData(
        name="occupancy_map",
        description="Time spent per bin in seconds",
        data=np.random.rand(num_units, num_bins_x, num_bins_y),
    ),
)

# Add to processing module
module = nwbfile.create_processing_module("behavior", "Behavioral data")
module.add(rate_maps)

# Write
with NWBHDF5IO("example.nwb", "w") as io:
    io.write(nwbfile)

# Read
with NWBHDF5IO("example.nwb", "r") as io:
    read_nwb = io.read()
    read_table = read_nwb.processing["behavior"]["place_rate_maps"]
    print(read_table.unit_of_measurement)  # "Hz"
    print(read_table["rate_map"][0].shape)  # (50, 50)
```

### 1D head direction tuning curves

```python
num_bins = 60

hd_maps = RateMapTable(
    name="hd_tuning_curves",
    description="Head direction tuning curves, 6-degree bins",
    bin_edges_dim0=np.linspace(0, 2 * np.pi, num_bins + 1),  # radians
    units=DynamicTableRegion(
        name="units",
        data=list(range(num_units)),
        description="units for each tuning curve",
        table=nwbfile.units,
    ),
    rate_map=VectorData(
        name="rate_map",
        description="Rate map values in Hz",
        data=np.random.rand(num_units, num_bins),
    ),
)
```

### Time support

Link the rate maps to the time intervals over which they were computed:

```python
from pynwb.epoch import TimeIntervals

# Create intervals for the run epochs used to compute rate maps
time_support = TimeIntervals(name="time_support", description="run epochs")
time_support.add_interval(start_time=0.0, stop_time=120.0)
time_support.add_interval(start_time=200.0, stop_time=350.0)

module.add(time_support)

rate_maps.time_support = time_support
```

This also works with `nwbfile.trials`, `nwbfile.epochs`, or any `TimeIntervals` table.

### Multiple conditions

Create separate tables for each condition:

```python
left_trials = RateMapTable(
    name="rate_maps_left_trials",
    description="Rate maps for left-choice trials",
    # ... same structure as above
)
right_trials = RateMapTable(
    name="rate_maps_right_trials",
    description="Rate maps for right-choice trials",
    # ... same structure as above
)
```

## Schema

### `RateMapTable` (extends `DynamicTable`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `unit_of_measurement` | text (fixed: "Hz") | Yes | Unit for rate values |
| `smoothing_kernel` | text | No | Smoothing kernel type (e.g., "gaussian") |
| `smoothing_kernel_width` | float64 | No | Kernel width, in same units as bin edges |
| `bin_edges_dim0` | float64 array | Yes | Bin edges along first dimension |
| `bin_edges_dim1` | float64 array | No | Bin edges along second dimension (2D only) |
| `units` | DynamicTableRegion | Yes | Reference to Units table |
| `rate_map` | VectorData (float64) | Yes | Rate map values in Hz |
| `occupancy_map` | VectorData (float64) | No | Time spent per bin in seconds |
| `spike_count_map` | VectorData (float64) | No | Spike count per bin |
| `source_timeseries` | link to TimeSeries | No | Source behavioral timeseries |
| `time_support` | link to TimeIntervals | No | Time intervals over which rate maps were computed |

---
This extension was created using [ndx-template](https://github.com/nwb-extensions/ndx-template).
