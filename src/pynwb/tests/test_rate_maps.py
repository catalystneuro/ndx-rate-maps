from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
from numpy.testing import assert_array_equal
from pynwb import NWBFile, NWBHDF5IO
from pynwb.behavior import Position, SpatialSeries
from pynwb.epoch import TimeIntervals
from pynwb.testing import TestCase
from hdmf.common import DynamicTableRegion, VectorData

from ndx_rate_maps import RateMapTable


def _make_nwbfile():
    """Create an NWBFile with a Units table for testing."""
    nwbfile = NWBFile(
        session_description="test session",
        identifier="test_id",
        session_start_time=datetime.now(ZoneInfo("UTC")),
    )
    # Add units
    nwbfile.add_unit_column("location", "brain region")
    for i in range(5):
        nwbfile.add_unit(spike_times=np.array([1.0, 2.0, 3.0]) + i, location="CA1")
    return nwbfile


def _make_rate_map_table_2d(nwbfile, name="place_rate_maps"):
    """Create a 2D RateMapTable for testing."""
    num_units = 3
    num_bins_x, num_bins_y = 10, 12

    units_region = DynamicTableRegion(
        name="units",
        data=[0, 1, 2],
        description="units for each rate map",
        table=nwbfile.units,
    )
    rate_map_data = VectorData(
        name="rate_map",
        description="Rate map values in Hz",
        data=np.random.rand(num_units, num_bins_x, num_bins_y),
    )
    occupancy_data = VectorData(
        name="occupancy_map",
        description="Time spent per bin in seconds",
        data=np.random.rand(num_units, num_bins_x, num_bins_y),
    )
    spike_count_data = VectorData(
        name="spike_count_map",
        description="Number of spikes per bin",
        data=np.random.randint(0, 100, (num_units, num_bins_x, num_bins_y)).astype("float64"),
    )

    return RateMapTable(
        name=name,
        description="2D spatial rate maps, 5cm bins, gaussian-smoothed",
        bin_edges_dim0=np.linspace(0, 50, num_bins_x + 1),
        dim0_label="x_position",
        dim0_unit="cm",
        bin_edges_dim1=np.linspace(0, 60, num_bins_y + 1),
        dim1_label="y_position",
        dim1_unit="cm",
        units=units_region,
        rate_map=rate_map_data,
        occupancy_map=occupancy_data,
        spike_count_map=spike_count_data,
        smoothing_kernel="gaussian",
        smoothing_kernel_width=3.0,
    )


def _make_rate_map_table_1d(nwbfile, name="hd_tuning_curves"):
    """Create a 1D RateMapTable for testing."""
    num_units = 3
    num_bins = 60

    units_region = DynamicTableRegion(
        name="units",
        data=[0, 1, 2],
        description="units for each rate map",
        table=nwbfile.units,
    )
    rate_map_data = VectorData(
        name="rate_map",
        description="Rate map values in Hz",
        data=np.random.rand(num_units, num_bins),
    )

    return RateMapTable(
        name=name,
        description="Head direction tuning curves, 6-degree bins",
        bin_edges_dim0=np.linspace(0, 2 * np.pi, num_bins + 1),
        dim0_label="head_direction",
        dim0_unit="radians",
        units=units_region,
        rate_map=rate_map_data,
    )


class TestRateMapTableConstructor(TestCase):
    """Test RateMapTable constructor."""

    def test_init_2d_all_fields(self):
        """Test construction of a 2D rate map table with all fields."""
        nwbfile = _make_nwbfile()
        table = _make_rate_map_table_2d(nwbfile)

        assert table.name == "place_rate_maps"
        assert table.description == "2D spatial rate maps, 5cm bins, gaussian-smoothed"
        assert len(table) == 3
        assert table.smoothing_kernel == "gaussian"
        assert table.smoothing_kernel_width == 3.0
        assert table.dim0_label == "x_position"
        assert table.dim0_unit == "cm"
        assert table.dim1_label == "y_position"
        assert table.dim1_unit == "cm"
        assert_array_equal(table.bin_edges_dim0, np.linspace(0, 50, 11))
        assert_array_equal(table.bin_edges_dim1, np.linspace(0, 60, 13))

    def test_init_1d_minimal(self):
        """Test construction of a 1D rate map table with only required fields."""
        nwbfile = _make_nwbfile()
        table = _make_rate_map_table_1d(nwbfile)

        assert table.name == "hd_tuning_curves"
        assert len(table) == 3
        assert table.dim0_label == "head_direction"
        assert table.dim0_unit == "radians"
        assert table.bin_edges_dim1 is None
        assert table.dim1_label is None
        assert table.dim1_unit is None

    def test_unit_of_measurement_is_hz(self):
        """Test that unit_of_measurement is always Hz."""
        nwbfile = _make_nwbfile()
        table = _make_rate_map_table_1d(nwbfile)
        assert table.unit_of_measurement == "Hz"


