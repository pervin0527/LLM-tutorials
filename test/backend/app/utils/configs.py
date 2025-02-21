import yaml
import logging

logger = logging.getLogger(__name__)

def load_config(file_path: str):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)   
        logger.info(f"Config loaded from {file_path}")
        
        return config
    

def save_config(config: dict, file_path: str):
    with open(file_path, 'w') as file:
        yaml.dump(config, file)

    logger.info(f"Config saved to {file_path}")