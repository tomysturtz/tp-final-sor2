# Análisis de registros de auditd con LLM local: Evaluación de phi3:mini frente a herramientas nativas

Trabajo Práctico Final - Sistemas Operativos y Redes II (Primer Semestre 2026) - Licenciatura en Sistemas, UNGS.

---

## Descripción del Pipeline

Este proyecto implementa un pipeline automatizado de procesamiento local para evaluar la viabilidad de utilizar LLMs compactos (`phi3:mini` y `llama3.2:3b`) en la detección de amenazas y clasificación de riesgo de eventos de auditoría del sistema operativo Linux (`auditd`) operando bajo hardware con recursos limitados.

El pipeline se compone de las siguientes etapas principales:

1. **Optimización de datasets - Opcional (`src/optimizar_dataset.py`)**:  Mediante un script en Python el log en formato RAW es sometido a una reducción de ruido ya que incluye metadatos repetitivos, descartando los campos innecesarios y dejando solo los campos imprescindibles, extrayendo únicamente **11 campos esenciales**:
   * **Identificadores de identidad**: `uid`, `euid`, `gid`, `auid`.
   * **Indicadores operacionales**: `syscall`, `success`, `exit`, `comm`, `exe`, `key`, `name` (para registros de PATH).
   * **Estructura base**: se preservan `type` y `msg`.
   A partir de esto, se generan las variantes de formato **RAW Reducido** y **JSON Reducido**.

   Esto genera dos variantes de formato, RAW reducido y JSON reducido. Esta optimización de formatos se lleva a cabo no solo para comparar qué formato funciona mejor, si para reducir el consumo de tokens de los modelos y reducir la sobrecarga computacional de la GPU.

2. **Inferencia Local y Orquestación (`src/pipeline.py`)**: El pipeline lee secuencialmente el dataset seleccionado y construye dinámicamente un prompt estructurado utilizando la técnica de **few-shot prompting**. Realiza peticiones síncronas HTTP POST a la API local de **Ollama** (puerto `11434`), la cual carga el LLM seleccionado en la GPU, configurando la inferencia de manera determinista (`"stream": false`) y forzando la salida en formato JSON estructurado (`"format": "json"`).

3. **Almacenamiento de Resultados**: El pipeline decodifica la respuesta de Ollama, extrayendo el nivel de riesgo clasificado (`ALTO`, `MEDIO`, `BAJO` o `INFO`), la justificación provista por el modelo y el tiempo de inferencia. Luego, indexa y exporta la información limpia en archivos CSV bajo la carpeta `results/prompt_utilizado/`.

---

## Instalación y Requisitos de Hardware

### Requisitos de Hardware
* **GPU**: Tarjeta gráfica local con al menos **4 GB de VRAM**.
* **RAM**: 8 GB o superior recomendados para el sistema.

### Requisitos de Software
* **Sistema Operativo**: Compatible con Python y Ollama (el proceso de inferencia y análisis se realizó en Windows).
* **Python**: Versión 3.12 o superior.
* **Ollama**: Motor de inferencia local instalado y corriendo como servicio en `localhost:11434`.

### Pasos para la Instalación

