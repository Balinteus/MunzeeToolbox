from PIL import Image, ImageDraw, ImageFilter
import PySimpleGUI as pgui

pgui.theme("DarkAmber")

empty_image = "C:\\Users\\balin\\Desktop\\Current Projects\\MunzeeSignatureGen\\img\\arrow.png"
arrow_image = "C:\\Users\\balin\\Desktop\\Current Projects\\MunzeeSignatureGen\\img\\arrow.png"

not_multi_input = True

# TODO: Create columns
windowLayout = [ [pgui.Text("Balinteus' Munzee Signature Generator", size=[44, 1], font="Helvitica 20 bold", justification="center", relief=pgui.RELIEF_RIDGE)], 
                [pgui.Frame("Imported QR Code", [[pgui.Image(empty_image, key="-qr_img-", size=(300, 300))]]),
                 pgui.Image(arrow_image, size=(100, 100)),
                 pgui.Frame("Generated QR Code", [[pgui.Image(empty_image, key="-rendered_img-", size=(300, 300))]])],
                [pgui.Button("Import QR Code(s)", size=[38, 1]), pgui.Button("Export", size=[38, 1])],
                [pgui.Button("Import Signiture Image", size=[38, 1]), pgui.Button("Batch Export", size=[38, 1], disabled=not_multi_input)] ]

mainWindow = pgui.Window("Munzee Signature Generator", windowLayout)

while True:
    event, values = mainWindow.read()
    if event == pgui.WIN_CLOSED or event == 'Cancel':
        break
    print("Input: ", values[0])

window.close()

