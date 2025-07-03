import os
import shutil
from PIL import Image, ImageChops
import xml.etree.ElementTree as ET
from xml.dom import minidom
from math import ceil, sqrt
from tqdm import tqdm

def trim(image):
    bg = Image.new(image.mode, image.size, (0, 0, 0, 0))
    diff = ImageChops.difference(image, bg)
    bbox = diff.getbbox()
    if bbox:
        return image.crop(bbox), bbox
    return image, (0, 0, image.width, image.height)

def group_images(images):
    grouped_images = {}
    for img in images:
        size = img.size
        if size not in grouped_images:
            grouped_images[size] = []
        grouped_images[size].append(img)
    return grouped_images

def find_leaf_folders(folder):
    leaf_folders = []
    for root, dirs, files in os.walk(folder):
        image_files = [f for f in files if f.lower().endswith(('png', 'jpg', 'jpeg'))]
        if image_files:
            leaf_folders.append(root)
    return leaf_folders

def generate_spritesheet(image_folder, output_folder):
    image_folders = find_leaf_folders(image_folder)

    for folder in tqdm(image_folders, desc="Procesando carpetas"):
        relative_path = os.path.relpath(folder, image_folder)
        final_output_dir = os.path.join(output_folder, os.path.dirname(relative_path))
        os.makedirs(final_output_dir, exist_ok=True)

        original_folder_name = os.path.basename(folder)
        image_files = sorted([file for file in os.listdir(folder) if file.endswith(('png', 'jpg', 'jpeg'))])
        images = [Image.open(os.path.join(folder, file)) for file in image_files]

        unique_images = []
        unique_image_files = []
        duplicate_image_files = []
        seen_images = set()
        original_sizes = {}
        bboxes = {}
        sprite_dict = {}
        image_hash_map = {}

        for img, file_name in zip(images, image_files):
            img_hash = hash(img.tobytes())
            if img_hash not in image_hash_map:
                image_hash_map[img_hash] = (img, file_name)
                unique_images.append(img)
                unique_image_files.append(file_name)
                original_sizes[file_name] = img.size
            else:
                duplicate_image_files.append((img_hash, file_name))

        trimmed_images = []
        for img in unique_images:
            trimmed_img, bbox = trim(img)
            trimmed_images.append(trimmed_img)
            bboxes[unique_image_files[unique_images.index(img)]] = bbox

        grouped_images = group_images(trimmed_images)
        total_area = sum((w + 10) * (h + 10) for img_list in grouped_images.values() for img in img_list for w, h in [img.size])
        initial_sheet_size = ceil(sqrt(total_area))

        max_width = max(img.width for img in trimmed_images)
        max_height = max(img.height for img in trimmed_images)
        sheet_size = max(initial_sheet_size, max_width, max_height)

        while True:
            try:
                spritesheet = Image.new("RGBA", (sheet_size, sheet_size), (0, 0, 0, 0))
                x_offset, y_offset = 0, 0
                max_height_in_row = 0
                root = ET.Element("TextureAtlas", imagePath=original_folder_name)
                index = 0
                for file_name, img in zip(unique_image_files, trimmed_images):
                    if x_offset + img.width + 10 > sheet_size:
                        x_offset = 0
                        y_offset += max_height_in_row + 10
                        max_height_in_row = 0

                    if y_offset + img.height + 10 > sheet_size:
                        raise ValueError("Increase sheet size")

                    spritesheet.paste(img, (x_offset, y_offset))
                    original_size = original_sizes[file_name]
                    bbox = bboxes[file_name]

                    sprite = ET.SubElement(root, "SubTexture")
                    sprite.set("name", os.path.splitext(file_name)[0])
                    sprite.set("x", str(x_offset))
                    sprite.set("y", str(y_offset))
                    sprite.set("width", str(img.width))
                    sprite.set("height", str(img.height))
                    sprite.set("frameWidth", str(original_size[0]))
                    sprite.set("frameHeight", str(original_size[1]))
                    sprite.set("frameX", str(-bbox[0]))
                    sprite.set("frameY", str(-bbox[1]))

                    sprite_dict[file_name] = {
                        "x": str(x_offset),
                        "y": str(y_offset),
                        "width": str(img.width),
                        "height": str(img.height),
                        "frameWidth": str(original_size[0]),
                        "frameHeight": str(original_size[1]),
                        "frameX": str(-bbox[0]),
                        "frameY": str(-bbox[1])
                    }

                    x_offset += img.width + 10
                    max_height_in_row = max(max_height_in_row, img.height)
                    index += 1

                for img_hash, file_name in duplicate_image_files:
                    original_file_name = image_hash_map[img_hash][1]
                    sprite = ET.SubElement(root, "SubTexture")
                    sprite.set("name", os.path.splitext(file_name)[0])
                    for key, value in sprite_dict[original_file_name].items():
                        sprite.set(key, value)

                sorted_subelements = sorted(root.findall('SubTexture'), key=lambda x: x.get('name', ''))
                for subelement in sorted_subelements:
                    root.remove(subelement)
                    root.append(subelement)

                spritesheet_path = os.path.join(final_output_dir, f"{original_folder_name}.png")
                spritesheet.save(spritesheet_path)

                xml_str = ET.tostring(root, encoding='utf-8')
                xml_str = minidom.parseString(xml_str).toprettyxml(indent="    ")
                xml_comment = "<?xml version='1.0' encoding='utf-8'?>\n<!-- OPTIMIZADO POR NOCTROX GATO -->\n"
                xml_str = xml_comment + xml_str.split("?>", 1)[1].strip()

                xml_file_path = os.path.join(final_output_dir, f"{original_folder_name}.xml")
                with open(xml_file_path, "w") as xml_file:
                    xml_file.write(xml_str)

                # Copiar el archivo .txt si existe con el mismo nombre
                txt_path = os.path.join(folder, f"{original_folder_name}.txt")
                if os.path.exists(txt_path):
                    shutil.copy2(txt_path, os.path.join(final_output_dir, f"{original_folder_name}.txt"))

                break
            except ValueError:
                sheet_size = int(sheet_size * 1.1)
                print(f"Incrementando el tamaño del spritesheet a {sheet_size}x{sheet_size}")

# Configuración
image_folder = "/storage/emulated/0/z/xml/frames_output"
output_folder = "/storage/emulated/0/z/xml/Quegod"

generate_spritesheet(image_folder, output_folder)
