"""Lab 04 — tdd ก่อนเขียน spice_engine.py

โมดูลนี้ต้องแปลงค่าจากฟอร์ม → netlist → เรียก ngspice → อ่านผลจริง
test ทุกตัวใช้ข้อมูลจำลองเฉพาะในชั้น parser ไม่ได้แต่งผล ngspice ขึ้นมาแจ้งว่าสำเร็จ
"""

import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from spice_engine import (
    SpiceRunError,
    SpiceValidationError,
    ac_points,
    ac_summary,
    build_netlist,
    parse_dc_print,
    parse_spice_form,
    parse_wrdata,
    run_simulation,
    transient_points,
    transient_summary,
)

DC_VALUES = {
    "vcc": "12", "r1": "100", "r2": "22", "rc": "2.2", "re": "1",
    "rl": "10", "cin": "10", "cout": "10",
}
SOURCE = {"amplitude": "10", "frequency": "1"}  # mV peak, kHz


class ParseSpiceFormTests(unittest.TestCase):
    def test_dc_does_not_require_source_values(self):
        data = parse_spice_form(DC_VALUES, "dc")
        self.assertAlmostEqual(data.r1, 100_000.0)
        self.assertAlmostEqual(data.c_in, 10e-6)
        self.assertAlmostEqual(data.rl, 10_000.0)

    def test_ac_requires_amplitude_and_frequency(self):
        with self.assertRaises(SpiceValidationError) as ctx:
            parse_spice_form(DC_VALUES, "ac")
        self.assertIn("amplitude", ctx.exception.errors)
        self.assertIn("frequency", ctx.exception.errors)

    def test_source_is_converted_to_si(self):
        data = parse_spice_form({**DC_VALUES, **SOURCE}, "transient")
        self.assertAlmostEqual(data.amplitude, 0.010)
        self.assertAlmostEqual(data.frequency, 1000.0)

    def test_rejects_zero_resistor_and_bad_number(self):
        with self.assertRaises(SpiceValidationError) as ctx:
            parse_spice_form({**DC_VALUES, "re": "0"}, "dc")
        self.assertIn("re", ctx.exception.errors)
        with self.assertRaises(SpiceValidationError) as ctx:
            parse_spice_form({**DC_VALUES, "rc": "2,2"}, "dc")
        self.assertIn("rc", ctx.exception.errors)

    def test_rejects_injection_text(self):
        with self.assertRaises(SpiceValidationError):
            parse_spice_form(
                {**DC_VALUES, **SOURCE, "frequency": "1k ; rm -rf /"}, "ac"
            )

    def test_rejects_unknown_analysis(self):
        with self.assertRaises(SpiceValidationError) as ctx:
            parse_spice_form(DC_VALUES, "something")
        self.assertIn("analysis", ctx.exception.errors)


class NetlistTests(unittest.TestCase):
    def test_dc_netlist_has_op_and_no_source_dependency(self):
        netlist = build_netlist("dc", parse_spice_form(DC_VALUES, "dc"))
        self.assertIn(".control", netlist)
        self.assertIn("op", netlist)
        self.assertIn("print V(base)", netlist)
        self.assertIn("@q1[ic]", netlist)
        self.assertIn("R1 VCC base 100k", netlist)
        self.assertIn("RE emitter 0 1k", netlist)
        self.assertIn(".model QNPN NPN", netlist)
        self.assertTrue(netlist.rstrip().endswith(".end"))
        self.assertNotIn("wrdata", netlist)

    def test_ac_netlist_has_sweep_and_wrdata(self):
        netlist = build_netlist(
            "ac", parse_spice_form({**DC_VALUES, **SOURCE}, "ac")
        )
        self.assertIn("ac dec", netlist)
        self.assertIn("set units=degrees", netlist)
        self.assertIn("set wr_singlescale", netlist)
        self.assertIn("set wr_vecnames", netlist)
        self.assertIn("wrdata ac.csv vm(out) vp(out) vm(src) vp(src)", netlist)
        self.assertIn("AC 0.01", netlist)

    def test_transient_netlist_uses_positive_tstep_and_cycles(self):
        netlist = build_netlist(
            "transient", parse_spice_form({**DC_VALUES, **SOURCE}, "transient")
        )
        self.assertIn("tran 10u 5m 0 10u", netlist)
        self.assertIn("set wr_singlescale", netlist)
        self.assertIn("set wr_vecnames", netlist)
        self.assertIn("wrdata tran.csv v(src) v(out)", netlist)
        self.assertIn("SIN(0 0.01 1000)", netlist)


