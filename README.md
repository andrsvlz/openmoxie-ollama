# OpenMoxie with Local Ollama, XAi Grok, and Local STT Support

<p align="center">
  <img src="./site/static/hive/openmoxie_logo.svg" width="200" height="200" alt="OpenMoxie Logo">
</p>

Welcome!  

If you're looking for a solution to run your **Embodied Moxie Robot** ...Maybe give it a different personality or run some unfiltered LLM models, Your in the right place!

Si tienes una GPU NVIDIA y quieres que Docker la utilice (Faster-Whisper,
Ollama), instala también el runtime de NVIDIA:

```bash
sudo apt-get install -y nvidia-driver-535 nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

Reinicia si el instalador lo solicita. Los servicios `stt` y `ollama` en
`docker-compose.yml` ya declaran soporte CUDA; sin este runtime Docker no los
arrancará.

---

## 📦 Based on the amazing work by [jbeghtol/openmoxie](https://github.com/jbeghtol/openmoxie)

<a href="https://github.com/sponsors/vapors"> # Sponsor my work! and future development </a>
---
---

## ⚠ Disclaimer

> **USE AT YOUR OWN RISK**  
> I take no responsibility for the output of these prompts or models. Or any resulting mental / physical health issues that arise from using them. 

>⚠️ **Not for children** ⚠️— may contain offensive language.

---

# 🚀 Quick Overview 

## Components

This project includes:

- **Django app** for basic web services and database (SQLite3).
- **MQTT-based remote chat** service with single prompt inferences from OpenAI.
- **Ollama for Local chat** ollama running llama3.2:3b - with the ability to update models.
- **Faster-Whisper Local (STT)** docker or venv for fully offline transcription (listening).
- **Support for XAi Grok chat** XAI api support as an alternative to OpenAi.


## 🛠 What You Need

0. A Moxie robot with the firmware update — or flash it yourself.
1. A computer (Ubuntu Linux / mac / Windows) on the same wireless network.

---

## 🔧 Easy Setup 

---

## 🪟 Windows / Mac / Ubuntu - Quick Start

  Requires Windows with virtualization enabled.

1. Install Docker Desktop (enable WSL2 engine) Download from Docker
   
    https://docs.docker.com/get-started/get-docker/
    

3. In PowerShell or bash:  Clone or download and build the repository (Downloads llama3.2:3b - 2gb)


    clone:

    ```powershell
  
      git clone https://github.com/vapors/openmoxie-ollama
      cd openmoxie-ollama
  
    ```
  
    build:

    ```powershell
  
      docker compose up -d model-init data-init stt mqtt ollama ollama-init web
  
    ```

4. Open the app
   
   Go to http://localhost:8000



---

## 💬 Using XAi Grok & OpenAi

1. Get an **XAi API key** and deposit funds: [https://x.ai/api](https://x.ai/api)
2. Get an **OpenAI API key**: [https://openai.com/index/openai-api/](https://openai.com/index/openai-api/)



----

## 🖥 More Complex Setup UBUNTU (.venv)

1. Clone this repo to your home directory

```bash
cd ~
git clone https://github.com/vapors/openmoxie-ollama.git

```
2. download models for local stt (speech recognition)

```bash

cd openmoxie-ollama
chmod +x scripts/get_models_linux.sh
./scripts/get_models_linux.sh faster-whisper-large

```
Model files should download to **~/openmoxie-ollama/site/services/stt/models** 

* Follow Remaining Instructions In Order

### 1️⃣ Install Docker Desktop or CLI
Download Docker
https://docs.docker.com/desktop/setup/install/linux/ubuntu/

```bash
#cd to downloads folder
sudo apt-get install ./docker-desktop-amd64.deb
```

If that doesn’t work, Just install the CLI manually:
```bash
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
```
Add the repository for docker:
```bash
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

---

### 2️⃣ Install Ollama and run a model
```bash
curl -fsSL https://ollama.com/install.sh | sh
```
Download and test a model (2GB CPU-friendly model example used in sample content):
more models(gemma, deepseek, gpt-oss, etc...) can be found at https://ollama.com/search keep the size reasonable for your computers power
```bash
ollama run llama3.2:3b
#test the model response and then you can exit by typing "/bye"

# you can stop the model it will relaunch if activated
ollama stop llama3.2:3b # stop model by name
ollama list # show all available models
```

