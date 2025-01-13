import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

class WebNode:
    """웹 페이지 노드를 구성하는 클래스"""
    def __init__(self, url):
        self.url = url
        self.children = []

    def add_child(self, child_node):
        self.children.append(child_node)

def is_valid_url(url, base_domain):
    """URL 유효성 검사 및 도메인 제한"""
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme) and parsed.netloc == base_domain

def get_links(url, base_domain):
    try:
        response = requests.get(url, timeout=5)

        # 인코딩 문제 해결: chardet이나 utf-8 기본값
        if not response.encoding or response.encoding.lower() == "ISO-8859-1".lower():
            response.encoding = "utf-8"  # utf-8로 강제 설정

        soup = BeautifulSoup(response.text, "html.parser")

        links = set()
        for anchor in soup.find_all("a", href=True):
            link = urljoin(url, anchor["href"])
            if is_valid_url(link, base_domain):
                links.add(link)
        return list(links)
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return []



def build_web_tree(root_url):
    """웹 트리를 생성하는 함수 (방문 URL 확인)"""
    visited = set()
    base_domain = urlparse(root_url).netloc
    root = WebNode(root_url)
    queue = [(root, root_url)]  # (노드, URL)

    while queue:
        current_node, current_url = queue.pop(0)

        if current_url in visited:
            continue
        visited.add(current_url)

        # Get child links
        child_links = get_links(current_url, base_domain)
        for link in child_links:
            if link not in visited:
                child_node = WebNode(link)
                current_node.add_child(child_node)
                queue.append((child_node, link))

    return root

def print_tree(node, depth=0):
    """트리를 계층적으로 출력하는 함수"""
    print("  " * depth + f"- {node.url}")
    for child in node.children:
        print_tree(child, depth + 1)

if __name__ == "__main__":
    root_url = input("Enter the root URL (e.g., https://example.com): ").strip()
    
    print("Building web tree...")
    root_node = build_web_tree(root_url)
    print("\nWeb Tree Structure:")
    print_tree(root_node)
