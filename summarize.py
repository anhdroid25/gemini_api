import google.generativeai as genai
import argparse
import os
import json
import trafilatura
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv


load_dotenv() #loads .env file which contains API key


def fetch_extract(url, max_retries=3, timeout: int = 30) -> str:
    #fetch and extract method
    for attempt in range(max_retries):
        download = trafilatura.fetch_url(url, no_ssl=True)
        if download:
            extract_text = trafilatura.extract(download)
            if extract_text:
                return extract_text
    
    #fall back methhod
    for attempt in range(max_retries):
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text()
            if text:
                return text
            
    return ""

def main():
    parser = argparse.ArgumentParser(description="Summarize a webapage in 3 sentences")
    parser.add_argument("--url", required=True,help="This is the URL to run the summary")
    args = parser.parse_args()
    url = args.url

    #fetching HTML content
    text = fetch_extract(url)
    if not text:
        print(json.dumps({"Summary": "Error fetching or extracting content", 
                          "Keywords": [], 
                          "References": url}, indent=2, ensure_ascii=False))
        return


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
    gemini_response = client.generate_content(prompt)

    #parse into JSON format
    try:
        data = json.loads(gemini_response.text)
    except json.JSONDecodeError as e:
        print("Error parsing JSON:", e)
        data = {"Summary": "Error parsing summary", "Keywords": [], "References": url}
    print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()