"""Constants for the TapHome Local integration."""

DOMAIN = "taphome_local"

CONF_URL = "url"
CONF_TOKEN = "token"
CONF_DEBUG_LOGGING = "debug_logging"

# --- NOVÉ KONŠTANTY PRE VÝBER ZARIADENÍ ---
CONF_EXPOSE_AS_LIGHT = "expose_as_light"
CONF_EXPOSE_AS_VALVE = "expose_as_valve"
CONF_EXPOSE_AS_SWITCH = "expose_as_switch"
CONF_EXPOSE_AS_COVER = "expose_as_cover" 
# ------------------------------------------

WEBHOOK_ID_PREFIX = "taphome_local_push_"
SIGNAL_BUTTON_PRESSED = "taphome_button_pressed_{}"
