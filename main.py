import argparse
import re
import os
import csv
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

def generate_id(template_path: str, name: str, profile_path: str, save_as: str):
    with Image.open(template_path) as template:
        try:
            profile_image = Image.open(profile_path or './profiles/unknown.jpeg')
        except FileNotFoundError:
            print(f"Error: The file at {profile_path} was not found.")
            return
        except UnidentifiedImageError:
            print(f"Error: The file at {profile_path} is not a valid image.")
            return

        side = min(template.width, template.height) // 2
        profile_image = profile_image.resize((side, side))

        mask = Image.new("L", (side, side))
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, side, side), fill=255)

        profile_image.putalpha(mask)

        offset = template.width - side
        x = offset // 2
        y = 3 * offset // 4

        template.paste(profile_image, (x, y), profile_image)

        draw = ImageDraw.Draw(template)
        font_path = "./fonts/Helvetica-Bold.ttf"

        max_font_size = 200
        for font_size in range(max_font_size, 10, -5):
            font = ImageFont.truetype(font_path, font_size)
            text_width = font.getlength(name)
            
            if text_width <= (template.width - 80):
                text_x = (template.width - text_width) / 2

                bbox = font.getbbox(name)
                text_height = bbox[3] + bbox[1]
                text_y = template.height - 100 - text_height

                draw.text((text_x, text_y), name, font=font, fill=(255, 255, 255))
                break

        back_cover = 'HeadBackTemplate.png' if 'head' in template_path.lower() else 'VolunteerBackTemplate.png'
        back_cover = Image.open(f'./templates/{back_cover}')
        pdf_path = save_as or f'{name.lower().replace(' ', '_')}.pdf'
        template.save(pdf_path, save_all=True, append_images=[back_cover])

def process_id_csv(csv_file, output_dir):
    if not output_dir: output_dir = 'ids'
    os.makedirs(output_dir, exist_ok=True)

    with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)

        for row in reader:
            generate_id(row['template'], row['name'], row['profile-pic'] or './profiles/unknown.jpeg', f"{output_dir}/{row['name'].lower().replace(' ', '_')}.pdf")

def generate_cert(template_path: str, name: str, save_as: str):
    with Image.open(template_path) as template:
        draw = ImageDraw.Draw(template)
        font_path = "./fonts/Helvetica-Bold.ttf"

        max_font_size = 80
        for font_size in range(max_font_size, 10, -5):
            font = ImageFont.truetype(font_path, font_size)
            text_width = font.getlength(name)
            
            if text_width <= (template.width * 0.7):
                text_x = 100

                bbox = font.getbbox(name)
                text_height = bbox[3] + bbox[1]
                text_y = template.height / 2 - text_height - 5

                draw.text((text_x, text_y), name, font=font, fill=(0, 0, 0))
                break

        pdf_path = save_as or f'{name.lower().replace(' ', '_')}.pdf'
        template.save(pdf_path)

def process_cert_csv(csv_file, output_dir):
    if not output_dir: output_dir = 'certs'
    os.makedirs(output_dir, exist_ok=True)

    with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)

        for row in reader:
            generate_cert(row['template'], row['name'], f"{output_dir}/{row['name'].lower().replace(' ', '_')}.pdf")

def to_title_case(image_name):
    full_name = os.path.splitext(image_name)[0].replace('_', ' ').split(' ')
    capitalize = lambda name: "'".join(map(str.capitalize, re.split(r"[\'\’]", name)))
    return ' '.join(map(capitalize, full_name))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Volunteer ID Generator")
    subparsers = parser.add_subparsers(dest='command', required=True)

    id_parser = subparsers.add_parser('id', description="Generate IDs")
    id_parser.add_argument('--template', type=str, help="Path to the template image")
    id_parser.add_argument('--name', type=str, help="Profile name")
    id_parser.add_argument('--profile-pic', type=str, help="Path to the profile picture")
    id_parser.add_argument('--output', type=str, help="Path to save the ID")
    id_parser.add_argument('--font-path', type=str, help="Path to a TTF font")
    id_parser.add_argument('--output-dir', type=str, help="Directory to save IDs when using CSV or a directory of images")
    id_parser.add_argument('--csv', type=str, help="CSV file with template, name, profile-pic")
    id_parser.add_argument('--directory', type=str, help="Directory with picture names as the person's name")

    cert_parser = subparsers.add_parser('cert', description="Generate certs")
    cert_parser.add_argument('--template', type=str, help="Path to the template image")
    cert_parser.add_argument('--name', type=str, help="Profile name")
    cert_parser.add_argument('--output', type=str, help="Path to save the ID")
    cert_parser.add_argument('--font-path', type=str, help="Path to a TTF font")
    cert_parser.add_argument('--output-dir', type=str, help="Directory to save IDs when using CSV or a directory of images")
    cert_parser.add_argument('--csv', type=str, help="CSV file with template, name, profile-pic")
    cert_parser.add_argument('--directory', type=str, help="Directory with picture names as the person's name")

    args = parser.parse_args()

    if args.command == 'id':
        if args.csv and args.output_dir:
            process_id_csv(args.csv, args.output_dir)
        elif args.template and args.directory and args.output_dir:
            os.makedirs(args.output_dir, exist_ok=True)
            images = os.listdir(args.directory)
            for image in images:
                name = to_title_case(image)
                generate_id(
                    args.template, 
                    name, 
                    os.path.join(args.directory, image), 
                    os.path.join(args.output_dir, os.path.splitext(image)[0] + '.pdf')
                )
        elif args.template and args.name and args.profile_pic:
            generate_id(args.template, args.name, args.profile_pic, args.output)
        else:
            print("Error: Provide a CSV file with --csv and --output-dir, or the necessary individual arguments (--template, --name, --profile-pic), or (--template, --directory, --output-dir).")
    elif args.command == 'cert':
        if args.template and args.name:
            generate_cert(args.template, args.name, args.output)
        elif args.csv and args.output_dir:
            process_cert_csv(args.csv, args.output_dir)
        else:
            print("Error: Provide the necessary individual arguments (--template, --directory, --output-dir).")
