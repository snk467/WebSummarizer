import os
import sys
import validators
import argparse
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from openai import OpenAI
from rich.console import Console
from rich.markdown import Markdown
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException


SYSTEM_PROMPT = "You are an assistant that analyzes the contents of a website \
and provides a short summary, ignoring text that might be navigation related. \
Respond in markdown."

class Website:

    @staticmethod
    def __get_page_content(url):
        driver = webdriver.Chrome()
        driver.get(url)
        WebDriverWait(driver, 30).until(lambda d: d.execute_script('return document.readyState') == 'complete')
        html_content = driver.page_source
        driver.quit()

        return html_content

    def __init__(self, url):
        """
        Create this Website object from the given url using the BeautifulSoup library
        """
        self.url = url
        page_content = self.__get_page_content(url)
        soup = BeautifulSoup(page_content, 'html.parser')
        self.title = soup.title.string if soup.title else "No title found"
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()
        self.text = soup.body.get_text(separator="\n", strip=True)

def user_prompt_for(website):
    user_prompt = f"You are looking at a website titled {website.title}"
    user_prompt += "\nThe contents of this website is as follows; \
please provide a short summary of this website in markdown. \
If it includes news or announcements, then summarize these too.\n\n"
    user_prompt += website.text
    return user_prompt

def messages_for(website):
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt_for(website)}
    ]

def summarize(url):
    website = Website(url)
    response = openai.chat.completions.create(
        model =  os.getenv("OPENAI_MODEL"),
        messages = messages_for(website)
    )
    return response.choices[0].message.content

def print_summary(url):
    summary = summarize(url)
    Console().print(Markdown(summary))

if __name__ == '__main__':
    load_dotenv(f"{os.getenv('ENVIRONMENT')}.env", override=True)
    openai = OpenAI()

    parser = argparse.ArgumentParser()
    parser.add_argument('url', nargs='?', help="URL of a website to be summarize.")
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    args = parser.parse_args()

    if not validators.url(args.url):
        print(f"{args.url} is not a valid URL.")
        parser.print_help()
        sys.exit(1)

    try:
        print_summary(args.url)
    except WebDriverException:
        print(f"There was an error loading {args.url} website.")
        sys.exit(1)
