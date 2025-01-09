import os
import random
import openai

from crawlers.saramin import SaraminCrawler

from utils.config_utils import read_config
from utils.crawler_utils import save_to_json, load_to_json

from dotenv import load_dotenv
load_dotenv('./keys.env')
openai_api_key = os.getenv('GRAVY_LAB_OPENAI')


def main(cfg):
    os.makedirs("../data", exist_ok=True)
    client = openai.OpenAI(api_key=openai_api_key)

    saramin_crawler = SaraminCrawler(cfg, client)
    # saramin_dataset = saramin_crawler.recruit_list_crawling()
    # save_to_json(saramin_dataset, "../data/saramin_summary_data.json")

    dataset = load_to_json("../data/saramin_summary_data.json")
    random.shuffle(dataset)

    total_data = saramin_crawler.recruit_post_crawling(dataset[:5])
    save_to_json(total_data, "../data/saramin_detail_data.json")


if __name__ == "__main__":
    cfg = read_config("../configs/config.yaml")
    main(cfg)