---

### 3️⃣ Set Up Server Environment
```bash
sudo apt install python3-venv
cd ~/openmoxie-ollama
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```
Install dependencies:
```bash
pip install -r requirements.txt
```
Run migrations:
```bash
python3 site/manage.py makemigrations
python3 site/manage.py migrate
```
Create superuser:
```bash
python site/manage.py createsuperuser
```
Import initial data:
```bash
python3 site/manage.py init_data
```

### 4️⃣ Start MQTT Broker and STT service for Speech Transcription
```bash
sudo docker compose up -d mqtt stt
```
*(Re-launches on reboot — check with `sudo docker ps`)*

- The STT docker reads model files from **./site/services/stt/models → /models** downloaded previously
- You can check health and model of stt:
  ```bash
  curl -s http://127.0.0.1:8001/health
  # should output {"ok": true, "model": "...", "device": "cpu|cuda", "compute": "int8|float16"}
  ```
  models can be selected in admin

> **Nota:** `faster-whisper-medium` ofrece buen balance tamaño/precisión (~0.6 GB, ≈3 GB VRAM). Si tu hardware es más potente puedes cambiar a `faster-whisper-large-v3` manualmente desde la configuración.
> para ejecutarse en `float16`. Si tu hardware no lo soporta cambia a un modelo
> más pequeño desde **Setup → Speech-to-Text** o redefiniendo `STT_MODEL` antes
> de iniciar el servicio.

Arranca también el runtime de Ollama (con soporte CUDA por defecto) y precarga
los modelos definidos en el compose:

```bash
sudo docker compose up -d ollama ollama-init
```

Comprueba que Ollama detectó tu GPU:

```bash
sudo docker exec -it $(sudo docker compose ps -q ollama) ollama info | \
  grep -E 'device|Backend'
```
---

