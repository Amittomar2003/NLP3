import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from transformers import pipeline
from textblob import TextBlob
import moviepy.editor as mp
import numpy as np
import cv2

# Function to summarize text
def summarize_text(text, max_length=150):
    summarization_pipeline = pipeline("summarization")
    summary = summarization_pipeline(text, max_length=max_length)
    return summary[0]['summary_text']

# Function to extract keywords
def extract_keywords(text):
    stop_words = set(stopwords.words('english'))
    lemmatizer = WordNetLemmatizer()

    words = word_tokenize(text)
    words = [lemmatizer.lemmatize(word.lower()) for word in words if word.isalnum()]
    keywords = [word for word in words if word not in stop_words and len(word) > 1]

    # Take top 5 most common keywords
    counter = CountVectorizer().fit_transform([' '.join(keywords)])
    indices = np.argsort(np.asarray(counter.sum(axis=0)).ravel())[::-1]
    top_keywords = [key for key, value in Counter(counter, vocabulary).items() if value > 1][:5]

    return top_keywords

# Function to perform topic modeling (LDA)
def topic_modeling(text):
    vectorizer = CountVectorizer(max_df=0.95, min_df=2, stop_words='english')
    tf = vectorizer.fit_transform([text])
    lda_model = LatentDirichletAllocation(n_components=5, max_iter=5, learning_method='online', random_state=42)
    lda_model.fit(tf)
    feature_names = vectorizer.get_feature_names_out()
    topics = []
    for topic_idx, topic in enumerate(lda_model.components_):
        topics.append([feature_names[i] for i in topic.argsort()[:-6:-1]])
    return topics

# Function to extract keyframes from video
def extract_keyframes(video_path, num_frames=5):
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)
    keyframes = []
    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            keyframes.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    cap.release()
    return keyframes

def main():
    st.title("YouTube Video Summarizer")

    # User input for YouTube video URL
    video_url = st.text_input("Enter YouTube Video URL:", "")

    # User customization options
    max_summary_length = st.slider("Max Summary Length:", 50, 300, 150)
    num_keyframes = st.slider("Number of Keyframes:", 1, 10, 5)

    if st.button("Summarize"):
        try:
            # Get transcript of the video
            transcript = YouTubeTranscriptApi.get_transcript(video_url)
            video_text = ' '.join([line['text'] for line in transcript])

            # Summarize the transcript
            summary = summarize_text(video_text, max_length=max_summary_length)

            # Extract keywords from the transcript
            keywords = extract_keywords(video_text)

            # Perform topic modeling
            topics = topic_modeling(video_text)

            # Extract keyframes from the video
            # Replace 'video_path' with the actual path to the downloaded video file
            video_path = 'video_path'
            keyframes = extract_keyframes(video_path, num_frames=num_keyframes)

            # Perform sentiment analysis
            sentiment = TextBlob(video_text).sentiment

            # Display summarized text, keywords, topics, keyframes, and sentiment
            st.subheader("Video Summary:")
            st.write(summary)

            st.subheader("Keywords:")
            st.write(keywords)

            st.subheader("Topics:")
            for idx, topic in enumerate(topics):
                st.write(f"Topic {idx+1}: {', '.join(topic)}")

            st.subheader("Keyframes:")
            for frame in keyframes:
                st.image(frame, caption='Keyframe', use_column_width=True)

            st.subheader("Sentiment Analysis:")
            st.write(f"Polarity: {sentiment.polarity}")
            st.write(f"Subjectivity: {sentiment.subjectivity}")

        except Exception as e:
            st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
