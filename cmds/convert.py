import requests
import discord
from discord.ext import commands
from pydub import AudioSegment
from faster_whisper import WhisperModel
import pandas as pd
from io import BytesIO
import subprocess
import os
import csv
import time

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# 初始化bot
intents = discord.Intents.default()                      # 啟用預設權限
intents.message_content = True                           # 讓bot可以讀訊息
bot = commands.Bot(command_prefix='[', intents=intents)  # 設置命令前綴

if not os.path.exists("output"):
    os.makedirs("output")

# youtube影片網址下載為mp3
def download_audio_from_youtube(video_url):
    try:
        output_file_yt = "yt.mp3"

        # -x是提取音訊用的 check=True表示如果yt-dlp命令失敗則會引發錯誤    
        subprocess.run(['yt-dlp', '-x', '--audio-format', 'mp3', video_url, '-o', output_file_yt], check=True) 
        print(f"音訊檔案已下載為 {output_file_yt}")
        return output_file_yt
    
    except Exception as e:
        print(f"下載音訊檔案時發生錯誤: {e}")
        return None
    
# 將音訊網址轉換為wav格式
def convert_audio_to_wav(audio_url):
    try:
        downloaded_file_yt = None  # 初始化變數

        # 如果是YouTube連結就下載音訊
        if "youtube.com" in audio_url or "youtu.be" in audio_url:
            downloaded_file_yt = download_audio_from_youtube(audio_url)

            # 如果下載成功就載入音訊
            if downloaded_file_yt:
                audio = AudioSegment.from_file(downloaded_file_yt)
        
        # 將音訊網址轉換為wav格式
        else:
            r = requests.get(audio_url)  #HTTP GET請求下載音訊
            r.raise_for_status()         #檢查請求是否成功 偵測錯誤

            # 使用BytesIO將下載的內容轉換為類似檔案的東西，然後用pydub讀取音訊
            audio = AudioSegment.from_file(BytesIO(r.content))

        output_file = "output.wav"
        audio.export(output_file, format = "wav")  #導出音檔
        print(f"音訊成功轉換並儲存為 {output_file}")

        # 清理下載的音訊檔案
        if downloaded_file_yt and os.path.exists(downloaded_file_yt):
            os.remove(downloaded_file_yt)
        return output_file  

    except Exception as e:
        print(f"轉檔時發生錯誤:{e}")

def transcribe(audio, lang, mod):
    print(f"transcribing({audio})") 
    model = WhisperModel(mod)
    segments, info = model.transcribe(audio, language=lang, vad_filter=False, vad_parameters=dict(min_silence_duration_ms=100))  
    # 假設 info 是個物件，語言應該可以透過 .language 來獲取
    language = info.language
    
    print("Transcription language", language)
    segments = list(segments) # 將 segments 轉換為列表
    return language, segments


def formattedtime(seconds):
    final_time = time.strftime("%H:%M:%S", time.gmtime(float(seconds))) #從檔案開始將每個間隔所表示時間寫成字串
    return f"{final_time},{seconds.split('.')[1]}"

def writetocsv(segments, output_csv_path):
    cols = ["start", "end", "text"]
    data = []
    for segment in segments:
        start = formattedtime(format(segment.start, ".3f"))
        end = formattedtime(format(segment.end, ".3f"))
        data.append([start, end, segment.text])

    df = pd.DataFrame(data, columns=cols)
    df.to_csv(output_csv_path, index=False, encoding='utf-8')
    return df  # 返回 DataFrame 而不是檔案路徑

def generatesrt(csv_file):
    rows = []
    count = 0
    with open(csv_file, encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile) 
        for row in reader:
            count += 1
            txt = f"{count}\n{row['start']} --> {row['end']}\n{row['text'].strip()}\n\n"  # srt檔案表示法(/表示分行): 順序/開始時間 --> 結束時間/文字
            rows.append(txt)  # 讀取csv檔並寫入srt
        return rows

