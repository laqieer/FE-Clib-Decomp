import io
import unittest

from utility import make_lyn_reference as ref
from utility import regenerate


class FakeSymbol:
    def __init__(self, name, address, symbol_type="STT_FUNC", bind="STB_GLOBAL"):
        self.name = name
        self.values = {
            "st_value": address,
            "st_info": {"type": symbol_type, "bind": bind},
        }

    def __getitem__(self, key):
        return self.values[key]


class MakeLynReferenceTest(unittest.TestCase):
    def test_symbol_name_validation(self):
        self.assertTrue(ref.is_exportable_name("gActiveUnit"))
        self.assertTrue(ref.is_exportable_name("ProcCmd_CALL_ROUTINE"))
        self.assertFalse(ref.is_exportable_name(".text"))
        self.assertFalse(ref.is_exportable_name("1Invalid"))

    def test_name_and_address_normalization(self):
        candidate = ref.symbol_candidate(FakeSymbol("foo.bar", 0x08000101))

        self.assertEqual(candidate.symbol, ref.ExportSymbol("foo_bar", 0x08000101, "func"))
        self.assertIsNone(ref.symbol_candidate(FakeSymbol(".hidden", 0x08000101)))
        self.assertEqual(ref.format_address(0x101), "0x00000101")
        with self.assertRaises(ValueError):
            ref.normalized_address(0x1_0000_0000)

    def test_duplicate_resolution_prefers_global_and_skips_ambiguous_locals(self):
        candidates = [
            ref.symbol_candidate(FakeSymbol("Shared", 0x08000101, bind="STB_LOCAL")),
            ref.symbol_candidate(FakeSymbol("Shared", 0x08000201)),
            ref.symbol_candidate(FakeSymbol("Ambiguous", 0x08000301, bind="STB_LOCAL")),
            ref.symbol_candidate(FakeSymbol("Ambiguous", 0x08000401, bind="STB_LOCAL")),
        ]

        symbols, conflicts = ref.resolve_export_symbols(candidates)

        self.assertIn(ref.ExportSymbol("Shared", 0x08000201, "func"), symbols)
        self.assertNotIn("Shared", conflicts)
        self.assertIn("Ambiguous", conflicts)

    def test_aliases_with_the_same_address_are_preserved(self):
        candidates = [
            ref.symbol_candidate(FakeSymbol("Primary", 0x08000101)),
            ref.symbol_candidate(FakeSymbol("Alias", 0x08000101)),
        ]

        symbols, conflicts = ref.resolve_export_symbols(candidates)

        self.assertEqual(len(symbols), 2)
        self.assertEqual(conflicts, {})

    def test_untyped_symbols_are_exported_as_data(self):
        candidate = ref.symbol_candidate(
            FakeSymbol("SymbolWithoutPrototype", 0x08000101, symbol_type="STT_NOTYPE")
        )

        self.assertEqual(candidate.symbol.kind, "data")

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

    def test_removed_symbols_are_not_rendered(self):
        output = io.StringIO()

        ref.write_ea_defines(
            output,
            [ref.ExportSymbol("RenamedSymbol", 0x08000A20, "func")],
            "game.elf",
            "test",
        )

        text = output.getvalue()
        self.assertIn("RenamedSymbol", text)
        self.assertNotIn("RemovedSymbol", text)

    def test_stale_elf_link_command_is_detected(self):
        self.assertTrue(
            regenerate.elf_would_be_relinked(
                "arm-none-eabi-ld -T ldscript.txt -o fireemblem8.elf",
                "fireemblem8.elf",
            )
        )
        self.assertFalse(
            regenerate.elf_would_be_relinked(
                "make -C tools/gbagfx",
                "fireemblem8.elf",
            )
        )


if __name__ == "__main__":
    unittest.main()
