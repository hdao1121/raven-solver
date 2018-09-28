from pathlib import Path

import numpy as np
from PIL import Image
from src.Shape import Shape, Op
from src.Transform import Transform


class Agent:
    def __init__(self):
        pass

    def Solve(self, problem):
        answer = -1
        np.set_printoptions(threshold=np.nan)
        path = Path("data/" + problem.problemSetName + "/" + problem.name)

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
                guessImage.show()
                break

        if answer == -1:
            for idx, sh in enumerate(choiceShapeSet):
                if Op.isBlurSimilar(guessImage, sh.img, p=False):
                    answer = idx + 1
                    guessImage.show()
                    break
        print(answer)
