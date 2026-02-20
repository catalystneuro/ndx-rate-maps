from pynwb import register_class, TimeSeries
from hdmf.common import DynamicTable, DynamicTableRegion, VectorData, ElementIdentifiers
from hdmf.utils import docval, popargs

NS = "ndx-rate-maps"


@register_class("RateMapTable", NS)
class RateMapTable(DynamicTable):
    """A table storing rate maps (spatial firing rate maps or tuning curves).

    Each row corresponds to a unit. All rate maps in a table share the same
    binning. For multiple conditions, create separate table instances.
    """

    __nwbfields__ = (
        "bin_edges_dim0",
        "bin_edges_dim1",
        "smoothing_kernel",
        "smoothing_kernel_width",
        {"name": "source_timeseries", "required_name": "source_timeseries"},
    )

    @docval(
        {"name": "name", "type": str, "doc": "Name of this rate map table"},
        {"name": "description", "type": str, "doc": "Description of this rate map table"},
        {
            "name": "bin_edges_dim0",
            "type": "array_data",
            "doc": "Bin edges along the first dimension (length = num_bins + 1)",
            "default": None,
        },
        {
            "name": "units",
            "type": DynamicTableRegion,
            "doc": "Reference to the units in the Units table that correspond to each row",
            "default": None,
        },
        {
            "name": "rate_map",
            "type": VectorData,
            "doc": "Rate map values in Hz",
            "default": None,
        },
        {
            "name": "bin_edges_dim1",
            "type": "array_data",
            "doc": "Bin edges along the second dimension (for 2D maps)",
            "default": None,
        },
        {
            "name": "occupancy_map",
            "type": VectorData,
            "doc": "Time spent per bin in seconds",
            "default": None,
        },
        {
            "name": "spike_count_map",
            "type": VectorData,
            "doc": "Number of spikes per bin",
            "default": None,
        },
        {
            "name": "source_timeseries",
            "type": TimeSeries,
            "doc": "Source behavioral timeseries (e.g., position data)",
            "default": None,
        },
        {
            "name": "smoothing_kernel",
            "type": str,
            "doc": "Type of smoothing kernel applied (e.g., 'gaussian', 'box')",
            "default": None,
        },
        {
            "name": "smoothing_kernel_width",
            "type": float,
            "doc": "Width/sigma of the smoothing kernel, in the same units as bin_edges",
            "default": None,
        },
        {
            "name": "id",
            "type": ("array_data", ElementIdentifiers),
            "doc": "Row IDs",
            "default": None,
        },
        {
            "name": "columns",
            "type": (list, tuple),
            "doc": "Columns for this table (used during read)",
            "default": None,
        },
        {
            "name": "colnames",
            "type": ("scalar_data", list, tuple, "array_data"),
            "doc": "Column names (used during read)",
            "default": None,
        },
        allow_extra=True,
    )
    def __init__(self, **kwargs):
        bin_edges_dim0, bin_edges_dim1 = popargs("bin_edges_dim0", "bin_edges_dim1", kwargs)
        smoothing_kernel, smoothing_kernel_width = popargs(
            "smoothing_kernel", "smoothing_kernel_width", kwargs
        )
        source_timeseries = popargs("source_timeseries", kwargs)
        units, rate_map = popargs("units", "rate_map", kwargs)
        occupancy_map, spike_count_map = popargs("occupancy_map", "spike_count_map", kwargs)
        kwargs.pop("unit_of_measurement", None)  # fixed value from spec, discard

        # Build columns list from individual args (user construction path)
        # During read, columns is already populated by the ObjectMapper
        columns = kwargs.get("columns")
        if columns is None and rate_map is not None:
            columns = []
            if units is not None:
                columns.append(units)
            columns.append(rate_map)
            if occupancy_map is not None:
                columns.append(occupancy_map)
            if spike_count_map is not None:
                columns.append(spike_count_map)
            kwargs["columns"] = columns

        super().__init__(**kwargs)

        # Set None for optional columns that weren't provided,
        # so the ObjectMapper can find the attribute during build
        colnames = self.colnames if self.colnames is not None else []
        if "occupancy_map" not in colnames:
            self.occupancy_map = None
        if "spike_count_map" not in colnames:
            self.spike_count_map = None

        self.bin_edges_dim0 = bin_edges_dim0
        self.bin_edges_dim1 = bin_edges_dim1
        self.smoothing_kernel = smoothing_kernel
        self.smoothing_kernel_width = smoothing_kernel_width
        self.source_timeseries = source_timeseries

    @property
    def unit_of_measurement(self):
        return "Hz"
