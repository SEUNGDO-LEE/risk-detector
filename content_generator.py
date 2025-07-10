# content_generator.py
import os
import streamlit as st
#import isodate
import re
from datetime import timedelta
from langchain_openai import ChatOpenAI

import feedparser
from youtube_transcript_api import YouTubeTranscriptApi
# pip install --upgrade google-api-python-client
from googleapiclient.discovery import build

os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_KEY"]
openai_api_key = os.environ.get("OPENAI_API_KEY")

@st.cache_resource
def get_youtube_api():
    return build("youtube", "v3", developerKey=os.environ.get("YOUTUBE_KEY"))

def generate_response(input_text):
    model = ChatOpenAI(model="gpt-4o", temperature=0.7, api_key=openai_api_key)
    response = model.invoke(input_text)
    return response.content

youtube = get_youtube_api()
def get_video_metadata(video_id):
   
    res = youtube.videos().list(part="snippet", id=video_id).execute()
    snippet = res["items"][0]["snippet"]
    return snippet["title"], snippet["description"]

def summarize_with_gpt(title, description, transcript):
    
    
    prompt = f"""다음은 유튜브 영상의 제목과 설명과 자막이야:

제목: {title}
설명: {description}
자막: {transcript}

이 내용을 500자 이내로 요약해줘. 사회적·정치적·윤리적 또는 법적 리스크가 있다면 함께 알려줘."""
    
    return generate_response(prompt)

    #chat_completion = openai.chat.completions.create(
    #    model="gpt-4o",
    #    messages=[{"role": "user", "content": prompt}]
    #)
    #return chat_completion.choices[0].message.content

def detect_risk(text):
    prompt = (
        "다음 콘텐츠에서 사회적, 정치적, 윤리적 또는 법적 리스크 요소를 요약해줘. "
        "리스크가 있는 경우 해당 문장을 직접 인용해서 표시해줘.\n\n"
        f"{text}"
    )
    
    return generate_response(prompt)
    #chat_completion = openai.chat.completions.create(
    #    model="gpt-4o",
    #    messages=[{"role": "user", "content": prompt}]
    #)
    #return chat_completion.choices[0].message.content

def get_transcript(video_id, lang_list=["ko", "en"]):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=lang_list)
        text = " ".join([seg["text"] for seg in transcript])
        return text
    except Exception as e:
        return f"❌ 자막 불러오기 실패: {str(e)}"
    

def fetch_filtered_rss_articles(keyword_list):
    results = []
    
    RSS_FEEDS = [
    "https://seekingalpha.com/etfs-and-funds/etf-articles.xml",
    "https://www.hani.co.kr/rss/economy/",
    "https://www.boannews.com/media/news_rss.xml",
    "https://www.yna.co.kr/finance/all?site=rss"
    ]   

    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = getattr(entry, "title", "")
            summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
            content = title + " " + summary

            if any(kw.lower() in content.lower() for kw in keyword_list):
                results.append({
                    "title": title,
                    "summary": summary,
                    "link": getattr(entry, "link", "#")
                })

    return results

def parse_iso8601_duration(duration_str):
    # 정규표현식 기반 ISO 8601 duration 파서
    pattern = re.compile(
        r'^P'                        # 시작 P
        r'(?:(\d+)D)?'               # 일
        r'(?:T'                      # T 다음에 시간 정보
        r'(?:(\d+)H)?'               # 시
        r'(?:(\d+)M)?'               # 분
        r'(?:(\d+(?:\.\d+)?)S)?'     # 초
        r')?$'
    )
    match = pattern.match(duration_str)
    if not match:
        raise ValueError(f"Invalid ISO 8601 duration: {duration_str}")
    
    days, hours, minutes, seconds = match.groups()
    return timedelta(
        days=int(days) if days else 0,
        hours=int(hours) if hours else 0,
        minutes=int(minutes) if minutes else 0,
        seconds=float(seconds) if seconds else 0,
    )
    
def get_video_duration_seconds(video_id):
    
    response = youtube.videos().list(
        part="contentDetails",
        id=video_id
    ).execute()

    duration_iso = response["items"][0]["contentDetails"]["duration"]
    #duration = isodate.parse_duration(duration_iso)
    duration = parse_iso8601_duration(duration_iso)
    return duration.total_seconds()

def search_youtube_video(query):
        search_response = youtube.search().list(
            q=query,
            part="snippet",
            maxResults=10,
            type="video"
        ).execute()

        for item in search_response["items"]:
            video_id = item["id"]["videoId"]
            title = item["snippet"]["title"]
            url = f"https://www.youtube.com/watch?v={video_id}"

            try:
                #duration_sec = get_video_duration_seconds(video_id)
                #if duration_sec >= 200:
                    return [{
                        "video_id": video_id,
                        "title": title,
                        "url": url
                    }]
            except Exception as e:
                
                print(f"⛔ duration 조회 실패: {e}")
                return [] 

    
