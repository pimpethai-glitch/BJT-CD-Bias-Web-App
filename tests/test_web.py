import unittest

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


if __name__ == "__main__":
    unittest.main()
