import os

EXECUTE_HOST = os.getenv("JUPYTER_ASCENDING_EXECUTE_HOST", "localhost")
EXECUTE_PORT = os.getenv("JUPYTER_ASCENDING_EXECUTE_PORT", 12517)

EXECUTE_HOST_LOCATION = (EXECUTE_HOST, EXECUTE_PORT)
EXECUTE_HOST_URL = f"http://{EXECUTE_HOST_LOCATION[0]}:{EXECUTE_HOST_LOCATION[1]}"

LOG_LEVEL = os.getenv("JUPYTER_ASCENDING_LOG_LEVEL", "INFO")
SHOW_TO_STDOUT = os.getenv("JUPYTER_ASCENDING_SHOW_TO_STDOUT", False)
# can either set this environment variable, or simply call logger.enable("jupyter_ascending") in order to see
# future log messages (obviously will be missing any messages that happend before your call to enable)
IS_LOGGING_ENABLED = os.getenv("JUPYTER_ASCENDING_IS_LOGGING_ENABLED", False)
# TODO: it would be great for this to be an environment variable... but unfortunately we need to know the value
#  on the javascript side as well, and I'm not sure how to get this value over there easily. Would love help!
SYNC_EXTENSION = "sync"
