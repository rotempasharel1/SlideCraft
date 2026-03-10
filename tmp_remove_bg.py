from PIL import Image

def remove_background(image_path):
    try:
        img = Image.open(image_path)
        img = img.convert("RGBA")
        datas = img.getdata()

        # Assuming the top-left pixel is the background color
        bg_color = img.getpixel((0, 0))
        tolerance = 25

        newData = []
        for item in datas:
            # Check if pixel color is close to the background color
            if (abs(item[0] - bg_color[0]) <= tolerance and
                abs(item[1] - bg_color[1]) <= tolerance and
                abs(item[2] - bg_color[2]) <= tolerance):
                newData.append((255, 255, 255, 0)) # Transparent
            else:
                newData.append(item)
        
        img.putdata(newData)
        img.save(image_path, "PNG")
        print("Background removed successfully.")
    except Exception as e:
        print(f"Error removing background: {e}")

if __name__ == "__main__":
    remove_background("logo.png")
