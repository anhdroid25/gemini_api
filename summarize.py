import google.generativeai as genai
import argparse
import os
import json
import trafilatura
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv

# URL used: https://www.cbsnews.com/news/venezuela-fighter-jets-navy-ship-trump-maduro/

load_dotenv() #loads .env file which contains API key


def fetch_extract(url, max_retries=3, timeout: int = 30) -> str:
    #fetch and extract method using trafilatura
    for attempt in range(max_retries): #retry for 3 times
        download = trafilatura.fetch_url(url, no_ssl=True) #fetch URL
        if download:
            extract_text = trafilatura.extract(download) #extract main content
            if extract_text: 
                return extract_text
    
    #fall back method
    for attempt in range(max_retries): #retry for 3 times
        response = requests.get(url, timeout=timeout) #request to fetch 
        if response.status_code == 200: #return 200 if successful
            soup = BeautifulSoup(response.text, 'html.parser') #parse HTML
            text = soup.get_text()
            if text:
                return text
            
    return ""

def main():
    #handles arguments
    parser = argparse.ArgumentParser(description="Summarize a webpage in 3 sentences")
    #the argument has to be in "--url" format
    parser.add_argument("--url", required=True,help="This is the URL to run the summary")
    #parse user arguments
    args = parser.parse_args()
    #store variable in URL
    url = args.url

    #fetching HTML content
    text = fetch_extract(url)
    if not text:
        print(json.dumps({"Summary": "Error fetching or extracting content", 
                          "Keywords": [], 
                          "References": url}, indent=2, ensure_ascii=False))
        return

    #setting up API key
    context = text.strip() #extract the text to feed to Gemini

    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    configuration={
        "temperature": 0.2,
        "top_k": 40,
        "top_p": 0.9,
        "max_output_tokens": 512,
        "response_mime_type": "application/json", #has to be in json format

    }
    #choosing model
    client = genai.GenerativeModel("gemini-1.5-flash", generation_config=configuration)

    #prompt engineering:
    prompt=f"""
    You are a professional summarizer. Summarize the following URL's content in a single paragraph with 3 sentences. Keep the summary factual, concise, and single-paragraphed. Do not add any additional information or context. Return valid JSON in this format:
    {{
        "From": "{url}",
        "Summary": "<One paragraph that contains 3 sentences>",
        "Keywords": ["<keyword1>", "<keyword2>", "<keyword3>", "<keyword4>", "<keyword5>"],
        "References": "{url}"
    }}
    Content: {context}
    """.strip()

    #generate the output
    gemini_response = client.generate_content(prompt)

    #parse into JSON format
    print("Raw response:", gemini_response.text)  # Debug: print the raw response
    try:
        data = json.loads(gemini_response.text)
    except json.JSONDecodeError as e:
        print("Error parsing JSON:", e)
        data = {"Summary": "Error parsing summary", "Keywords": [], "References": url}
    print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()