import requests
import json
import csv
import time

# Configuración
OLLAMA_URL = 'http://localhost:11434/api/generate'
# phi3:mini o llama3.2:3b
MODEL = 'phi3:mini'
ESCENARIO = 'escenario2'
# Elegir formato a probar: 'raw_completo', 'raw_reducido' o 'json_reducido'
FORMATO_ENTRADA = 'raw_completo'
# Elegir entre 'prompt1','prompt2','prompt3'
PROMPT_UTILIZAR = 'prompt2'

if MODEL == 'phi3:mini':
    modelo = 'phi3mini'

if FORMATO_ENTRADA == 'raw_completo':
    INPUT_FILE = f'data/{ESCENARIO}_raw.log'
elif FORMATO_ENTRADA == 'raw_reducido':
    INPUT_FILE = f'data/{ESCENARIO}_raw_reducido.log'
elif FORMATO_ENTRADA == 'json_reducido':
    INPUT_FILE = f'data/{ESCENARIO}_json_reducido.json'

if PROMPT_UTILIZAR == 'prompt1':
    OUTPUT_FILE = f'results/{PROMPT_UTILIZAR}/{ESCENARIO}_resultados_{FORMATO_ENTRADA}_{modelo}.csv'
elif PROMPT_UTILIZAR == 'prompt2':
    OUTPUT_FILE = f'results/{PROMPT_UTILIZAR}/{ESCENARIO}_resultados_{FORMATO_ENTRADA}_{modelo}.csv'
elif PROMPT_UTILIZAR == 'prompt3':
    OUTPUT_FILE = f'results/{PROMPT_UTILIZAR}/{ESCENARIO}_resultados_{FORMATO_ENTRADA}_{modelo}.csv'

# Prompt Base (Estrategia Few-Shot)
# Se le da instrucciones claras y un par de ejemplos para que entienda el formato esperado.
PROMPT_TEMPLATE1 = """
Sos un experto en ciberseguridad analizando logs de auditd de Linux.
Tu tarea es analizar el siguiente log y responder ÚNICAMENTE en formato JSON con la siguiente estructura:
{{"riesgo": "ALTO/MEDIO/BAJO/INFO", "justificacion": "Explicación en una línea"}}

REGLA ESTRICTA: NUNCA uses comillas dobles (") dentro del texto de la justificación. Si necesitas citar algo, usa comillas simples (').

Ejemplo 1:
Log: type=SYSCALL msg=audit(1621234567.890:123): arch=c000003e syscall=59 success=yes exit=0 a0=55f1a2b3c4d5 a1=55f1a2b3c4e0 a2=55f1a2b3c4f0 a3=8 items=2 ppid=1234 pid=5678 auid=1000 uid=0 gid=0 euid=0 suid=0 fsuid=0 egid=0 sgid=0 fsgid=0 tty=pts0 ses=1 comm="whoami" exe="/usr/bin/whoami" key="root_commands"
Respuesta: {{"riesgo": "BAJO", "justificacion": "El usuario ejecutó whoami con privilegios, lo cual es normal en tareas administrativas, pero requiere monitoreo."}}

Ejemplo 2:
Log: type=SYSCALL msg=audit(1700000000.001:101): arch=c000003e syscall=257 success=no exit=-13 a0=ffffff9c a1=7ffdc... items=1 ppid=2000 pid=2002 auid=1000 uid=1000 gid=1000 euid=1000 tty=pts0 comm="cat" exe="/usr/bin/cat" key="shadow_access"
Respuesta: {{"riesgo": "ALTO", "justificacion": "Intento fallido de lectura de un archivo crítico (/etc/shadow) por falta de permisos (exit=-13), posible intento de robo de credenciales."}}

Log a analizar:
{log_line}
"""
# Con 4 ejemplos
PROMPT_TEMPLATE2 = """
Sos un experto en ciberseguridad analizando logs de auditd de Linux.
Tu tarea es analizar el siguiente log y responder ÚNICAMENTE en formato JSON con la siguiente estructura:
{{"riesgo": "ALTO/MEDIO/BAJO/INFO", "justificacion": "Explicación en una línea"}}

REGLA ESTRICTA: NUNCA uses comillas dobles (") dentro del texto de la justificación. Si necesitas citar algo, usa comillas simples (').

Ejemplo 1:
Log: type=SYSCALL msg=audit(1700000010.000:105): arch=c000003e syscall=257 success=yes exit=3 a0=ffffff9c a1=7ffdc... items=1 ppid=1 pid=500 auid=unset uid=0 euid=0 tty=(none) comm="systemd" exe="/lib/systemd/systemd"
Respuesta: {{"riesgo": "INFO", "justificacion": "Proceso interno del sistema operativo ejecutando tareas de rutina sin impacto de seguridad."}}

Ejemplo 2:
Log: type=SYSCALL msg=audit(1621234567.890:123): arch=c000003e syscall=59 success=yes exit=0 ... uid=1000 euid=1000 comm="cat" exe="/usr/bin/cat" key="passwd_changes"
Respuesta: {{"riesgo": "BAJO", "justificacion": "El usuario realizó una lectura normal de un archivo del sistema, comportamiento esperado y sin privilegios elevados."}}

Ejemplo 3:
Log: type=USER_AUTH msg=audit(1700000020.000:110): pid=1000 uid=1000 auid=1000 ses=1 msg='op=PAM:authentication grantors=? acct="root" exe="/usr/bin/su" hostname=? addr=? terminal=pts/0 res=failed'
Respuesta: {{"riesgo": "MEDIO", "justificacion": "Intento de autenticación fallido para escalar privilegios a root mediante su, requiere revisión."}}

Ejemplo 4:
Log: type=SYSCALL msg=audit(1700000000.001:101): arch=c000003e syscall=257 success=no exit=-13 ... uid=1000 euid=1000 comm="cat" exe="/usr/bin/cat" key="shadow_access"
Respuesta: {{"riesgo": "ALTO", "justificacion": "Intento fallido de lectura de un archivo crítico (/etc/shadow) por falta de permisos (exit=-13), posible intento de robo de credenciales."}}

Log a analizar:
{log_line}
"""

