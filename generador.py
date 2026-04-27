import pandas as pd
import fitz  # PyMuPDF
import json
import re

# ==========================================
# 1. FUNCIONES MATEMÁTICAS
# ==========================================
def limpiar_precio_sucio(valor):
    if pd.isna(valor) or valor == "": return ""
    v = str(valor).strip()
    if v.endswith('.0'): v = v[:-2]
    v = v.replace('.', '').replace(',', '')
    if len(v) >= 3:
        v = v[:-1] 
        enteros = v[:-2] 
        decimales = v[-2:] 
        if enteros == "": enteros = "0"
        try:
            enteros_fmt = f"{int(enteros):,}".replace(',', '.')
            return f"{enteros_fmt},{decimales}"
        except:
            return f"{enteros},{decimales}"
    return v

def obtener_precio_num(valor):
    if pd.isna(valor) or valor == "": return 0.0
    v = str(valor).strip()
    if v.endswith('.0'): v = v[:-2]
    v = v.replace('.', '').replace(',', '')
    if len(v) >= 3:
        v = v[:-1] 
        enteros = v[:-2] 
        decimales = v[-2:] 
        if enteros == "": enteros = "0"
        try:
            return float(f"{enteros}.{decimales}")
        except:
            return 0.0
    return 0.0

def formatear_promo_limpia(valor):
    if pd.isna(valor) or valor == "": return ""
    try:
        numero = float(valor)
        return f"{numero:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except: return str(valor).strip()

def normalizar_codigo(texto):
    return re.sub(r'[^A-Z0-9]', '', str(texto).upper())

# ==========================================
# 2. MOTOR DE ESCANEO "PDF-FIRST"
# ==========================================
print("Cargando base de datos...")
df = pd.read_excel('precios.xlsx', dtype={'Codigo de Producto': str})
df['Codigo Limpio'] = df['Codigo de Producto'].apply(lambda x: normalizar_codigo(x))

doc = fitz.open('catalogo.pdf')
resultados = []
codigos_encontrados = set()

print(f"Procesando {len(doc)} páginas con Radar de Súper Precisión...")

for num_pagina in range(len(doc)):
    pagina = doc.load_page(num_pagina)
    palabras = pagina.get_text("words") 
    
    tags_pagina = []
    
    for i, p in enumerate(palabras):
        texto_pdf = p[4]
        texto_limpio = re.sub(r'[^A-Z0-9:]', '', texto_pdf.upper())
        codigo_detectado = ""
        
        if "COD" in texto_limpio or "CÓD" in texto_limpio:
            posible = texto_limpio.replace("COD:", "").replace("COD", "").replace("CÓD:", "").replace("CÓD", "")
            if posible: 
                codigo_detectado = posible
            elif i + 1 < len(palabras):
                codigo_detectado = re.sub(r'[^A-Z0-9]', '', palabras[i+1][4].upper())
        
        if codigo_detectado:
            filtro = df[df['Codigo Limpio'] == codigo_detectado]
            if not filtro.empty:
                row = filtro.iloc[0]
                precio_raw = row['Precio']
                precio_num = obtener_precio_num(precio_raw)
                
                item = {
                    "pagina": num_pagina + 1,
                    "codigo": row['Codigo de Producto'],
                    "precio_num": precio_num,
                    "precio_normal": limpiar_precio_sucio(precio_raw),
                    "precio_promo": formatear_promo_limpia(row['Precio Promo']),
                    "x": round((p[0] / pagina.rect.width) * 100, 2),
                    "y": round((p[1] / pagina.rect.height) * 100, 2)
                }
                tags_pagina.append(item)

    # --- AJUSTE DE PRECISIÓN RADAR ---
    grupos = []
    for tag in tags_pagina:
        agregado = False
        for grupo in grupos:
            ref = grupo[0]
            # Reducimos la tolerancia vertical a 0.8 (menos de 1%)
            # Esto permite que cada línea de la Yerba tenga su propio precio
            if abs(tag['x'] - ref['x']) < 10 and abs(tag['y'] - ref['y']) < 0.8:
                grupo.append(tag)
                agregado = True
                break
        if not agregado:
            grupos.append([tag])
            
    for grupo in grupos:
        validos = [t for t in grupo if t['precio_num'] > 0]
        if not validos: continue
            
        # Prioridad: Promo > Precio más alto
        validos.sort(key=lambda x: (bool(x['precio_promo']), x['precio_num']), reverse=True)
        ganador = validos[0]
        
        del ganador['precio_num'] 
        resultados.append(ganador)
        codigos_encontrados.add(ganador['codigo'])

with open('datos.json', 'w', encoding='utf-8') as f:
    json.dump(resultados, f, indent=4, ensure_ascii=False)

print("-" * 30)
print(f"¡Hecho! Se procesaron {len(codigos_encontrados)} productos. Ahora cada línea debería tener su precio.")