class TestRateMapTableValidation(TestCase):
    """Test RateMapTable dimensionality validation."""

    def test_2d_rate_map_with_1d_bin_edges_raises(self):
        """Providing 2D rate maps without bin_edges_dim1 should raise."""
        nwbfile = _make_nwbfile()
        with self.assertRaises(ValueError):
            RateMapTable(
                name="bad",
                description="bad",
                bin_edges_dim0=np.linspace(0, 50, 11),
                dim0_label="x_position",
                dim0_unit="cm",
                units=DynamicTableRegion(
                    name="units", data=[0, 1, 2],
                    description="units", table=nwbfile.units,
                ),
                rate_map=VectorData(
                    name="rate_map", description="rate map",
                    data=np.random.rand(3, 10, 12),  # 2D maps
                ),
            )

    def test_1d_rate_map_with_2d_bin_edges_raises(self):
        """Providing 1D rate maps with bin_edges_dim1 should raise."""
        nwbfile = _make_nwbfile()
        with self.assertRaises(ValueError):
            RateMapTable(
                name="bad",
                description="bad",
                bin_edges_dim0=np.linspace(0, 50, 11),
                dim0_label="x_position",
                dim0_unit="cm",
                bin_edges_dim1=np.linspace(0, 60, 13),
                dim1_label="y_position",
                dim1_unit="cm",
                units=DynamicTableRegion(
                    name="units", data=[0, 1, 2],
                    description="units", table=nwbfile.units,
                ),
                rate_map=VectorData(
                    name="rate_map", description="rate map",
                    data=np.random.rand(3, 10),  # 1D maps
                ),
            )

    def test_2d_occupancy_map_mismatch_raises(self):
        """Providing 1D occupancy_map with 2D bin_edges should raise."""
        nwbfile = _make_nwbfile()
        with self.assertRaises(ValueError):
            RateMapTable(
                name="bad",
                description="bad",
                bin_edges_dim0=np.linspace(0, 50, 11),
                dim0_label="x_position",
                dim0_unit="cm",
                bin_edges_dim1=np.linspace(0, 60, 13),
                dim1_label="y_position",
                dim1_unit="cm",
                units=DynamicTableRegion(
                    name="units", data=[0, 1, 2],
                    description="units", table=nwbfile.units,
                ),
                rate_map=VectorData(
                    name="rate_map", description="rate map",
                    data=np.random.rand(3, 10, 12),
                ),
                occupancy_map=VectorData(
                    name="occupancy_map", description="occupancy",
                    data=np.random.rand(3, 10),  # wrong: 1D
                ),
            )


