from machine import UART, Pin
from time import sleep, sleep_ms, time
import network
import ubinascii
import ujson
import urequests

# --- Configuração ---
WIFI_SSID = "NOME_DA_REDE"
WIFI_PASSWORD = "SENHA"
API_BASE = "http://IP_LOCAL:3000/vehicle-locations"
START_ROUTE_URL = API_BASE + "/start-route"
TRACK_URL = API_BASE + "/track"
INTERVALO_ENVIO_S = 30

# True = usa coordenadas fixas abaixo; False = lê o módulo GPS real via UART
SIMULAR_GPS = True
LAT_SIM = -15.794228
LON_SIM = -47.882168

# Usa o MAC da placa como identificador (cadastre o mesmo valor no veículo na API)
DEVICE_ID = ubinascii.hexlify(network.WLAN().config("mac"), ":").decode()

# --- Hardware ---
gps = None if SIMULAR_GPS else UART(1, baudrate=9600, rx=16, tx=17)
led = Pin(13, Pin.OUT)
btn = Pin(5, Pin.IN, Pin.PULL_UP)

# --- Estado ---
estado = False
ultimo_estado_btn = 1
ultimo_envio = 0
service_request_id = None


def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        print("Conectando ao WiFi...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)

        tentativas = 0
        while not wlan.isconnected():
            sleep(0.5)
            tentativas += 1
            if tentativas > 60:
                print("Falha ao conectar WiFi")
                return False

    print("WiFi conectado:", wlan.ifconfig())
    print("Device ID:", DEVICE_ID)
    return True


def nmea_para_decimal(valor, direcao):
    if not valor:
        return None

    valor_float = float(valor)
    graus = int(valor_float // 100)
    minutos = valor_float % 60
    decimal = graus + (minutos / 60)

    if direcao in ("S", "W"):
        decimal = -decimal

    return decimal


def parsear_gpgga(linha):
    partes = linha.split(",")

    if len(partes) < 6 or not linha.startswith("$GPGGA"):
        return None

    if partes[6] in ("", "0"):
        return None

    lat_dec = nmea_para_decimal(partes[2], partes[3])
    lon_dec = nmea_para_decimal(partes[4], partes[5])

    if lat_dec is None or lon_dec is None:
        return None

    return lat_dec, lon_dec


def iniciar_rota():
    global service_request_id, estado

    headers = {
        "Content-Type": "application/json",
        "X-Device-Identifier": DEVICE_ID,
    }

    try:
        response = urequests.post(START_ROUTE_URL, headers=headers)
        print("Start route:", response.status_code, response.text)

        if response.status_code in (200, 201):
            data = ujson.loads(response.text)
            service_request_id = data.get("id")
            print("Servico em rota, id:", service_request_id)
        else:
            service_request_id = None
            estado = False
            print("Nao foi possivel iniciar a rota. Sistema desligado.")

        response.close()
    except Exception as erro:
        service_request_id = None
        estado = False
        print("Erro ao iniciar rota:", erro)


def enviar_localizacao(latitude, longitude):
    headers = {
        "Content-Type": "application/json",
        "X-Device-Identifier": DEVICE_ID,
    }

    payload = {
        "latitude": latitude,
        "longitude": longitude,
    }

    if service_request_id is not None:
        payload["service_request_id"] = service_request_id

    try:
        response = urequests.post(
            TRACK_URL,
            headers=headers,
            data=ujson.dumps(payload),
        )
        print("Track:", response.status_code, response.text)
        response.close()
    except Exception as erro:
        print("Erro ao enviar:", erro)


def processar_coordenadas(lat_dec, lon_dec):
    global ultimo_envio

    if service_request_id is None:
        return

    print("Lat:", lat_dec)
    print("Lon:", lon_dec)
    print("---")

    agora = time()
    if agora - ultimo_envio >= INTERVALO_ENVIO_S:
        enviar_localizacao(lat_dec, lon_dec)
        ultimo_envio = agora


def ligar_sistema():
    global ultimo_envio
    ultimo_envio = 0
    iniciar_rota()


def desligar_sistema():
    global service_request_id
    service_request_id = None
    print("Sistema desligado")


# --- Inicialização ---
conectar_wifi()
print("GPS simulado" if SIMULAR_GPS else "Aguardando GPS...")
print("Pressione o botão para ligar/desligar o rastreamento.")

while True:
    leitura = btn.value()

    if leitura == 0 and ultimo_estado_btn == 1:
        sleep_ms(50)
        if btn.value() == 0:
            estado = not estado
            if estado:
                print("Sistema ligado")
                ligar_sistema()
            else:
                desligar_sistema()

    ultimo_estado_btn = leitura

    if estado and service_request_id is not None:
        led.value(1)

        if SIMULAR_GPS:
            processar_coordenadas(LAT_SIM, LON_SIM)
            sleep(1)
        elif gps.any():
            linha = gps.readline()
            if not linha:
                continue

            linha = linha.decode("ascii", "ignore").strip()

            if linha.startswith("$GPGGA"):
                resultado = parsear_gpgga(linha)
                if resultado:
                    lat_dec, lon_dec = resultado
                    processar_coordenadas(lat_dec, lon_dec)
    else:
        led.value(0)

    sleep(0.01)