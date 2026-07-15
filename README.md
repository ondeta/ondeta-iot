# OndeTá IoT

Módulo IoT da plataforma **OndeTá**, responsável pelo rastreamento em tempo real de veículos prestadores de serviço utilizando uma placa **BitDogLab** executando **MicroPython**, um módulo **GPS NEO-6M** e comunicação com a API do sistema via HTTPS.

O dispositivo identifica automaticamente o veículo através do endereço MAC da placa, inicia uma rota junto à API e envia periodicamente sua localização para acompanhamento em tempo real pelo aplicativo.

### Visão Geral

O dispositivo possui três responsabilidades principais:

1. Conectar-se à rede Wi-Fi.
2. Obter a localização atual através do módulo GPS.
3. Enviar periodicamente a posição para a API OndeTá.

O rastreamento é iniciado e interrompido através de um botão físico presente no dispositivo.

### Tecnologias

- BitDogLab
- MicroPython
- UART
- GPS NEO-6M
- HTTPS
- REST API
- JSON
- Wi-Fi

### Hardware Utilizado

- BitDogLab
- Módulo GPS NEO-6M
- LED indicador
- Botão Push Button
- Antena GPS
- Rede Wi-Fi

### Arquitetura

```text
                Satélites GPS
                       │
                       ▼
                Módulo GPS NEO-6M
                       │ UART
                       ▼
                   BitDogLab
                       │
             MicroPython Firmware
                       │
             HTTPS (Wi-Fi)
                       │
                       ▼
                OndeTá API
                       │
                       ▼
              Aplicativo Mobile
```

### Funcionamento

#### Inicialização

Ao energizar o dispositivo:

- inicializa o GPS;
- configura o botão;
- configura o LED;
- conecta ao Wi-Fi;
- identifica o dispositivo pelo MAC Address.

#### Identificação do Veículo

Cada placa utiliza seu endereço MAC como identificador único.

```python
DEVICE_ID = MAC Address da BitDogLab
```

Esse identificador deve estar previamente cadastrado na API para que o veículo seja reconhecido.

#### Início da Rota

Quando o botão é pressionado:

```
Botão
      │
      ▼
Iniciar Rastreamento
      │
      ▼
POST /vehicle-locations/start-route
```

A API responde com o identificador da solicitação de serviço.

```
service_request_id
```

Esse identificador será utilizado durante todo o rastreamento.

#### Leitura do GPS

O módulo GPS comunica-se utilizando UART.

```
GPS
 │
UART
 │
 ▼
BitDogLab
```

O firmware suporta sentenças:

- `$GPGGA`
- `$GNGGA`

A partir dessas sentenças são extraídos:

- latitude
- longitude

#### Conversão das Coordenadas

O GPS fornece coordenadas no formato NMEA.

O firmware converte automaticamente para graus decimais.

Exemplo:

```
1534.1254,S

↓

-15.568756
```

#### Envio da Localização

Após iniciar uma rota, a localização é enviada periodicamente.

Fluxo:

```
GPS

↓

Latitude
Longitude

↓

JSON

↓

POST /vehicle-locations/track
```

Payload enviado:

```json
{
  "latitude": -6.12345,
  "longitude": -35.12345,
  "service_request_id": "..."
}
```

### Simulação de GPS

O projeto possui modo de desenvolvimento.

```python
SIMULAR_GPS = True
```

Nesse modo são utilizadas coordenadas fixas.

```python
LAT_SIM
LON_SIM
```

Isso permite testar toda a comunicação com a API mesmo sem um módulo GPS conectado.

## Estados do Sistema

O firmware possui dois estados principais.

#### Desligado

- LED apagado
- não envia localização
- rota inexistente

#### Ligado

- LED aceso
- GPS ativo
- rota iniciada
- localização enviada periodicamente

### Fluxo Completo

```text
Ligar BitDogLab

↓

Conectar Wi-Fi

↓

Aguardar botão

↓

Usuário pressiona botão

↓

Iniciar rota

↓

Receber service_request_id

↓

Ler GPS continuamente

↓

Converter coordenadas

↓

Enviar localização

↓

Repetir
```

### Comunicação com a API

#### Iniciar rota

```
POST

/vehicle-locations/start-route
```

Header:

```
X-Device-Identifier
```

#### Enviar localização

```
POST

/vehicle-locations/track
```

Payload:

```json
{
  "latitude": "...",
  "longitude": "...",
  "service_request_id": "..."
}
```

### Configuração

As configurações principais encontram-se no início do arquivo.

```python
WIFI_SSID

WIFI_PASSWORD

API_BASE

INTERVALO_ENVIO_S

SIMULAR_GPS

LAT_SIM

LON_SIM
```

### Estrutura do Projeto

```
ondeta-iot/main.py
```

Toda a lógica da aplicação encontra-se concentrada no arquivo principal.

### Componentes do Firmware

#### conectar_wifi()

Responsável pela conexão da BitDogLab à rede Wi-Fi.

#### iniciar_rota()

Solicita à API o início do rastreamento.

#### enviar_localizacao()

Envia latitude e longitude para a API.

#### parsear_gga()

Extrai informações das sentenças NMEA.

#### nmea_para_decimal()

Converte coordenadas NMEA para graus decimais.

#### atualizar_coordenadas()

Atualiza as coordenadas mais recentes obtidas pelo GPS.

#### tentar_enviar_se_devido()

Controla o intervalo de envio das posições.

#### ligar_sistema()

Inicializa o rastreamento.

#### desligar_sistema()

Finaliza a rota localmente.

### Indicadores

#### LED

Ligado:

```
Rastreamento ativo
```

Desligado:

```
Sistema parado
```

---

#### Botão

Pressão única:

```
Alterna entre

Ligado

↓

Desligado
```

### Dependências

Bibliotecas MicroPython utilizadas:

- machine
- network
- ubinascii
- ujson
- urequests
- time

### Instalação

#### Gravar MicroPython na BitDogLab

Instale uma versão compatível do firmware MicroPython.

#### Configurar Wi-Fi

Edite:

```python
WIFI_SSID

WIFI_PASSWORD
```

#### Configurar API

```python
API_BASE
```

#### Configurar modo de operação

```python
SIMULAR_GPS = False
```

para utilizar o GPS real.

Ou

```python
SIMULAR_GPS = True
```

para simulação.

#### Executar

Envie o arquivo:

```
main.py
```

para a placa utilizando:

- Thonny
- mpremote
- ampy

Ao reiniciar a BitDogLab, o firmware será executado automaticamente.

### Integração com a Plataforma OndeTá

Este módulo faz parte do ecossistema **OndeTá**, integrando-se aos demais componentes:

- **OndeTá API**: gerenciamento das rotas, veículos e armazenamento das localizações.
- **OndeTá App**: visualização do veículo em tempo real, acompanhamento das solicitações e interação entre clientes e prestadores de serviço.

O firmware foi desenvolvido para ser leve, simples e adequado ao ambiente embarcado da BitDogLab, servindo como ponte entre o hardware de rastreamento e a infraestrutura da plataforma.

### Licença

Projeto integrante da plataforma **OndeTá**, destinado ao rastreamento de veículos prestadores de serviço utilizando dispositivos IoT.
