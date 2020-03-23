from Objects.Shape import Shape

class Lane():
    def __init__(self,id,idLeft,idRight,width,speed,turn):
        self.id=id
        self.leftBorderType=-1
        self.rightBorderType=-1
        self.direction="FORWARD"
        self.Neighbors=""
        self.points=[]
        self.leftBorderPoints=[]
        self.rightBorderPoints=[]
        self.idLeftBorder=idLeft
        self.idRightBorder=idRight
        self.width=width
        self.turn=turn
        self.speed=speed