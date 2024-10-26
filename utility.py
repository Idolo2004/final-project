from rembg import remove
from PIL import Image
import io

with open("webapp.jpeg", 'rb') as input_file:
     input_image = input_file.read()

output_image = remove(input_image)

with open("logo.jpg", "wb") as output_file:
    output_file.write(output_image)
