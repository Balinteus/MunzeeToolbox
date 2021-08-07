#!/usr/bin/env python3
import io
import sys
import base64
import html.parser

from PIL import Image
import PySimpleGUI as pgui

pgui.theme("DarkBrown4")

# Preparing the asset directory
# https://stackoverflow.com/questions/31836104/pyinstaller-and-onefile-how-to-include-an-image-in-the-exe-file
if getattr(sys, "frozen", False):  # Check if running as compiled
    image_dir = sys._MEIPASS + "/img/"  # In production (compiled with PyInstaller)
else:
    image_dir = "./img/"  # Path name when run with Python interpreter

# Create image paths
icon_image = image_dir + "icon.ico"
empty_image = image_dir + "empty.png"
multiple_image = image_dir + "multiple.png"
arrow_image = image_dir + "arrow.png"

# Global Variables
qr_paths = []
ps_paths = []
html_splits = []
html_path = ""
sign_path = ""
export_location = ""
total_session_gens = 0
printsheet = None

# Default Settings
qr_size = 500
sign_size = 100
output_size = 85

# Constants
A4_SIZE = (2480, 3508)

# PySimpleGUI Layouts
# fmt: off
menubar_layout = [
    ["&File", ["&Import...", ["&QR Code(s)", "&Signature Image"], "Specify &export location", "---", "!&Generate", "!&Print", "&Clear inputs", "---", "E&xit"]],
    ["&Toolbox", ["&HTML sheet splitter", "&Print sheet generator"]],
    ["Se&ttings"],
    ["&About", ["!Made by: Balinteus", "---",  "My website", "The project's github page"]]
]

generator_layout = [
    [pgui.Column([ [pgui.Frame("Imported QR Code", [[pgui.Image(empty_image, key="-qr_img-", size=(300, 300))]])],
                 [pgui.Button("Import QR Code(s)", size=[38, 1], key="-import_qr-")],
                 [pgui.Button("Import Signature Image", size=[38, 1], key="-import_sign-")] ]),
    pgui.Column([ [pgui.Image(arrow_image, size=(100, 100))] ]),
    pgui.Column([ [pgui.Frame("Generated QR Code", [[pgui.Image(empty_image, key="-rendered_img-", size=(300, 300))]])],
                 [pgui.Button("Specify export location", size=[38, 1], key="-set_export_location-")],
                 [pgui.Button("Generate", size=[38, 1], disabled=True, key="-generate-")] ])]
]

htmlsplitter_layout = [
    [pgui.Column([[pgui.Frame("HTML sheet splitter", [[pgui.Button("Import HTML sheet", size=[38, 1], key="-hs_import-")],
                [pgui.HorizontalSeparator(pad=(10, 10))],
                [pgui.Button("Save QR Code(s)", size=[38, 1], key="-hs_save-", disabled=True)],
                [pgui.HorizontalSeparator(pad=(10, 10))],
                [pgui.Button("Export QR Code(s) into Signature Generator", size=[38, 1], key="-hs_exp_sg-", disabled=True)],
                [pgui.Button("Export QR Code(s) into Print Sheet Generator", size=[38, 1], key="-hs_exp_ps-", disabled=True)] ], pad=(225, 100)) ]]) ]
]

printsheet_layout = [
    [pgui.Column([ [pgui.Frame("Print sheet generator", [
                      [pgui.Button("Import QR Code(s)", size=[38, 1], key="-ps_imp-")],
                      [pgui.HorizontalSeparator(pad=(10, 10))],
                      [pgui.Text("Paper size: "), pgui.DropDown(["A4"], default_value="A4", readonly=True, key="-ps_papertype-")],
                      [pgui.Text("Margin size: "), pgui.Spin([i for i in range(1, 1500)], initial_value=10, key="-ps_margin-"), pgui.Text("px")],
                      [pgui.HorizontalSeparator(pad=(10, 10))],
                      [pgui.Button("Generate", size=[38, 1], key="-ps_gen-", disabled=True)],
                      [pgui.Button("Save generated image", size=[38, 1], key="-ps_save-", disabled=True)], ], pad=(20, 10))] ]),
    pgui.Column([ [pgui.Image(arrow_image, size=(100, 100))] ]),
    pgui.Column([ [pgui.Frame("Output", [[pgui.Image(empty_image, key="-ps_img-", size=(248, 350))]])]])]
]

settings_layout = [
    [pgui.Text("Settings")],
    [pgui.Text("Imported QR Code size: "), pgui.Input()],
    [pgui.Text("Signature image size (on generated img): "), pgui.Input()],
]

