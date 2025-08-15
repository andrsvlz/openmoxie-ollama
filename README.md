# OpenMoxie with Local Ollama and XAi Support

<p align="center">
  <img src="./site/static/hive/openmoxie_logo.svg" width="200" height="200" alt="OpenMoxie Logo">
</p>

Welcome!  

If you're looking for a solution to run your **Embodied Moxie Robot** in case their cloud infrastructure shuts down, you're in the right place!  

Some of you may be concerned this is going to be complicated—don’t worry. For those who just want to install and run something, we’ll cover that first.

---

## 📦 Based on the amazing work by [jbeghtol/openmoxie](https://github.com/jbeghtol/openmoxie)

---

## 🛠 What You Need

0. A Moxie robot with the firmware update — or flash it yourself.
1. A computer (Ubuntu/Linux/possibly Windows) on the same wireless network.
2. An **OpenAI** account and **XAi** credits to pay for Speech-to-Text and Chat.
3. **Ollama** and **Docker** installed.  
   - Docker Desktop: [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)  
   - *(No paid license needed for personal use)*

---

# 🚀 Quick Overview (Not So Quick Start)

## Components

This project includes:

- **Django app** for basic web services and database (SQLite3).
- **pymqtt**-based service code to handle device communication.
- **MQTT-based Speech-to-Text (STT)** provider using OpenAI Whisper.
- **MQTT-based remote chat** service with single prompt inferences from OpenAI.

---

## 💬 Using XAi Grok & Local Ollama

1. Get an **XAi API key** and deposit funds: [https://x.ai/api](https://x.ai/api)
2. Get an **OpenAI API key**: [https://openai.com/index/openai-api/](https://openai.com/index/openai-api/)

---

## 🖥 Initial Setup

1. Clone this repo
2. Follow instructions in order

### 1️⃣ Install Docker
```bash
sudo apt-get install ./docker-desktop-amd64.deb
```
If that doesn’t work, install the CLI manually:
```bash
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
```
Add the repository:
```bash
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

---

### 2️⃣ Install Ollama
```bash
curl -fsSL https://ollama.com/install.sh | sh
```
Download and test a model (CPU-friendly example):
```bash
ollama run llama3.2:3b
ollama stop llama3.2:3b
ollama list
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

---

### 4️⃣ Configure MQTT (if needed)
Edit `site/openmoxie-ollama/settings.py`:
```python
MQTT_ENDPOINT = {
    'host': 'localhost',
    'port': 8883,
    'project': 'openmoxie',
    'cert_required': False,
}
```

---

### 5️⃣ Start MQTT Broker
```bash
docker compose up -d mqtt
```
*(Re-launches on reboot — check with `sudo docker ps`)*

---

### 6️⃣ Start the OpenMoxie Server
```bash
python3 site/manage.py runserver --noreload
```
Open [http://localhost:8000/](http://localhost:8000/)  
Setup page: [http://localhost:8000/hive/setup](http://localhost:8000/hive/setup)  

Enter **XAi** and **OpenAI** API keys.

> ⚠️ Currently, all providers still use remote OpenAI Whisper for STT — both API keys are required.

---

## ⚙ Loading Sample Schedules & Chats

1. Click **"Choose file"**
2. Select:
   ```
   ~/moxieserver/samples/moxie_server_content.json
   ```
3. Click **"Upload for review"**
4. Select schedules and conversations → **Import**

---

## 🔄 Switching AI Provider or Model

1. Click your Moxie device name under **Devices**.
2. Select a schedule from the dropdown (e.g., `only_chat_xai_grok`).

---

## 📅 Change Moxie Schedule

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

---

## 📝 Editing Single Prompt Chats

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

## ⚠ Disclaimer

> **USE AT YOUR OWN RISK**  
> I take no responsibility for the output of these prompts or models.  
> **Not for children** — may contain offensive language.

---

## 🎉 Enjoy OpenMoxie!

# fetch models (small.en + base.en)
scripts/get_models.sh faster-whisper-small.en faster-whisper-base.en
# then:
docker compose up -d stt mqtt




chmod +x scripts/get_models.sh
# Example: fetch the two you’ve been using
scripts/get_models.sh faster-whisper-small.en faster-whisper-base.en
