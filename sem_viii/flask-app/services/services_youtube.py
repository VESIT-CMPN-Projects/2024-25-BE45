import nltk
import pandas as pd
nltk.download('vader_lexicon', quiet=True)

from nltk.sentiment import SentimentIntensityAnalyzer
from googleapiclient.discovery import build
from langchain_community.document_loaders import YoutubeLoader


def get_comments(youtube, video_id):
    try:
        comments = []
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100
        )
        response = request.execute()

        for item in response.get("items", []):
            comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            comments.append(comment)

        while "nextPageToken" in response:
            request = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=100,
                pageToken=response["nextPageToken"]
            )
            response = request.execute()

            for item in response.get("items", []):
                comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                comments.append(comment)
    except:
        return []
    return comments


def search_youtube(query, max_results=100, api_key="YOUR_API_KEY"):
    vader = SentimentIntensityAnalyzer()
    youtube = build('youtube', 'v3', developerKey=api_key)

    request = youtube.search().list(
        q=query,  
        part="snippet",
        type="video",  
        videoCaption="closedCaption",
        maxResults=max_results ,
        order="relevance",
    )
    response = request.execute()

    videos = []
    for item in response.get('items', []):
        video_id = item['id']['videoId']

        # Fetch video statistics (including like count)
        stats_request = youtube.videos().list(
            part="statistics",
            id=video_id
        )
        stats_response = stats_request.execute()
        stats = stats_response['items'][0]['statistics'] if stats_response['items'] else {}

        video_data = {
            "id": video_id,
            "title": item['snippet']['title'],
            "channel": item['snippet']['channelTitle'],
            "publish_date": item['snippet']['publishedAt'],
            "video_url": f"https://www.youtube.com/watch?v={video_id}",
            "like_count": stats.get('likeCount', 0),
            "view_count": stats.get('viewCount', 0),
        }
        video_data["caption"] = captionloader(video_data['video_url'])
        video_data["comments"] = get_comments(youtube, video_data['id'])
        video_data['desc_polarity_score'] = video_data['caption'].apply(lambda x: vader.polarity_scores(x)['compound'] if type(x) != float else x)
        video_data['comment_polarity_score'] = video_data['comments'].apply(lambda x: vader.polarity_scores(x)['compound'] if type(x) != float else x)
        videos.append(video_data)
    return videos


def captionloader(url):
    try:
        loader = YoutubeLoader.from_youtube_url(
                url,
                add_video_info=False,
                language=["en","en-US","en-IN","en-GB","hi"],
                translation="en",
            )
        
        caption = loader.load()[0].page_content
        return caption
    except:
        return -1
    