# 3 ejemplos + reglas
PROMPT_TEMPLATE3 = """
Sos un experto en ciberseguridad analizando logs de auditd de Linux.
Tu tarea es analizar el siguiente log y responder ÚNICAMENTE en formato JSON con la siguiente estructura:
{{"riesgo": "ALTO/MEDIO/BAJO/INFO", "justificacion": "Explicación en una línea"}}

CRITERIOS DE CLASIFICACIÓN:
- INFO: Ruido del sistema, demonios (systemd, cron) o autenticaciones normales.
- BAJO: Lectura exitosa de archivos generales por usuarios sin privilegios.
- MEDIO: Uso de comandos administrativos (sudo, su), modificaciones menores o intentos de autenticación fallidos.
- ALTO: Modificación de archivos críticos (/etc/sudoers), acceso denegado (exit=-13) a credenciales (/etc/shadow), o comandos de persistencia (useradd).

REGLA ESTRICTA: NUNCA uses comillas dobles (") dentro del texto de la justificación. Si necesitas citar algo, usa comillas simples (').

Ejemplo 1:
Log: type=SYSCALL msg=audit(1700000010.000:105): comm="systemd" uid=0
Respuesta: {{"riesgo": "INFO", "justificacion": "Actividad de demonio del sistema sin relevancia de seguridad."}}

Ejemplo 2:
Log: type=USER_AUTH msg=audit(1700000020.000:110): comm="su" res=failed
Respuesta: {{"riesgo": "MEDIO", "justificacion": "Intento fallido de cambio de usuario, posible intento de escalada."}}

Ejemplo 3:
Log: type=SYSCALL msg=audit(1700000000.001:101): comm="cat" key="shadow_access" exit=-13
Respuesta: {{"riesgo": "ALTO", "justificacion": "Acceso denegado a credenciales críticas, fuerte indicador de compromiso."}}

Log a analizar:
{log_line}
"""

