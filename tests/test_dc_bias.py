import unittest

from dc_bias import BiasInput, Region, ValidationError, parse_form, solve

VALID = {
    "vcc": "12", "r1": "100", "r2": "22", "rc": "2.2",
    "re": "1", "beta": "100", "vbe": "0.70",
}


class ParseFormTests(unittest.TestCase):
    def test_parses_valid_values_to_floats(self):
        data = parse_form(VALID)
        self.assertIsInstance(data, BiasInput)
        self.assertAlmostEqual(data.r1, 100.0, places=9)

    def test_missing_field_rejected(self):
        values = dict(VALID)
        del values["rc"]
        with self.assertRaises(ValidationError) as ctx:
            parse_form(values)
        self.assertIn("rc", ctx.exception.errors)

    def test_blank_field_rejected(self):
        values = dict(VALID, r2="   ")
        with self.assertRaises(ValidationError) as ctx:
            parse_form(values)
        self.assertIn("r2", ctx.exception.errors)

    def test_non_numeric_rejected(self):
        values = dict(VALID, r1="abc")
        with self.assertRaises(ValidationError) as ctx:
            parse_form(values)
        self.assertIn("r1", ctx.exception.errors)

    def test_comma_decimal_rejected(self):
        values = dict(VALID, rc="2,2")
        with self.assertRaises(ValidationError) as ctx:
            parse_form(values)
        self.assertIn("rc", ctx.exception.errors)

    def test_zero_or_negative_resistance_rejected(self):
        values = dict(VALID, r1="0", r2="-22")
        with self.assertRaises(ValidationError) as ctx:
            parse_form(values)
        self.assertIn("r1", ctx.exception.errors)
        self.assertIn("r2", ctx.exception.errors)

    def test_zero_sum_divider_rejected(self):
        values = dict(VALID, r1="0", r2="0")
        with self.assertRaises(ValidationError) as ctx:
            parse_form(values)
        self.assertIn("r1", ctx.exception.errors)

    def test_non_positive_beta_rejected(self):
        values = dict(VALID, beta="0")
        with self.assertRaises(ValidationError) as ctx:
            parse_form(values)
        self.assertIn("beta", ctx.exception.errors)

    def test_vbe_must_be_below_vcc(self):
        values = dict(VALID, vbe="12")
        with self.assertRaises(ValidationError) as ctx:
            parse_form(values)
        self.assertIn("vbe", ctx.exception.errors)

    def test_vcc_error_does_not_duplicate_vbe_error(self):
        values = dict(VALID, vcc="abc")
        with self.assertRaises(ValidationError) as ctx:
            parse_form(values)
        self.assertIn("vcc", ctx.exception.errors)
        self.assertNotIn("vbe", ctx.exception.errors)


class SolveTests(unittest.TestCase):
    def test_reference_operating_point(self):
        result = solve(parse_form(VALID))
        self.assertAlmostEqual(result.vth, 2.1639, places=4)
        self.assertAlmostEqual(result.rth, 18032.79, places=2)
        self.assertAlmostEqual(result.ib * 1e6, 12.299, places=3)
        self.assertAlmostEqual(result.ic * 1e3, 1.2299, places=4)
        self.assertAlmostEqual(result.ie * 1e3, 1.2422, places=4)
        self.assertAlmostEqual(result.ve, 1.2422, places=4)
        self.assertAlmostEqual(result.vb, 1.9422, places=4)
        self.assertAlmostEqual(result.vc, 9.2943, places=4)
        self.assertAlmostEqual(result.vce, 8.0522, places=4)
        self.assertIs(result.region, Region.ACTIVE)
        self.assertEqual(result.warnings, ())

    def test_kohm_to_ohm_scaling(self):
        result = solve(parse_form(VALID))
        self.assertAlmostEqual(result.rth, 18032.79, places=2)


class RegionTests(unittest.TestCase):
    def test_cutoff_region_warns_and_zeroes_current(self):
        values = dict(VALID, r1="470", r2="22")          # VTH ≈ 0.5366 V < VBE
        result = solve(parse_form(values))
        self.assertIs(result.region, Region.CUTOFF)
        self.assertEqual(result.ic, 0.0)
        self.assertEqual(result.ie, 0.0)
        self.assertAlmostEqual(result.vb, 0.5366, places=3)
        self.assertAlmostEqual(result.vc, 12.0, places=9)
        self.assertTrue(result.warnings)

    def test_saturation_region_warns(self):
        values = dict(VALID, rc="47")                    # IC*RC ≈ 57.8 V > VCC
        result = solve(parse_form(values))
        self.assertIs(result.region, Region.SATURATION)
        self.assertTrue(result.warnings)

    def test_negative_vce_is_never_reported_as_active(self):
        values = dict(VALID, rc="10")                    # IC*RC ≈ 12.3 V → VCE ≈ -1.54 V
        result = solve(parse_form(values))
        self.assertLess(result.vce, 0.3)
        self.assertIsNot(result.region, Region.ACTIVE)
        self.assertTrue(result.warnings)


    def test_non_finite_values_rejected(self):
        for field, value in (("r1", "nan"), ("beta", "inf"), ("vcc", "1e400")):
            with self.subTest(field=field):
                values = dict(VALID, **{field: value})
                with self.assertRaises(ValidationError) as ctx:
                    parse_form(values)
                self.assertIn(field, ctx.exception.errors)


if __name__ == "__main__":
    unittest.main()
