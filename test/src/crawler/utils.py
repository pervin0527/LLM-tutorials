import json

def save_tree(tree, filename="crawl_result.json"):
    """크롤링 결과를 JSON 파일로 저장"""
    with open(filename, "w", encoding="utf-8") as json_file:
        json.dump(tree, json_file, ensure_ascii=False, indent=4)
        
    print(f"크롤링 결과가 {filename} 파일로 저장되었습니다.")