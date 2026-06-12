import io
import unittest

from utility import make_lyn_reference as ref


class MakeLynReferenceTest(unittest.TestCase):
    def test_symbol_name_validation(self):
        self.assertTrue(ref.is_exportable_name("gActiveUnit"))
        self.assertTrue(ref.is_exportable_name("ProcCmd_CALL_ROUTINE"))
        self.assertFalse(ref.is_exportable_name(".text"))
        self.assertFalse(ref.is_exportable_name("1Invalid"))

    def test_sorted_symbols_orders_by_address_then_name(self):
        symbols = [
            ref.ExportSymbol("b", 0x08000004, "data"),
            ref.ExportSymbol("a", 0x08000004, "func"),
            ref.ExportSymbol("c", 0x03000000, "data"),
        ]

        self.assertEqual(
            ref.sorted_symbols(symbols),
            [
                ref.ExportSymbol("c", 0x03000000, "data"),
                ref.ExportSymbol("a", 0x08000004, "func"),
                ref.ExportSymbol("b", 0x08000004, "data"),
            ],
        )

    def test_write_lyn_reference(self):
        output = io.StringIO()
        symbols = [
            ref.ExportSymbol("AgbMain", 0x08000A20, "func"),
            ref.ExportSymbol("gActiveUnit", 0x03004E50, "data"),
        ]

        ref.write_lyn_reference(output, symbols, "fireemblem8.elf", "test")

        text = output.getvalue()
        self.assertIn("SET_FUNC AgbMain, 0x08000A20", text)
        self.assertIn("SET_DATA gActiveUnit, 0x03004E50", text)

    def test_write_ea_defines(self):
        output = io.StringIO()
        symbols = [
            ref.ExportSymbol("AgbMain", 0x08000A20, "func"),
            ref.ExportSymbol("gActiveUnit", 0x03004E50, "data"),
        ]

        ref.write_ea_defines(output, symbols, "fireemblem8.elf", "test")

        text = output.getvalue()
        self.assertIn("#define AgbMain     0x08000A20", text)
        self.assertIn("#define gActiveUnit 0x03004E50", text)


if __name__ == "__main__":
    unittest.main()
