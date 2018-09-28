# Your Agent for solving Raven's Progressive Matrices. You MUST modify this file.
#
# You may also create and submit new files in addition to modifying this file.
#
# Make sure your file retains methods with the signatures:
# def __init__(self)
# def Solve(self,problem)
#
# These methods will be necessary for the project's main method to run.

# Install Pillow and uncomment this line to access image processing.
# Floodfill only works with RGB
from PIL import Image, ImageChops, ImageFilter, ImageDraw, ImageOps, ImageEnhance
import copy
import numpy as np
from pathlib import Path
import math

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

    def getPattern(self,img):
        devImg = img.copy()

        devImg = ImageOps.expand(devImg, border=2, fill=Op.WHITE_VALUE)
        ImageDraw.floodfill(devImg, xy=(0, 0), value=Op.FLOODFILL_VALUE)
        if devImg.getextrema()[1] < 255: return Shape.SOLID

        whitePx = Op.detectEdge(devImg, fill=Op.WHITE_VALUE)
        ImageDraw.floodfill(devImg, xy=(whitePx[1], whitePx[0]), value=Op.BLACK_VALUE)
        if devImg.getextrema()[1] < 255: return Shape.VOID

        return Shape.PATTERN

    @staticmethod
    def fill(img):
        devImg = img.copy()
        devImg = ImageOps.expand(devImg, border=2, fill=Op.WHITE_VALUE)
        ImageDraw.floodfill(devImg, xy=(0, 0), value=Op.FLOODFILL_VALUE)
        devImg = ImageOps.crop(devImg, border=2)
        pixels = np.array(devImg)
        pixels[pixels != Op.FLOODFILL_VALUE] = Op.BLACK_VALUE
        pixels[pixels != Op.BLACK_VALUE] = Op.WHITE_VALUE
        devImg = Image.fromarray(pixels, mode='L')
        return devImg

    def getDetail(self):
        print(self.height, self.width, self.pattern, self.name, self.child)

    def show(self):
        self.img.show()

class Transform:
    def __init__(self):
        self.mod = {'remove': [], 'add': [], 'transform': [], 'fill': [], 'rotate': []}

    def extract(self, group1, group2):
        group1 = copy.deepcopy(group1)
        group2 = copy.deepcopy(group2)
        transformMod = None
        for shapeA in group1:
            for shapeB in group2:
                if shapeA.isProcessed or shapeB.isProcessed: continue
                if self.checkExistence(shapeA, shapeB, False):
                    shapeA.isProcessed = True
                    shapeB.isProcessed = True
                    continue
                patternMod = self.checkPattern(shapeA, shapeB)
                if patternMod is not None:
                    self.mod['fill'].append(patternMod)
                    shapeA.isProcessed = True
                    shapeB.isProcessed = True
                    continue
                transform = self.checkTransformation(shapeA, shapeB)
                if transform is not None:
                    transformMod = transform
                    shapeA.isProcessed = True
                    shapeB.isProcessed = True
                    continue
                rotateMod = self.checkRotation(shapeA, shapeB)
                if rotateMod is not None:
                    self.mod['rotate'].append(rotateMod)
                    shapeA.isProcessed = True
                    shapeB.isProcessed = True
            if not shapeA.isProcessed:
                shapeA.isProcessed = True
                self.mod['remove'].append(shapeA)
        if transformMod is not None:
            self.mod['transform'].append(transformMod)


        for shape in group2:
            if not shape.isProcessed:
                self.mod['add'].append(shape)

    def apply(self, image):
        for val in self.mod['remove']:
            edge = Op.detectEdge(val.img)
            Op.updateOriginalImage(image, edge)
        for val in self.mod['add']:
            image = Op.addImage(image, val.img)
        for val in self.mod['fill']:
            if val is Shape.SOLID:
                image = Shape.fill(image)
        for val in self.mod['transform']:
            if val is not None:
                image = image.transpose(val)
        for val in self.mod['rotate']:
            image = image.rotate(val)
            image = ImageOps.expand(image, border=2, fill=Op.BLACK_VALUE)
            ImageDraw.floodfill(image, xy=(0, 0), value=Op.WHITE_VALUE)
            image = ImageOps.crop(image, border=2)
        return image

    def checkExistence(self, shapeA, shapeB, p = False):
        if Op.isHistSimilar(shapeA.img, shapeB.img, p):
            return True
        return False

    def checkTransformation(self, shapeA, shapeB):
        ops = [Image.FLIP_LEFT_RIGHT, Image.FLIP_TOP_BOTTOM, Image.ROTATE_90, Image.ROTATE_180,
                        Image.ROTATE_270]
        for op in ops:
            modifiedShape = shapeA.img.transpose(op)
            if Op.isHistSimilar(modifiedShape, shapeB.img, False):
                return op
        return None

    def checkRotation(self, shapeA, shapeB):
        ops = [45, -45, 125, -125]
        for op in ops:
            modifiedShape = ImageOps.expand(shapeA.img, border=100, fill=Op.WHITE_VALUE) # shape will get cut off when rotates if it is close to the border
            modifiedShape = modifiedShape.rotate(op)
            modifiedShape = ImageOps.expand(modifiedShape, border=2, fill=Op.BLACK_VALUE)
            ImageDraw.floodfill(modifiedShape, xy=(0, 0), value=Op.WHITE_VALUE)
            modifiedShape = ImageOps.crop(modifiedShape, border=102)
            if Op.isHistSimilar(modifiedShape, shapeB.img, shouldCrop=True, p=False):
                return op
        return None

    def checkPattern(self, shapeA, shapeB):
        solidA = Shape.fill(shapeA.img)
        solidB = Shape.fill(shapeB.img)
        if shapeA.pattern != shapeB.pattern and shapeB.pattern == Shape.SOLID and Op.isHistSimilar(solidA, solidB):
            return Shape.SOLID
        return None

