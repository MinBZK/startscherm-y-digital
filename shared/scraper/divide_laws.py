import json
from pathlib import Path
from os import path, makedirs


if __name__ == "__main__":
    print("Dividing law articles...")
    json_file: str = "laws/articles/law_articles.json"
    with open(
        Path(__file__).parent.parent / json_file,
        "r"
    ) as f:
        law_articles = json.load(f)

    for law_name, articles in law_articles.items():
        for article_number, article in articles.items():

            _article_number: str = article_number.strip(".")

            article_file: str = f"laws/articles/{law_name}/{_article_number}.json"

            if not path.exists(Path(__file__).parent.parent / f"laws/articles/{law_name}"):
                makedirs(Path(__file__).parent.parent / f"laws/articles/{law_name}")

            with open(
                Path(__file__).parent.parent / article_file,
                "w"
            ) as f:
                json.dump(article, f, indent=2)
    print("Finished dividing law articles.")
