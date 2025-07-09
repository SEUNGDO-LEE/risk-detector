#main.py
import os
import streamlit as st
import pandas as pd
import numpy as np
import os
from openai import OpenAI
import isodate
import assemblyai as aai
import feedparser
from youtube_transcript_api import YouTubeTranscriptApi
# pip install --upgrade google-api-python-client
from googleapiclient.discovery import build

st.set_page_config(page_title="Augmented LLM 콘텐츠 대응 Agent", layout="wide")

st.title("📺 Augmented LLM 기반 디지털 콘텐츠 대응 Agent")

# API 키 설정
os.environ["YOUTUBE_API_KEY"] = st.secrets["YOUTUBE_KEY"]
os.environ["ASSEMBLY_API_KEY"] = st.secrets["ASSEMBLYAI_KEY"]
os.environ["OPENAI_API_KEY"] = st.secrets['OPENAI_KEY']

aai.settings.api_key = os.environ.get("ASSEMBLY_API_KEY")

@st.cache_resource
def get_youtube_api():
    return build("youtube", "v3", developerKey=os.environ.get("YOUTUBE_KEY"))
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

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
            
tab1, tab2 = st.tabs(["📰 RSS 뉴스 분석", "📹 YouTube 영상 분석"])

with tab1:
    st.title("📰 뉴스 기사 크롤링")
    raw_keywords = st.text_input("🔍 뉴스 검색 키워드를 입력하세요 (예: ETF, 리스크, 위험, 변동성, 금융, 파생, 자산운용)")

    if raw_keywords:
        keyword_list = [kw.strip() for kw in raw_keywords.split(",") if kw.strip()]
        st.write("📌 입력된 키워드 리스트:", raw_keywords)
    
        with st.expander("📡 RSS Feed 기반 관련 뉴스 수집"):
            
            etf_articles = []
    
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
                        etf_articles.append({
                            "title": title,
                            "summary": summary,
                            "link": getattr(entry, "link", "#")
                        })

            
            for art in etf_articles:
                st.markdown(f"#### 🔗 [{art['title']}]({art['link']})")
                st.write(art['summary'])
        
            all_summaries = "\n\n".join([f"[{art['title']}]\n{art['summary']}" for art in etf_articles])

            if st.button("⚠ 전체 뉴스 요약 기반 GPT-4 리스크 분석"):
               
                if len(all_summaries) < 100:
                    st.error("⚠ 분석할 뉴스 요약이 부족합니다.")
   
                else:
                    with st.spinner('리스크 분석 중'):
                        try:
                            MAX_TOKENS = 3000
                            if len(all_summaries.split()) > MAX_TOKENS:
                                all_summaries = " ".join(all_summaries.split()[:MAX_TOKENS])
                                prompt = (
                                    "다음 콘텐츠에서 사회적, 정치적, 윤리적 또는 법적 리스크 요소를 요약해줘. "
                                    "리스크가 있는 경우 해당 문장을 직접 인용해서 표시해줘.\n\n"
                                    f"{all_summaries}"
                                )
                                
                                response = client.chat.completions.create(
                                    model="gpt-4o",
                                    messages=[{"role": "user", "content": prompt}]
                                )
                            st.markdown("🧠 **GPT-4 리스크 분석 결과 (전체 기사 요약 기반)**:")
                            st.warning(response)
                            
                        except Exception as e:
                            st.error(f"❌ GPT 분석 중 오류 발생: {str(e)}")
                           
with tab2:
    st.title("🎬 YouTube 영상 크롤링")
    youtube = get_youtube_api()
    keyword = st.text_input("🔍 YouTube 검색 키워드를 입력하세요 (예: ETF, 리스크, 위험, 변동성, 금융, 파생, 자산운용)")

    if keyword:
        with st.spinner("YouTube 영상 검색 중..."):
            
            video = search_youtube_video(keyword)[0]
            if not video:
                st.error("❌ 적합한 영상을 찾을 수 없습니다. 키워드를 바꿔보세요.")
                
            else:  
                    st.markdown(f"### 🎥 [{video['title']}])")
                    st.markdown(f"🔗 URL: {video['url']}")
                    
                    try:
                        video_response = youtube.videos().list(
                            part="contentDetails",
                            id=video['video_id']
                        ).execute()
                    
                        duration_iso = video_response["items"][0]["contentDetails"]["duration"]
                        duration = isodate.parse_duration(duration_iso)
                        title, desc = duration.total_seconds()
                        
                        try:
                            transcript = YouTubeTranscriptApi.get_transcript(video['video_id'], languages='ko')
                            text = " ".join([seg["text"] for seg in transcript])
                            result_transcript = text
                        except Exception as e:
                            st.error(f"❌ 자막 불러오기 실패: {str(e)}")
                        
                        prompt = f"""다음은 유튜브 영상의 제목과 설명과 자막이야:

                            제목: {title}
                            설명: {desc}
                            자막: {result_transcript}
                            
                            이 내용을 500자 이내로 요약해줘. 사회적·정치적·윤리적 또는 법적 리스크가 있다면 함께 알려줘."""
                            
                        summary = client.chat.completions.create(
                                model="gpt-4o",
                                messages=[{"role": "user", "content": prompt}]
                            )
                        st.text_area("영상 분석 내용", summary)
                    except Exception as e:
                        st.error(f"❌ 영상 내용 요약 중 오류 발생: {str(e)}")
