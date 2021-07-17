from PIL import Image, ImageDraw, ImageFilter
import PySimpleGUI as pgui

pgui.theme("DarkAmber")

empty_image = "C:\\Users\\balin\\Desktop\\Current Projects\\MunzeeSignatureGen\\img\\arrow.png"
arrow_image = "C:\\Users\\balin\\Desktop\\Current Projects\\MunzeeSignatureGen\\img\\arrow.png"

qr_paths = []
sign_path = ""
export_location = ""

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

mainWindow = pgui.Window("Munzee Signature Generator", windowLayout)

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


while True:
    event, values = mainWindow.read()
    if event == pgui.WIN_CLOSED or event == 'Cancel':
        break
    elif event == "-import_qr-":
        qr_files = pgui.popup_get_file("Choose your QR code(s) you want to sign!", multiple_files=True)
        print(qr_files)    # DEBUG
        # Example files string: "C:/Users/balin/Desktop/gen.png;C:/Users/balin/Desktop/index.png"
        if (qr_files != None) and (qr_files != ""):
            qr_paths = qr_files.split(";")
        print(qr_paths) # DEBUG
    elif event == "-import_sign-":
        sign_path = pgui.popup_get_file("Choose your signature image!")
        print(sign_path)    # DEBUG
    elif event == "-set_export_location-":
        export_location = pgui.popup_get_folder("Choose your output folder!")
        print(export_location)  # DEBUG
    elif event == "-generate-":
        # TODO: Implement this shit
        pass
    readyCheck()
    print(event[0])

window.close()

