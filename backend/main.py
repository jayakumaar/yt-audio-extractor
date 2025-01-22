import os
import warnings
from fastapi import FastAPI, Form
from fastapi.responses import FileResponse, JSONResponse
import yt_dlp
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import shutil

# Suppress specific warnings
warnings.simplefilter("ignore", category=FutureWarning)

app = FastAPI()

# Enable CORS for all origins (frontend compatibility)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

@app.post("/download-audio")
async def download_audio(url: str = Form(...)):
    try:
        # Validate if the URL is a YouTube URL
        if not ("youtube.com" in url or "youtu.be" in url):
            return JSONResponse(content={"error": "Invalid URL. Please enter a valid YouTube URL."}, status_code=400)

        # Step 1: Extract audio from YouTube link
        audio_path = extract_audio(url)

        # Check if the file exists before returning it
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"File at path {audio_path} does not exist.")

        # Return the audio file as a downloadable response
        return FileResponse(
            path=audio_path,
            filename="extracted_audio.mp3",
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=extracted_audio.mp3"}  # Forces download
        )
    except yt_dlp.utils.DownloadError as e:
        print(f"Download error: {str(e)}")
        return JSONResponse(content={"error": "Invalid URL or download error"}, status_code=400)
    except Exception as e:
        print(f"Error during audio extraction: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

def extract_audio(url):
    # Use yt-dlp for audio extraction
    # Define the Downloads directory path
    downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    temp_audio_path = os.path.join(downloads_dir, "extracted_audio.%(ext)s")  # Temporary file path with extension placeholder
    final_audio_path = os.path.join(downloads_dir, "extracted_audio.mp3")  # Final file path
    
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': temp_audio_path,  # Output path for the audio file
            'ffmpeg_location': r'C:\ffmpeg\ffmpeg-master-latest-win64-gpl-shared\ffmpeg-master-latest-win64-gpl-shared\bin',  # Ensure this is the correct path to ffmpeg
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])  # Download and extract audio from the provided URL
        
        # Rename the file to the final path
        temp_audio_path_with_ext = temp_audio_path.replace(".%(ext)s", ".mp3")
        if os.path.exists(temp_audio_path_with_ext):
            os.rename(temp_audio_path_with_ext, final_audio_path)
        else:
            raise FileNotFoundError(f"File at path {temp_audio_path_with_ext} does not exist.")
    except yt_dlp.utils.DownloadError as e:
        print(f"Download error: {str(e)}")
        raise
    except Exception as e:
        print(f"Error downloading audio: {e}")
        raise
    # Return the full path of the audio file
    return final_audio_path


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
