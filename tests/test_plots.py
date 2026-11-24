"""Lab 04 — กราฟต้องสร้างจากจุดข้อมูลที่ส่งมา ไม่ใช่รูปที่ฝังไว้"""

import unittest

from plots import bode_svg, gain_svg, phase_svg, wave_svg
from spice_engine import AcPoint, TimePoint


class PlotTests(unittest.TestCase):
    def test_bode_svg_has_axes_units_and_both_traces(self):
        points = (
            AcPoint(100.0, 1.0, 170.0),
            AcPoint(1000.0, 6.0, -175.0),
            AcPoint(10000.0, 2.0, -179.0),
        )
        svg = bode_svg(points)
        self.assertIn("<svg", svg)
        self.assertIn("Frequency [Hz]", svg)
        self.assertIn("Gain [dB]", svg)
        self.assertIn("Phase [deg]", svg)
        self.assertEqual(svg.count("<polyline"), 2)
        self.assertIn('class="gain"', svg)
        self.assertIn('class="phase"', svg)

    def test_bode_svg_has_right_phase_axis_scale(self):
        points = (
            AcPoint(100.0, 1.0, 170.0),
            AcPoint(1000.0, 6.0, -175.0),
            AcPoint(10000.0, 2.0, -179.0),
        )
        svg = bode_svg(points)
        self.assertEqual(svg.count('class="axis-label phase-label"'), 3)
        self.assertIn(">180</text>", svg)
        self.assertIn(">0</text>", svg)
        self.assertIn(">-180</text>", svg)
        self.assertIn('class="axis-title phase-title"', svg)

    def test_gain_and_phase_are_separate_svg_charts(self):
        points = (
            AcPoint(100.0, 1.0, 170.0),
            AcPoint(1000.0, 6.0, -175.0),
            AcPoint(10000.0, 2.0, -179.0),
        )
        gain = gain_svg(points)
        phase = phase_svg(points)

        self.assertEqual(gain.count("<polyline"), 1)
        self.assertIn('class="gain"', gain)
        self.assertNotIn('class="phase"', gain)
        self.assertIn("Frequency [Hz]", gain)
        self.assertIn("Gain [dB]", gain)
        self.assertNotIn("Phase [deg]", gain)

        self.assertEqual(phase.count("<polyline"), 1)
        self.assertIn('class="phase"', phase)
        self.assertNotIn('class="gain"', phase)
        self.assertIn("Frequency [Hz]", phase)
        self.assertIn("Phase [deg]", phase)
        self.assertNotIn("Gain [dB]", phase)
        self.assertEqual(phase.count('class="axis-label phase-label"'), 3)

    def test_separate_charts_show_empty_message_without_placeholder(self):
        for empty in (gain_svg(()), phase_svg(())):
            self.assertIn("ไม่มีข้อมูล", empty)
            self.assertNotIn("<polyline", empty)

    def test_wave_svg_has_time_voltage_units_and_legend(self):
        points = (TimePoint(0.0, 0.01, -0.02), TimePoint(1.0, -0.01, 0.02))
        svg = wave_svg(points)
        self.assertIn("Time [ms]", svg)
        self.assertIn("Voltage [V]", svg)
        self.assertIn("Vin", svg)
        self.assertIn("Vout", svg)
        self.assertEqual(svg.count("<polyline"), 2)

    def test_empty_data_shows_message_not_placeholder_graph(self):
        self.assertIn("ไม่มีข้อมูล", bode_svg(()))
        self.assertNotIn("<polyline", bode_svg(()))
        self.assertIn("ไม่มีข้อมูล", wave_svg(()))


if __name__ == "__main__":
    unittest.main()