class TestRateMapTableRoundTrip2D(TestCase):
    """Test round-trip for 2D RateMapTable."""

    def test_roundtrip_2d(self):
        """Write and read back a 2D rate map table."""
        nwbfile = _make_nwbfile()
        table = _make_rate_map_table_2d(nwbfile)

        module = nwbfile.create_processing_module("behavior", "Behavioral data")
        module.add(table)

        with NWBHDF5IO("test_2d.nwb", "w") as io:
            io.write(nwbfile)

        with NWBHDF5IO("test_2d.nwb", "r") as io:
            read_nwb = io.read()
            read_table = read_nwb.processing["behavior"]["place_rate_maps"]

            assert isinstance(read_table, RateMapTable)
            assert len(read_table) == 3
            assert read_table.unit_of_measurement == "Hz"
            assert read_table.smoothing_kernel == "gaussian"
            assert read_table.smoothing_kernel_width == 3.0
            assert read_table.dim0_label == "x_position"
            assert read_table.dim0_unit == "cm"
            assert read_table.dim1_label == "y_position"
            assert read_table.dim1_unit == "cm"
            assert_array_equal(read_table.bin_edges_dim0[:], table.bin_edges_dim0)
            assert_array_equal(read_table.bin_edges_dim1[:], table.bin_edges_dim1)
            assert_array_equal(read_table["rate_map"][0], table["rate_map"][0])
            assert_array_equal(read_table["occupancy_map"][0], table["occupancy_map"][0])
            assert_array_equal(read_table["spike_count_map"][0], table["spike_count_map"][0])

        import os
        os.remove("test_2d.nwb")

    def test_roundtrip_2d_with_source_timeseries(self):
        """Write and read back with a source_timeseries link."""
        nwbfile = _make_nwbfile()
        table = _make_rate_map_table_2d(nwbfile)

        position = Position(name="position")
        spatial_series = SpatialSeries(
            name="animal_position",
            data=np.random.rand(100, 2),
            timestamps=np.linspace(0, 10, 100),
            reference_frame="top-left corner of arena",
        )
        position.add_spatial_series(spatial_series)

        module = nwbfile.create_processing_module("behavior", "Behavioral data")
        module.add(position)

        table.source_timeseries = spatial_series
        module.add(table)

        with NWBHDF5IO("test_2d_ts.nwb", "w") as io:
            io.write(nwbfile)

        with NWBHDF5IO("test_2d_ts.nwb", "r") as io:
            read_nwb = io.read()
            read_table = read_nwb.processing["behavior"]["place_rate_maps"]
            assert read_table.source_timeseries is not None
            assert read_table.source_timeseries.name == "animal_position"

        import os
        os.remove("test_2d_ts.nwb")

    def test_roundtrip_2d_with_time_support(self):
        """Write and read back with a time_support link."""
        nwbfile = _make_nwbfile()
        table = _make_rate_map_table_2d(nwbfile)

        # Create time intervals
        time_support = TimeIntervals(name="time_support", description="run epochs")
        time_support.add_interval(start_time=0.0, stop_time=5.0)
        time_support.add_interval(start_time=10.0, stop_time=15.0)

        module = nwbfile.create_processing_module("behavior", "Behavioral data")
        module.add(time_support)

        table.time_support = time_support
        module.add(table)

        with NWBHDF5IO("test_2d_ts_support.nwb", "w") as io:
            io.write(nwbfile)

        with NWBHDF5IO("test_2d_ts_support.nwb", "r") as io:
            read_nwb = io.read()
            read_table = read_nwb.processing["behavior"]["place_rate_maps"]
            assert read_table.time_support is not None
            assert len(read_table.time_support) == 2
            assert read_table.time_support["start_time"][0] == 0.0
            assert read_table.time_support["stop_time"][1] == 15.0

        import os
        os.remove("test_2d_ts_support.nwb")


class TestRateMapTableRoundTrip1D(TestCase):
    """Test round-trip for 1D RateMapTable."""

    def test_roundtrip_1d(self):
        """Write and read back a 1D rate map table."""
        nwbfile = _make_nwbfile()
        table = _make_rate_map_table_1d(nwbfile)

        module = nwbfile.create_processing_module("behavior", "Behavioral data")
        module.add(table)

        with NWBHDF5IO("test_1d.nwb", "w") as io:
            io.write(nwbfile)

        with NWBHDF5IO("test_1d.nwb", "r") as io:
            read_nwb = io.read()
            read_table = read_nwb.processing["behavior"]["hd_tuning_curves"]

            assert isinstance(read_table, RateMapTable)
            assert len(read_table) == 3
            assert read_table.unit_of_measurement == "Hz"
            assert read_table.dim0_label == "head_direction"
            assert read_table.dim0_unit == "radians"
            assert read_table.bin_edges_dim1 is None
            assert read_table.dim1_label is None
            assert read_table.dim1_unit is None
            assert_array_equal(read_table.bin_edges_dim0[:], table.bin_edges_dim0)
            assert_array_equal(read_table["rate_map"][0], table["rate_map"][0])

        import os
        os.remove("test_1d.nwb")
