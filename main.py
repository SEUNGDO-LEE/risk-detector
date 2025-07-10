#main.py
import os
import streamlit as st

st.set_page_config(page_title="Augmented LLM 콘텐츠 대응 Agent", layout="wide")

st.title("📺 Augmented LLM 기반 디지털 콘텐츠 대응 Agent")

# API 키 설정
os.environ["OPENAI_API_KEY"] = st.secrets['OPENAI_KEY']
os.environ["YOUTUBE_API_KEY"] = st.secrets["YOUTUBE_KEY"]

from content_generator import get_video_metadata, fetch_filtered_rss_articles, get_transcript, summarize_with_gpt, search_youtube_video, detect_risk

tab1, tab2 = st.tabs(["📰 RSS 뉴스 분석", "📹 YouTube 영상 분석"])

with tab1:
    st.title("📰 뉴스 기사 크롤링")
    raw_keywords = st.text_input("🔍 뉴스 검색 키워드를 입력하세요 (예: ETF, 리스크, 위험, 변동성, 금융, 파생, 자산운용)")

    if raw_keywords:
        keyword_list = [kw.strip() for kw in raw_keywords.split(",") if kw.strip()]
        st.write("📌 입력된 키워드 리스트:", raw_keywords)
    
        with st.expander("📡 RSS Feed 기반 관련 뉴스 수집"):
            etf_articles = fetch_filtered_rss_articles(keyword_list)
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
                            result = detect_risk(all_summaries)
                            st.markdown("🧠 **GPT-4 리스크 분석 결과 (전체 기사 요약 기반)**:")
                            st.warning(result)
                            
                        except Exception as e:
                            st.error(f"❌ GPT 분석 중 오류 발생: {str(e)}")

with tab2:
    st.title("🎬 YouTube 영상 크롤링")

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
                        title, desc = get_video_metadata(video['video_id'])
                        transcript = get_transcript(video['video_id'], 'ko')
                        
                        summary = summarize_with_gpt(title, desc, transcript)
                        
                        st.text_area("영상 분석 내용", summary)
                    except Exception as e:
                        st.error(f"❌ 영상 내용 요약 중 오류 발생: {str(e)}")
