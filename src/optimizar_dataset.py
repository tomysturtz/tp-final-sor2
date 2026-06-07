import re
import json

# Cambiar el nombre del archivo según el escenario a procesar
ESCENARIO = 'ruido' 
INPUT_FILE = f'data/{ESCENARIO}_raw.log'
OUTPUT_RAW_REDUCIDO = f'data/{ESCENARIO}_raw_reducido.log'
OUTPUT_JSON_REDUCIDO = f'data/{ESCENARIO}_json_reducido.json'

CAMPOS_PERMITIDOS = {
    'syscall', 'success', 'exit', 'uid', 'euid', 'gid', 
    'comm', 'exe', 'key', 'auid', 'name'
}

def parsear_linea(linea_raw):
    patron = re.compile(r'([a-zA-Z0-9_]+)=("[^"]+"|\S+)')
    matches = patron.findall(linea_raw)
    
    dict_reducido = {}
    lista_raw_reducido = []
    
    # Guardar type y msg para el RAW
    tipo_msg = re.search(r'(type=\S+\smsg=\S+)', linea_raw)
    if tipo_msg:
        lista_raw_reducido.append(tipo_msg.group(1))
        
    # Buscar los campos permitidos
    for clave, valor in matches:
        if clave in CAMPOS_PERMITIDOS:
            valor_limpio = valor.strip('"')
            dict_reducido[clave] = valor_limpio
            lista_raw_reducido.append(f"{clave}={valor}")
            
    # Inyectar el 'type' y devolver la línea, tenga o no tenga campos extra
    # No descarta nada
    match_tipo = re.search(r'type=(\S+)', linea_raw)
    if match_tipo:
        dict_reducido['type'] = match_tipo.group(1)
        
    raw_reducido_str = " ".join(lista_raw_reducido)
    return raw_reducido_str, dict_reducido

def main():
    logs_json = []
    logs_raw_reducido = []
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        lineas = f.readlines()
        
    for linea in lineas:
        linea = linea.strip()
        if not linea: continue
            
        raw_red, dict_red = parsear_linea(linea)
        
        if dict_red: # Si encontró campos útiles
            logs_json.append(dict_red)
            logs_raw_reducido.append(raw_red)
            
    # Guardar el RAW reducido
    with open(OUTPUT_RAW_REDUCIDO, 'w', encoding='utf-8') as f:
        for log in logs_raw_reducido:
            f.write(log + '\n')
            
    # Guardar el JSON reducido
    with open(OUTPUT_JSON_REDUCIDO, 'w', encoding='utf-8') as f:
        json.dump(logs_json, f, indent=4)
        
    print(f"Procesado {INPUT_FILE}")
    print(f" -> Generado: {OUTPUT_RAW_REDUCIDO}")
    print(f" -> Generado: {OUTPUT_JSON_REDUCIDO}")

if __name__ == "__main__":
    main()