### 5️⃣ Start the OpenMoxie Server and do the usual Wifi and or Migration QR code
```bash
python3 site/manage.py runserver --noreload
```
### Main admin
Open [http://localhost:8000/](http://localhost:8000/)  

### API Setup
Setup page: [http://localhost:8000/hive/setup](http://localhost:8000/hive/setup)  

Enter **XAi** and **OpenAI** API keys.


# Choose options for Local or OpenAi whisper STT

> ⚠️ OpenAI Whisper for STT — still requires API key

---

## ⚙ Loading Sample Schedules & Chats

1. Click **"Choose file"**
2. Select:
   ```
   ~/openmoxie-ollama/samples/ollama_local_sample.json
   ```
3. Click **"Upload for review"**
4. Select schedules and conversations → **Import**

---

## 🔄 Switch to a different AI Provider or Model by changing schedules

1. Click your Moxie device name under **Devices**.
2. Select a schedule from the dropdown (e.g., `only_chat_xai_grok`).

---

---

## 📝 Changing Moxies Attitude - Editing Single Prompt Chats

In Admin → Single prompt chats → Edit:
http://localhost:8000/admin/hive/singlepromptchat/

- **Module ID:** `OPENMOXIE_CHAT`
- **Content ID:** unique to your chat.
- **Opener:** What Moxie says to start the chat.
- **Prompt:** System prompt for attitude/behavior.
- **Vendor:** AI provider.
- **Model:** Full model name.

Load additional Local model example:
```bash
ollama run <model-name>
ollama stop <model-name>
ollama list
```
In addition to changing the local models you can experiment with other remote API models for example: `"grok-4"`

- **Max tokens:** Fewer Tokens = shorter response. For local ollama 0 = unlimited (may take forever to respond.)
- **Temperature:** Adjust randomness level.

After changes:
```bash
python3 site/manage.py runserver --noreload
```
Changing face color may also trigger updates.

---


## 📅 Edit Moxie Schedule

In Admin → Moxie schedules → Edit:
http://localhost:8000/admin/hive/moxieschedule/

Schedules:
- `only_chat_xai_grok`
- `only_chat_ollama_local`

Example schedule JSON:
```json
{
  "provided_schedule": [
    { "module_id": "OPENMOXIE_CHAT", "content_id": "grok" }
  ],
  "chat_request": { "module_id": "OPENMOXIE_CHAT", "content_id": "grok" }
}
```



## ⚠ Disclaimer

> **USE AT YOUR OWN RISK**  
> I take no responsibility for the output of these prompts or models.  
> **Not for children** — may contain offensive language.

---

## 🎉 Enjoy OpenMoxie!

---

---
# Additional Technical details and troubleshooting


### 🔇 Offline Speech-to-Text (Local STT)

You can run speech-to-text **fully offline** using a small local service based on **Faster-Whisper**.

**Preferred (Docker)**
- Use `docker compose up -d stt` as shown above. The service exposes:
  - `/health` → model/device/compute
  - `/stt` → transcription endpoint
  - `/control/models` → discover available model folders under `/models`
  - `/control/reload` → hot-switch model/device/compute without restart

**Alternative (venv)**
If you don’t want Docker, you can run the service directly:
```bash
sudo apt-get update && sudo apt-get install -y ffmpeg

# from repo root
export STT_MODEL="$(pwd)/site/services/stt/models/faster-whisper-medium"
export STT_DEVICE=auto            # auto prefers CUDA when available
export STT_COMPUTE=auto           # auto → float16 on CUDA, int8 on CPU
uvicorn --app-dir site services.stt.stt_service:app --host 0.0.0.0 --port 8001
```

Tip: the helper script `scripts/run_stt_local.sh` auto-installs the CUDA-enabled
CTranslate2 wheel whenever `nvidia-smi` is available. Override `CUDA_INDEX_URL`
if you need a different CUDA build (defaults to the cu121 artifacts published on
the PyTorch wheel index).

---

## 🔧 Configure STT in Setup

Open **Setup → Speech-to-Text**:
- **Backend**: Local (faster-whisper) or OpenAI Whisper
- **Local STT URL**: `http://127.0.0.1:8001/stt` (Docker and venv default)
- **Default language**: `en`
- **Device / Compute / Model**: choose from dropdowns when Local is selected  
  (Model list comes from the running STT service; adding a new model folder under `site/services/stt/models/` shows up after refresh.)

When you click **Save**, the server requests a **hot reload** on the STT service so changes apply instantly (no container restart needed).

---


## ⚙️ Environment Knobs

**Django/OpenMoxie**
- `LLM_PROVIDER=ollama|openai|xai`
- `OLLAMA_HOST=http://127.0.0.1:11434`
- `OLLAMA_MODEL=llama3.2:3b`
- `STT_BACKEND=local|openai`
- `STT_URL=http://127.0.0.1:8001/stt`
- `STT_LANG=en`

**Local STT service (Docker or venv)**
- `STT_MODEL=/models/faster-whisper-medium` *(Docker path; venv can use `site/services/stt/models/...`)*
- `STT_DEVICE=auto|cpu|cuda`
- `STT_COMPUTE=auto|int8|int8_float16|float16|float32`
- `STT_VAD=1|0` (silence filtering)

---

## ✅ Health & Debug

- STT service: `curl -s localhost:8001/health`
- List available models: `curl -s localhost:8001/control/models | jq .`
- Switch model/device/compute on the fly:
  ```bash
  curl -s -X POST -H "Content-Type: application/json"     --data '{"model":"/models/faster-whisper-base.en","device":"auto","compute":"int8"}'     http://127.0.0.1:8001/control/reload | jq .
  ```
- Django probe (shell):
```python
from hive.stt import transcribe_wav_bytes
wav = open("/path/to.wav","rb").read()
print(transcribe_wav_bytes(wav,"en")[0])
```

---

## 🧰 Troubleshooting

- “address already in use” → another STT instance is on that port. Kill it or use a new port.
- “python-multipart required” (venv) → `pip install python-multipart`.
- Empty transcripts → try `STT_VAD=0` to test very quiet audio.
- GPU not used in Docker → set `gpus: all` and `STT_DEVICE=cuda`; verify with `/health` shows `"device":"cuda"`.

---
