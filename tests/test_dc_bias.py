import unittest

from dc_bias import BiasInput, Region, ValidationError, parse_form, solve, solve_mode

VALID = {
    "vcc": "12", "r1": "100", "r2": "22", "rc": "2.2",
    "re": "1", "beta": "100", "vbe": "0.70",
}
FIXED = {
    "vcc": "12", "rb": "1", "rc": "2.2", "beta": "100", "vbe": "0.70",
}
EMITTER = dict(FIXED, re="1")


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


class Lab03ParseFormTests(unittest.TestCase):
    def test_fixed_accepts_only_its_own_fields(self):
        data = parse_form(FIXED, mode="fixed")
        self.assertAlmostEqual(data.rb, 1.0)
        self.assertEqual(data.r1, 0.0)

    def test_emitter_requires_re(self):
        values = dict(FIXED)
        with self.assertRaises(ValidationError) as ctx:
            parse_form(values, mode="emitter")
        self.assertIn("re", ctx.exception.errors)

    def test_divider_fields_are_not_required_in_fixed_mode(self):
        values = dict(FIXED, r1="", r2="")
        data = parse_form(values, mode="fixed")   # ต้องไม่สน r1/r2
        self.assertAlmostEqual(data.rb, 1.0)

    def test_fixed_rb_must_be_positive(self):
        values = dict(FIXED, rb="0")
        with self.assertRaises(ValidationError) as ctx:
            parse_form(values, mode="fixed")
        self.assertIn("rb", ctx.exception.errors)

    def test_unknown_mode_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            parse_form(FIXED, mode="unknown")
        self.assertIn("mode", ctx.exception.errors)


class Lab03SolveModeTests(unittest.TestCase):
    def test_fixed_reference_operating_point(self):
        result = solve_mode("fixed", parse_form(FIXED, mode="fixed"))
        self.assertAlmostEqual(result.ib * 1e6, 11.3, places=4)
        self.assertAlmostEqual(result.ic * 1e3, 1.13, places=4)
        self.assertAlmostEqual(result.ve, 0.0, places=9)
        self.assertAlmostEqual(result.vb, 0.7, places=9)
        self.assertAlmostEqual(result.vc, 9.514, places=4)
        self.assertAlmostEqual(result.vce, 9.514, places=4)
        self.assertIs(result.region, Region.ACTIVE)
        self.assertEqual(result.warnings, ())

    def test_rb_megaohm_to_ohm_scaling(self):
        result = solve_mode("fixed", parse_form(FIXED, mode="fixed"))
        # RB = 1 MΩ ต้องแปลงเป็น 1,000,000 Ω ไม่ใช่ 1,000 Ω
        self.assertAlmostEqual((12.0 - 0.70) / result.ib, 1_000_000.0, places=3)

    def test_emitter_reference_operating_point(self):
        result = solve_mode("emitter", parse_form(EMITTER, mode="emitter"))
        self.assertAlmostEqual(result.ic * 1e3, 1.0263, places=4)
        self.assertAlmostEqual(result.ve, 1.0366, places=4)
        self.assertAlmostEqual(result.vce, 8.7054, places=4)
        self.assertIs(result.region, Region.ACTIVE)

    def test_larger_re_reduces_ic(self):
        small = solve_mode("emitter", parse_form(EMITTER, mode="emitter"))
        large = solve_mode("emitter", parse_form(dict(EMITTER, re="2"), mode="emitter"))
        self.assertLess(large.ic, small.ic)
        self.assertAlmostEqual(large.ic * 1e3, 0.9401, places=4)
        self.assertAlmostEqual(large.vce, 8.0328, places=4)

    def test_unknown_mode_in_solve_mode(self):
        with self.assertRaises(ValueError):
            solve_mode("unknown", parse_form(FIXED, mode="fixed"))


if __name__ == "__main__":
    unittest.main()
