from Resources.CustomShader import CustomShader

#------------------------------------------------------------------------------------
# Sphere carving shader
#------------------------------------------------------------------------------------
class SphereCarvingShader(CustomShader):

  shaderfParams = { 'radius' : { 'displayName' : 'Radius', 'min' : 0.0, 'max' : 100.0, 'defaultValue' : 50.0 }}  
  shader4fParams = {'centerPoint': {'displayName': 'centerPoint', 'defaultValue': {'x': 0.0, 'y': 0.0, 'z': 0.0, 'w': 0.0}}}
  def __init__(self, shaderPropertyNode):
    CustomShader.__init__(self,shaderPropertyNode)

  @classmethod
  def GetDisplayName(cls):
    return 'Sphere Carving'

  def setupShader(self):
    super(SphereCarvingShader,self).setupShader()
    x = self.param4fValues['centerPoint']['x']
    y = self.param4fValues['centerPoint']['y']
    z = self.param4fValues['centerPoint']['z']
    w = self.param4fValues['centerPoint']['w']
    self.shaderUniforms.SetUniform4f('centerPoint', [x, y, z , w])

    self.shaderUniforms.SetUniformf("radius", self.paramfValues['radius'])
    replacement = """
      vec3 center = centerPoint.xyz;
      vec4 texCoordRAS = in_volumeMatrix[0] * in_textureDatasetMatrix[0]  * vec4(g_dataPos, 1.);
      g_skip = length(texCoordRAS.xyz - center) < radius;
    """
    # (bool) Skip computation of current iteration step if true
    self.shaderProperty.AddFragmentShaderReplacement("//VTK::Cropping::Impl", True, replacement, False)

  def setPathEnds(self,entry,target):
    self.shaderUniforms.SetUniform3f("center", entry)