class ParserTests(unittest.TestCase):
    DC_STDOUT = """
Note: No compatibility mode selected!
No. of Data Rows : 1
v(base) = 1.949112e+00
v(emitter) = 1.289454e+00
v(collector) = 9.189410e+00
v(base)-v(emitter) = 6.596584e-01
@q1[ic] = 1.278193e-03
@q1[ib] = 1.191895e-05
@q1[ie] = -1.29011e-03
"""

    def test_parse_dc_print_reads_all_seven_values(self):
        point = parse_dc_print(self.DC_STDOUT)
        self.assertAlmostEqual(point.vb, 1.949112)
        self.assertAlmostEqual(point.ve, 1.289454)
        self.assertAlmostEqual(point.vc, 9.189410)
        self.assertAlmostEqual(point.vce, 9.189410 - 1.289454)
        self.assertAlmostEqual(point.ic, 1.278193e-3)
        self.assertAlmostEqual(point.ib, 1.191895e-5)
        self.assertAlmostEqual(point.ie, 1.29011e-3)

    def test_parse_dc_print_rejects_empty_output(self):
        with self.assertRaises(SpiceRunError):
            parse_dc_print("No. of Data Rows : 0")

    def test_parse_wrdata_reads_header_and_single_scale_columns(self):
        # wr_singlescale: column แรกคือ scale, ตามด้วยข้อมูลแต่ละเวกเตอร์
        text = (
            " time            v(src)          v(out)\n"
            " 1.00000000e+00  2.00000000e+00  3.00000000e+00\n"
            " 4.00000000e+00  5.00000000e+00  6.00000000e+00\n"
        )
        self.assertEqual(parse_wrdata(text, 2), ((1.0, 2.0, 3.0), (4.0, 5.0, 6.0)))

    def test_parse_wrdata_rejects_corrupt_data_row(self):
        text = " time v(src) v(out)\n 1.0 2.0 not-a-number\n"
        with self.assertRaises(SpiceRunError):
            parse_wrdata(text, 2)

    def test_ac_points_computes_gain_db_and_phase(self):
        rows = ((1000.0, 0.01, 179.0, 0.01, 0.0),)
        points = ac_points(rows)
        self.assertAlmostEqual(points[0].frequency_hz, 1000.0)
        self.assertAlmostEqual(points[0].gain_db, 0.0, places=5)
        self.assertAlmostEqual(points[0].phase_deg, 179.0, places=5)

    def test_ac_summary_reports_midband_and_missing_cutoff(self):
        rows = ((1.0, 1e-6, 180.0, 0.01, 0.0),
                (1000.0, 0.02, 180.0, 0.01, 0.0))
        summary = ac_summary(ac_points(rows))
        self.assertAlmostEqual(summary["gain_mid_db"], 6.0206, places=3)
        self.assertIn("not determined", summary["cutoff"])

    def test_transient_points_use_milliseconds(self):
        points = transient_points(((0.0, 0.001, 0.002), (0.001, -0.001, -0.002)))
        self.assertAlmostEqual(points[1].time_ms, 1.0)
        self.assertAlmostEqual(points[1].vin_v, -0.001)

    def test_transient_summary_detects_phase_inversion(self):
        rows = tuple(
            (i / 1000.0, 0.01 * (1 if i % 2 == 0 else -1),
             -0.02 * (1 if i % 2 == 0 else -1))
            for i in range(100)
        )
        summary = transient_summary(transient_points(rows))
        self.assertEqual(summary["phase_relation"], "inverted")
        self.assertAlmostEqual(summary["vin_peak_mv"], 10.0, places=3)
        self.assertAlmostEqual(summary["vout_peak_mv"], 20.0, places=3)


class RunSimulationTests(unittest.TestCase):
    def test_missing_engine_returns_clear_error(self):
        with self.assertRaises(SpiceRunError) as ctx:
            run_simulation("dc", DC_VALUES,
                           executable="C:/definitely/not/here/ngspice.exe")
        self.assertIn("ngspice", str(ctx.exception))

    def test_empty_output_is_not_reported_as_success(self):
        done = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
        with patch("spice_engine.subprocess.run", return_value=done):
            with self.assertRaises(SpiceRunError):
                run_simulation("dc", DC_VALUES, executable="fake-ngspice")

    def test_nonzero_return_code_is_error(self):
        done = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="Error: transient aborted"
        )
        with patch("spice_engine.subprocess.run", return_value=done):
            with self.assertRaises(SpiceRunError) as ctx:
                run_simulation("dc", DC_VALUES, executable="fake-ngspice")
        self.assertIn("transient aborted", str(ctx.exception))

    def test_solver_error_in_log_is_not_success_even_if_exit_zero(self):
        done = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout="Error: transient simulation(s) aborted\n", stderr=""
        )
        with patch("spice_engine.subprocess.run", return_value=done):
            with self.assertRaises(SpiceRunError) as ctx:
                run_simulation("dc", DC_VALUES, executable="fake-ngspice")
        self.assertIn("transient simulation(s) aborted", str(ctx.exception))

    def test_successful_run_parses_generated_csv(self):
        def fake_run(args, **kwargs):
            workdir = Path(kwargs["cwd"])
            (workdir / "ac.csv").write_text(
                " frequency vm(out) vp(out) vm(src) vp(src)\n"
                " 1.0e3 0.02 0.0 0.01 0.0\n",
                encoding="utf-8",
            )
            return subprocess.CompletedProcess(args=args, returncode=0,
                                               stdout="", stderr="")

        with patch("spice_engine.subprocess.run", side_effect=fake_run):
            result = run_simulation(
                "ac", {**DC_VALUES, **SOURCE}, executable="fake-ngspice"
            )
        self.assertEqual(result.status, "success")
        self.assertEqual(result.analysis, "ac")
        self.assertEqual(len(result.ac), 1)
        self.assertAlmostEqual(result.ac[0].gain_db, 6.0206, places=3)
        self.assertIn("wrdata ac.csv", result.netlist)


if __name__ == "__main__":
    unittest.main()
