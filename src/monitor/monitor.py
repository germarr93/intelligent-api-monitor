"""
API Health Monitor
==================
Este módulo verifica continuamente si las APIs están "vivas" y funcionales.

¿Qué hace?
- Hace un ping a cada API cada X segundos
- Mide el tiempo de respuesta
- Clasifica como: UP, DEGRADED, DOWN
- Guarda el histórico
"""

import requests
import time
from datetime import datetime
from typing import Dict, List
import json


class APIMonitor:
    """
    Monitor que verifica la salud de APIs.
    
    Ejemplo de uso:
        monitor = APIMonitor()
        monitor.add_api("Kayak Search", "https://api.kayak.com/search")
        health = monitor.check_all()
        print(health)
    """
    
    def __init__(self):
        """Inicializa el monitor sin APIs."""
        self.apis = {}
        self.history = []
    
    def add_api(self, name: str, url: str, timeout: int = 5) -> None:
        """
        Añade una API para monitorear.
        
        Args:
            name: Nombre descriptivo (ej: "Kayak Search")
            url: URL del endpoint (ej: "https://api.kayak.com/health")
            timeout: Segundos máximo para esperar respuesta
        """
        self.apis[name] = {
            "url": url,
            "timeout": timeout,
            "last_status": None,
            "last_check": None
        }
        print(f"✅ API añadida: {name}")
    
    def check_api_health(self, name: str) -> Dict:
        """
        Verifica la salud de UNA sola API.
        
        Returns:
            {
                "name": "Kayak Search",
                "status": "UP" | "DEGRADED" | "DOWN",
                "response_time": 1.23,
                "status_code": 200,
                "timestamp": "2024-08-19 14:30:22",
                "error": None
            }
        """
        if name not in self.apis:
            return {"error": f"API {name} not found"}
        
        api_config = self.apis[name]
        start_time = time.time()
        
        try:
            # Hacer el request
            response = requests.get(
                api_config["url"],
                timeout=api_config["timeout"]
            )
            response_time = time.time() - start_time
            
            # Clasificar el status
            if response.status_code == 200:
                status = "UP"
            elif 200 <= response.status_code < 500:
                status = "DEGRADED"
            else:
                status = "DOWN"
            
            result = {
                "name": name,
                "status": status,
                "response_time": round(response_time, 2),
                "status_code": response.status_code,
                "timestamp": datetime.now().isoformat(),
                "error": None
            }
        
        except requests.exceptions.Timeout:
            result = {
                "name": name,
                "status": "DOWN",
                "response_time": api_config["timeout"],
                "status_code": None,
                "timestamp": datetime.now().isoformat(),
                "error": "Timeout - API no responde en tiempo"
            }
        
        except requests.exceptions.ConnectionError:
            result = {
                "name": name,
                "status": "DOWN",
                "response_time": None,
                "status_code": None,
                "timestamp": datetime.now().isoformat(),
                "error": "Connection Error - No se puede alcanzar la API"
            }
        
        except Exception as e:
            result = {
                "name": name,
                "status": "DOWN",
                "response_time": None,
                "status_code": None,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        
        # Guardar en histórico
        self.history.append(result)
        self.apis[name]["last_status"] = result["status"]
        self.apis[name]["last_check"] = result["timestamp"]
        
        return result
    
    def check_all(self) -> List[Dict]:
        """
        Verifica la salud de TODAS las APIs registradas.
        
        Returns:
            Lista con el status de todas las APIs
        """
        results = []
        for api_name in self.apis:
            health = self.check_api_health(api_name)
            results.append(health)
        
        return results
    
    def get_summary(self) -> Dict:
        """
        Devuelve un resumen del estado general.
        
        Returns:
            {
                "total_apis": 3,
                "up": 2,
                "degraded": 1,
                "down": 0,
                "timestamp": "2024-08-19 14:30:22"
            }
        """
        all_results = self.check_all()
        
        up_count = sum(1 for r in all_results if r["status"] == "UP")
        degraded_count = sum(1 for r in all_results if r["status"] == "DEGRADED")
        down_count = sum(1 for r in all_results if r["status"] == "DOWN")
        
        return {
            "total_apis": len(self.apis),
            "up": up_count,
            "degraded": degraded_count,
            "down": down_count,
            "timestamp": datetime.now().isoformat(),
            "details": all_results
        }
    
    def export_history(self, filename: str = "history.json") -> None:
        """Guarda el histórico en un archivo JSON."""
        with open(filename, 'w') as f:
            json.dump(self.history, f, indent=2)
        print(f"📁 Histórico guardado en {filename}")


# Ejemplo de uso
if __name__ == "__main__":
    # Crear monitor
    monitor = APIMonitor()
    
    # Añadir APIs para monitorear
    monitor.add_api("Kayak Search", "https://api.kayak.com/search")
    monitor.add_api("Google API", "https://www.google.com")
    monitor.add_api("JSON Placeholder", "https://jsonplaceholder.typicode.com/posts")
    
    # Verificar todas las APIs
    print("\n🔍 Verificando APIs...\n")
    summary = monitor.get_summary()
    
    # Mostrar resumen
    print(f"Total APIs: {summary['total_apis']}")
    print(f"✅ UP: {summary['up']}")
    print(f"⚠️  DEGRADED: {summary['degraded']}")
    print(f"❌ DOWN: {summary['down']}\n")
    
    # Mostrar detalles
    for detail in summary['details']:
        status_emoji = "✅" if detail['status'] == "UP" else "❌"
        print(f"{status_emoji} {detail['name']}: {detail['status']} ({detail.get('response_time', 'N/A')}s)")
        if detail['error']:
            print(f"   Error: {detail['error']}")
    
    # Guardar histórico
    monitor.export_history()