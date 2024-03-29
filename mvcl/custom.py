'''
 # @ Author: Zongjing Li
 # @ Create Time: 2024-02-02 03:21:43
 # @ Modified by: Zongjing Li
 # @ Modified time: 2024-02-02 03:21:49
 # @ Description: This file is distributed under the MIT license.
'''
import torch
import torch.nn as nn
from rinarak.dklearn.nn.mlp import FCBlock
from rinarak.dklearn.cv.unet import UNet
import math

class UnivseralMapper(nn.Module):
    def __init__(self,input_dim,output_dim):
        super().__init__()
        latent_dim = 100
        self.conv1 = nn.Conv2d(input_dim,latent_dim,3,1,1)
        self.conv2 = nn.Conv2d(latent_dim,latent_dim,3,1,1)
        self.fc1 = FCBlock(latent_dim,2,100,output_dim)
    def forward(self, x):
        x = self.conv1(x)
        outputs = self.conv2(x)
        return self.fc1(outputs.permute(0,2,3,1))
    
class IdMap(nn.Module):
    def __init__(self):
        super().__init__()
    def forward(self, x):
        return x.permute(0,2,3,1)

class ColorMapper(nn.Module):
    def __init__(self,input_dim,output_dim):
        super().__init__()
        latent_dim = 100
        self.conv = nn.Conv2d(input_dim,latent_dim,3,1,1)
        self.fc1 = FCBlock(100,2,latent_dim,output_dim)
    
    def forward(self, x):
        if len(x.shape) == 2:
            N, D = x.shape
            W = H = int(math.sqrt(N))
            x = x.reshape([1,W,H,D])
        if len(x.shape) == 3:
            B, N, D = x.shape
            W = H = int(math.sqrt(N))
            x = x.reshape([B,W,H,D])
        x = x.permute(0,3,1,2)
        outputs = self.conv(x).flatten(start_dim = -2,end_dim = -1).permute(0,2,1)
        return torch.tanh(self.fc1(outputs)) * 3.

class ShapeMapper(nn.Module):
    def __init__(self,input_dim,output_dim):
        super().__init__()
        latent_dim = 100
        self.conv =UNet(input_dim, latent_dim)
        #self.fc1 = FCBlock(100,2,latent_dim,output_dim)
    
    def forward(self, x):
        if len(x.shape) == 2:
            N, D = x.shape
            W = H = int(math.sqrt(N))
            x = x.reshape([1,W,H,D])
        if len(x.shape) == 3:
            B, N, D = x.shape
            W = H = int(math.sqrt(N))
            x = x.reshape([B,W,H,D])
        x = x.permute(0,3,1,2)
        outputs = self.conv(x).flatten(start_dim = -2,end_dim = -1).permute(0,2,1)
        EPS = 7.
        return torch.tanh(EPS * outputs)#torch.tanh(self.fc1(outputs)) * 3.

class ObjectAffinityFeatures(nn.Module):
    def __init__(self, input_dim, output_dim):
        super().__init__()
        assert input_dim % 2 == 0,"input dim should be divisble by 2 as it is a pair of patches features"

class ColorAffinityFeatures(nn.Module):
    def __init__(self,input_dim, output_dim):
        super().__init__()
        assert input_dim % 2 == 0, "input dim should be divisble by 2 as it is a pair of patches features"
    
    def forward(self, x):
        return x

class CategoryAffinityFeatures(nn.Module):
    def __init__(self,input_dim, output_dim):
        super().__init__()
        assert input_dim % 2 == 0, "input dim should be divisible by 2 as it is a pair of patchs features"
    
    def forward(self, x):
        return x

def build_demo_domain(model):
    from .primitives import Primitive
    model.implementations["universal"] = IdMap()#UnivseralMapper(4,132)
    model.implementations["color"] = ColorMapper(4,model.config.object_dim)
    model.implementations["shape"] = ShapeMapper(4,model.config.concept_dim)
    # [Pre-define some concept mapper]
    color = Primitive.GLOBALS["color"]
    color.value = lambda x: {**x, "features": x["model"].get_mapper("color")(x["features"])}
    shape = Primitive.GLOBALS["shape"]
    shape.value = lambda x: {**x, "features": x["model"].get_mapper("shape")(x["features"])}
    return model

def build_line_demo_domain(model):
    from .primitives import Primitive
    model.implementations["universal"] = nn.Linear(1, 32)
    model.implementations["color"] = nn.Linear(32, 1)
    # [Pre-define some concept mappers]
    color = Primitive.GLOBALS["color"]
    color.value = lambda x: {**x, "features": x["model"].get_mapper("color")(x["features"])}
    return model

def build_custom(model, domain_name):
    if domain_name == "demo": return build_demo_domain(model)
    if domain_name == "line_demo": return build_line_demo_domain(model)