from enum import Enum
from django.db import models
from django.core.validators import validate_comma_separated_integer_list
from django.core.exceptions import ValidationError

class AIVendor(Enum):
    OPEN_AI = 1
    OLLAMA  = 2
    XAI  = 3

class SinglePromptChat(models.Model):
    name = models.CharField(max_length=200)
    module_id = models.CharField(max_length=200)
    content_id = models.CharField(max_length=200)
    max_history = models.IntegerField(default=20)
    max_volleys = models.IntegerField(default=9999)
    opener = models.TextField()
    prompt = models.TextField()
    vendor = models.IntegerField(choices=[(tag.value, tag.name) for tag in AIVendor],default=AIVendor.OPEN_AI.value)
    # model name comes from DB; for OLLAMA this could be "llama3", "mistral",
    # "qwen2", etc.; for OpenAI your usual "gpt-3.5-turbo" etc.
    model = models.CharField(max_length=200, default="gpt-3.5-turbo")
    max_tokens = models.IntegerField(default=70)
    temperature = models.FloatField(default=0.5)
    code = models.TextField(null=True, blank=True) # Python code for filter methods
    source_version = models.IntegerField(default=1)
    
    def __str__(self):
        return self.name
    
    # --- optional helpers (nice to have) ---
    @property
    def vendor_enum(self) -> AIVendor:
        """Return AIVendor enum regardless of whether DB gave us an int or the enum."""
        v = self.vendor
        return v if isinstance(v, AIVendor) else AIVendor(int(v))

    def is_openai(self) -> bool:
        return self.vendor_enum == AIVendor.OPEN_AI

    def is_ollama(self) -> bool:
        return self.vendor_enum == AIVendor.OLLAMA

    def is_grok(self) -> bool:
        return self.vendor_enum == AIVendor.XAI
    
class MoxieSchedule(models.Model):
    name = models.CharField(max_length=200)
    schedule = models.JSONField()
    source_version = models.IntegerField(default=1)
    
    def __str__(self):
        return self.name

class DevicePermit(Enum):
    UNKNOWN = 1
    PENDING = 2
    ALLOWED = 3

class MoxieDevice(models.Model):
    device_id = models.CharField(max_length=200)
    email = models.EmailField(null=True, blank=True)
    permit = models.IntegerField(choices=[(tag.value, tag.name) for tag in DevicePermit],default=DevicePermit.UNKNOWN.value)
    schedule = models.ForeignKey(MoxieSchedule, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    last_connect = models.DateTimeField(null=True, blank=True)
    last_disconnect = models.DateTimeField(null=True, blank=True)
    state = models.JSONField(null=True, blank=True)
    state_updated = models.DateTimeField(null=True, blank=True)
    robot_config = models.JSONField(null=True, blank=True)
    robot_settings = models.JSONField(null=True, blank=True)

    def is_paired(self):
        if self.robot_config:
            return not (self.robot_config.get('pairing_status') == 'unpairing')
        return True

    def __str__(self):
        return self.name if self.name else self.device_id

class MoxieLogs(models.Model):
    device = models.ForeignKey(MoxieDevice, on_delete=models.CASCADE)
    timestamp = models.TimeField()
    uid = models.IntegerField()
    tag = models.CharField(max_length=80)
    message = models.TextField()

class HiveConfiguration(models.Model):
    name = models.CharField(max_length=200)
    openai_api_key = models.TextField(null=True, blank=True, default='')
    #xai_api_key    = models.CharField(max_length=256, blank=True, default="")   
    xai_api_key    = models.TextField(blank=True, default="")  # NEW

    external_host = models.CharField(max_length=255, null=True, blank=True, default='')
    allow_unverified_bots = models.BooleanField(default=False)
    google_api_key = models.TextField(null=True, blank=True, default='')
    common_config = models.JSONField(null=True, blank=True)
    common_settings = models.JSONField(null=True, blank=True)

    # sst config
    stt_backend = models.CharField(
        max_length=16,
        choices=[("local", "Local (faster-whisper)"), ("openai", "OpenAI Whisper")],
        default="openai"
    )
    stt_url = models.CharField(max_length=255, blank=True, null=True, help_text="Local STT endpoint, e.g. http://127.0.0.1:8001/stt")
    stt_lang = models.CharField(max_length=16, default="en")
    stt_device = models.CharField(
        max_length=8,
        choices=[("auto", "Auto"), ("cpu", "CPU"), ("cuda", "CUDA (GPU)")],
        default="auto",
    )
    stt_model = models.CharField(max_length=255, blank=True, null=True, help_text="Selected local STT model path (inside container)")
    stt_compute = models.CharField(
        max_length=16,
        choices=[
            ("auto", "Auto"),
            ("int8", "int8 (CPU best)"),
            ("int8_float16", "int8/FP16 (mixed)"),
            ("float16", "float16 (GPU best)"),
            ("float32", "float32"),
        ],
        default="auto",
    )

    def __str__(self):
        return self.name

class MentorBehavior(models.Model):
    device = models.ForeignKey(MoxieDevice, on_delete=models.CASCADE)
    # Fields for MBH
    module_id = models.CharField(max_length=80, null=True, blank=True)
    content_id = models.CharField(max_length=80, null=True, blank=True)
    content_day = models.CharField(max_length=80, null=True, blank=True)
    timestamp = models.BigIntegerField()
    action = models.CharField(max_length=80, null=True, blank=True)
    instance_id = models.BigIntegerField()
    ended_reason = models.CharField(max_length=80, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['device', 'timestamp'], name='device_timestamp_idx'),
        ]

    def __str__(self):
        return f'{self.timestamp}-{self.device}-{self.module_id}/{self.content_id}-{self.action}'


class GlobalAction(Enum):
    RESPONSE = 1
    LAUNCH = 2
    CONFIRM_LAUNCH = 3
    METHOD = 4

class GlobalResponse(models.Model):
    name = models.TextField()      # common name
    pattern = models.TextField()   # regex pattern to match speech
    entity_groups = models.CharField(max_length=255, validators=[validate_comma_separated_integer_list], null=True, blank=True)
    action = models.IntegerField(choices=[(tag.value, tag.name) for tag in GlobalAction],default=GlobalAction.RESPONSE.value)
    response_text = models.TextField(null=True, blank=True)  # plaintext response
    response_markup = models.TextField(null=True, blank=True)  # markup override response
    module_id = models.CharField(max_length=80, null=True, blank=True)  # for launches, module ID to target
    content_id = models.CharField(max_length=80, null=True, blank=True) # for launches, content ID to target
    code = models.TextField(null=True, blank=True) # Python code for METHOD, w/ def get_response(request, response, entities):
    sort_key = models.IntegerField(default=1) # in case ordering matters, they order desc so high goes first
    source_version = models.IntegerField(default=1)

    # Ensure we have all we need
    def clean(self):
        if self.action == GlobalAction.METHOD.value and not self.code:
            raise ValidationError({'code': 'Code is required for METHOD action'})
        elif (self.action == GlobalAction.LAUNCH.value or self.action == GlobalAction.CONFIRM_LAUNCH.value) and not self.module_id:
            raise ValidationError({'module_id': 'Module ID is required for LAUNCH actions'})
        elif self.action != GlobalAction.METHOD.value and not self.response_text:
            raise ValidationError({'response_text': 'Response Text is required for actions except METHOD'})
        
    def __str__(self):
        return self.name
    
class PersistentData(models.Model):
    device = models.OneToOneField(MoxieDevice, on_delete=models.CASCADE)
    data = models.JSONField()

    def __str__(self):
        return f'{self.device} - Data'