tab_layout = [
    [
        pgui.Tab("Signature generator", generator_layout),
        pgui.Tab("HTML sheet splitter", htmlsplitter_layout),
        pgui.Tab("Print sheet generator", printsheet_layout),
        pgui.Tab("Settings", settings_layout),
    ]
]

main_layout = [ 
    [pgui.Menu(menubar_layout)],
    [pgui.Text("Balinteus' Munzee Toolbox", size=[46, 1], font="Helvitica 20 bold", justification="center", relief=pgui.RELIEF_RIDGE)],
    [pgui.TabGroup(tab_layout, tab_location="topleft")]
]
# fmt: on

main_window = pgui.Window("Munzee Toolbox", main_layout, icon=icon_image)


def ready_check():
    """Checks if all the required inputs are fulfilled. Enables/disables buttons
    if these requirements are met."""
    print("Ready check!")
    # SG Ready check
    if (
        (len(qr_paths) > 0)
        and (sign_path != "")
        and (sign_path != None)
        and (export_location != "")
        and (export_location != None)
    ):
        main_window.Element("-generate-").Update(disabled=False)
        print("SG READY!")
    else:
        main_window.Element("-generate-").Update(disabled=True)
    # PSG Ready check
    if len(ps_paths) > 0:
        main_window.Element("-ps_gen-").Update(disabled=False)
        main_window.Element("-ps_save-").Update(disabled=False)
        print("PSG READY!")
    else:
        main_window.Element("-ps_gen-").Update(disabled=True)
        main_window.Element("-ps_save-").Update(disabled=True)
    # HS Ready check
    if len(html_splits) > 0:
        main_window.Element("-hs_save-").Update(disabled=False)
        main_window.Element("-hs_exp_sg-").Update(disabled=False)
        main_window.Element("-hs_exp_ps-").Update(disabled=False)
        print("HS READY!")
    else:
        main_window.Element("-hs_save-").Update(disabled=True)
        main_window.Element("-hs_exp_sg-").Update(disabled=True)
        main_window.Element("-hs_exp_ps-").Update(disabled=True)


