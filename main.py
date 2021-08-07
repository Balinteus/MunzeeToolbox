import io
import sys
from PIL import Image, ImageDraw, ImageFilter
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

qr_paths = []
ps_paths = []
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

# fmt: off
menubarLayout = [
    ["&File", ["&Import...", ["&QR Code(s)", "&Signature Image"], "Specify &export location", "---", "!&Generate", "!&Print", "&Clear inputs", "---", "E&xit"]],
    ["&Toolbox", ["&HTML sheet splitter", "&Print sheet generator"]],
    ["Se&ttings"],
    ["&About", ["!Made by: Balinteus", "---",  "My website", "The project's github page"]]
]

generatorLayout = [
    [pgui.Column([ [pgui.Frame("Imported QR Code", [[pgui.Image(empty_image, key="-qr_img-", size=(300, 300))]])],
                 [pgui.Button("Import QR Code(s)", size=[38, 1], key="-import_qr-")],
                 [pgui.Button("Import Signature Image", size=[38, 1], key="-import_sign-")] ]),
    pgui.Column([ [pgui.Image(arrow_image, size=(100, 100))] ]),
    pgui.Column([ [pgui.Frame("Generated QR Code", [[pgui.Image(empty_image, key="-rendered_img-", size=(300, 300))]])],
                 [pgui.Button("Specify export location", size=[38, 1], key="-set_export_location-")],
                 [pgui.Button("Generate", size=[38, 1], disabled=True, key="-generate-")] ])]
]

htmlsplitterLayout = [
    [pgui.Column([[pgui.Frame("HTML sheet splitter", [[pgui.Button("Import HTML sheet", size=[38, 1], key="-hs_import-")],
                [pgui.HorizontalSeparator(pad=(10, 10))],
                [pgui.Button("Save QR Code(s)", size=[38, 1], key="-hs_save-", disabled=True)],
                [pgui.HorizontalSeparator(pad=(10, 10))],
                [pgui.Button("Export QR Code(s) into Signature Generator", size=[38, 1], key="-hs_exp_sg-", disabled=True)],
                [pgui.Button("Export QR Code(s) into Print Sheet Generator", size=[38, 1], key="-hs_exp_ps-", disabled=True)] ], pad=(225, 100)) ]]) ]
]

