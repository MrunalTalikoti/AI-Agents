import asyncio
import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import re
import platform
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import arxiv
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
from datetime import datetime
import streamlit as st
import aiohttp

# FastAPI setup
app = FastAPI()

# CORS setup for potential API access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API keys (replace with your own)
YOUTUBE_API_KEY = "YOUR_YOUTUBE_API_KEY"  # Get from Google Cloud Console

# Data models
class UserPrompt(BaseModel):
    topic: str

class TopicData(BaseModel):
    title: str
    tags: List[str]

class VideoSummary(BaseModel):
    video_id: str
    title: str
    summary: str

class PaperSummary(BaseModel):
    paper_id: str
    title: str
    summary: str

class BlogPost(BaseModel):
    title: str
    content: str
    tags: List[str]

# YouTube API search
async def youtube_search(topic: str) -> List[Dict]:
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        request = youtube.search().list(q=topic, part='snippet', maxResults=3, type='video')
        response = request.execute()
        videos = []
        for item in response['items']:
            video_id = item['id']['videoId']
            title = item['snippet']['title']
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
                transcript_text = " ".join([entry['text'] for entry in transcript])
            except NoTranscriptFound:
                transcript_text = "No transcript available."
            videos.append({
                'video_id': video_id,
                'title': title,
                'transcript': transcript_text[:1000]  # Limit for brevity
            })
        return videos
    except HttpError as e:
        raise HTTPException(status_code=500, detail=f"YouTube API error: {str(e)}")

# Arxiv API search
async def arxiv_search(topic: str) -> List[Dict]:
    try:
        search = arxiv.Search(query=topic, max_results=3, sort_by=arxiv.SortCriterion.SubmittedDate)
        papers = []
        for result in search.results():
            papers.append({
                'paper_id': result.entry_id,
                'title': result.title,
                'abstract': result.summary
            })
        return papers
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Arxiv API error: {str(e)}")