if PROMPT_UTILIZAR == 'prompt1':
    PROMPT_TEMPLATE = PROMPT_TEMPLATE1
elif PROMPT_UTILIZAR == 'prompt2':
    PROMPT_TEMPLATE = PROMPT_TEMPLATE2
elif PROMPT_UTILIZAR == 'prompt3':
    PROMPT_TEMPLATE = PROMPT_TEMPLATE3

def analizar_log(log_line):
    prompt = PROMPT_TEMPLATE.format(log_line=log_line)
    
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json" # Forzamos a que Ollama devuelva JSON para facilitar el parseo
    }
    
    start_time = time.time()
    
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        
        end_time = time.time()
        tiempo_inferencia = round(end_time - start_time, 2)
        
        result_text = response.json().get("response", "{}")
        
        # Intentar parsear la respuesta JSON del LLM
        try:
            parsed_result = json.loads(result_text)
            riesgo = parsed_result.get("riesgo", "ERROR")
            justificacion = parsed_result.get("justificacion", result_text)
        except json.JSONDecodeError:
            riesgo = "ERROR_PARSE"
            # Limpiar los saltos de línea y limitamos a 150 caracteres para no arruinar el CSV
            texto_limpio = result_text.replace('\n', ' ').replace('\r', '')
            justificacion = f"FALLO_LLM: {texto_limpio[:150]}..."

        return riesgo, justificacion, tiempo_inferencia

    except Exception as e:
        print(f"Error al conectar con Ollama: {e}")
        return "ERROR_API", str(e), 0.0

def main():
    # Lectura dependiendo si es JSON o texto plano
    if FORMATO_ENTRADA == 'json_reducido':
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            lineas = json.load(f)
            # Convertir cada diccionario a string para el prompt
            lineas = [json.dumps(l) for l in lineas] 
    else:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            lineas = [l.strip() for l in f.readlines() if l.strip()]
            
    print(f"Iniciando análisis de {len(lineas)} logs. Formato: {FORMATO_ENTRADA}")

    CAMPOS_CLAVE_JSON = ['syscall', 'success', 'exit', 'uid', 'euid', 'gid', 'comm', 'exe', 'key', 'auid', 'name']
    # Para texto plano, le agrego el "=" para evitar falsos positivos al buscar la palabra sola
    CAMPOS_CLAVE = [f"{c}=" for c in CAMPOS_CLAVE_JSON]
    
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as outfile:
        csv_writer = csv.writer(outfile)
        csv_writer.writerow(['Log', 'Riesgo', 'Justificacion', 'Tiempo Respuesta (s)', 'Modelo'])
        
        for i, linea in enumerate(lineas):
            print(f"Procesando {i+1}/{len(lineas)}...", end=" ")
            
            # LÓGICA DE FILTRADO
            # Si es raw_completo, mandamos todo al LLM obligatoriamente.
            if FORMATO_ENTRADA == 'raw_completo':
                necesita_llm = True
            else:
                # Si es un formato reducido, aplicamos el filtro inteligente
                if FORMATO_ENTRADA == 'json_reducido':
                    claves = json.loads(linea).keys()
                    necesita_llm = any(k in claves for k in CAMPOS_CLAVE_JSON)
                else:
                    necesita_llm = any(k in linea for k in CAMPOS_CLAVE)

            # EJECUCIÓN
            if necesita_llm:
                print("(Enviando a Ollama)")
                riesgo, justificacion, tiempo = analizar_log(linea)
            else:
                print("(Omitido por falta de campos clave)")
                riesgo = "INFO"
                justificacion = "Omitido del análisis LLM por falta de campos relevantes."
                tiempo = 0.0
                
            csv_writer.writerow([linea, riesgo, justificacion, tiempo, MODEL])
            
    print(f"Resultados guardados en {OUTPUT_FILE}")

if __name__ == "__main__":
    main()