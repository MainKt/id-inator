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

def process_csv(csv_file, output_dir):
    if not output_dir: output_dir = 'ids'
    os.makedirs(output_dir, exist_ok=True)

    with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)

        for row in reader:
            generate_id(row['template'], row['name'], row['profile-pic'] or './profiles/unknown.jpeg', f"{output_dir}/{row['name'].lower().replace(' ', '_')}.pdf")


def to_title_case(image_name):
    full_name = os.path.splitext(image_name)[0].replace('_', ' ').split(' ')
    capitalize = lambda name: "'".join(map(str.capitalize, re.split(r"[\'\’]", name)))
    return ' '.join(map(capitalize, full_name))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate ID for volunteers")
    parser.add_argument('--template', type=str, help="Path to the template image")
    parser.add_argument('--name', type=str, help="Profile name")
    parser.add_argument('--profile-pic', type=str, help="Path to the profile picture")
    parser.add_argument('--output', type=str, help="Path to save the id")
    parser.add_argument('--font-path', type=str, help="Path to a ttf font")

    parser.add_argument('--output-dir', type=str, help="Dir to save the ids in case of CSV")
    parser.add_argument('--csv', type=str, help="CSV file with template,name,profile-pic")
    parser.add_argument('--directory', type=str, help="Directory with picture names as the person's name")

    args = parser.parse_args()

    if args.csv and args.output_dir:
        process_csv(args.csv, args.output_dir)
    elif args.template and args.directory and args.output_dir:
        os.makedirs(args.output_dir, exist_ok=True)
        images = os.listdir(args.directory)
        for image in images:
            name = to_title_case(image)
            print(name)
            generate_id(args.template, name, os.path.join(args.directory, image), os.path.join(args.output_dir, os.path.splitext(image)[0] + '.pdf'))
    elif args.template and args.name and args.profile_pic:
        generate_id(args.template, args.name, args.profile_pic, args.output)
    else:
        print("Error: Either provide a CSV file to --csv-file or the necessary individual arguments (--template, --name, --profile-pic) or (--template, --directory).")
