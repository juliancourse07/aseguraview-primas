import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / 'app.py'


def load_line_adjustment_factor():
    source = APP_PATH.read_text(encoding='utf-8')
    module = ast.parse(source, filename=str(APP_PATH))

    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name == '_line_adjustment_factor':
            isolated_module = ast.Module(body=[node], type_ignores=[])
            namespace = {}
            exec(compile(isolated_module, filename=str(APP_PATH), mode='exec'), namespace)
            return namespace['_line_adjustment_factor']

    raise AssertionError('No se encontró _line_adjustment_factor en app.py')


class LineAdjustmentFactorTests(unittest.TestCase):
    def test_line_adjustment_factor_returns_expected_values(self):
        factor_fn = load_line_adjustment_factor()

        self.assertEqual(factor_fn('FIANZAS'), 0.97)
        self.assertEqual(factor_fn('SOAT'), 1.0)
        self.assertEqual(factor_fn('AUTOS'), 0.995)
        self.assertEqual(factor_fn('VIDA'), 0.995)

    def test_app_uses_centralized_adjustment_helper_in_forecast_views(self):
        source = APP_PATH.read_text(encoding='utf-8')

        expected_snippets = [
            "pronostico_mes_full = pronostico_mes_full * _line_adjustment_factor(linea)",
            "fc_valores_list = [v * _line_adjustment_factor(linea) for v in fc_valores_list]",
            "proy_total = proy_total * _line_adjustment_factor(filters['linea_plus'])",
            "fc_display['Pronostico_mensual'] = fc_display['Pronostico_mensual'] * _line_adjustment_factor(filters['linea_plus'])",
            "factor_sel = _line_adjustment_factor(linea_seleccionada)",
        ]

        for snippet in expected_snippets:
            self.assertIn(snippet, source)


if __name__ == '__main__':
    unittest.main()
