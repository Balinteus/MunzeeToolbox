import io
import sys
from PIL import Image, ImageDraw, ImageFilter
import PySimpleGUI as pgui

pgui.theme("DarkBrown4")

# Preparing the asset directory
# https://stackoverflow.com/questions/31836104/pyinstaller-and-onefile-how-to-include-an-image-in-the-exe-file
if getattr(sys, 'frozen', False):       # Check if running as compiled
    image_dir = sys._MEIPASS + "/img/"  # In production (compiled with PyInstaller)
else:
    image_dir = "./img/"                # Path name when run with Python interpreter

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

windowLayout = [ [pgui.Text("Balinteus' Munzee Signature Generator", size=[46, 1], font="Helvitica 20 bold", justification="center", relief=pgui.RELIEF_RIDGE)],
                [pgui.Column([ [pgui.Frame("Imported QR Code", [[pgui.Image(empty_image, key="-qr_img-", size=(300, 300))]])],
                             [pgui.Button("Import QR Code(s)", size=[38, 1], key="-import_qr-")],
                             [pgui.Button("Import Signature Image", size=[38, 1], key="-import_sign-")] ]),
                pgui.Column([ [pgui.Image(arrow_image, size=(100, 100))] ]),
                pgui.Column([ [pgui.Frame("Generated QR Code", [[pgui.Image(empty_image, key="-rendered_img-", size=(300, 300))]])],
                             [pgui.Button("Specify export location", size=[38, 1], key="-set_export_location-")],
                             [pgui.Button("Generate", size=[38, 1], disabled=True, key="-generate-")] ])] ]

mainWindow = pgui.Window("Munzee Signature Generator", windowLayout, icon=icon_image)

def readyCheck():
    print("Ready check!")   # DEBUG
    if (len(qr_paths) > 0) and (sign_path != "") and (export_location != "") and (sign_path != None) and (export_location != None):
        mainWindow.Element("-generate-").Update(disabled=False)
        print("READY!")    # DEBUG

def generateSignature(qr_path, sign_path):
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
    generated_img = generated_img.resize((output_size, output_size), Image.BILINEAR)

    return generated_img

def updateThumbnails():
    print("Updating thumbnails...")
    if len(qr_paths) > 1:
        mainWindow.Element("-qr_img-").Update(filename=multiple_image, size=(300, 300))
        if (sign_path != "") and (sign_path != None):
            mainWindow.Element("-rendered_img-").Update(filename=multiple_image, size=(300, 300))
    elif len(qr_paths) == 1:
        # Update QR thumbnail
        qr_image = Image.open(qr_paths[0])
        qr_image.thumbnail((300, 300))
        qr_thumbnail = io.BytesIO()
        qr_image.save(qr_thumbnail, format="PNG")
        mainWindow.Element("-qr_img-").Update(filename=None, data=qr_thumbnail.getvalue(), size=(300, 300))
        # Update Rendered thumbnail
        if (sign_path != "") and (sign_path != None):
            rendered_image = generateSignature(qr_paths[0], sign_path).resize((300, 300), Image.BILINEAR)
            rendered_image.thumbnail((300, 300))
            rendered_thumbnail = io.BytesIO()
            rendered_image.save(rendered_thumbnail, format="PNG")
            mainWindow.Element("-rendered_img-").Update(filename=None, data=rendered_thumbnail.getvalue(), size=(300, 300))
        else:
            mainWindow.Element("-rendered_img-").Update(filename=None, data=qr_thumbnail.getvalue(), size=(300, 300))
    else:
        mainWindow.Element("-qr_img-").Update(filename=empty_image, size=(300, 300))
        mainWindow.Element("-rendered_img-").Update(filename=empty_image, size=(300, 300))

while True:
    event, values = mainWindow.read()
    if event == pgui.WIN_CLOSED or event == 'Cancel':
        break
    elif event == "-import_qr-":
        qr_files = pgui.popup_get_file("Choose your QR code(s) you want to sign!", multiple_files=True, icon=icon_image)
        print(qr_files)    # DEBUG
        # Example files string: "C:/Users/balin/Desktop/gen.png;C:/Users/balin/Desktop/index.png"
        if (qr_files != None) and (qr_files != ""):
            qr_paths = qr_files.split(";")
        print(qr_paths) # DEBUG
    elif event == "-import_sign-":
        sign_path = pgui.popup_get_file("Choose your signature image!", icon=icon_image)
        print(sign_path)    # DEBUG
    elif event == "-set_export_location-":
        export_location = pgui.popup_get_folder("Choose your output folder!", icon=icon_image)
        print(export_location)  # DEBUG
    elif event == "-generate-":
        generated_images = []
        for i in range(len(qr_paths)):
            generated_images.append(generateSignature(qr_paths[i], sign_path))
        for i in range(len(generated_images)):
            generated_images[i].save(f"{export_location}{'' if export_location.endswith('/') else '/'}gen_{total_session_gens}_{i}.png")
        total_session_gens += 1  # This prevents regenerating the previously generated images
    readyCheck()
    updateThumbnails()
    print(event[0])

mainWindow.close()

