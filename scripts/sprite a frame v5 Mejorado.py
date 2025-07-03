import os
from PIL import Image
import xml.etree.ElementTree as ET
from tqdm import tqdm
import re
from concurrent.futures import ThreadPoolExecutor

def sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*]', '_', name)

def extract_frames(png_path, xml_path, output_dir, overall_progress, file_progress, task_index, relative_path):
    try:
        image = Image.open(png_path).convert("RGBA")
        tree = ET.parse(xml_path)
        root = tree.getroot()
        png_name = os.path.splitext(os.path.basename(png_path))[0]
        
        # Create subfolder respecting original structure
        frame_output_dir = os.path.join(output_dir, relative_path, png_name)
        os.makedirs(frame_output_dir, exist_ok=True)
        
        # Create canvas size text file
        canvas_size_file = os.path.join(frame_output_dir, f"{image.width}x{image.height}.txt")
        with open(canvas_size_file, 'w') as f:
            f.write(f"Original sprite sheet dimensions: {image.width}x{image.height}")
        
        subtextures = root.findall(".//SubTexture")
        
        for subtexture in subtextures:
            name = sanitize_filename(subtexture.attrib['name'])
            x = int(float(subtexture.attrib.get('x', 0)))
            y = int(float(subtexture.attrib.get('y', 0)))
            width = int(float(subtexture.attrib.get('width', 0)))
            height = int(float(subtexture.attrib.get('height', 0)))
            frameX = int(float(subtexture.attrib.get('frameX', 0)))
            frameY = int(float(subtexture.attrib.get('frameY', 0)))
            frameWidth = int(float(subtexture.attrib.get('frameWidth', width)))
            frameHeight = int(float(subtexture.attrib.get('frameHeight', height)))
            rotated = subtexture.attrib.get('rotated', 'false').lower() == 'true'
            
            sprite_crop = image.crop((x, y, x + width, y + height))
            if rotated:
                sprite_crop = sprite_crop.transpose(Image.ROTATE_90)
                width, height = height, width
            
            frame_image = Image.new("RGBA", (frameWidth, frameHeight), (0, 0, 0, 0))
            paste_x = -frameX if frameX < 0 else 0
            paste_y = -frameY if frameY < 0 else 0
            frame_image.paste(sprite_crop, (paste_x, paste_y))
            
            frame_path = os.path.join(frame_output_dir, f"{name}.png")
            frame_image.save(frame_path, "PNG")
            
            file_progress[task_index].update(1)
            overall_progress.update(1)
        
        print(f"Procesamiento de {png_name}: Completado correctamente.")
    
    except ET.ParseError as e:
        print(f"Error parsing {xml_path}: {e}")
    except Exception as e:
        print(f"Unexpected error processing {png_path} and {xml_path}: {e}")

def collect_tasks(base_dir):
    tasks = []
    skip_dirs = {'frames_output', 'Quegod', 'frames'}

    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for file in files:
            if file.endswith(".png"):
                png_path = os.path.join(root, file)
                xml_path = os.path.splitext(png_path)[0] + ".xml"
                if os.path.exists(xml_path):
                    try:
                        tree = ET.parse(xml_path)
                        root_xml = tree.getroot()
                        frame_count = len(root_xml.findall(".//SubTexture"))
                        relative_path = os.path.relpath(os.path.dirname(png_path), base_dir)
                        tasks.append((png_path, xml_path, relative_path, frame_count))
                    except ET.ParseError:
                        print(f"Error parsing {xml_path}, skipping.")
    return tasks

def process_directory(base_dir):
    output_base_dir = os.path.join(base_dir, 'frames')
    os.makedirs(output_base_dir, exist_ok=True)

    tasks = collect_tasks(base_dir)
    total_frames = sum(task[3] for task in tasks)

    overall_progress = tqdm(total=total_frames, desc="Progreso general", unit="frame", position=0)
    file_progress = [
        tqdm(total=task[3], desc=f"Procesando {os.path.basename(task[0])}", unit="frame", position=i + 1)
        for i, task in enumerate(tasks)
    ]

    with ThreadPoolExecutor() as executor:
        futures = []
        for i, (png_path, xml_path, relative_path, frame_count) in enumerate(tasks):
            futures.append(executor.submit(
                extract_frames, png_path, xml_path, output_base_dir, overall_progress, file_progress, i, relative_path
            ))
        for future in futures:
            future.result()
    
    for bar in file_progress:
        bar.close()
    overall_progress.close()

# Ruta base
base_dir = '/storage/emulated/0/z/xml/'

# Ejecutar
process_directory(base_dir)
