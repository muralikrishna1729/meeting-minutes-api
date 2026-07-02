import logging
import json
import datetime  

class JSONFormatter(logging.Formatter):
    def format(self,record:logging.LogRecord)->str:
        log_dict = {
            "time": datetime.datetime.now(datetime.UTC),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "correlation_id": getattr(record, "correlation_id", None)
        }
        return json.dumps(log_dict)
        
def setup_logging()->None:
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)