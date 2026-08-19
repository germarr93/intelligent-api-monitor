"""
API Incident Analyzer
"""

import os
import json
from anthropic import Anthropic
from typing import Dict, Optional
from datetime import datetime


class IncidentAnalyzer:
    """
    Analizador que usa Claude para diagnosticar problemas de APIs.
    
    Necesita:
        ANTHROPIC_API_KEY en variables de entorno
    
    Ejemplo de uso:
        analyzer = IncidentAnalyzer(api_key="sk-...")
        analysis = analyzer.analyze_logs("Connection refused", "kayak-api")
        print(analysis['diagnosis'])
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa el analizador con Claude.
        
        Args:
            api_key: Tu clave de API de Anthropic (o variable ANTHROPIC_API_KEY)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "❌ ANTHROPIC_API_KEY no encontrada. "
                "Configura la variable de entorno o pasa api_key."
            )
        
        self.client = Anthropic(api_key=self.api_key)
        self.analysis_history = []
    
    def analyze_logs(self, logs: str, api_name: str) -> Dict:
        """
        Analiza logs de error usando Claude IA.
        
        Args:
            logs: Texto con los errores (puede ser multi-línea)
            api_name: Nombre de la API afectada
        
        Returns:
            {
                "api": "kayak-api",
                "diagnosis": "Database connection pool exhausted...",
                "severity": "CRITICAL",
                "affected_component": "Database",
                "recommended_actions": ["Action 1", "Action 2", ...],
                "timestamp": "2024-08-19T14:30:22",
                "raw_response": "..."
            }
        """
        
        # Prompt que enviamos a Claude
        prompt = f"""
Analiza estos logs de error de la API "{api_name}" y proporciona:
1. Causa probable del problema
2. Severidad (CRITICAL/HIGH/MEDIUM/LOW)
3. Componente o servicio afectado
4. 3-5 pasos recomendados para resolver

LOGS:
{logs}

Responde ÚNICAMENTE en este formato JSON (sin markdown):
{{
    "diagnosis": "explicación clara de qué está mal",
    "severity": "CRITICAL|HIGH|MEDIUM|LOW",
    "affected_component": "nombre del componente",
    "root_cause": "causa raíz del problema",
    "recommended_actions": ["paso 1", "paso 2", "paso 3"],
    "impact": "descripción del impacto en usuarios",
    "estimated_resolution_time": "tiempo estimado para resolver"
}}
"""
        
        try:
            # Llamar a Claude
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extraer respuesta
            response_text = message.content[0].text
            
            # Limpiar si tiene markdown
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            # Parsear JSON
            analysis_result = json.loads(response_text)
            
            # Añadir metadatos
            analysis_result["api"] = api_name
            analysis_result["timestamp"] = datetime.now().isoformat()
            analysis_result["raw_response"] = response_text
            
            # Guardar en histórico
            self.analysis_history.append(analysis_result)
            
            return analysis_result
        
        except Exception as e:
            return {
                "api": api_name,
                "error": str(e),
                "diagnosis": f"❌ Error analizando logs: {str(e)}",
                "severity": "UNKNOWN",
                "timestamp": datetime.now().isoformat()
            }
    
    def generate_incident_report(self, analysis: Dict) -> str:
        """
        Genera un reporte legible a partir del análisis.
        
        Args:
            analysis: Resultado del método analyze_logs
        
        Returns:
            String formateado como reporte profesional
        """
        
        if "error" in analysis:
            return f"❌ Error en análisis: {analysis['error']}"
        
        severity_emoji = {
            "CRITICAL": "🚨",
            "HIGH": "⚠️ ",
            "MEDIUM": "⚡",
            "LOW": "ℹ️ "
        }.get(analysis.get("severity", "UNKNOWN"), "❓")
        
        report = f"""
╔════════════════════════════════════════════════════╗
║         INCIDENT ANALYSIS REPORT                   ║
╚════════════════════════════════════════════════════╝

API Afectada: {analysis['api']}
Timestamp: {analysis['timestamp']}
Severity: {severity_emoji} {analysis.get('severity', 'UNKNOWN')}

┌─ DIAGNÓSTICO ─────────────────────────────────────┐
{analysis.get('diagnosis', 'N/A')}

┌─ CAUSA RAÍZ ──────────────────────────────────────┐
{analysis.get('root_cause', 'N/A')}

┌─ COMPONENTE AFECTADO ─────────────────────────────┐
{analysis.get('affected_component', 'N/A')}

┌─ IMPACTO ─────────────────────────────────────────┐
{analysis.get('impact', 'N/A')}

┌─ PASOS RECOMENDADOS ──────────────────────────────┐
"""
        
        actions = analysis.get('recommended_actions', [])
        for i, action in enumerate(actions, 1):
            report += f"{i}. {action}\n"
        
        report += f"""
┌─ TIEMPO ESTIMADO DE RESOLUCIÓN ───────────────────┐
{analysis.get('estimated_resolution_time', 'N/A')}

═══════════════════════════════════════════════════════
Generado por: Intelligent API Monitor
"""
        
        return report
    
    def analyze_and_report(self, logs: str, api_name: str) -> Dict:
        """
        Analiza logs Y genera reporte en un paso.
        
        Returns:
            {
                "analysis": {...},
                "report": "..."
            }
        """
        analysis = self.analyze_logs(logs, api_name)
        report = self.generate_incident_report(analysis)
        
        return {
            "analysis": analysis,
            "report": report
        }


# Ejemplo de uso
if __name__ == "__main__":
    # Inicializar analizador
    # IMPORTANTE: Configura ANTHROPIC_API_KEY en tu .env
    try:
        analyzer = IncidentAnalyzer()
        
        # Logs de ejemplo (simulado)
        sample_logs = """
[2024-08-19 14:30:22] ERROR: Connection refused at 127.0.0.1:5432
[2024-08-19 14:30:23] ERROR: Database query timeout after 30s
[2024-08-19 14:30:24] FATAL: Connection pool exhausted (500/500 connections)
[2024-08-19 14:30:25] ERROR: Unable to acquire connection from pool
[2024-08-19 14:30:26] WARNING: Request queued, waiting for available connection
        """
        
        print("🔍 Analizando logs con Claude...\n")
        
        # Analizar
        result = analyzer.analyze_and_report(sample_logs, "kayak-database-api")
        
        # Mostrar análisis
        print("📊 ANÁLISIS:")
        print(f"Severidad: {result['analysis']['severity']}")
        print(f"Causa: {result['analysis'].get('root_cause', 'N/A')}\n")
        
        # Mostrar reporte
        print(result['report'])
        
    except ValueError as e:
        print(f"⚠️  {e}")
        print("\nPara usar este analizador, necesitas:")
        print("1. Instalar: pip install anthropic")
        print("2. Obtener API key en: https://console.anthropic.com")
        print("3. Configurar: export ANTHROPIC_API_KEY='sk-...'")