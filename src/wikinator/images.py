# Image Manipulation Tools

from io import BytesIO
import logging
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from pillow_heif import register_heif_opener

from PIL import Image

log = logging.getLogger(__name__)

# Load the HEIF libs. See https://github.com/bigcat88/pillow_heif
register_heif_opener()


def convert_to(source:Path, format:str="jpeg", quality:int=85) -> Path:
    """
    Loads a supported image, convertes it to expected, stores in a tmp file, returns the path
    Format defaults to jpeg.  Quality defaults to 85.
    """
    image = Image.open(source)
    image_ext = "." + format
    tmp_file = NamedTemporaryFile(prefix=source.stem, suffix=image_ext, delete=False)
    image.save(tmp_file, format=format, quality=quality, optimize=True)
    return Path(tmp_file.name)


# from doxcit

def compress(content:bytes, content_type:str, quality:int=75) -> bytes:
    image_data = BytesIO(content)
    image = Image.open(image_data)

    image_format = content_type.lower()
    if image_format.startswith("image/"):
        image_format = image_format[6:]

    compressed = BytesIO()
    image.save(compressed, format=image_format, quality=quality, optimize=True)
    compressed = compressed.getbuffer()

    # don't know why, but it's often the case
    if len(compressed) > len(content):
        compressed = content
    else:
        log.info(f"Compressed image by {100-(len(compressed)/len(content))*100:.2f}%")

    return compressed


# def write_images(outroot:Path):
#     # save all images
#     image_folder = Path(outroot, "images")
#     images = {}
#     for rel in doc.part.rels.values():
#         if "image" in rel.reltype:
#             image_filename = save_image(rel.target_part, image_folder)
#             images[rel.rId] = image_filename[len(outroot)+1:]
#             # use relative
#             log.info("image file:", rel.rId, ":", image_filename, "-->", images[rel.rId])
#         # else:
#         #     log.info(f"rel.rId={rel.rId}, rel.reltype={rel.reltype}")
#     return images


def save_image(image_part, output_folder):
    """Save an image to the output folder and return the filename."""
    os.makedirs(output_folder, exist_ok=True)
    image_filename = os.path.join(output_folder, os.path.basename(image_part.partname))
    with open(image_filename, "wb") as img_file:
        img_file.write(image_part.blob)
    return str(image_filename).replace("\\", "/")


# For testing the image stuff
def main():
    import sys
    source = sys.argv[1]
    path = Path(source)
    print(f"Converting {path}")
    result = convert_to(path)
    print(f"Converted to {result}")


if __name__ == "__main__":
    main()