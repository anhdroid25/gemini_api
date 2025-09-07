import google.generativeai as genai
import argparse
import os
import json
import argparse
import trafilatura
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv

load_dotenv() #loads .env file which contains API key

def main():
    parser = argparse.ArgumentParser(description="Summarize a webapage in 3 sentences")
    parser.add_argument("url", help="The URL of the webpage to summarize")
    args = parser.parse_args()
    url = args.url

    #fetching HTML content
    response = requests.get(url)
    content = response.text
    
    
    #content extraction !!! still missing site policies and handle errors with retries !!!
    text = trafilatura.extract(content)

    #setting up API key
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    configuration={
        "temperature": 0.2,
        "top_k": 40,
        "top_p": 0.9,
        "max_output_tokens": 512,
        "response_mime_type": "application/json" #this ensure json format is returned

    }
    #choosing model
    client = genai.GenerativeModel("gemini-1.5-flash", generation_config=configuration)

    #prompt engineering:
    prompt=f"""You are a professional summarizer. Summarize the following URL's content in a single paragraph with 3 setences. Keep the summmry factual, concise, and single-paragraphed. Do not add any additional information or context. Return JSON file like this:
    {{'Summary': '<One paragraph that contains 3 sentences>',
    'Keywords': ['<keyword1>', '<keyword2>', '<keyword3>', '<keyword4>', '<keyword5>'],
    'References': "{url}"
    }}"""

    #generate the output
    response = client.generate_content(prompt)

    #parse into JSON format
    try:
        data = json.loads(response.text)
    except json.JSONDecodeError as e:
        print("Error parsing JSON:", e)
        data = {"Summary": "Error parsing summary", "Keywords": [], "References": url}
    print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()