import unittest
from unittest.mock import patch

from app import app


class IndexPageTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_get_index_returns_form(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        for field in ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"):
            self.assertIn(f'name="{field}"', body)

    def test_form_is_prefilled_with_lab_defaults(self):
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn('value="12"', body)
        self.assertIn('value="100"', body)


class CalculateTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def post(self, **overrides):
        data = {"vcc": "12", "r1": "100", "r2": "22", "rc": "2.2",
                "re": "1", "beta": "100", "vbe": "0.70"}
        data.update(overrides)
        return self.client.post("/", data=data)

    def test_valid_input_renders_results(self):
        response = self.post()
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("9.294", body)          # VC
        self.assertIn("1.230", body)          # IC [mA]
        self.assertIn("8.052", body)          # VCE
        self.assertIn("Forward Active", body)

    def test_invalid_input_returns_400_with_message(self):
        response = self.post(r1="0")
        self.assertEqual(response.status_code, 400)
        body = response.get_data(as_text=True)
        self.assertIn("R1", body)
        self.assertNotIn("8.052", body)       # ไม่แสดงผลลัพธ์

    def test_empty_post_returns_400(self):
        response = self.client.post("/", data={})
        self.assertEqual(response.status_code, 400)
        self.assertIn("กรุณากรอก", response.get_data(as_text=True))

    def test_entered_value_is_escaped_in_form(self):
        response = self.post(r1="<script>alert(1)</script>")
        body = response.get_data(as_text=True)
        self.assertNotIn("<script>alert(1)</script>", body)

    def test_saturation_shows_warning(self):
        response = self.post(rc="47")
        body = response.get_data(as_text=True)
        self.assertIn("Saturation", body)


class Lab03WebTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_mode_selector_is_visible(self):
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn('name="mode"', body)
        for option in ("divider", "fixed", "emitter"):
            self.assertIn(f'value="{option}"', body)

    def test_fixed_mode_renders_result_without_r1_r2(self):
        response = self.client.post("/", data={
            "mode": "fixed", "vcc": "12", "rb": "1", "rc": "2.2",
            "beta": "100", "vbe": "0.70",
        })
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Fixed Bias", body)
        self.assertIn("1.130", body)
        self.assertIn("9.514", body)
        self.assertNotIn("VTH", body)

    def test_emitter_mode_renders_result(self):
        response = self.client.post("/", data={
            "mode": "emitter", "vcc": "12", "rb": "1", "re": "1",
            "rc": "2.2", "beta": "100", "vbe": "0.70",
        })
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Emitter Bias", body)
        self.assertIn("1.026", body)
        self.assertIn("8.705", body)

    def test_unknown_mode_returns_400(self):
        response = self.client.post("/", data={"mode": "unknown"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("โหมด", response.get_data(as_text=True))

    def test_invalid_fixed_input_does_not_show_old_result(self):
        data = {"mode": "fixed", "vcc": "12", "rb": "0", "rc": "2.2",
                "beta": "100", "vbe": "0.70"}
        response = self.client.post("/", data=data)
        self.assertEqual(response.status_code, 400)
        body = response.get_data(as_text=True)
        self.assertIn("RB", body)
        self.assertNotIn("9.514", body)


class Lab04WebTests(unittest.TestCase):
    """Lab 04: หน้าเดิมต้องไม่เสีย และผล SPICE ต้องแยกจากผล Analytical"""

    def setUp(self):
        self.client = app.test_client()
        self.spice_data = {
            "form": "spice", "analysis": "dc",
            "vcc": "12", "r1": "100", "r2": "22", "rc": "2.2", "re": "1",
            "rl": "10", "cin": "10", "cout": "10",
        }

    def test_page_shows_analysis_selector_and_engine_label(self):
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn('name="analysis"', body)
        for option in ("dc", "ac", "transient"):
            self.assertIn(f'value="{option}"', body)
        self.assertIn("ngspice", body)
        self.assertIn('name="form" value="spice"', body)

    def test_dc_run_shows_spice_result_with_provenance(self):
        from spice_engine import DcPoint, SimulationResult

        fake = SimulationResult(
            analysis="dc", engine="ngspice-47", model="QNPN", netlist="* netlist",
            log="* log", dc=DcPoint(1.949, 1.289, 9.189, 7.900, 0.001278,
                                    1.19e-5, 0.00129),
        )
        with patch("app.spice_engine.run_simulation", return_value=fake):
            response = self.client.post("/", data=self.spice_data)
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("1.949", body)          # VB จาก ngspice
        self.assertIn("1.278", body)          # IC [mA] จาก ngspice
        self.assertIn("7.900", body)          # VCE จาก ngspice
        self.assertIn("ngspice-47", body)
        self.assertIn("QNPN", body)
        self.assertIn("ผลจาก ngspice", body)
        self.assertNotIn("ผลจากสมการ Lab 03", body.split("ผลจาก ngspice")[0][-400:])

    def test_spice_inputs_do_not_leak_into_analytical_form(self):
        from spice_engine import DcPoint, SimulationResult

        fake = SimulationResult(
            analysis="dc", engine="ngspice-47", model="QNPN", netlist="* netlist",
            log="* log", dc=DcPoint(1.9, 1.3, 9.2, 7.9, 0.00128, 1.2e-5, 0.00129),
        )
        data = dict(self.spice_data, re="2")
        with patch("app.spice_engine.run_simulation", return_value=fake):
            response = self.client.post("/", data=data)
        body = response.get_data(as_text=True)
        self.assertRegex(body, r'id="re" name="re"[^>]*value="1"')
        self.assertRegex(body, r'id="s-re" name="re"[^>]*value="2"')

    def test_invalid_re_returns_400_without_fake_success(self):
        data = dict(self.spice_data, re="0")
        response = self.client.post("/", data=data)
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 400)
        self.assertIn("RE ต้องมากกว่า 0", body)
        self.assertNotIn("Run Status: Success", body)

    def test_engine_failure_returns_error_not_old_success(self):
        from spice_engine import SpiceRunError

        with patch("app.spice_engine.run_simulation",
                   side_effect=SpiceRunError("ngspice run failed")):
            response = self.client.post("/", data=self.spice_data)
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 400)
        self.assertIn("ngspice run failed", body)
        self.assertNotIn("Run Status: Success", body)
        self.assertNotIn("VCE", body.split("Engineering Results")[0][-500:])

    def test_lab03_analytical_route_still_works_unchanged(self):
        response = self.client.post("/", data={
            "mode": "divider", "vcc": "12", "r1": "100", "r2": "22",
            "rc": "2.2", "re": "1", "beta": "100", "vbe": "0.70",
        })
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("ผลการคำนวณ DC Bias — Voltage Divider Bias", body)
        self.assertIn("1.230", body)
        self.assertIn("8.052", body)


if __name__ == "__main__":
    unittest.main()
