import asyncio
import json
import os
import urllib.parse
import edge_tts
import google.generativeai as genai
from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips
import requests

# 1. إعداد المفتاح المجاني
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
  genai.configure(api_key=API_KEY)


def generate_video(topic):
  print(f"🚀 جاري إنشاء فيديو عن: {topic}")

  # توليد السكربت مجاناً عبر Gemini
  model = genai.GenerativeModel("gemini-1.5-flash")
  prompt = f"""
    اكتب سكريبت ممتع عن: {topic}. قسم المحتوى إلى 3 مشاهد.
    قم بإرجاع النتيجة حصراً بصيغة JSON بدون أي كلام إضافي:
    {{
        "scenes": [
            {{
                "text": "الكلام الذي سيقال بصوت الراوي بالعربية",
                "image_prompt": "English visual description for AI image generation, cinematic, highly detailed"
            }}
        ]
    }}
    """
  response = model.generate_content(prompt)
  clean_json = response.text.replace("```json", "").replace("```", "").strip()
  data = json.loads(clean_json)

  clips = []
  for i, scene in enumerate(data["scenes"]):
    audio_file = f"audio_{i}.mp3"
    image_file = f"image_{i}.jpg"

    # تحويل النص لصوت مجاناً
    communicate = edge_tts.Communicate(scene["text"], "ar-SA-HamedNeural")
    asyncio.run(communicate.save(audio_file))

    # جلب صورة مجاناً
    encoded_prompt = urllib.parse.quote(scene["image_prompt"])
    img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&nologo=true"
    res = requests.get(img_url)
    with open(image_file, "wb") as f:
      f.write(res.content)

    # دمج المشهد
    a_clip = AudioFileClip(audio_file)
    i_clip = ImageClip(image_file).set_duration(a_clip.duration)
    clips.append(i_clip.set_audio(a_clip))

  # تجميع الفيديو النهائي
  final_video = concatenate_videoclips(clips, method="compose")
  final_video.write_videofile("output_video.mp4", fps=24, codec="libx264")
  print("🎉 تم إنشاء الفيديو بنجاح!")


if __name__ == "__main__":
  import sys

  topic = sys.argv[1] if len(sys.argv) > 1 else "قصة قصيرة"
  generate_video(topic)