# Save draft to local file
async def save_draft(blog: BlogPost) -> str:
    try:
        os.makedirs("drafts", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = re.sub(r'[^\w\s-]', '', blog.title).replace(' ', '_').lower()
        filename = f"drafts/{safe_title}_{timestamp}.md"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(blog.content)
        return os.path.abspath(filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save draft: {str(e)}")

# Agent 1: Prompt Reader
async def prompt_reader_agent(prompt: str) -> TopicData:
    title = prompt.capitalize()
    tags = [word.lower() for word in re.findall(r'\w+', prompt)[:5]]
    return TopicData(title=title, tags=tags)

# Agent 2: YouTube Researcher
async def youtube_researcher_agent(topic_data: TopicData) -> List[VideoSummary]:
    videos = await youtube_search(topic_data.title)
    summaries = []
    for video in videos:
        summary = f"Summary of '{video['title']}': {video['transcript'][:100]}..."
        summaries.append(VideoSummary(video_id=video['video_id'], title=video['title'], summary=summary))
    return summaries

# Agent 3: Paper Researcher
async def paper_researcher_agent(topic_data: TopicData) -> List[PaperSummary]:
    papers = await arxiv_search(topic_data.title)
    summaries = []
    for paper in papers:
        summary = f"Summary of '{paper['title']}': {paper['abstract'][:100]}..."
        summaries.append(PaperSummary(paper_id=paper['paper_id'], title=paper['title'], summary=summary))
    return summaries

# Agent 4: Blog Writer
async def blog_writer_agent(topic_data: TopicData, video_summaries: List[VideoSummary], paper_summaries: List[PaperSummary]) -> BlogPost:
    title = f"Exploring {topic_data.title}: Insights from Videos and Research"
    content = f"# {title}\n\n"
    content += f"## Introduction\nThis blog post dives into {topic_data.title}, combining insights from popular YouTube videos and cutting-edge research papers.\n\n"
    content += "## YouTube Video Insights\n"
    for vs in video_summaries:
        content += f"### {vs.title}\n{vs.summary}\n\n"
    content += "## Research Paper Findings\n"
    for ps in paper_summaries:
        content += f"### {ps.title}\n{ps.summary}\n\n"
    content += "## Conclusion\nThis exploration of {topic_data.title} shows the synergy between public media and academic research.\n\n"
    content += f"**Keywords**: {', '.join(topic_data.tags)}"
    return BlogPost(title=title, content=content, tags=topic_data.tags)

# Agent 5: Draft Saver
async def draft_saver_agent(blog: BlogPost) -> str:
    return await save_draft(blog)

# Agent 6: Orchestrator
async def orchestrator_agent(prompt: str) -> Dict:
    try:
        topic_data = await prompt_reader_agent(prompt)
        youtube_task = youtube_researcher_agent(topic_data)
        paper_task = paper_researcher_agent(topic_data)
        video_summaries, paper_summaries = await asyncio.gather(youtube_task, paper_task)
        blog = await blog_writer_agent(topic_data, video_summaries, paper_summaries)
        draft_path = await draft_saver_agent(blog)
        return {
            "topic": topic_data,
            "video_summaries": video_summaries,
            "paper_summaries": paper_summaries,
            "blog": blog,
            "draft_path": draft_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# FastAPI endpoint
@app.post("/generate-blog/")
async def generate_blog(prompt: UserPrompt):
    result = await orchestrator_agent(prompt.topic)
    return result

# Streamlit frontend
def streamlit_app():
    st.title("Blog Generator")
    st.write("Create SEO-friendly blog posts from a simple topic")

    # Input
    topic = st.text_input("Enter Blog Topic", placeholder="e.g., Artificial Intelligence in 2025")

    # Session state for results and toggle
    if 'result' not in st.session_state:
        st.session_state.result = None
    if 'show_details' not in st.session_state:
        st.session_state.show_details = False
    if 'progress' not in st.session_state:
        st.session_state.progress = 0
    if 'status' not in st.session_state:
        st.session_state.status = ""

    # Buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        generate_button = st.button("Generate Blog", disabled=not topic)
    with col2:
        details_button = st.button("View Summary Details" if not st.session_state.show_details else "Hide Summary Details")
    with col3:
        save_button = st.button("Save Draft", disabled=not st.session_state.result)

    # Progress bar and status
    progress_bar = st.progress(st.session_state.progress)
    status_text = st.empty()
    status_text.text(st.session_state.status)

    # Handle button actions
    async def run_orchestrator():
        st.session_state.status = "Processing prompt..."
        st.session_state.progress = 10
        progress_bar.progress(st.session_state.progress)
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post("http://localhost:8000/generate-blog/", json={"topic": topic}) as response:
                    st.session_state.progress = 60
                    progress_bar.progress(st.session_state.progress)
                    if response.status != 200:
                        raise Exception(f"API error: {await response.text()}")
                    st.session_state.result = await response.json()
                    st.session_state.progress = 100
                    progress_bar.progress(st.session_state.progress)
                    st.session_state.status = "Blog generated successfully!"
                    await asyncio.sleep(1)
                    st.session_state.progress = 0
                    progress_bar.progress(st.session_state.progress)
            except Exception as e:
                st.session_state.status = f"Error: {str(e)}"
                st.session_state.progress = 0
                progress_bar.progress(st.session_state.progress)

    if generate_button:
        asyncio.run(run_orchestrator())

    if details_button:
        st.session_state.show_details = not st.session_state.show_details

    if save_button and st.session_state.result:
        st.session_state.status = "Saving draft..."
        st.session_state.progress = 50
        progress_bar.progress(st.session_state.progress)
        draft_path = st.session_state.result['draft_path']
        st.session_state.status = f"Draft saved at: {draft_path}"
        st.session_state.progress = 100
        progress_bar.progress(st.session_state.progress)
        asyncio.run(asyncio.sleep(1))
        st.session_state.progress = 0
        progress_bar.progress(st.session_state.progress)

    # Display results
    if st.session_state.show_details and st.session_state.result:
        st.subheader("YouTube Summaries")
        for vs in st.session_state.result['video_summaries']:
            st.markdown(f"**{vs['title']}**")
            st.write(vs['summary'])

        st.subheader("Research Paper Summaries")
        for ps in st.session_state.result['paper_summaries']:
            st.markdown(f"**{ps['title']}**")
            st.write(ps['summary'])

    if st.session_state.result:
        st.subheader("Blog Preview")
        st.markdown(st.session_state.result['blog']['content'])

# Main entry
if platform.system() == "Emscripten":
    asyncio.ensure_future(streamlit_app())
else:
    if __name__ == "__main__":
        # Start FastAPI in a separate process
        import uvicorn
        from multiprocessing import Process
        def run_fastapi():
            uvicorn.run(app, host="0.0.0.0", port=8000)
        fastapi_process = Process(target=run_fastapi)
        fastapi_process.start()
        # Run Streamlit
        st.set_page_config(page_title="Blog Generator", layout="wide")
        streamlit_app()
        fastapi_process.terminate()