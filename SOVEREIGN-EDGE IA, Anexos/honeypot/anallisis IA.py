import json
import subprocess
import os
import requests

WEBHOOK_URL = "https://discord.com/api/webhooks/1497713671638614037/Ieuj9v6HhFTvdu5GuOc7R41-UtLow58Z9Kq4ozs91Ygl-ir9dYynR3p5dAJq81XwffAZ"

def obtener_geolocalizacion(ip):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}?fields=country,city,isp", timeout=5)
        datos = response.json()
        if datos['status'] == 'success':
            return f"{datos['city']}, {datos['country']} (ISP: {datos['isp']})"
        return "Ubicación desconocida"
    except:
        return "Error al rastrear IP"

def enviar_discord(mensaje):
    data = {"content": mensaje}
    try:
        response = requests.post(WEBHOOK_URL, json=data, timeout=10)
        if response.status_code == 204:
            print("✅ Notificación enviada a Discord")
        else:
            print(f"❌ Error Discord: {response.status_code}")
    except Exception as e:
        print(f"❌ Error de conexión con Discord: {e}")

def obtener_ultimos_ataques():
    log_file = os.path.expanduser('~/honeypot/cowrie-logs/cowrie.json')
    if not os.path.exists(log_file):
        return None

    ataques = []
    with open(log_file, 'r') as f:
        for linea in f:
            try:
                datos = json.loads(linea)
                if datos.get('eventid') == 'cowrie.command.input':
                    ataques.append({
                        "comando": datos.get('input'),
                        "ip": datos.get('src_ip')
                    })
            except:
                continue
    return ataques[-5:]

def consultar_dolphin(comandos_texto):
    prompt = (
        f"Analiza estos ataques detectados en mi Honeypot:\n\n{comandos_texto}\n\n"
        "Dime exactamente qué intentan hacer y asigna un nivel de peligrosidad (Bajo, Medio, Alto, Crítico). "
        "Responde de forma técnica y directa. Al final, añade una sección llamada 'VEREDICTO FINAL' "
        "donde recomiendes: Baneo inmediato, Monitorizar o Ignorar."
    )

    print("\n--- 🛡️ GENERANDO ANÁLISIS DE INTELIGENCIA ---")

    try:
        resultado = subprocess.check_output(
            ['docker', 'exec', 'ollama', 'ollama', 'run', 'dolphin-llama3', prompt],
            text=True
        )

        print(resultado)

        mensaje_para_discord = (
            "🌍 **INTELIGENCIA DE AMENAZAS - SOVEREIGN EDGE** 🌍\n"
            "**Registro de Actividad:**\n"
            f"```\n{comandos_texto}\n```\n"
            "🧠 **Análisis de Dolphin-IA:**\n"
            f"{resultado}"
        )

        enviar_discord(mensaje_para_discord)

    except Exception as e:
        print(f"❌ Error al conectar con Dolphin: {e}")

print("🔍 Escaneando registros de actividad sospechosa...")
ataques = obtener_ultimos_ataques()

if ataques:
    texto_final = ""
    for ataque in ataques:
        geo = obtener_geolocalizacion(ataque['ip'])
        texto_final += f"📍 IP: {ataque['ip']} ({geo}) | CMD: {ataque['comando']}\n"

    consultar_dolphin(texto_final)
else:
    print("✅ No se encontraron comandos sospechosos en los logs.")
