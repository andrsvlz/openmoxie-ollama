from django.apps import AppConfig

class HiveConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hive'

    def ready(self):
        from django.conf import settings
        from .mqtt.moxie_server import create_service_instance, get_instance

        log = logging.getLogger("hive")
        try:
            if get_instance() is None:
                ep = settings.MQTT_ENDPOINT
                create_service_instance(
                    ep["project"], ep["host"], ep["port"], ep.get("cert_required", True)
                )
                log.info("Moxie server singleton created in AppConfig.ready().")
        except Exception as e:
            log.warning(f"Deferred Moxie server startup: {e}")
