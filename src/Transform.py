import copy
from src.Const import Const
from PIL import Image, ImageDraw, ImageOps
from src.Shape import Shape, Op

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
            image = ImageOps.expand(image, border=2, fill=Const.BLACK_VALUE)
            ImageDraw.floodfill(image, xy=(0, 0), value=Const.WHITE_VALUE)
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
            modifiedShape = ImageOps.expand(shapeA.img, border=100, fill=Const.WHITE_VALUE) # shape will get cut off when rotates if it is close to the border
            modifiedShape = modifiedShape.rotate(op)
            modifiedShape = ImageOps.expand(modifiedShape, border=2, fill=Const.BLACK_VALUE)
            ImageDraw.floodfill(modifiedShape, xy=(0, 0), value=Const.WHITE_VALUE)
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