class Op:
    WHITE_VALUE = 255
    BLACK_VALUE = 0
    FLOODFILL_VALUE = 140
    FLOODFILL_RGB_VALUE = (FLOODFILL_VALUE, FLOODFILL_VALUE, FLOODFILL_VALUE)
    EXPLORE_THRESHOLD = 15 # used to continue with loop to search for shapes 10
    CROP_THRESHOLD = 120 # used for cropping image after extracting a shape
    SIMILARITY_THRESHOLD = 50

    @staticmethod
    def explore(img):
        shapes = []
        img = img.copy()
        shouldContinue = True
        # while img.getextrema()[0] == 0:
        while shouldContinue:
            # index = len(shapes)
            # if index > 0:
            #     shapes[-1].child = "S" + str(index)
            edgeCoor = Op.detectEdge(img)
            if edgeCoor is None:
                return shapes
            extractedShape = Op.extractShape(img, edgeCoor)
            shape = Shape(extractedShape)
            shapes.append(shape)
            Op.updateOriginalImage(img, edgeCoor) # usually cause 'NoneType' object has no attribute 'size', debug by image.show()

            stagingImg = Op.trimWhite(img)
            whiteImg = Image.new("L", stagingImg.size, Op.WHITE_VALUE)
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
        ImageDraw.floodfill(img, xy=(edge[1], edge[0]), value=Op.FLOODFILL_VALUE, border=Op.WHITE_VALUE)
        pixels = np.array(img)
        pixels[pixels != Op.FLOODFILL_VALUE] = Op.WHITE_VALUE
        pixels[pixels == Op.FLOODFILL_VALUE] = Op.BLACK_VALUE
        return Image.fromarray(pixels, mode = 'L')

    @staticmethod
    def isHistSimilar(img1, img2, shouldCrop = False, withSolid = False, p = False):
        # dif = ImageChops.difference(img1, img2).filter(ImageFilter.GaussianBlur(radius=1.5))
        # if max(list(dif.getdata())) < Op.SIMILARITY_THRESHOLD:
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
        if rms < Op.SIMILARITY_THRESHOLD:
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
        mostDifPixel = dif.getextrema()[1]
        if mostDifPixel < 225:
            return True
        return False


    @staticmethod
    def getPosition(img):
        whiteBg = Image.new('L', img.size, 255)
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

class Agent:
    # The default constructor for your Agent. Make sure to execute any
    # processing necessary before your Agent starts solving problems here.
    #
    # Do not add any variables to this signature; they will not be used by
    # main().
    def __init__(self):
        pass

    # The primary method for solving incoming Raven's Progressive Matrices.
    # For each problem, your Agent's Solve() method will be called. At the
    # conclusion of Solve(), your Agent should return an int representing its
    # answer to the question: 1, 2, 3, 4, 5, or 6. Strings of these ints 
    # are also the Names of the individual RavensFigures, obtained through
    # RavensFigure.getName(). Return a negative number to skip a problem.
    #
    # Make sure to return your answer *as an integer* at the end of Solve().
    # Returning your answer as a string may cause your program to crash.

    WHITE_IMG = Image.new('L', (184,184), 255)

    def Solve(self,problem):
        answer = -1
        np.set_printoptions(threshold=np.nan)
        path = Path("Problems/" + problem.problemSetName + "/" + problem.name)

        pathA = path.joinpath("A.png")
        pathB = path.joinpath("B.png")
        pathC = path.joinpath("C.png")

        imA = Image.open(pathA).convert('L')
        imB = Image.open(pathB).convert('L')
        imC = Image.open(pathC).convert('L')

        shapesA = Op.explore(imA)
        shapesB = Op.explore(imB)
        shapesC = Op.explore(imC)

        trans = Transform()
        trans.extract(shapesA, shapesB)
        trans.extract(shapesA, shapesC)
        guessImage = trans.apply(imA)
        guessShape = Shape(guessImage)

        choiceShapeSet = []
        for choice in range(1, 7):
            choicePath = path.joinpath(str(choice) + ".png")
            choiceImg = Image.open(choicePath).convert('L')
            choiceShapeSet.append(Shape(choiceImg))

        for idx, sh in enumerate(choiceShapeSet):
            if Op.isShapeSimilar(guessShape, sh):
                answer = idx + 1
                break

        if answer == -1:
            for idx, sh in enumerate(choiceShapeSet):
                if Op.isBlurSimilar(guessImage, sh.img, p=False):
                    answer = idx + 1
                    break

        print(answer)
        return answer