1. **Instalar Ollama y descargar los modelos**:
   Descargar e instalar [Ollama](https://ollama.com/). Luego, descargar los dos modelos a evaluar desde una terminal:
   ```bash
   ollama pull phi3:mini
   ollama pull llama3.2:3b
   ```

2. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/tomysturtz/tp-final-sor2.git
   cd tp-final-sor2
   ```

3. **Instalar dependencias de Python**:
   Instalar los paquetes requeridos especificados en `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

---

## Modelos Evaluados

Debido a la restricción física de hardware (GPU de 4GB de VRAM), se evaluaron modelos de lenguaje compactos locales:

* **`phi3:mini`**: Modelo base principal del trabajo, desarrollado por Microsoft. Cuenta con **3.800 millones (3.8B) de parámetros**.
* **`llama3.2:3b`**: Modelo secundario de comparación desarrollado por Meta, con **3.000 millones (3B) de parámetros**.

Ambos modelos operaron localmente sin conexión a servicios externos en la nube, garantizando el control absoluto y la privacidad de la información contenida en los logs del sistema operativo.

---

## Comandos de Ejecución

### 1. Optimización del Dataset (Opcional)
Si se desea regenerar los datasets reducidos (RAW Reducido y JSON Reducido):
1. Abrir `src/optimizar_dataset.py` y cambiar la variable `ESCENARIO` al escenario correspondiente (ej. `'ruido'`, `'escenario1'`).
2. Ejecutar el script:
   ```bash
   python src/optimizar_dataset.py
   ```

### 2. Ejecutar el Pipeline de Inferencia
1. Configurar los parámetros en la sección inicial de `src/pipeline.py`:
   * `MODEL`: Modelo a evaluar (`'phi3:mini'` o `'llama3.2:3b'`).
   * `ESCENARIO`: Escenario de logs (`'escenario1'`, `'escenario2'`, `'escenario3'`, `'escenario4'`, `'escenario5'`, o `'ruido'`).
   * `FORMATO_ENTRADA`: Nivel de reducción de los logs (`'raw_completo'`, `'raw_reducido'`, o `'json_reducido'`).
   * `PROMPT_UTILIZAR`: Estrategia de prompt a emplear (`'prompt1'`, `'prompt2'`, o `'prompt3'`).
2. Ejecutar el script desde la raíz del repositorio:
   ```bash
   python src/pipeline.py
   ```
   *Nota: Los resultados clasificados se guardarán en un archivo CSV en la carpeta correspondiente a `results/{PROMPT_UTILIZAR}/`.*

---

## 🗂️ Descripción de los Datasets de `data/`

La carpeta `data/` almacena los datasets organizados por escenarios de prueba en tres formatos distintos (RAW Completo, RAW Reducido y JSON Reducido), complementados con logs de ruido del sistema operativo:

* **Escenario 1 - Acceso normal a `/etc/passwd`**: Lectura rutinaria del archivo de cuentas del sistema mediante comandos de usuario común (`cat /etc/passwd`, `tail -n 5 /etc/passwd`, `grep "root" /etc/passwd`). Contiene **139 eventos**.
* **Escenario 2 - Intento de escalada de privilegios**: Registro de fallos de autorización por un usuario común que intenta comandos restringidos de elevación de privilegios (`sudo -l` fallido, `su - root`, `sudo cat /etc/shadow`). Contiene **7 eventos**.
* **Escenario 3 - Ejecución de comando como root**: Registro de tareas de administración habituales ejecutadas con privilegios elevados (`sudo apt-get update`, `sudo systemctl status auditd`, `sudo useradd usuario_fantasma`). El dataset original fue acotado de 652 eventos a **10 eventos** para aislar el ruido repetitivo de actualización de paquetes.
* **Escenario 4 - Modificación de `/etc/sudoers`**: Modificación física directa y de metadatos sobre el archivo de privilegios (uso de `visudo`, `touch /etc/sudoers` y `chmod 0440 /etc/sudoers`). Contiene **76 eventos**.
* **Escenario 5 - Acceso a `/etc/shadow` por proceso no autorizado**: Intentos directos de lectura de hashes de contraseñas por un usuario sin privilegios (`cat /etc/shadow`, `head -n 1 /etc/shadow`, `cp /etc/shadow /tmp/shadow_copy`). Contiene **243 eventos**.
* **Log de ruido**: Registros de actividad normal y de fondo del sistema operativo durante tareas cotidianas (creación de archivos no críticos, navegación de directorios, etc.), utilizado para medir la tasa de falsos positivos. Contiene **475 eventos** (de los cuales se evaluó en el formato RAW_reducido, el cual contiene **244 eventos**).
* **Baseline (`data/baseline/`)**: Reglas de filtrado tradicionales basadas en expresiones de búsqueda sintáctica mediante `ausearch` y `grep` para contrastar los resultados del LLM.

---

## Metodología

1. **Generación de datasets**: Los logs se generan en una máquina virtual (Ubuntu Server 22.04 LTS) simulando escenarios de vulnerabilidad y actividad normal. A través del subsistema de auditoría del kernel (`auditd`), se capturan las llamadas al sistema (syscalls) basadas en reglas configuradas y se extraen en formato RAW usando la utilidad `ausearch`.
2. **Optimización de datasets**: Se redujeron los datasets para eliminar el ruido y se generaron archivos en los formatos RAW_reducido y JSON_reducido.
3. **Ejecución del pipeline**: Se realizaron ejecuciones (`phi3:mini`) de todos los escenarios en todos los formatos. Además, se probaron tres variantes de prompts utilizando la estrategua **few-shot prompting**, con el formato que obtuvo mejores resultados (RAW completo). La granularidad del análisis del LLM se realizó a nivel unitario (**log por log**).
2. **Construcción de Ground Truth**: Para evaluar las clasificaciones del LLM, se desarrolló un módulo en `Jupyter Notebook` que implementa un Ground Truth basado en reglas lógicas sobre los metadatos de los logs (por ejemplo, llamadas de lectura del usuario común a `/etc/passwd` se definieron como `BAJO` / `INFO`, llamadas denegadas en `/etc/shadow` con `EXIT=-13` como `ALTO`, y comandos administrativos root legítimos como `MEDIO` / `BAJO`).
4. **Reproducibilidad y Significancia**: Se ejecutó el pipeline en **5 iteraciones independientes** para calcular el desvío estándar y el intervalo de confianza al 95% de cada escenario. Se aplicó la prueba estadística **t de Student** (con un nivel de significancia $p < 0.05$) mediante la librería `SciPy` para contrastar de manera rigurosa la efectividad entre `phi3:mini` y `llama3.2:3b`.
5. **Evaluación frente a Ruido**: Se procesaron los logs de ruido del sistema para cuantificar la tasa de falsos positivos que provocaría el LLM operando cotidianamente.

---

## Resultados y Limitaciones

### Resultados Principales

* **LLM vs. Baseline**: `phi3:mini` logró clasificar con éxito el riesgo en los escenarios 1, 2, 4 y 5, manteniendo una precisión superior al **73%** bajo el formato `RAW Completo`. En contraste, el filtrado tradicional del baseline (`ausearch`) alcanza una detección del 100% de los ataques simulados pero carece de adaptabilidad contextual, arrastrando un volumen masivo de ruido operativo (por ejemplo, comandos ordinarios del sistema) que requiere interpretación manual exhaustiva por parte del administrador.
* **Escenario con peor resultado**: En el escenario 3, la precisión de `phi3:mini` se desplomó al **10.00%** (8.00% en el promedio de repeticiones). Esto se debe a que el modelo sobreestimó comandos administrativos legítimos de root (como `sudo apt-get update`), etiquetándolos erróneamente como `ALTO` en lugar de `MEDIO` o `INFO`.
* **Impacto del Formato**:
  * El formato **RAW Completo** obtuvo los mejores resultados. Esto denota que el modelo asimila mejor la sintaxis lineal nativa clave-valor de auditd separada por espacios, mapeando dependencias semánticas complejas si no se alteran los metadatos contextuales generados por el kernel. 
  * El formato **JSON Reducido** desploma la precisión a rangos de **34% - 35%**. Esto indica que la sintaxis JSON estructurada (llaves, comillas dobles, comas) satura los mecanismos de atención del modelo, consumiendo recursos cognitivos en decodificar la estructura en lugar de analizar el comportamiento del log.
  * El formato **RAW Reducido** eliminó el ruido en el Escenario 3 (elevando la precisión al **70.00%**), pero causó pérdidas críticas de información en los escenarios de escalada e intrusión (e.g. la precisión en el Escenario 2 cayó al **28.57%**), demostrando que la reducción agresiva de metadatos ciega la capacidad interpretativa del LLM.
* **Impacto del Prompt**: El **Prompt 1** (2 ejemplos de referencia) fue el más estable. La inyección de más ejemplos (como el Prompt 2 con 4 ejemplos) satura la ventana de atención activa del modelo y eleva las alucinaciones en muestras grandes.

#### Pruebas de Reproducibilidad (5 Corridas Independientes)
Para garantizar que los resultados no fueran producto de una anomalía estadística o un accidente de una única corrida, se ejecutó el pipeline en 5 iteraciones independientes sobre el formato de mayor rendimiento (RAW Completo) y con el Prompt 1:

**Tabla 1. Estabilidad y precisión de `phi3:mini`**
| Escenario | Repetición 1 | Repetición 2 | Repetición 3 | Repetición 4 | Repetición 5 | Promedio | Desvío Estándar | Intervalo de Confianza (95%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Escenario 1** (Lectura passwd) | 73.38% | 60.43% | 63.31% | 61.87% | 62.59% | **64.32%** | 5.18% | [57.89%, 70.75%] |
| **Escenario 2** (Escalada de priv.) | 85.71% | 85.71% | 85.71% | 85.71% | 85.71% | **85.71%** | 0.00% | - |
| **Escenario 3** (Comandos root) | 10.00% | 0.00% | 20.00% | 10.00% | 0.00% | **8.00%** | 8.37% | [0.00%, 18.39%] |
| **Escenario 4** (Modif. sudoers) | 73.68% | 75.00% | 71.05% | 72.37% | 68.42% | **72.10%** | 2.53% | [68.96%, 75.24%] |
| **Escenario 5** (Lectura shadow) | 73.08% | 72.65% | 70.09% | 69.66% | 71.37% | **71.37%** | 1.51% | [69.49%, 73.25%] |

**Tabla 2. Estabilidad y precisión de `llama3.2:3b`**
| Escenario | Repetición 1 | Repetición 2 | Repetición 3 | Repetición 4 | Repetición 5 | Promedio | Desvío Estándar | Intervalo de Confianza (95%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Escenario 1** (Lectura passwd) | 53.96% | 54.68% | 49.64% | 51.08% | 51.80% | **52.23%** | 2.07% | [49.65%, 54.81%] |
| **Escenario 2** (Escalada de priv.) | 28.57% | 57.14% | 28.57% | 42.86% | 14.29% | **34.29%** | 16.29% | [14.07%, 54.51%] |
| **Escenario 3** (Comandos root) | 20.00% | 30.00% | 20.00% | 30.00% | 20.00% | **24.00%** | 5.48% | [17.20%, 30.80%] |
| **Escenario 4** (Modif. sudoers) | 68.42% | 72.37% | 65.79% | 64.47% | 61.84% | **66.58%** | 4.01% | [61.60%, 71.56%] |
| **Escenario 5** (Lectura shadow) | 71.37% | 76.92% | 78.21% | 73.08% | 77.78% | **75.47%** | 3.06% | [71.67%, 79.27%] |

#### Análisis de Significancia Estadística (Prueba t de Student)
Para contrastar ambos modelos e identificar si las diferencias de precisión observadas son estadísticamente significativas, se ejecutó una prueba t de Student con muestras independientes estableciendo un nivel de significancia de $p < 0.05$:

**Tabla 3. Resultados de significancia y conclusiones analíticas**
| Escenario | Promedio `phi3:mini` | Promedio `llama3.2:3b` | p-valor | Conclusión ($p < 0.05$) |
| :---: | :---: | :---: | :---: | :--- |
| **1** | 64.32% | 52.23% | **0.0041** | **phi3:mini** es significativamente mejor en este escenario. |
| **2** | 85.71% | 34.29% | **0.0021** | **phi3:mini** es significativamente mejor (llama mostró alta inestabilidad). |
| **3** | 8.00% | 24.00% | **0.0092** | **llama3.2:3b** es significativamente superior (aunque ambos fallan gravemente). |
| **4** | 72.10% | 66.58% | **0.0364** | **phi3:mini** es significativamente mejor en este escenario. |
| **5** | 71.37% | 75.47% | **0.0372** | **llama3.2:3b** es significativamente superior en este escenario. |

En términos generales, `phi3:mini` consolida un rendimiento más robusto y consistente en escenarios críticos de seguridad (como los intentos de escalada de privilegios y accesos a archivos passwd/sudoers), superando a su contraparte por una diferencia notable de hasta un **51.42%** en el Escenario 2. En contraste, `llama3.2:3b` presenta una ventaja de velocidad, con tiempos promedio de inferencia por debajo de los 5 segundos.

### Limitaciones Identificadas

1. **Pérdida de capacidad analítica por reducción de campos**: Al intentar optimizar tokens con el formato RAW Reducido, la eliminación agresiva de variables degradó el razonamiento del modelo. Esto provocó que en el escenario 2 (escalada de privilegios) la precisión cayera al 28.57%, evidenciando que simplificar en exceso los metadatos de las syscalls impide al LLM comprender el contexto de seguridad.
2. **Saturación de contexto ante prompts extensos**: Los modelos compactos (<4B parámetros) mostraron alta sensibilidad al tamaño de las instrucciones. Con el Prompt 2 (4 ejemplos), el modelo sufrió un colapso cognitivo en escenarios con más eventos (1 y 5), reduciendo drásticamente su precisión al no poder retener directivas lógicas si se agotan sus tokens de atención.
3. **Falta de correlación temporal**: Debido al procesamiento secuencial unitario (log por log), la solución es incapaz de detectar ataques multi-paso complejos distribuidos en el tiempo.
4. **Latencia inadecuada para tiempo real**: Con una latencia media de **6.69 segundos por log**, la inferencia local de Ollama sobre GPU de 4GB de VRAM genera un cuello de botella crítico, inviable para el análisis de flujos masivos de eventos en tiempo real.

---

## Autores y contexto académico

- Tomás Sturtz: autor principal y desarrollador
- Benjamín Chuquimango: coautor y director académico

Trabajo Final Individual de SOR2, UNGS, primer semestre de 2026.

---

## Citación Provisional

> Sturtz, T. (2026). *Análisis de registros de auditd con LLM local: Evaluación de phi3:mini frente a herramientas nativas* (Trabajo Práctico Final - Sistemas Operativos y Redes II). Licenciatura en Sistemas, Universidad Nacional de General Sarmiento.