# Análisis de registros de auditd con LLM local: Evaluación de phi3:mini frente a herramientas nativas

Trabajo Práctico Final - Sistemas Operativos y Redes II (Primer Semestre 2026) - Licenciatura en Sistemas, UNGS.

Este proyecto implementa un pipeline automatizado de procesamiento local para evaluar la viabilidad de utilizar LLMs compactos (`phi3:mini` y `llama3.2:3b`) en la detección de amenazas y clasificación de riesgo de eventos de auditoría (`auditd`) en Linux con una GPU de 4GB de VRAM. El objetivo es mitigar la fatiga por alertas de los administradores de sistemas y preservar la privacidad de los datos corporativos operando bajo hardware con recursos limitados.

## 🗂️ Estructura del Repositorio

* `data/` → Datasets de los escenarios de prueba en formatos RAW y JSON, además de los registros de ruido.
* `data/baseline/` → Baseline utilizado para la comparación.
* `notebooks/` → Jupyter notebooks con el análisis de los resultados.
* `results/prompt1` → Salidas del pipeline en formato CSV del prompt1.
* `results/prompt2` → Salidas del pipeline en formato CSV del prompt2.
* `results/prompt3` → Salidas del pipeline en formato CSV del prompt3.
* `results/charts` → Gráficos generados a partir de los resultados.
* `src/` → Código fuente en Python para la optimización de logs y la orquestación del pipeline.
* `informe/` → Documento PDF con el informe final de la investigación.

## 🛠️ Prerrequisitos

Para ejecutar este proyecto de forma local, es necesario contar con:
* **Python:** 3.12 o superior.
* **Ollama:** Instalado y corriendo como servicio en el puerto local por defecto (`localhost:11434`).

## ⚙️ Instalación

1. **Instalar Ollama y descargar los modelos:**
   Asegurarse de tener [Ollama](https://ollama.com/) instalado en el sistema. Luego, abrir una terminal y descargar los modelos utilizados en este trabajo:
   ```bash
   ollama pull phi3:mini
   ollama pull llama3.2:3b
2. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/tomysturtz/tp-final-sor2.git
   cd tp-final-sor2
   ```
3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Ejecución

1. **Configurar los parámetros:**
   Abrir el archivo `src/pipeline.py` y modificar las variables de la sección de configuración según se desee evaluar:
   * `MODEL`: Modelo a evaluar (`'llama3.2:3b'` o `'phi3:mini'`).
   * `ESCENARIO`: Escenario de logs a analizar (ej. `'escenario3'`).
   * `FORMATO_ENTRADA`: Nivel de reducción de los logs (`'raw_completo'`, `'raw_reducido'` o `'json_reducido'`).
   * `PROMPT_UTILIZAR`: Estrategia de prompt (`'prompt1'`, `'prompt2'` o `'prompt3'`).

2. **Ejecutar el pipeline:**
   Correr el script desde la raíz del proyecto para iniciar el análisis de los logs según el modelo y prompt configurados:
   ```bash
   python src/pipeline.py
   ```
   *(Nota: El script procesará los registros fila por fila para no saturar la ventana de contexto y exportará los resultados directamente a la carpeta results/prompt_utilizado).*
---

**Autor:** Tomás Sturtz