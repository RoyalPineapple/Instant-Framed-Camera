from PIL import Image, ImageOps, ImageEnhance, ImageMath

# prepare any image for display on a 7 color e-ink screen
def processForEInk(imagePath, outputPath, imgSize):

        # get image
        print("Processing begin")

        print(f"- Opening imag {imagePath}")
        img = Image.open(imagePath)

        print(f"- Resizing image: {imgSize}")
        # correct resolution for display
        img = ImageOps.fit(img, imgSize)
        
        print("- Converting to RGB")
        # make RGB only
        img.convert('RGB')

        print("- Adjusting saturation")

        # initial overall saturation
        saturation = ImageEnhance.Color(img)
        img = saturation.enhance(3)

        # magenta is a problematic color on ink displays
        r, g, b = img.split()
        imgMask = ImageMath.eval("255*( (float(r)/255)**10*1.3 * (float(b)/255)**10*1.3 * (1-(float(g)/255)**10)*1.3 * 4 )", r=r, g=g, b=b) # (strong) mask magenta
        imgMask = imgMask.convert('L')

        # desaturated version to overlay
        saturation = ImageEnhance.Color(img)
        imgFixed = saturation.enhance(.3)
        brightness = ImageEnhance.Brightness(imgFixed)
        imgFixed = brightness.enhance(1.8)
        r, g, b = imgFixed.split()
        g = g.point(lambda i: i * .9) # slightly less green
        b = b.point(lambda i: i * .8) # less blue
        imgFixed = Image.merge('RGB', (r, g, b))

        # save
        print(f"- Saving file: {outputPath}")
        imgFixed.save(outputPath)

