# -*- coding: utf-8 -*-
from pathlib import Path

from pynwb.spec import (
    NWBNamespaceBuilder,
    NWBGroupSpec,
    NWBDatasetSpec,
    NWBAttributeSpec,
    NWBLinkSpec,
    export_spec,
)


def main():
    ns_builder = NWBNamespaceBuilder(
        name="""ndx-rate-maps""",
        version="""0.1.0""",
        doc="""NWB extension for storing rate maps (spatial firing rate maps, tuning curves)""",
        author=[
            "Ben Dichter",
        ],
        contact=[
            "ben.dichter@catalystneuro.com",
        ],
    )

    ns_builder.include_type("DynamicTable", namespace="hdmf-common")
    ns_builder.include_type("DynamicTableRegion", namespace="hdmf-common")
    ns_builder.include_type("VectorData", namespace="hdmf-common")
    ns_builder.include_type("TimeSeries", namespace="core")
    ns_builder.include_type("TimeIntervals", namespace="core")

    rate_map_table = NWBGroupSpec(
        neurodata_type_def="RateMapTable",
        neurodata_type_inc="DynamicTable",
        doc=(
            "A table storing rate maps (spatial firing rate maps or tuning curves). "
            "Each row corresponds to a unit. All rate maps in a table share the same "
            "binning. For multiple conditions, create separate table instances."
        ),
        attributes=[
            NWBAttributeSpec(
                name="unit_of_measurement",
                dtype="text",
                value="Hz",
                doc="Unit for rate map values (always Hz)",
            ),
            NWBAttributeSpec(
                name="smoothing_kernel",
                dtype="text",
                doc="Type of smoothing kernel applied (e.g., 'gaussian', 'box')",
                required=False,
            ),
            NWBAttributeSpec(
                name="smoothing_kernel_width",
                dtype="float64",
                doc="Width/sigma of the smoothing kernel, in the same units as bin_edges",
                required=False,
            ),
        ],
        datasets=[
            # Non-column datasets: shared bin edges
            NWBDatasetSpec(
                name="bin_edges_dim0",
                dtype="float64",
                shape=(None,),
                dims=("num_bins_dim0_plus_1",),
                doc="Bin edges along the first dimension (length = num_bins + 1)",
            ),
            NWBDatasetSpec(
                name="bin_edges_dim1",
                dtype="float64",
                shape=(None,),
                dims=("num_bins_dim1_plus_1",),
                doc=(
                    "Bin edges along the second dimension (length = num_bins + 1). "
                    "Only present for 2D rate maps."
                ),
                quantity="?",
            ),
            # Columns
            NWBDatasetSpec(
                name="units",
                neurodata_type_inc="DynamicTableRegion",
                doc="Reference to the units in the Units table that correspond to each row",
            ),
            NWBDatasetSpec(
                name="rate_map",
                neurodata_type_inc="VectorData",
                dtype="float64",
                doc=(
                    "Rate map values in Hz. Shape per row is (num_bins,) for 1D maps "
                    "or (num_bins_x, num_bins_y) for 2D maps."
                ),
            ),
            NWBDatasetSpec(
                name="occupancy_map",
                neurodata_type_inc="VectorData",
                dtype="float64",
                doc="Time spent per bin in seconds. Same shape as rate_map.",
                quantity="?",
            ),
            NWBDatasetSpec(
                name="spike_count_map",
                neurodata_type_inc="VectorData",
                dtype="float64",
                doc="Number of spikes per bin. Same shape as rate_map.",
                quantity="?",
            ),
        ],
        links=[
            NWBLinkSpec(
                name="source_timeseries",
                target_type="TimeSeries",
                doc="Source behavioral timeseries (e.g., position data)",
                quantity="?",
            ),
            NWBLinkSpec(
                name="time_support",
                target_type="TimeIntervals",
                doc=(
                    "Time intervals over which these rate maps were computed "
                    "(e.g., trials, epochs, or custom intervals)"
                ),
                quantity="?",
            ),
        ],
    )

    new_data_types = [rate_map_table]

    output_dir = str((Path(__file__).parent.parent.parent / "spec").absolute())
    export_spec(ns_builder, new_data_types, output_dir)


if __name__ == "__main__":
    main()
