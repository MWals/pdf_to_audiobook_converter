import html
import os
import pdfplumber
import google.cloud.texttospeech as tts

# TODO implement offset for table of contents, etc

infile = "ojeichwachse.pdf"
inpath = "in/"
outpath = "out/"
joinedpath = "joined/"

serviceaccount = "google.json"
language_code = "de-DE"
voice_name = "de-DE-Wavenet-B"

lenght = 0
text = ""
apilengthlimit = 5000


def ssml_to_mp3(voice_name: str, text: str, dest: str, filename: str):
    language_code = "-".join(voice_name.split("-")[:2])
    text_input = tts.SynthesisInput(ssml=text)
    voice_params = tts.VoiceSelectionParams(
        language_code=language_code, name=voice_name
    )
    audio_config = tts.AudioConfig(audio_encoding=tts.AudioEncoding.MP3, sample_rate_hertz=44100)

    client = tts.TextToSpeechClient.from_service_account_file(serviceaccount)
    response = client.synthesize_speech(
        input=text_input, voice=voice_params, audio_config=audio_config
    )

    filename = f"{filename}.mp3"
    with open(dest + filename, "wb") as out:
        out.write(response.audio_content)
        print(f'Generated speech saved to "{filename}"')


def text_to_ssml(inputfile):
    raw_lines = inputfile

    # Replace special characters with HTML Ampersand Character Codes
    # These Codes prevent the API from confusing text with
    # SSML commands
    # For example, '<' --> '&lt;' and '&' --> '&amp;'

    escaped_lines = html.escape(raw_lines)

    # Convert plaintext to SSML
    # Wait two seconds between each address
    ssml = "<speak>{}</speak>".format(
        escaped_lines
            .replace("\n\n", '\n\n<break time="0.3s"/>')
            .replace(",", ',<break time="0.2s"/>')
            .replace(". ", '. <break time="0.3s"/>')
            .replace("?", '?<break time="0.3s"/>')
            .replace("!", '!<break time="0.3s"/>')
            .replace("_", '')
            .replace("https://", '')
            .replace("http://", '')
            .replace("ﬂ", 'fl')
            .replace("ﬀ", 'ff')
            .replace("ﬁ", 'fi')
            .replace("ﬃ", 'ffi')
            .replace("ﬄ", 'ffl')
            .replace("ﬆ", 'st')
            .replace("ĳ", 'ij')
            .replace("ﬆ", 'st')
            .replace("æ", 'ae')
            .replace("œ", 'oe')
    )

    # Return the concatenated string of ssml script
    return ssml


def list_voices(language_code=None):
    client = tts.TextToSpeechClient.from_service_account_file(serviceaccount)
    response = client.list_voices(language_code=language_code)
    voices = sorted(response.voices, key=lambda voice: voice.name)

    print(f" Voices: {len(voices)} ".center(60, "-"))
    for voice in voices:
        languages = ", ".join(voice.language_codes)
        name = voice.name
        gender = tts.SsmlVoiceGender(voice.ssml_gender).name
        rate = voice.natural_sample_rate_hertz
        print(f"{languages:<8} | {name:<24} | {gender:<8} | {rate:,} Hz")


def get_chunks(s, maxlength):
    start = 0
    end = 0
    while start + maxlength < len(s) and end != -1:
        end = s.rfind(" ", start, start + maxlength + 1)
        if s[(end - len("<break")):end] == "<break":
            end -= (len("<break") + 1)
        yield s[start:end]
        start = end + 1
    yield s[start:]


# print(list_voices(language_code))
#
with pdfplumber.open(inpath + infile) as pdf:
    for page in pdf.pages:
        currenttext = page.extract_text()
        if currenttext:
            newtext = text_to_ssml(str(page.extract_text()))
            text += newtext
            lenght += len(newtext)

processedlenght = 0
print(lenght)
chunks = get_chunks(text, apilengthlimit)
for index, chunk in enumerate(chunks):
    processedlenght += len(chunk)
    print("prodessing", processedlenght, "of", lenght)
    print(index, len(chunk), "\n", chunk.replace("\n", ""), "\n")

    # ssml_to_mp3(voice_name, chunk, outpath, f'{infile.replace(".pdf", "")}_{index}')

exit()

filelist = os.listdir(outpath)
filelist.sort(key=lambda x: os.path.getmtime(outpath + x))
os.system(
    f'ffmpeg -i "concat:{"|".join([outpath + x for x in filelist])}" -acodec copy {joinedpath}{infile.replace(".pdf", "")}.mp3')
