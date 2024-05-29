from shiny.express import input, render, ui
from query import query
from shinymedia import input_video_clip, audio_spinner


input_video_clip("clip", style="max-width: 600px;", class_="mx-auto py-3")
#Creates a place for you to upload file

@render.express #Things that appear at the top are what we humans see
def video_size():
    if input.clip() is None:
        return
    with ui.Progress() as p:
        p.set(message="Processing.....")
        audio_uri = query(input.clip())
    audio_spinner(src=audio_uri, controls=True)



    #Anything that changes it will reexecute this
    #Using input keyword I can access the input_file first
    #parameter. The word short is the "id". () calls it like function




    



