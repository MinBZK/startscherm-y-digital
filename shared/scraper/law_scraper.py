from itertools import count
from markdownify import MarkdownConverter
from bs4 import BeautifulSoup, Tag
from requests import Session
from pandas import read_csv
from re import search
from os import path, makedirs
from json import dump
from pathlib import Path
from datetime import datetime

from models import LawChapter, LawInfo, LawArticle


class LawInfoScraper:
    def __init__(self, law_urls_file: str):
        self.law_urls_file: Path = Path(__file__).parent / law_urls_file
        self.session: Session = Session()
        self.converter: MarkdownConverter = MarkdownConverter()
        self.law_chapters: dict[str, dict[str, str]] = {}
        self.law_articles: dict[str, dict[str, str]] = {}
        self.date = datetime.now().strftime("%Y-%m-%d")


    def _read_laws_to_dict(self) -> dict:
        law_urls = read_csv(self.law_urls_file)
        return law_urls.to_dict(orient="index")


    def _get_law_info(self) -> dict[str, LawInfo]:
        laws_metadata = self._read_laws_to_dict()
        # print(laws_metadata)
        laws: dict[str, LawInfo] = {}

        for law in laws_metadata:
            # print("law:", law)
            laws[laws_metadata[law]["title"]] = (
                LawInfo(
                    id = laws_metadata[law]["id"],
                    title = laws_metadata[law]["title"],
                    description = laws_metadata[law]["description"],
                    url = laws_metadata[law]["url"],
                )
            )
        return laws


    # def get_law(self, law: LawInfo) -> str:
    def get_law(self, law: LawInfo) -> BeautifulSoup:
        response = self.session.get(law.url)
        soup = BeautifulSoup(response.text, "html.parser")
        return soup
        # return self.converter.convert(soup.prettify())


    def _get_chapter_id_and_title(self, chapter: Tag, i: int) -> tuple[str, str]:
        try:
            chapter_h3 = chapter.find("h3")
            if not chapter_h3:
                chapter_id = f"unknown_id_{i}"
                chapter_title = ""
            else:
                chapter_id = chapter_h3["id"]
                chapter_title = chapter_h3.text
                return chapter_id, chapter_title
        except KeyError:
            chapter_id = f"unknown_id_{i}"
            chapter_title = "unknown_title"

        return chapter_id, chapter_title


    def _get_chapter_content(self, chapter: Tag) -> str:
        return self.converter.convert(chapter.prettify())
        # return self.converter.convert(chapter.text)


    def _get_chapter_url(self, chapter: Tag) -> str:
        try:
            url = str(chapter.find(class_="popuppermanentelink")["href"])
        except KeyError:
            return "unknown_url"
        return url


    def get_law_chapters(self, law: BeautifulSoup, law_name: str) -> dict[str, str]:
        chapters_dict: dict[str, str] = {}

        chapters = law.find_all(class_="article__header--law article__header--law--chapter")
        for i, chapter_html in enumerate(chapters):
            # print(chapter_html)

            chapter_id, chapter_title = self._get_chapter_id_and_title(chapter_html, i)
            chapter_url = self._get_chapter_url(chapter_html)
            chapter_body = self._get_chapter_content(chapter_html)


            chapters_dict[chapter_title] = LawChapter(
                id = i,
                law_name = law_name,
                chapter_id = chapter_id,
                title = chapter_title,
                body = chapter_body,
                url = "".join(["https://wetten.overheid.nl", chapter_url]),
                date = self.date,
            ).model_dump()
        return chapters_dict


    def _get_article_number_from_title(self, article_title: str) -> str:
        # res = search(r"\s(\d+(\.?(\d+\.?(\w)?\.?)?)?)\s", article_title)
        print(f"Article title: {article_title}")
        # res = search(r"\s(\d+(\.?(\d+)?\.?(\w)?\.?))\s", article_title)
        res = search(r"Artikel\s+([\d:.\w]+)", article_title)
        try:
            return str(res.groups()[0])
        except:
            return "unknown_article_number"


    def _get_article_id_title_and_number(self, article: Tag, i: int) -> tuple[str, str]:
        try:
            article_h4 = article.find("h4")
            if not article_h4:
                article_id = f"unknown_id_{i}"
                article_title = ""
                article_number = ""
            else:
                article_id = article_h4["id"]
                article_title = article_h4.text
                article_number = self._get_article_number_from_title(article_title)
                return article_id, article_title, article_number
        except KeyError:
            article_id = f"unknown_id_{i}"
            article_title = "unknown_title"
            article_number = ""

        return article_id, article_title, article_number


    def _get_article_content(self, article: Tag, article_title: str) -> str:
        # breakpoint()
        try:
            article.find('ul', {'aria-label': f'Lijst met mogelijke acties voor {article_title}.'}).decompose()
        except AttributeError:
            return self.converter.convert(article.prettify())
        return self.converter.convert(article.prettify())
        # return self.converter.convert(article.text)

    def _get_article_url(self, article: Tag) -> str:
    # First try the expected class
        permalink = article.find("a", class_="popuppermanentelink")
        if permalink and permalink.get("href"):
            return permalink["href"]

        # Fallback: look for any anchor tag with 'Artikel' in the href
        for a in article.find_all("a", href=True):
            href = a["href"]
            if "Artikel" in href:
                return href

        return "unknown_url"


    def get_law_articles(
            self, law: BeautifulSoup, law_name: str
    ) -> dict[str, LawArticle]:
        article_dict: dict[str, str] = {}

        # def not_article_header(class_name: str) -> bool:
        #     unwanted_class_name = re.compile("article__header--law").search(class_name)
        #     wanted_class_name = re.compile("artikel").search(class_name)
        #     return wanted_class_name and not unwanted_class_name
        #
        # articles = law.find_all(class_=not_article_header)
        articles = law.find_all(class_="artikel")

        count = 0

        for article in articles:
            if not 'div class="artikel" id="Hoofdstuk' in str(article):
                continue
            count += 1

            article_id, article_title, article_number = \
                self._get_article_id_title_and_number(article, count)
            article_url = self._get_article_url(article)
            if article_url == "unknown_url":
                continue
            article_body = self._get_article_content(article, article_title)


            article_dict[article_number] = LawArticle(
                id = count,
                law_name = law_name,
                article_id = article_id,
                article_number = article_number,
                title = article_title,
                body = article_body,
                url = "".join(["https://wetten.overheid.nl", article_url]),
                date = self.date,
            ).model_dump()
        return article_dict

    def save_law_articles(self) -> None:
        print("Saving law articles...")
        if not path.exists(Path(__file__).parent.parent / "laws/articles"):
            makedirs(Path(__file__).parent.parent / "laws/articles")
        dump(
            self.law_articles,
            open(Path(__file__).parent.parent / "laws/articles/law_articles.json", "w"),
            indent=2,
        )
        print("Finished saving law articles.")


    def run(self) -> None:
        print("Running law scraper...")
        self.law_info: dict[str, LawInfo] = self._get_law_info()
        laws: dict[str, BeautifulSoup] = {}

        for law_name, law in self.law_info.items():
            law_markdown = self.get_law(law)
            # print(law_markdown)
            laws[law_name] = self.get_law(law)
            self.law_chapters[law_name] = self.get_law_chapters(
                laws[law_name], law_name
            )
            self.law_articles[law_name] = self.get_law_articles(
                laws[law_name], law_name
            )

            # breakpoint()
            # with open(f"../laws/{law_name}.md", "w") as f:
            #     f.write(law_markdown)
            
            # self.get_law_articles(law)
            # self.save_law_articles(law)

        print("Finished scraping laws.")



if __name__ == "__main__":
    # TODO: Use argparser to pass the law_urls_file, but default to "law_urls.csv"
    scraper = LawInfoScraper("law_urls.csv")
    scraper.run()
    scraper.save_law_articles()
