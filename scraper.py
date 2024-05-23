from pathlib import Path
import requests               # Används för att skicka HTTP-förfrågningar.
from bs4 import BeautifulSoup # Används för att parsa HTML-dokument.


# scrape: hämtar sidan och extraherar länkar från ett specifikt HTML-element. 
# Returnerar en uppsättning länkar i ett dictionary-format där nyckeln är ett segment av URL:en.
class NBILinkScraper:
    def __init__(self) -> None:
        self.base_url = "https://www.nbi-handelsakademin.se"

    def scrape(self, pathname, query=""):
        url = f"{self.base_url}/{pathname}/{query}"
        all_links_raw = ExtractHtml.soup(url).select(
            ".wpgb-card-media-content-bottom > a[href]"
        )

        extracted_links = set(link["href"] for link in all_links_raw)
        extracted_links = {url.split("/")[-2]: url for url in extracted_links}

        return extracted_links

# scrape: Hämtar och returnerar textinnehåll från specifika HTML-element på en sida.
class DataScraper:
    def __init__(self, pathname, query="") -> None:
        self.links = NBILinkScraper().scrape(pathname, query)

    def scrape(self, subject):
        description_raw = ExtractHtml.soup(self.links[subject]).select(
            ".wpb_text_column span, p,h4+ul li"
        )

        description = " ".join(
            [
                raw.text
                for raw in description_raw
                if not "\xa0" in raw.get_text()  # or "@" in raw.text)
            ]
        )

        return description


class EducationScraper(DataScraper):
    def __init__(self) -> None:
        super().__init__("utbildningar", query="/?_programkurser=program")


class CourseScraper(DataScraper):
    def __init__(self) -> None:
        super().__init__("kurser")

# soup: En statisk metod som hämtar en webbsida och returnerar en BeautifulSoup-objekt för att parsa HTML.
class ExtractHtml:
    @staticmethod
    def soup(url):
        response = requests.get(url)
        return BeautifulSoup(response.text, "html.parser")

# extract_text: Extraherar text från alla element som matchar en given CSS-selektor och returnerar som en sammansatt sträng.
# extract_list: Returnerar en lista med text från alla element som matchar en given CSS-selektor.
class ScrapeFormat:
    def __init__(self, pathname) -> None:
        base_url = NBILinkScraper().base_url
        url = f"{base_url}/{pathname}"
        self.soup = ExtractHtml.soup(url)

    def extract_text(self, tag):
        text_list = [tag.text for tag in self.soup.select(tag)]
        return " ".join(text_list)

    def extract_list(self, tag):
        return [tag.text for tag in self.soup.select(tag)]

# En specialiserad klass för att skrapa ansökningssidor och extrahera 
# specifik information såsom beskrivningar, tidsplan, tillgängliga utbildningar och ansökningssteg.
class ApplicationScraper:
    def __init__(self, pathname="ansokan") -> None:
        self._scraper = ScrapeFormat(pathname)

    @property
    def description(self):
        return self._scraper.extract_text("h1, h1~*")

    @property
    def time_plan(self) -> list:
        return self._scraper.extract_list("#tab-tidplan ul li, #tab-tidplan ul + p")

    @property
    def available_educations(self) -> list:
        return self._scraper.extract_list("#tab-ansok li")

    @property
    def application_steps(self) -> list:
        return self._scraper.extract_list("h3 a")

# En specialiserad klass för att skrapa FAQ-sidor och extrahera frågor och svar.
class FaqScraper:
    def __init__(self, pathname="faq") -> None:
        self._scraper = ScrapeFormat(pathname)

    @property
    def faq(self) -> list:
        return self._scraper.extract_list(".toggle.default a, .toggle.default p")


class ExportScrapedText:
    def __init__(self, filename, content) -> None:

        data_path = Path(__file__).parent / "data"
        data_path.mkdir(parents=True, exist_ok=True)

        with open(data_path / filename, "w") as file:
            file.write(content)
