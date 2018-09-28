import math
import numpy as np
from PIL import Image, ImageChops, ImageFilter, ImageDraw, ImageOps
from src.Const import Const

class Shape:
    SOLID = 0
    VOID = 1
    PATTERN = 2

    def __init__(self, img):
        self.img = img
        self.height = min(img.size)
        self.width = max(img.size)
        self.position = Op.getPosition(img)
        self.pattern = self.getPattern(img)
        self.isProcessed = False

    def getPattern(self, img):
        devImg = img.copy()

        devImg = ImageOps.expand(devImg, border=2, fill=Const.WHITE_VALUE)
        ImageDraw.floodfill(devImg, xy=(0, 0), value=Const.FLOODFILL_VALUE)
        if devImg.getextrema()[1] < Const.WHITE_VALUE: return Shape.SOLID

        whitePx = Op.detectEdge(devImg, fill=Const.WHITE_VALUE)
        ImageDraw.floodfill(devImg, xy=(whitePx[1], whitePx[0]), value=Const.BLACK_VALUE)
        if devImg.getextrema()[1] < Const.WHITE_VALUE: return Shape.VOID

        return Shape.PATTERN

    @staticmethod
    def fill(img):
        devImg = img.copy()
        devImg = ImageOps.expand(devImg, border=2, fill=Const.WHITE_VALUE)
        ImageDraw.floodfill(devImg, xy=(0, 0), value=Const.FLOODFILL_VALUE)
        devImg = ImageOps.crop(devImg, border=2)
        pixels = np.array(devImg)
        pixels[pixels != Const.FLOODFILL_VALUE] = Const.BLACK_VALUE
        pixels[pixels != Const.BLACK_VALUE] = Const.WHITE_VALUE
        devImg = Image.fromarray(pixels, mode='L')
        return devImg

    def getDetail(self):
        print(self.height, self.width, self.pattern)

    def show(self):
        self.img.show()

class Op:
    @staticmethod
    def explore(img):
        shapes = []
        img = img.copy()
        shouldContinue = True
        while shouldContinue:
            edgeCoor = Op.detectEdge(img)
            if edgeCoor is None:
                return shapes
            extractedShape = Op.extractShape(img, edgeCoor)
            shape = Shape(extractedShape)
            shapes.append(shape)
            Op.updateOriginalImage(img, edgeCoor) # usually cause 'NoneType' object has no attribute 'size', debug by image.show()

            stagingImg = Op.trimWhite(img)
            whiteImg = Image.new("L", stagingImg.size, Const.WHITE_VALUE)
            shouldContinue = not Op.isHistSimilar(stagingImg, whiteImg)
        return shapes

    @staticmethod
    def detectEdge(img, fill=0):
        it = np.nditer(img, flags=['multi_index'])
        while not it.finished:
            pixel = it[0]
            if pixel == fill:
                return it.multi_index
            else:
                it.iternext()

    @staticmethod
    def extractShape(img, edge):
        ImageDraw.floodfill(img, xy=(edge[1], edge[0]), value=Const.FLOODFILL_VALUE, border=Const.WHITE_VALUE)
        pixels = np.array(img)
        pixels[pixels != Const.FLOODFILL_VALUE] = Const.WHITE_VALUE
        pixels[pixels == Const.FLOODFILL_VALUE] = Const.BLACK_VALUE
        return Image.fromarray(pixels, mode = 'L')

    @staticmethod
    def isHistSimilar(img1, img2, shouldCrop = False, p = False):
        im1 = img1.copy()
        im2 = img2.copy()

        if shouldCrop:
            im1 = Op.trimWhite(im1)
            im2 = Op.trimWhite(im2)

        # Calculate the root-mean-square difference between two images
        dif = ImageChops.difference(im1, im2)
        h = dif.histogram()
        sq = (value * (idx ** 2) for idx, value in enumerate(h))
        sum_of_squares = sum(sq)
        rms = math.sqrt(sum_of_squares / float(im1.size[0] * im2.size[1]))
        if p:
            print(rms)
            dif.show()
        if rms < Const.SIMILARITY_THRESHOLD:
            return True
        return False

    @staticmethod
    def isShapeSimilar(shape1, shape2, p = False):
        pos1 = shape1.position
        pos2 = shape2.position

        if pos1 == None:
            pos1 = [0 ,0]
        if pos2 == None:
            pos2 = [0, 0]

        img1 = Op.trimWhite(shape1.img)
        img2 = Op.trimWhite(shape2.img)

        if Op.isHistSimilar(img1, img2, p) and abs(pos1[0] - pos2[0]) < 10 and abs(pos1[1] - pos2[1]) < 10:
            return True
        return False

    @staticmethod
    def isBlurSimilar(img1, img2, p = False):
        img1 = img1.filter(ImageFilter.GaussianBlur(radius=2.5))
        dif = ImageChops.difference(img1, img2)

        if p:
            dif.show()
        mostDifPixel = dif.getextrema()[1]
        if mostDifPixel < Const.BLUR_THRESHOLD:
            return True
        return False


    @staticmethod
    def getPosition(img):
        whiteBg = Image.new('L', img.size, Const.WHITE_VALUE)
        diff = ImageChops.difference(img, whiteBg)
        return diff.getbbox()

    @staticmethod
    def trimWhite(img):
        cropPos = Op.getPosition(img)
        # TODO: use this box coordinate to set location for shape
        return img.crop(cropPos)

    @staticmethod
    def updateOriginalImage(img, edge):
        ImageDraw.floodfill(img, xy=(edge[1], edge[0]), value=255, border=255)

    @staticmethod
    def addImage(img, shape):
        return ImageChops.darker(img, shape)