from PIL import Image, ImageDraw, ImageFilter
import PySimpleGUI as pgui

pgui.theme("DarkAmber")

empty_image = "C:\\Users\\balin\\Desktop\\Current Projects\\MunzeeSignatureGen\\img\\arrow.png"
arrow_image = "C:\\Users\\balin\\Desktop\\Current Projects\\MunzeeSignatureGen\\img\\arrow.png"

not_multi_input = True

# Default Settings
qr_size = 500
sign_size = 100
output_size = 85

# TODO: Create columns
windowLayout = [ [pgui.Text("Balinteus' Munzee Signature Generator", size=[44, 1], font="Helvitica 20 bold", justification="center", relief=pgui.RELIEF_RIDGE)], 
                [pgui.Frame("Imported QR Code", [[pgui.Image(empty_image, key="-qr_img-", size=(300, 300))]]),
                 pgui.Image(arrow_image, size=(100, 100)),
                 pgui.Frame("Generated QR Code", [[pgui.Image(empty_image, key="-rendered_img-", size=(300, 300))]])],
                [pgui.Button("Import QR Code(s)", size=[38, 1]), pgui.Button("Export", size=[38, 1])],
                [pgui.Button("Import Signiture Image", size=[38, 1]), pgui.Button("Batch Export", size=[38, 1], disabled=not_multi_input)] ]

mainWindow = pgui.Window("Munzee Signature Generator", windowLayout)

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
    print("Input: ", values[0])

window.close()

