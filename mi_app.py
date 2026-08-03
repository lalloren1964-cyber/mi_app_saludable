import streamlit as st
from groq import Groq
import os
import glob
import re

st.set_page_config(page_title="App de Ana para mejorar rutinas personales", layout="wide")

# ------------------------------------------------------------
# 1. FUNCIONES PARA MANEJAR MULTIPLES CHATS (ARCHIVOS TXT)
# ------------------------------------------------------------
def limpiar_nombre_archivo(nombre):
    """Convierte el nombre del usuario en un nombre de archivo válido."""
    nombre_seguro = nombre.strip().lower().replace(" ", "_")
    return re.sub(r'[^a-z0-9_]', '', nombre_seguro)

def listar_chats():
    """Busca todos los archivos de chat en el directorio actual."""
    archivos = glob.glob("chat_*.txt")
    chats = []
    for f in archivos:
        nombre_limpio = f.replace("chat_", "").replace(".txt", "").replace("_", " ").capitalize()
        chats.append(nombre_limpio)
    chats.sort()
    return chats

def guardar_en_historial(nombre_chat, pregunta, respuesta):
    """Añade una nueva entrada al archivo txt del chat seleccionado."""
    nombre_seguro = limpiar_nombre_archivo(nombre_chat)
    nombre_archivo = f"chat_{nombre_seguro}.txt"
    with open(nombre_archivo, mode="a", encoding="utf-8") as f:
        f.write(f"Pregunta Usuario:\n{pregunta}\n")
        f.write(f"Respuesta IA:\n{respuesta}\n")
        f.write("--------------------------------------------------------------------------------\n")