printsheetLayout = [
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

settingsLayout = [
    [pgui.Text("Settings")],
    [pgui.Text("Imported QR Code size: "), pgui.Input()],
    [pgui.Text("Signature image size (on generated img): "), pgui.Input()],
]

tabLayout = [
    [
        pgui.Tab("Signature generator", generatorLayout),
        pgui.Tab("HTML sheet splitter", htmlsplitterLayout),
        pgui.Tab("Print sheet generator", printsheetLayout),
        pgui.Tab("Settings", settingsLayout),
    ]
]

mainLayout = [ 
    [pgui.Menu(menubarLayout)],
    [pgui.Text("Balinteus' Munzee Toolbox", size=[46, 1], font="Helvitica 20 bold", justification="center", relief=pgui.RELIEF_RIDGE)],
    [pgui.TabGroup(tabLayout, tab_location="topleft")]
]
# fmt: on

mainWindow = pgui.Window("Munzee Toolbox", mainLayout, icon=icon_image)


def readyCheck():
    print("Ready check!")
    if (
        (len(qr_paths) > 0)
        and (sign_path != "")
        and (sign_path != None)
        and (export_location != "")
        and (export_location != None)
    ):
        mainWindow.Element("-generate-").Update(disabled=False)
        print("READY!")
    else:
        mainWindow.Element("-generate-").Update(disabled=True)
    if len(ps_paths) > 0:
        mainWindow.Element("-ps_gen-").Update(disabled=False)
        mainWindow.Element("-ps_save-").Update(disabled=False)
    else:
        mainWindow.Element("-ps_gen-").Update(disabled=True)
        mainWindow.Element("-ps_save-").Update(disabled=True)


def generateSignature(qr_path, sign_path, isThumbnail=False, isBinary=False):
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


def generateThumbnail(base_image, size=(300, 300)):
    # Create a copy of the base image, this way we don't overwrite it
    work_image = base_image.copy()

    # Create thumbnail
    work_image.thumbnail(size)

    # Write the img into BytesIO, so we can pass the raw data into the img element
    generated_thumbnail = io.BytesIO()
    work_image.save(generated_thumbnail, format="PNG")

    return generated_thumbnail


def updateThumbnails():
    print("Updating thumbnails...")
    # Update SG thumbnails
    if len(qr_paths) > 1:
        mainWindow.Element("-qr_img-").Update(filename=multiple_image, size=(300, 300))
        if (sign_path != "") and (sign_path != None):
            mainWindow.Element("-rendered_img-").Update(
                filename=multiple_image, size=(300, 300)
            )
    elif len(qr_paths) == 1:
        # Update QR thumbnail
        qr_thumbnail = generateThumbnail(Image.open(qr_paths[0]))
        mainWindow.Element("-qr_img-").Update(
            filename=None, data=qr_thumbnail.getvalue(), size=(300, 300)
        )
        # Update Rendered thumbnail
        if (sign_path != "") and (sign_path != None):
            rendered_image = generateSignature(qr_paths[0], sign_path, True)
            rendered_thumbnail = generateThumbnail(rendered_image)
            mainWindow.Element("-rendered_img-").Update(
                filename=None, data=rendered_thumbnail.getvalue(), size=(300, 300)
            )
        else:
            mainWindow.Element("-rendered_img-").Update(
                filename=None, data=qr_thumbnail.getvalue(), size=(300, 300)
            )
    else:
        mainWindow.Element("-qr_img-").Update(filename=empty_image, size=(300, 300))
        mainWindow.Element("-rendered_img-").Update(
            filename=empty_image, size=(300, 300)
        )
    # Update PS thumbnails
    if printsheet == None:
        mainWindow.Element("-ps_img-").Update(filename=empty_image, size=(248, 350))


def parsePaths(raw_paths: str):
    parsed_paths = []
    if (raw_paths != None) and (raw_paths != ""):
        parsed_paths = raw_paths.split(";")
    return parsed_paths


def addMargin(base_image_path: str, margin_size: int):
    base_image = Image.open(base_image_path)
    background = Image.new(
        "RGBA",
        (base_image.width + margin_size * 2, base_image.height + margin_size * 2),
        (255, 255, 255),
    )
    return generateSignature(background, base_image, True, True)


def generatePrintsheet(qr_codes: dict):
    # Get generator settings
    margin_size = mainWindow.Element("-ps_margin-").Get()
    paper_size = mainWindow.Element("-ps_papertype-").Get()
    if paper_size == "A4":
        paper_size = A4_SIZE
    else:
        paper_size = A4_SIZE

    # Marginize images
    marginized_imgs = []
    for i in range(len(qr_codes)):
        marginized_imgs.append(addMargin(qr_codes[i], margin_size))

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
            pgui.popup_error(f"Too many inputs! Couldn't fit the last {imgs_left} image{'' if imgs_left <= 1 else 's'}!")
            break
        paper.paste(marginized_imgs[i], place_counter)
        place_counter = (place_counter[0] + marginized_imgs[i].width, place_counter[1])

    return paper


while True:
    event, values = mainWindow.read()
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

    # Signature Generator commands
    elif event == "-import_qr-" or event == "QR Code(s)":
        qr_files = pgui.popup_get_file(
            "Choose your QR code(s) you want to sign!",
            multiple_files=True,
            icon=icon_image,
        )
        print(qr_files)
        # Example files string: "C:/Users/balin/Desktop/gen.png;C:/Users/balin/Desktop/index.png"
        qr_paths = parsePaths(qr_files)
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
            generated_images.append(generateSignature(qr_paths[i], sign_path))
        for i in range(len(generated_images)):
            generated_images[i].save(
                f"{export_location}{'' if export_location.endswith('/') else '/'}gen_{total_session_gens}_{i}.png"
            )
        total_session_gens += (
            1  # This prevents regenerating the previously generated images
        )

    # Print Sheet Generator commands
    elif event == "-ps_imp-":
        ps_files = pgui.popup_get_file(
            "Choose your QR codes(s) you want to stitch together!",
            multiple_files=True,
            icon=icon_image,
        )
        print(ps_files)
        ps_paths = parsePaths(ps_files)
        print(ps_paths)
    elif event == "-ps_gen-":
        printsheet = generatePrintsheet(ps_paths)
        mainWindow.Element("-ps_img-").Update(
            filename=None,
            data=generateThumbnail(printsheet, (248, 350)).getvalue(),
            size=(248, 350),
        )
    elif event == "-ps_save-":
        ps_export_location = pgui.popup_get_folder(
            "Choose your output folder!", icon=icon_image
        )
        printsheet.save(
            f"{ps_export_location}{'' if ps_export_location.endswith('/') else '/'}printsheet.png"
        )

    readyCheck()
    updateThumbnails()
    print(event)

mainWindow.close()