class Convert(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
        if not os.path.exists("output"):
            os.makedirs("output")

    @discord.slash_command(description='將YouTube網址轉換為文字')
    @discord.option('url', str, description='你想轉換成文字的YouTube網址')
    @discord.option('language', str, description='你想轉換成的語言（請用小寫英文字母）', required=False, default=None)
    @discord.option('model', str, description='你想使用的轉錄模型', required=False, default='base', choices=['tiny', 'base', 'medium', 'large'])
    async def convert_green_banana(self, ctx: discord.ApplicationContext, url: str, language: str = None, model: str = 'model'):
            print("正在執行...")  
            await ctx.defer()  # 延長回應時間限制
            await ctx.followup.send("等億下會怎樣...")
            output_file = convert_audio_to_wav(url) 
            
            file_size = os.path.getsize(output_file)                # 偵測檔案大小
            file_size_MB = round(file_size / (1024 * 1024), 1)      # 轉為MB

            if output_file:
                try:
                    # 使用 faster-whisper 進行轉錄
                    lang, segments = transcribe(output_file, language, model)


                    # 寫入文字稿
                    with open('output.txt', 'w', encoding='utf8') as outputFile:
                        for segment in segments:
                            outputFile.write(segment.text + '\n')

                    await ctx.followup.send(content="以下為轉換的文字稿:", file=discord.File('output.txt'))
                    print("成功轉換成文字稿")

                    # 清理檔案
                    os.remove('output.txt')
                    os.remove(output_file)

                except Exception as e:
                    print(f"產生文字稿時發生錯誤: {e}")
                    await ctx.followup.send(f"產生文字稿時發生錯誤: {e}")
            else:
                await ctx.followup.send("轉檔失敗，請檢查輸入的連結")
                    
    @discord.slash_command(description='將網址轉為Wav檔')
    @discord.option('url', str, description='你想轉換成Wav檔的網址')
    async def convert_to_wav(self, ctx: discord.ApplicationContext, url: str):
        print("正在執行...")  
        await ctx.send("等億下會怎樣...")
        output_file = convert_audio_to_wav(url) 
        
        file_size = os.path.getsize(output_file)                # 偵測檔案大小
        file_size_MB = round(file_size / (1024 * 1024), 1)      # 轉為MB

        try:
            if output_file:
                await ctx.send(file=discord.File(output_file))
                await ctx.send("好了啦")
                print("完成執行")

                os.remove(output_file)  # 轉檔後刪除 WAV 檔案  
            else:
                await ctx.send("轉檔失敗 請檢查輸入的連結")
                
        except Exception as e:
            await ctx.send("檔案太大 目前太窮沒辦法升級discord 所以沒辦法回傳")
            await ctx.send(f"此檔案大小為{file_size_MB}MB 根據測試應該小於25MB才能回傳")
            print(f"此檔案大小為{file_size_MB}MB")
            print(f"發生錯誤:{e}")

            os.remove(output_file)  # 轉檔後刪除 WAV 檔案

    @discord.slash_command(description='將YouTube網址轉換為文字')
    @discord.option('url', str, description='你想轉換成文字的YouTube網址')
    @discord.option('language', str, description='你想轉換成的語言（請用小寫英文字母）', required=False, default=None)
    @discord.option('model', str, description='你想使用的轉錄模型', required=False, default='base', choices=['tiny', 'base', 'medium', 'large'])
    async def convert_to_srt(self, ctx: discord.ApplicationContext, url, language, model):
        print("正在執行...")  
        await ctx.defer()  # 延長回應時間限制
        await ctx.followup.send("等億下會怎樣...")

        output_file = convert_audio_to_wav(url) 
        
        if output_file:
            try:
                # 使用 faster-whisper 進行轉錄
                lang, segments = transcribe(output_file, language, model)

                # 寫入csv文字稿
                output_csv_path = os.path.join("output", "output.csv")
                writetocsv(segments, output_csv_path)

                # 產生SRT檔
                srt_data = generatesrt(output_csv_path)
                output_srt_path = os.path.join("output", "output.srt")
                with open(output_srt_path, "w") as srt_file:
                    for row in srt_data:
                        srt_file.write(row)

                await ctx.followup.send(content=f"Here is your srt file in language {lang}!", file=discord.File(output_srt_path))
                print("成功轉換成srt檔")

                # 清理檔案
                if os.path.exists(output_srt_path):
                    os.remove(output_srt_path)
                if os.path.exists(output_csv_path):
                    os.remove(output_csv_path)
                if os.path.exists(output_file):
                    os.remove(output_file)

            except Exception as e:
                print(f"產生文字稿時發生錯誤: {e}")
                await ctx.followup.send(f"產生文字稿時發生錯誤: {e}")
        else:
            await ctx.followup.send("轉檔失敗，請檢查輸入的連結")

def setup(bot):
    bot.add_cog(Convert(bot))