def leer_historial(nombre_chat):
    """Devuelve el contenido completo del chat seleccionado."""
    if not nombre_chat:
        return ""
    nombre_seguro = limpiar_nombre_archivo(nombre_chat)
    nombre_archivo = f"chat_{nombre_seguro}.txt"
    try:
        with open(nombre_archivo, mode="r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""

def obtener_historial_para_ia(nombre_chat):
    """Lee el archivo de texto y lo formatea como la lista de mensajes para Groq."""
    contenido = leer_historial(nombre_chat)
    mensajes_ia = []
    
    if not contenido:
        return mensajes_ia

    bloques = contenido.split("--------------------------------------------------------------------------------\n")
    
    for bloque in bloques:
        if "Pregunta Usuario:" in bloque and "Respuesta IA:" in bloque:
            partes = bloque.split("Respuesta IA:\n")
            pregunta = partes[0].replace("Pregunta Usuario:\n", "").strip()
            respuesta = partes[1].strip()
            
            mensajes_ia.append({"role": "user", "content": pregunta})
            mensajes_ia.append({"role": "assistant", "content": respuesta})
            
    return mensajes_ia

def eliminar_chat_fisico(nombre_chat):
    """Elimina permanentemente el archivo txt del chat seleccionado."""
    nombre_seguro = limpiar_nombre_archivo(nombre_chat)
    nombre_archivo = f"chat_{nombre_seguro}.txt"
    if os.path.exists(nombre_archivo):
        os.remove(nombre_archivo)

def obtener_system_prompt(nivel):
    """Devuelve el texto del system prompt según la elección del usuario."""
    if nivel == "Nutrición":
        return """
### ROL
Eres un Nutricionista Deportivo de Élite especializado exclusivamente en mujeres de 60 a 65 años. Tu objetivo es optimizar la salud, el rendimiento físico y la recuperación de este perfil demográfico mediante evidencia científica actualizada.

### REGLAS CRÍTICAS DE RESPUESTA
1. SOLO responde preguntas sobre nutrición, suplementación deportiva y su relación directa con el ejercicio. En tus respuestas puedes incluir recetas, si te lo solicitan, y además su valor nutricional.
2. Si el usuario pregunta sobre cualquier otro tema (política, tecnología, medicina general no nutricional, ocio, etc.), debes responder exactamente: "Lo siento, como experto en nutrición deportiva para mujeres senior, solo puedo asesorarte en temas relacionados con la alimentación y suplementación para tu actividad física."
3. Sé claro, conciso, concreto y directo. Evita introducciones innecesarias o conclusiones genéricas.
4. Mantén un tono profesional, empoderador y amable.
5. Cualquier cosa que no tenga que ver con la nutricion directamente responde con esto: "Solo respondo a preguntas sobre nutrición"

### CONOCIMIENTO ESPECÍFICO (CONTEXTO)
- Prioriza la prevención de la sarcopenia (pérdida de masa muscular) mediante una ingesta proteica óptima (1.2 - 1.6 g/kg/día).
- Enfócate en la SPM (Síntesis de Proteína Muscular) y la resistencia anabólica propia de la edad.
- Considera la salud ósea (osteoporosis) y micronutrientes clave: Vitamina D, Calcio, Magnesio y B12.
- Suplementación recomendada con evidencia: Creatina monohidrato, AGPI n-3 (Ácidos Grasos Poliinsaturados Omega-3) y proteínas de alta calidad (suero/leucina).

### FORMATO DE SALIDA
- Usa listas numeradas o puntos para recomendaciones.
- Si mencionas términos técnicos, explica brevemente su beneficio para el rendimiento.
"""

    elif nivel == "Ejercicio":
        return """
### ROL
Eres un Fisioterapeuta y Entrenador Personal experto, especializado exclusivamente en mujeres de 60 a 65 años. Tu objetivo es optimizar la salud musculoesquelética, la fuerza, el equilibrio, la movilidad y la prevención de caídas en este perfil demográfico, mediante la prescripción de ejercicios seguros y efectivos basados en evidencia científica.

### REGLAS CRÍTICAS DE RESPUESTA
1. SOLO responde preguntas sobre ejercicio físico, fisioterapia, entrenamiento de fuerza, flexibilidad, equilibrio, movilidad y prevención de caídas.
2. Si el usuario pregunta sobre cualquier otro tema (nutrición, política, tecnología, medicina general no relacionada con el ejercicio, ocio, etc.), debes responder exactamente: "Lo siento, como fisioterapeuta y entrenador personal especializado en mujeres senior, solo puedo asesorarte en temas relacionados con el ejercicio físico, la fisioterapia y el movimiento."
3. Sé claro, conciso, concreto y directo. Evita introducciones innecesarias o conclusiones genéricas.
4. Explica los ejercicios en detalle, paso a paso, incluyendo la postura correcta, el número de repeticiones/series y la frecuencia recomendada.
5. Siempre enfatiza la importancia de escuchar al cuerpo y consultar a un profesional de la salud antes de iniciar cualquier rutina nueva.
6. Mantén un tono profesional, empoderador y amable.
7.Cualquier cosa que no tenga que ver con el ejercicio físico directamente responde con esto: "Solo respondo a preguntas sobre ejercicio físico"

### CONOCIMIENTO ESPECÍFICO (CONTEXTO)
- Prioriza ejercicios de fuerza para combatir la **sarcopenia** (pérdida de masa muscular) y la **osteoporosis** (pérdida de densidad ósea), utilizando el propio peso corporal, bandas de resistencia o pesas ligeras.
- Incluye ejercicios de equilibrio y movilidad para reducir el riesgo de caídas y mejorar la autonomía.
- Considera la importancia de la flexibilidad y el estiramiento para mantener el rango de movimiento articular.
- Adapta las recomendaciones a condiciones comunes en esta edad, como la artrosis o la hipertensión, sugiriendo modificaciones si es necesario.
- Fomenta la actividad física regular, con un mínimo de 150 minutos de actividad aeróbica moderada y 2 o más días de entrenamiento de fuerza a la semana.

### FORMATO DE SALIDA
- Usa listas numeradas para describir los ejercicios, con un paso por cada punto.
- Incluye una sección de "Recomendaciones Generales" al final de cada respuesta con consejos de seguridad y progresión.
- Si mencionas términos técnicos, explica brevemente su relevancia para el ejercicio o la salud.
"""

    elif nivel == "General":
        return "Actúa como una IA experta. Responde con detalle y profundidad a todas las consultas del usuario, pero de forma clara concisa y concreta."
    else:
        st.error("Por favor selecciona un tipo de consulta.")
        return "Eres un asistente útil."

# ------------------------------------------------------------
# 2. CONFIGURACIÓN DE LA BARRA LATERAL (GESTIÓN DE CHATS)
# ------------------------------------------------------------
with st.sidebar:
    st.title("🍉 App de ejercicio y menú diario")
    st.image("img/miapp.jpg", caption="Imagen Añadida Ejercicio y Nutrición")
    # BOTON PARA SELECCIONAR LA TEMPERATURA  DE LA IA
    st.divider()
        

    st.subheader("📁 Gestión de Chats")
    
    lista_de_chats = listar_chats()
    
    if not lista_de_chats:
        lista_de_chats = ["Chat principal"]
        with open("chat_chat_principal.txt", "w", encoding="utf-8") as f:
            f.write("")
            
    # Crear nuevo chat
    with st.popover("➕ Crear Nuevo Chat"):
        nuevo_nombre = st.text_input("Nombre del chat:", placeholder="Ej. Tarea Historia, Dudas Python...")
        if st.button("Confirmar y Crear"):
            if nuevo_nombre.strip() != "":
                nombre_formateado = nuevo_nombre.strip().capitalize()
                nombre_seguro = limpiar_nombre_archivo(nombre_formateado)
                with open(f"chat_{nombre_seguro}.txt", "w", encoding="utf-8") as f:
                    f.write("")
                st.session_state.chat_actual = nombre_formateado
                st.rerun()
            else:
                st.warning("El nombre no puede estar vacío.")

    # Control de estados de sesión
    if "chat_actual" not in st.session_state:
        st.session_state.chat_actual = lista_de_chats[0]

    if st.session_state.chat_actual not in lista_de_chats:
        st.session_state.chat_actual = lista_de_chats[0]

    # Selector de chat activo
    chat_seleccionado = st.selectbox(
        "Selecciona el chat activo:",
        lista_de_chats,
        index=lista_de_chats.index(st.session_state.chat_actual),
        key="selector_chat"
    )
    st.session_state.chat_actual = chat_seleccionado

    # BOTÓN PARA DESCARGAR EL HISTORIAL ACTUAL
    st.divider()
    st.subheader("📥 Exportar")
    historial_bruto = leer_historial(st.session_state.chat_actual)
    
    # El botón solo se habilitará si el archivo de texto contiene mensajes
    st.download_button(
        label="⬇️ Descargar Historial (.txt)",
        data=historial_bruto,
        file_name=f"historial_{limpiar_nombre_archivo(st.session_state.chat_actual)}.txt",
        mime="text/plain",
        disabled=not bool(historial_bruto.strip())
    )

    # BOTÓN PARA BORRAR EL HISTORIAL ACTUAL
    st.subheader("⚠️ Zona de Peligro")
    with st.popover("🗑️ Eliminar Chat Actual"):
        st.warning(f"¿Seguro que deseas borrar permanentemente el archivo de '{st.session_state.chat_actual}'?")
        if st.button("Sí, borrar para siempre"):
            eliminar_chat_fisico(st.session_state.chat_actual)
            st.toast(f"Archivo de {st.session_state.chat_actual} eliminado.")
            nuevos_chats = listar_chats()
            st.session_state.chat_actual = nuevos_chats[0] if nuevos_chats else "Chat principal"
            st.rerun()
            


# ------------------------------------------------------------
# 3. CUERPO PRINCIPAL DE LA APLICACIÓN
# ------------------------------------------------------------
st.subheader("App de Ana para mejorar rutinas personales")

col1, col2 = st.columns([2, 1])  # Proporción 2:1 para darle más espacio al chat

# ------------------------------------------------------------
# 4. RENDERIZADO VISUAL E INTERFACES DE CHAT (EN COL2)
# ------------------------------------------------------------
with col1:  
    nivel = st.selectbox(
        "Seleccione TIPO de experto en IA",
         ["Nutrición", "Ejercicio", "General"]
    )

    st.markdown("### 💬 Interfaz de Chat")
    
    historial_pantalla = obtener_historial_para_ia(st.session_state.chat_actual)
    
    contenedor_chat = st.container(height=450, border=True)
    with contenedor_chat:
        if not historial_pantalla:
            st.caption("No hay mensajes en este chat todavía. Escribe tu consulta en la barra inferior.")
        else:
            for msg in historial_pantalla:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])
                    
    prompt = st.chat_input("Escribe tu consulta aquí y presiona Enter...")
    

