
from transformers import VisionEncoderDecoderModel, TrOCRProcessor
import torch
from PIL import Image


def solve_captcha(image_path):
    # Load model and processor
    # use_fast=False if you need consistency with the slow processor
    processor = TrOCRProcessor.from_pretrained("anuashok/ocr-captcha-v2", use_fast=False)
    model = VisionEncoderDecoderModel.from_pretrained("anuashok/ocr-captcha-v2")
    
    # Load image
    image = Image.open(image_path).convert("RGB")
    
    # Prepare image
    pixel_values = processor(image, return_tensors="pt").pixel_values
    
    # Generate text
    generated_ids = model.generate(pixel_values)
    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
    if generated_text=='' or generated_text==None:
        return None
    return generated_text.replace(" ", "")

# sol=solve_captcha('temp_captcha.png')
# print("Solved Captcha:", sol)