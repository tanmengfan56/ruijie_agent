from difflib import SequenceMatcher

def get_similarity(text1: str, text2: str) -> float:
    return round(SequenceMatcher(None, text1, text2).ratio(),4)

if __name__ == '__main__':
    print(get_similarity("人工智能是未来的关键技术","AI 技术将引领未来发展"))