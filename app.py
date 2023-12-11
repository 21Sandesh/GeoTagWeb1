from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import requests
from PIL.ExifTags import TAGS, GPSTAGS

def get_geotagging_info(exif):
    if not exif:
        raise ValueError("No EXIF metadata found")

    geotagging_info = {}
    
    for (idx, tag) in TAGS.items():
        if tag == 'GPSInfo':
            if idx not in exif:
                raise ValueError("No EXIF geotagging found")

            for (key, val) in GPSTAGS.items():
                if key in exif[idx]:
                    geotagging_info[val] = exif[idx][key]

    return geotagging_info

def get_date_time_original(exif):
    if not exif:
        raise ValueError("No EXIF metadata found")

    for (idx, tag) in TAGS.items():
        if tag == 'DateTimeOriginal':
            if idx in exif:
                return exif[idx]

    raise ValueError("No DateTimeOriginal tag found")

# Your image processing function
def process_image(img_path, address, city, state, country, output_path):
    try:
        # Open the image file
        img = Image.open(img_path)

        # Get Exif data
        exif_data = img._getexif()

        # Retrieve geotagging information
        geotagging_info = get_geotagging_info(exif_data)

        # Retrieve date and time
        date_time_original = get_date_time_original(exif_data)

        # Create a new image with additional information at the bottom
        draw = ImageDraw.Draw(img)

        # Specify font sizes
        font_size_large = 35
        font_size_small = 22

        # Calculate positions for the two-column layout
        middle_position = img.width // 2
        thumbnail_position = (middle_position - 365, img.height - 212)
        info_container_position = (middle_position - 175, img.height - 200)
        info_position = (middle_position - 165, img.height - 200)  # Start at the same height as the thumbnail

        thumbnail_link = "https://i.postimg.cc/brvbvFQt/mapsthumbnail.png"
        TimeZone = "IST (UTC+5:30)"

        # Add existing image as the Google Maps thumbnail to Column 1 with spacing
        thumbnail_response = requests.get(thumbnail_link)
        thumbnail = Image.open(BytesIO(thumbnail_response.content))
        thumbnail = thumbnail.resize((180, 180))  # Resize to fit the layout
        img.paste(thumbnail, thumbnail_position)

        # Split info_text into lines
        info_text = f"{city}, {state}, {country}\n" \
                    f"{address}\n" \
                    f"Lat: {geotagging_info.get('GPSLatitude')[2]} | Lng:  {geotagging_info.get('GPSLongitude')[2]}\n" \
                    f"{date_time_original[:10]} | {date_time_original[11:]} | {TimeZone}\n" \
                    f"Social Welfare and Development Committee, VIT Pune"
        lines = info_text.split('\n')

        # Calculate maximum text size
        max_text_width = max(draw.textbbox((0, 0), line, font=ImageFont.truetype("arial.ttf", font_size_large))[2] for line in lines)

        # Draw semi-transparent rectangle as background
        rect_padding = 10
        rect_width = max_text_width - 290
        rect_height = len(lines) * (font_size_large) + 5  # Adjust for spacing
        rect_position = (info_position[0] - rect_padding, info_position[1] - rect_padding)
        rect = Image.new("RGBA", (rect_width, rect_height), (0, 0, 0, 128))
        img.paste(rect, rect_position, rect)

        # Draw each line with the corresponding font size and spacing
        for i, line in enumerate(lines):
            if i == 0:
                font = ImageFont.truetype("arial.ttf", font_size_large)
                line_height = font_size_large + 13
            else:
                font = ImageFont.truetype("arial.ttf", font_size_small)
                line_height = font_size_small + 8

            # Draw the line
            draw.text(info_position, line, fill="white", font=font)

            # Update Y position for the next line
            info_position = (info_position[0], info_position[1] + line_height)

        # Save the modified image
        img.save(output_path)

        print(f"Image with additional information saved to {output_path}")

    except (AttributeError, KeyError, IndexError, TypeError) as e:
        print(f"Error: Unable to process image. {str(e)}")
    

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Get user input
        address = request.form["address"]
        city = request.form["city"]
        state = request.form["state"]
        country = request.form["country"]
        image_file = request.files["image"]

        # Save the image temporarily
        img_path = "temp_image.jpg"
        image_file.save(img_path)

        # Process the image
        output_path = "output_image.jpg"
        process_image(img_path, address, city, state, country, output_path)

        # Send the processed image to the user
        return send_file(output_path, as_attachment=True)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
