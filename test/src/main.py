from crawler.web_tree import crawl_website
from crawler.utils import save_tree

if __name__ == "__main__":
    root_name = "현대자동차그룹"
    root_url = "https://audit.hyundai.com/"
    web_tree = crawl_website(root_url)
    save_tree(web_tree, f"../data/{root_name}.json")

    