import os
from pathlib import Path

import dotenv
from openai import OpenAI

from media_extractor import split_video
import datauri


# # Multimodal demo
# 
# This is an example of how to simulate a video- and audio-aware model using existing LLM vision models (that take text and images as input, and generate text as output).

# Load OpenAI API key from .env file
dotenv.load_dotenv()
if os.environ.get("OPENAI_API_KEY") is None:
    raise ValueError("OPENAI_API_KEY not found in .env file")

client = OpenAI()


# This is the input video that we'll turn into the user prompt.

def query(video_file):
    # At the time of this writing, the GPT-4o API doesn't directly support video or audio input. Instead, we'll decode the video into frames and feed them to the model as images, and decode the audio into text and feed it to the model as text.

    audio_uri, image_uris = split_video(video_file)
    


    # Decode the audio file into text, using OpenAI's `whisper-1` model. The result will serve as the text prompt for the LLM.

    with datauri.as_tempfile(audio_uri) as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1", file=Path(audio_file)
        )

    user_prompt = transcription.text
    


    # We're ready to talk to the LLM: use the text and images as input, and get generated text back.

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    *[
                        {
                            "type": "image_url",
                            "image_url": {"url": image_uri, "detail": "auto"},
                        }
                        for image_uri in image_uris
                    ],
                ],
            },
            {
                "role": "system",
                "content": Path("system_prompt.txt").read_text(),
            },
        ],
    )
    response_text = response.choices[0].message.content
    


    # Use OpenAI's text-to-speech model to turn the generated text into audio.

    audio = client.audio.speech.create(
        model="tts-1",
        voice="echo",
        input=response_text,
        response_format="mp3",
    )
    response_audio_uri = datauri.from_bytes(audio.read(), "audio/mpeg")
    return response_audio_uri
