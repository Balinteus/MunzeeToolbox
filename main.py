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
sign_path = ""
export_location = ""
total_session_gens = 0

# Default Settings
qr_size = 500
sign_size = 100
output_size = 85

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

printsheetLayout = [
    [pgui.Column([ [pgui.Frame("Options", [
                      [pgui.Button("Import QR Code(s)", size=[38, 1], key="-ps_imp-")],
                      [pgui.HorizontalSeparator(pad=(10, 10))],
                      [pgui.Text("Paper size: "), pgui.DropDown(["A4"], default_value="A4", readonly=True)],
                      [pgui.Text("Margin size: "), pgui.Spin([i for i in range(1, 1500)], initial_value=10), pgui.Text("px")],
                      [pgui.HorizontalSeparator(pad=(10, 10))],
                      [pgui.Button("Generate", size=[38, 1], key="-ps_gen-")],
                      [pgui.Button("Save generated image", size=[38, 1], key="-ps_save-")], ])] ]),
    pgui.Column([ [pgui.Image(arrow_image, size=(100, 100))] ]),
    pgui.Column([ [pgui.Frame("Output", [[pgui.Image(empty_image, key="-rendered_img-", size=(248, 350))]])]])]
]

settingsLayout = [
    [pgui.Text("Settings")],
    [pgui.Text("Imported QR Code size: "), pgui.Input()],
    [pgui.Text("Signature image size (on generated img): "), pgui.Input()],
]

tabLayout = [
    [
        pgui.Tab("Signature generator", generatorLayout),
        pgui.Tab("HTML sheet splitter", generatorLayout),
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


def generateSignature(qr_path, sign_path, isThumbnail=False):
    # Load the base images
    qr_img = Image.open(qr_path)
    sign_img = Image.open(sign_path)

    # ...and resize them
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


def generateThumbnail(base_image):
    base_image.thumbnail((300, 300))
    generated_thumbnail = io.BytesIO()
    base_image.save(generated_thumbnail, format="PNG")
    return generated_thumbnail


def updateThumbnails():
    print("Updating thumbnails...")
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


while True:
    event, values = mainWindow.read()
    if event == pgui.WIN_CLOSED or event == "Exit":
        break
    elif event == "-import_qr-" or event == "QR Code(s)":
        qr_files = pgui.popup_get_file(
            "Choose your QR code(s) you want to sign!",
            multiple_files=True,
            icon=icon_image,
        )
        print(qr_files)
        # Example files string: "C:/Users/balin/Desktop/gen.png;C:/Users/balin/Desktop/index.png"
        if (qr_files != None) and (qr_files != ""):
            qr_paths = qr_files.split(";")
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
    elif event == "Clear inputs":
        qr_paths = []
        sign_path = ""
        export_location = ""
    readyCheck()
    updateThumbnails()
    print(event)

mainWindow.close()