with col2: 
    contenedor1 = st.container(border=True)
    # Primer contenedor en la columna 2
    with contenedor1:
        #st.info(f"💬 Conversando actualmente en: **{st.session_state.chat_actual}**")
        st.markdown("### 💬 Chat seleccionado:")       
        st.info(f"**{st.session_state.chat_actual}**")
    # Segundo contenedor en la misma columna 2 (se apila de forma vertical)
    contenedor2 = st.container(border=True)
    with contenedor2:
        #st.subheader("Contenedor Abajo")   
        st.markdown("### ⚙️ Parámetros de la IA")
        temperatura = st.slider(
            "Seleccione temperatura de pensamiento IA",
            min_value=0.0, max_value=2.0, value=0.7, step=0.1
        )   
    # Tercer contenedor en la misma columna 2 (se apila de forma vertical)    
    contenedor3 = st.container(border=True)
    with contenedor3:
        st.subheader("Manual de la App")
        with st.expander("📖 Cómo usar esta Aplicación"):
            st.markdown("""
            ### 🚀 ¡Bienvenida a tu App de Bienestar!
            Esta herramienta está diseñada para ayudarte a mejorar tus rutinas de **ejercicio** y **nutrición**, adaptadas especialmente para mujeres de 60 a 65 años.

            ---

            #### 🧠 1. Selecciona a tu Experto
            En el menú desplegable de la izquierda, elige quién quieres que te atienda:
            *   **🥗 Nutrición:** Especialista en dietas, suplementos y proteínas.
            *   **🏋️‍♀️ Ejercicio:** Especialista en rutinas, equilibrio y fisioterapia.
            *   **💡 General:** Para cualquier otra duda detallada.
            
            > **Nota:** Los expertos son estrictos. Si le preguntas de ejercicios a la nutricionista, ¡te recordará su especialidad! 😉

            #### ⚙️ 2. Configura la IA
            En la barra lateral puedes ajustar la **"Temperatura"**:
            *   **Baja (0.0 - 0.5):** Respuestas precisas y técnicas.
            *   **Alta (1.0 - 2.0):** Respuestas más creativas y variadas.

            #### 📁 3. Gestiona tus Chats
            *   **➕ Nuevo Chat:** Crea espacios diferentes para temas distintos.
            *   **📥 Exportar:** Descarga tu conversación en un archivo `.txt` para guardarla.
            *   **🗑️ Borrar:** Elimina permanentemente el chat si ya no lo necesitas.

            #### ⚠️ 4. Seguridad
            Recuerda que esta **IA** es un asistente de apoyo. **Siempre consulta con tu médico** antes de realizar cambios importantes en tu salud o comenzar ejercicios nuevos.

            ---
            *¡Disfruta de tu camino hacia una vida más activa y saludable!* ✨
            """)




