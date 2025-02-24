import os
import random
import openai

from crawlers.wanted import WantedCrawler
from crawlers.saramin import SaraminCrawler

from utils.config_utils import read_config
from utils.crawler_utils import save_to_json, load_to_json

from dotenv import load_dotenv
load_dotenv('./keys.env')
openai_api_key = os.getenv('GRAVY_LAB_OPENAI')


def main(cfg):
    os.makedirs(cfg['save_path'], exist_ok=True)
    client = openai.OpenAI(api_key=openai_api_key)

    ## 사람인
    # saramin_crawler = SaraminCrawler(cfg, client)
    # saramin_dataset = saramin_crawler.recruit_list_crawling()
    # save_to_json(saramin_dataset, f"{cfg['save_path']}/data/saramin_summary_data.json")

    # dataset = load_to_json(f"{cfg['save_path']}/data/saramin_summary_data.json")
    # crawling_data, failed_data = saramin_crawler.recruit_post_crawling(dataset)
    # save_to_json(crawling_data, f"{cfg['save_path']}/data/saramin_detail_data.json")
    # save_to_json(failed_data, f"{cfg['save_path']}/data/failed_detail_data.json")

    ## 원티드
    wanted_crawler = WantedCrawler(cfg, client)
    crawling_data = wanted_crawler.scroll_and_collect_incremental_urls()
    save_to_json(crawling_data, f"{cfg['save_path']}/data/wanted_data.json")


if __name__ == "__main__":
    cfg = read_config("../configs/config.yaml")
    main(cfg)