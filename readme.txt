

To use XAi Grok and Local Ollama 

get an XAi api key and deposit funds https://x.ai/api
and an OpenAi Key https://openai.com/index/openai-api/

Initial Setup:

Install docker:
sudo apt-get install ./docker-desktop-amd64.deb

If that doesnt work you might need to install the docker-ce-cli

sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
# Add the repository to Apt sources:
echo   "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" |   sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin





Install Ollama:

curl -fsSL https://ollama.com/install.sh | sh

Download whatever model you want to try from https://ollama.com/search i am using a lightweight one on an older machine (CPU only)

This will download the model that we are using in the example content
ollama run llama3.2:3b

once it is running stop it
ollama stop llama3.2:3b

verify it is installed
ollama list


Set up server environment:

Running in virtual environment Ubuntu 24.04 probably works in other distros

sudo apt install python3-venv
python3 -m venv .venv
cd openmoxie
source .venv/bin/activate
python -m pip install --upgrade pip

Install requirements
python3 -m pip install -r requirements.txt

Make initial migrations
python3 site/manage.py makemigrations

Run initial migration
python3 site/manage.py migrate

Create a superuser
python site/manage.py createsuperuser

Run the initial data import
python3 site/manage.py init_data

You may need to edit site\openmoxie\settings.py and edit this block to point to localhost for mqtt although it is likely already updated.

MQTT_ENDPOINT = {
    'host': 'localhost',
    'port': 8883,
    'project': 'openmoxie',
    'cert_required': False,
}

Start the MQTT Broker
docker compose up -d mqtt

(this should relaunch on reboot [sudo docker ps] to check status)

start the openmoxie server
python3 site/manage.py runserver --noreload


If everything went well you should be able to open the moxie server control panel at 
http://localhost:8000/

Visit http://localhost:8000/hive/setup
enter the API keys for XAi and OpenAi currently the "speech to text" conversion for all the providers still uses remote OpenAi Whisper so you need both API keys (The next version i will try to integrate a local STT)



**USE at your own risk I take no License or Responsibility for the (sometimes rude and offensive language) results of these prompts or models ** 
***NOT FOR KIDS!***
To load the sample schedules and single promt chats for XAi (Grok grok-3-mini) and local ollama (running llama3.2:3b)
click "choose file"
browse to find "~/moxieserver/samples/moxie_server_content.json"
click "upload for review"
select the schedules and conversations then "import"


Switching Ai provider or model (activate a schedule)

Click the moxie device name under devices and select the schedule from the dropdown
ie only_chat_xai_grok

Change moxie schedule

The "only_chat_xai_grok" and "only_chat_ollama_local" are both single prompt chat schedules. 
You can create your own schedules and add additional content from moxie defaults using "Moxie schedules" if you like.

example from Grok schedule: 
{"provided_schedule": [{"module_id": "OPENMOXIE_CHAT", "content_id": "grok"}], "chat_request": {"module_id": "OPENMOXIE_CHAT", "content_id": "grok"}}

module_id - value should match single prompt chat "Module ID:"
content_id - value should match single prompt chat "Content id:"

Change single prompt chat:

Click admin under devices and use superuser credentials to edit database entries for single prompt chat ie "OpenMoxie Chat - XAi - grok-3-mini"

"Module ID:" should be OPENMOXIE_CHAT (for single prompt)  - read by schedule

"Content id:" should be unique to your single prompt chat. the schedule calls this to activate the content and model - read by schedule

"Opener:" is the line that moxie uses to start the chat after waking up

"Prompt:" This is where you can change the attitude and behavior using the system prompt

"Vendor:" select your Ai provider for this 


"Model:" change text field to the full name of the model <whatever the model name is>

if you want to try a different local models they need to be installed first using 

ollama run <whatever the model name is> 

it should download and launch automatically so you can stop the newly installed model after it runs

ollama stop <whatever the model name is> 

to see available local models use

ollama list 

*you can also experiment with different remote API models by entering the name ie "grok-4"

"Max tokens:" controls the length of response (fewer tokens = shorter response), setting this to 0 will allow unlimited tokens when using larger models locally

"Temperature:" adjust the jibberish level

After any database updates click refresh from DB
you might need to go through the moxie mentor check and sometimes moxie needs to go to sleep to update active schedule or model
it doesn't hurt to restart the server either.

python3 site/manage.py runserver --noreload

I found that changing the face color seems to send the schedule update also.

Enjoy!