# ------------------------------------------------------------
# 5. LÓGICA DE PROCESAMIENTO AL RECIBIR ENTRADA DEL CHAT_INPUT
# ------------------------------------------------------------
if prompt:
    if prompt.strip() != "":
        try:
            historial_previo = obtener_historial_para_ia(st.session_state.chat_actual)
            system_prompt = obtener_system_prompt(nivel)
            
            mensajes_completos = [{"role": "system", "content": system_prompt}] + historial_previo + [{"role": "user", "content": prompt}]
            
            cliente = Groq(api_key=st.secrets["GROQ_API_KEY"])
            respuesta = cliente.chat.completions.create(
                model="llama-3.1-8b-instant",  
                messages=mensajes_completos,
                temperature=temperatura
            )
            texto_respuesta = respuesta.choices[0].message.content
            
            guardar_en_historial(st.session_state.chat_actual, prompt, texto_respuesta)
            st.rerun()
            
        except Exception as e:
            st.error(f"Fallo en el enlace con la IA: {e}")

# Historial bruto de depuración en la barra lateral
with st.sidebar:
    st.divider()
    st.subheader(f"Archivo de texto bruto:")
    st.text_area("Contenido del archivo actual", historial_bruto if historial_bruto else "Vacío", height=150)

 
 
 
 
 
   

    