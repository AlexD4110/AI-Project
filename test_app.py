import os
from pathlib import Path
import dotenv
from openai import OpenAI

from media_extractor import split_video
import datauri

# Load OpenAI API key from .env file
dotenv.load_dotenv()
if os.environ.get("OPENAI_API_KEY") is None:
    raise ValueError("OPENAI_API_KEY not found in .env file")

client = OpenAI()

def query(video_file):
    audio_uri, image_uris = split_video(video_file)
    with datauri.as_tempfile(audio_uri) as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1", file=Path(audio_file)
        )
    user_prompt = transcription.text
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
    audio = client.audio.speech.create(
        model="tts-1",
        voice="echo",
        input=response_text,
        response_format="mp3",
    )
    response_audio_uri = datauri.from_bytes(audio.read(), "audio/mpeg")
    return response_audio_uri

if __name__ == "__main__":
    # Example video file path
    video_file = "input.mov"
    
    # Test query function
    audio_uri = query(video_file)
    print(f"Generated audio URI: {audio_uri}")

    # To test the Shiny app
    from shiny import App, ui
    from shiny.express import render

    app_ui = ui.page_fluid(
        ui.input_file("clip", label="Upload a Short Video!"),
        ui.output_ui("video_size"),
    )

    def server(input, output, session):
        @output
        @render.ui
        def video_size():
            clip = input.clip()
            if clip is None:
                return ui.tags.p("No video uploaded yet!")
            video_file = clip[0]["datapath"]
            audio_uri = query(video_file)
            return ui.tags.audio(src=audio_uri, controls=True)

    app = App(app_ui, server)
    app.run()
