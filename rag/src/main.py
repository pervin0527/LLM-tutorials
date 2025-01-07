import os

from crawlers.saramin import SaraminCrawler

from utils.config_utils import read_config
from utils.crawler_utils import save_to_json



def main(cfg):
    os.makedirs("../data", exist_ok=True)

    saramin_crawler = SaraminCrawler(cfg)
    saramin_dataset = saramin_crawler.crawling()
    save_to_json(saramin_dataset, "../data/saramin_raw.json")
        
if __name__ == "__main__":
    cfg = read_config("../configs/config.yaml")
    main(cfg)