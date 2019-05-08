from Objects.Shape import Shape

class Junction():
    def __init__(self,id):
        self.id=id
        self.width=3
        self.speed=20
        self.points=[]
        self.borderLeft=[]
        self.borderRight=[]
        self.direction="FORWARD"