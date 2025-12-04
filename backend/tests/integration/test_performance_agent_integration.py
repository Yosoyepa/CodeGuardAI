import unittest
import time
from src.agents.performance_agent import PerformanceAgent
from src.schemas.analysis import AnalysisContext
from src.schemas.finding import Severity

class TestPerformanceAgentIntegration(unittest.TestCase):
    """
    Tests de integración para el PerformanceAgent.
    Valida el flujo completo de análisis y la detección correcta de múltiples patrones
    en escenarios realistas.
    """
    
    def setUp(self):
        """Inicializa el agente antes de cada test."""
        self.agent = PerformanceAgent()

    def test_analyze_detects_all_smells_and_formats_findings(self):
        """
        Valida que el agente detecte múltiples tipos de problemas en un solo archivo
        y que los hallazgos tengan el formato y severidad correctos.
        """
        # Código que contiene intencionalmente 3 problemas de rendimiento
        code_content = """
def complex_processing(data):
    # 1. Bucles anidados (O(n^2)) - CRITICAL
    results = []
    for i in data:
        for j in data:
            results.append(i + j)
            
    # 2. Búsqueda ineficiente en bucle - MEDIUM
    whitelist = [1, 2, 3]
    filtered = []
    for item in data:
        if item in whitelist:  # Linear search inside loop
            filtered.append(item)
            
    # 3. Fuga de recursos - HIGH
    f = open("data.txt", "r")
    content = f.read()
    # Falta f.close() o uso de 'with'
    
    return results
"""
        context = AnalysisContext(
            code_content=code_content,
            filename="integration_test_complex.py"
        )
        
        # Ejecutar análisis
        findings = self.agent.analyze(context)
        
        # Verificaciones generales
        self.assertGreaterEqual(len(findings), 3, "Debería detectar al menos 3 problemas")
        
        # 1. Verificar detección de Bucles Anidados
        nested_loops = next((f for f in findings if f.rule_id == "PERF001_NESTED_LOOPS"), None)
        self.assertIsNotNone(nested_loops, "No se detectaron bucles anidados")
        self.assertEqual(nested_loops.severity, Severity.CRITICAL)
        self.assertIn("complejidad O(n^2)", nested_loops.message)
        
        # 2. Verificar detección de Búsqueda Lineal
        linear_search = next((f for f in findings if f.rule_id == "PERF002_LINEAR_SEARCH"), None)
        self.assertIsNotNone(linear_search, "No se detectó búsqueda lineal en bucle")
        self.assertEqual(linear_search.severity, Severity.MEDIUM)
        
        # 3. Verificar detección de Fuga de Recursos
        resource_leak = next((f for f in findings if f.rule_id == "PERF003_RESOURCE_LEAK"), None)
        self.assertIsNotNone(resource_leak, "No se detectó fuga de recursos (open)")
        self.assertEqual(resource_leak.severity, Severity.HIGH)

    def test_analyze_with_large_input_performance(self):
        """
        Prueba de estrés con un archivo grande pero limpio.
        Verifica que no haya falsos positivos y que el tiempo de ejecución sea aceptable.
        """
        # Generar 500 líneas de código simple sin problemas de rendimiento
        lines = ["def safe_function():"]
        for i in range(500):
            lines.append(f"    x_{i} = {i} * 2")
        lines.append("    return x_499")
        
        code_content = "\n".join(lines)
        
        context = AnalysisContext(
            code_content=code_content,
            filename="large_clean_file.py"
        )
        
        start_time = time.time()
        findings = self.agent.analyze(context)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Verificar rendimiento (debería ser muy rápido, < 1 segundo para 500 líneas)
        self.assertLess(execution_time, 1.0, f"El análisis tomó demasiado tiempo: {execution_time:.4f}s")
        
        # Verificar ausencia de falsos positivos
        self.assertEqual(len(findings), 0, f"Se encontraron hallazgos inesperados en código limpio: {findings}")

if __name__ == '__main__':
    unittest.main()
