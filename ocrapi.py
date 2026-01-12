
import requests

def solve_captcha(image_path):
    API_KEY = "K83400982888957"
    # API_KEY = "K88015472288957"
    url = "https://api.ocr.space/parse/image"
    with open(image_path, "rb") as f:
        payload = {
            "apikey": API_KEY,
            "language": "eng",
            "OCREngine": 2  # Better accuracy engine
        }
        response = requests.post(url, files={"file": f}, data=payload)
    result = response.json()
    # print(result)
    if result["IsErroredOnProcessing"]:
        return None
    return result["ParsedResults"][0]["ParsedText"].strip().replace(" ", "")

# sol=solve_captcha('temp_captcha.png')
# print("Solved Captcha:", sol)