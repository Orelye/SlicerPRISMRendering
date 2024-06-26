from PRISMRenderingShaders.CustomShader import CustomShader
from PRISMRenderingParams import *

"""OutlineShader Class containing the code for the Outline shader.

:param CustomShader:  Parent class containing the function to access the parameters of the shader. 
:type CustomShader: class.
""" 

class OutlineShader(CustomShader):
  
  gradStepParam = FloatParam("gradStep","Gradient Step", 0.001, 0.001, 0.02)
  VATParam = FloatParam("VAT", "Virtual Alpha Lower Than", 0.85, 0.0, 1.0)
  thresholdParam = FloatParam("threshold","Threshold", 0.05, 0.0, 0.5)
  stepParam = RangeParam("step", "Step", [0.0, 1])

  param_list = [gradStepParam, VATParam, thresholdParam, stepParam]
  sampleValues = {"gradStep" : 0.001, "VAT" : 0.6, "threshold" : 0.11, "step" : [0.0, 0.46]}
  
  def __init__(self, shaderPropertyNode, volumeNode = None, logic = None, paramlist = param_list):
    CustomShader.__init__(self,shaderPropertyNode, volumeNode)
    self.param_list = paramlist
    self.createMarkupsNodeIfNecessary(logic)

  @classmethod
  def GetDisplayName(cls):
    return 'Outline'
 
  @classmethod
  def GetBasicDescription(cls):
    """Function to get a basic description of the current shader.
    
    :return: Description of the current shader.
    :rtype: str
    """
    return 'Highlights the borders of the volume and is particularly useful for visualizing complex structures such as the blood vessels of the brain.'
  
  def setupShader(self):
    super(OutlineShader,self).setupShader()

    self.shaderProperty.ClearAllFragmentShaderReplacements()

    croppingDecCode = """

    vec4 ComputeGradient(in sampler3D volume, vec3 pos, float gradStep)
    {
      vec3 g1;
      g1.x = texture3D(volume, pos + vec3(gradStep,0.0,0.0) ).x;
      g1.y = texture3D(volume, pos +  vec3(0.0, gradStep, 0.0)).x;
      g1.z = texture3D(volume, pos +  vec3(0.0,0.0, gradStep)).x;
      vec3 g2;
      g2.x = texture3D(volume, pos -  vec3(gradStep,0.0,0.0)).x;
      g2.y = texture3D(volume, pos -  vec3(0.0, gradStep, 0.0)).x;
      g2.z = texture3D(volume, pos -  vec3(0.0,0.0, gradStep)).x;
      vec3 n = (g2 - g1) / (2.0 * gradStep);
      float nLength = length(n);
      if(nLength > 0.0)
          n = normalize(n);
      else
          n = vec3(0.0, 0.0, 0.0);
      vec4 ret;
      ret.rgb = n;
      ret.a = nLength;
      return ret;
    }

    float sampleThreshold = threshold;
    vec2 step = vec2(stepMin, stepMax);
    float virtualAlpha = 0.0;
    """
    self.shaderProperty.AddFragmentShaderReplacement("//VTK::Cropping::Dec", True, croppingDecCode, False)

    shadingImplCode = """
    if (!g_skip)
    {
      vec4 scalar = texture3D(in_volume[0], g_dataPos);
      scalar.r = scalar.r * in_volume_scale[0].r + in_volume_bias[0].r;
      scalar = vec4(scalar.r);
      g_srcColor = vec4(0.0);
      float inAlpha = computeOpacity(scalar);
      if(inAlpha > sampleThreshold && virtualAlpha < VAT)
      {
        vec4 n = ComputeGradient(in_volume[0], g_dataPos, gradStep);
        if(n.a > 0.0)
        {
          // Phong shading parameters
          vec3 lightPos = g_eyePosObj.xyz;//(ip_inverseTextureDataAdjusted * vec4(g_eyePosObj.xyz,1.0) ).xyz;
          vec3 viewPos = -g_eyePosObj.xyz - vec3(0.1, 0.0, 0.0);// vec3(1.0, 1.0, 1.0); // Position de la caméra - vous pouvez la rendre dynamique
          vec3 lightColor = vec3(1.0, 1.0, 1.0); // Lumière blanche
          vec3 objectColor = vec3(1.0, 1.0, 1.0); // Couleur de l'objet, blanc pour l'effet "glass-like"

          vec3 norm = n.rgb;
          vec3 lightDir = normalize(lightPos - g_dataPos);
          //float diff = max(dot(norm, lightDir), 0.0);
          vec3 diffuse = vec3(1.0, 1.0, 1.0)*1.2;

          vec3 viewDir = normalize(viewPos - g_dataPos);
          vec3 reflectDir = reflect(-lightDir, norm);
          float spec = pow(max(dot(viewDir, reflectDir), 0.0), 64.0); // Augmentation de l'exposant pour un effet plus brillant
          vec3 specular = 10.0 * spec * lightColor ; // Augmenter la contribution spéculaire
              
          vec3 result = (diffuse + specular) * objectColor;
                
          float factor = computeOpacity(n) * (1.0 - abs(dot(normalize(g_dirStep), n.rgb)));
          float alpha = smoothstep(step.x, step.y, factor) * 0.3; // Ajuster la transparence pour l'effet "glass-like"
          g_srcColor = vec4(result, alpha);
        }
      }
      virtualAlpha += (1-virtualAlpha) * inAlpha;
      g_srcColor.rgb *= g_srcColor.a;
      g_fragColor = (1.0f - g_fragColor.a) * g_srcColor + g_fragColor;
    }"""

    self.shaderProperty.AddFragmentShaderReplacement("//VTK::Shading::Impl", True, shadingImplCode, False)