def generate_signature(qr_path, sign_path, isThumbnail=False, isBinary=False):
    """Generates a signatured image by combining two images, a background image
    (in our case this will a QR code) and a signature image.

    Args:
        qr_path: Path to the background image (in our case a QR code).
        sign_path: Path to the signature image.
        isThumbnail (bool, optional): Skips the resize process. Usually used on
            thumbnail generations. Defaults to False.
        isBinary (bool, optional): Set to True if the two input images are
            PIL.Image objects. Defaults to False.

    Returns:
        PIL.Image object: The merged image.
    """
    # Load the base images
    if not isBinary:
        qr_img = Image.open(qr_path)
        sign_img = Image.open(sign_path)
    else:
        qr_img, sign_img = qr_path, sign_path

    # ...and resize them
    if not isBinary:
        qr_img = qr_img.resize((qr_size, qr_size), Image.BILINEAR)
        sign_img = sign_img.resize((sign_size, sign_size), Image.BILINEAR)

    # Calculate the center offset
    qr_w, qr_h = qr_img.size
    sign_w, sign_h = sign_img.size
    center_offset = ((qr_w - sign_w) // 2, (qr_h - sign_h) // 2)

    # Generate the signatured image
    generated_img = qr_img.copy()
    generated_img.paste(sign_img, center_offset)
    if not isThumbnail:
        generated_img = generated_img.resize((output_size, output_size), Image.BILINEAR)

    return generated_img


def generate_thumbnail(base_image, size=(300, 300)):
    """Creates a thumbnailed version of a given image and saves it to memory.

    Args:
        base_image (string): This image will be thumbnailed.
        size (tuple, optional): The size of the generated thumbnail.
            Defaults to (300, 300).

    Returns:
        PIL.Image object: The thumbnailed version of the image.
    """
    # Create a copy of the base image, this way we don't overwrite it
    work_image = base_image.copy()

    # Create thumbnail
    work_image.thumbnail(size)

    # Write the img into BytesIO, so we can pass the raw data into the img element
    generated_thumbnail = io.BytesIO()
    work_image.save(generated_thumbnail, format="PNG")

    return generated_thumbnail


def update_thumbnails():
    """Controls all the GUI Image elements' state."""
    print("Updating thumbnails...")
    # Update SG thumbnails
    if len(qr_paths) > 1:
        main_window.Element("-qr_img-").Update(filename=multiple_image, size=(300, 300))
        if (sign_path != "") and (sign_path != None):
            main_window.Element("-rendered_img-").Update(
                filename=multiple_image, size=(300, 300)
            )
    elif len(qr_paths) == 1:
        # Update QR thumbnail
        qr_thumbnail = generate_thumbnail(Image.open(qr_paths[0]))
        main_window.Element("-qr_img-").Update(
            filename=None, data=qr_thumbnail.getvalue(), size=(300, 300)
        )
        # Update Rendered thumbnail
        if (sign_path != "") and (sign_path != None):
            rendered_image = generate_signature(qr_paths[0], sign_path, True)
            rendered_thumbnail = generate_thumbnail(rendered_image)
            main_window.Element("-rendered_img-").Update(
                filename=None, data=rendered_thumbnail.getvalue(), size=(300, 300)
            )
        else:
            main_window.Element("-rendered_img-").Update(
                filename=None, data=qr_thumbnail.getvalue(), size=(300, 300)
            )
    else:
        main_window.Element("-qr_img-").Update(filename=empty_image, size=(300, 300))
        main_window.Element("-rendered_img-").Update(
            filename=empty_image, size=(300, 300)
        )
    # Update PS thumbnails
    if printsheet == None:
        main_window.Element("-ps_img-").Update(filename=empty_image, size=(248, 350))


def parse_paths(raw_paths: str):
    """Parses file/folder paths from a given string.

    Example for this string:
        "C:/Users/bali/Desktop/gen.png;C:/Users/bali/Desktop/index.png"

    Args:
        raw_paths (str): The provided paths in raw format.

    Returns:
        List: A list filled with the parsed paths.
    """
    parsed_paths = []
    if (raw_paths != None) and (raw_paths != ""):
        parsed_paths = raw_paths.split(";")
    return parsed_paths


def add_margin(base_image_path: str, margin_size: int):
    """Adds a margin to a given image. This process is done by creating a new
    "background" image thats bigger than the original one and putting the
    original image into the center of this newly created white background.

    Args:
        base_image_path (str): The path to the provided image.
        margin_size (int): This number determines the thickness of the margin.

    Returns:
        PIL.Image object: The marginized image.
    """
    base_image = Image.open(base_image_path)
    background = Image.new(
        "RGBA",
        (base_image.width + margin_size * 2, base_image.height + margin_size * 2),
        (255, 255, 255),
    )
    return generate_signature(background, base_image, True, True)


def generate_printsheet(qr_codes: list):
    """Generates a print sheet from the given QR codes.

    Args:
        qr_codes (list): A list which contains marginized PIL.Image objects. 

    Returns:
        PIL.Image object: The generated print sheet.
    """
    # Get generator settings
    margin_size = main_window.Element("-ps_margin-").Get()
    paper_size = main_window.Element("-ps_papertype-").Get()
    # TODO: Rewrite this section to use dicts
    if paper_size == "A4":
        paper_size = A4_SIZE
    else:
        paper_size = A4_SIZE

    # Marginize images
    marginized_imgs = []
    for i in range(len(qr_codes)):
        marginized_imgs.append(add_margin(qr_codes[i], margin_size))

    # Create background
    paper = Image.new("RGBA", paper_size, (255, 255, 255))

    # Place the images on the paper
    place_counter = (0, 0)
    for i in range(len(marginized_imgs)):
        # Prevent horizontal overflow
        if (paper_size[0] - place_counter[0]) < marginized_imgs[i].width:
            place_counter = (0, place_counter[1] + marginized_imgs[i].height)
        # Prevent vertical overflow
        if (paper_size[1] - place_counter[1]) < marginized_imgs[i].height:
            imgs_left = len(marginized_imgs) - i
            pgui.popup_error(
                f"Too many inputs! Couldn't fit the last {imgs_left} image{'' if imgs_left <= 1 else 's'}!"
            )
            break
        paper.paste(marginized_imgs[i], place_counter)
        place_counter = (place_counter[0] + marginized_imgs[i].width, place_counter[1])

    return paper


class HTMLReader(html.parser.HTMLParser):
    """A custom HTML parser, that collects all the Base64 image data from an
    HTML input.

    Args:
        collector (list): All the Base64 encoded images will be placed here.
    """

    def __init__(self, collector: list):
        """Inits HTMLReader."""
        html.parser.HTMLParser.__init__(self)
        self.collector = collector

    def handle_starttag(self, tag, attrs):
        """Detects HTML starttags.

        Args:
            tag (string): The name of the HTML tag.
            attrs (string): All the attributes of the detected tag.
        """
        # Only collects the img tags & removes the data prefixes
        if tag == "img":
            self.collector.append(attrs[1][1].split("data:image/png;base64,")[1])

    def handle_endtag(self, tag):
        pass

    def handle_data(self, data):
        pass

    def handle_comment(self, data):
        pass

    def handle_entityref(self, name):
        pass

    def handle_charref(self, name):
        pass

    def handle_decl(self, data):
        pass


def split_htmlsheet(html_path: str):
    """Collects all the Base64 encoded images from the provided HTML file. And
    converts them into PIL.Image objects.

    Args:
        html_path (str): Path to the provided HTML file.

    Returns:
        List: A list filled with PIL.Image objects.
    """
    encoded_imgs = []
    html_file = open(html_path, "r").read()
    parser = HTMLReader(encoded_imgs)
    parser.feed(html_file)

    # Decode images from Base64 strings into PIL Image objects
    decoded_imgs = []
    for i in range(len(encoded_imgs)):
        temp_img = Image.open(io.BytesIO(base64.b64decode(encoded_imgs[i])))
        decoded_imgs.append(temp_img)

    return decoded_imgs


while True:
    event, values = main_window.read()
    if event == pgui.WIN_CLOSED or event == "Exit":
        break
    elif event == "Clear inputs":
        # Clear SG inputs
        qr_paths = []
        sign_path = ""
        export_location = ""
        # Clear PS inputs
        ps_paths = []
        printsheet = None
        # Clear HS inputs
        html_path = ""
        html_splits = []

    # Signature Generator commands
    elif event == "-import_qr-" or event == "QR Code(s)":
        qr_files = pgui.popup_get_file(
            "Choose your QR code(s) you want to sign!",
            multiple_files=True,
            icon=icon_image,
        )
        print(qr_files)
        qr_paths = parse_paths(qr_files)
        print(qr_paths)
    elif event == "-import_sign-" or event == "Signature Image":
        sign_path = pgui.popup_get_file("Choose your signature image!", icon=icon_image)
        print(sign_path)
    elif event == "-set_export_location-" or event == "Specify export location":
        export_location = pgui.popup_get_folder(
            "Choose your output folder!", icon=icon_image
        )
        print(export_location)
    elif event == "-generate-" or event == "Generate":
        generated_images = []
        for i in range(len(qr_paths)):
            generated_images.append(generate_signature(qr_paths[i], sign_path))
        for i in range(len(generated_images)):
            generated_images[i].save(
                f"{export_location}{'' if export_location.endswith('/') else '/'}gen_{total_session_gens}_{i}.png"
            )
        total_session_gens += (
            1  # This prevents regenerating the previously generated images
        )

    # HTML Sheet Splitter commands
    elif event == "-hs_import-":
        html_path = pgui.popup_get_file(
            "Choose an HTML sheet to split!",
            icon=icon_image,
            file_types=(("HTML files", "*.html"),),
        )
        html_splits = split_htmlsheet(html_path)
    elif event == "-hs_save-":
        export_folder = pgui.popup_get_folder(
            "Choose your output folder!", icon=icon_image
        )
        for i in range(len(html_splits)):
            html_splits[i].save(
                f"{export_folder}{'' if export_folder.endswith('/') else '/'}export_{i}.png"
            )
    elif event == "-hs_exp_sg-":
        # TODO: Implement the Signature Generator importer
        pass
    elif event == "-hs_exp_ps-":
        # TODO: Implement the Print Sheet Generator importer
        pass

    # Print Sheet Generator commands
    elif event == "-ps_imp-":
        ps_files = pgui.popup_get_file(
            "Choose your QR codes(s) you want to stitch together!",
            multiple_files=True,
            icon=icon_image,
        )
        print(ps_files)
        ps_paths = parse_paths(ps_files)
        print(ps_paths)
    elif event == "-ps_gen-":
        printsheet = generate_printsheet(ps_paths)
        main_window.Element("-ps_img-").Update(
            filename=None,
            data=generate_thumbnail(printsheet, (248, 350)).getvalue(),
            size=(248, 350),
        )
    elif event == "-ps_save-":
        ps_export_location = pgui.popup_get_folder(
            "Choose your output folder!", icon=icon_image
        )
        printsheet.save(
            f"{ps_export_location}{'' if ps_export_location.endswith('/') else '/'}printsheet.png"
        )

    ready_check()
    update_thumbnails()
    print(event)

main_window.close()
