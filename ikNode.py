from    maya.api    import OpenMaya
import  math

class IkNode(OpenMaya.MPxNode):

    # Define the plugin variables for the register.
    kPluginNodeName         = 'ikNode'
    kPluginNodeClassify     = 'rig'

    # Define the inputs and output connections.
    inPositionBoneA         = OpenMaya.MObject()
    inPositionBoneB         = OpenMaya.MObject()
    inPositionBoneC         = OpenMaya.MObject()

    outTransformBoneA       = OpenMaya.MObject()
    outTransformBoneB       = OpenMaya.MObject()

    def __init__(self):
        # Use the parent class init.
        OpenMaya.MPxNode.__init__(self)

    def cosinusLaw(self, lengthA, lengthB, lengthC):
        ''' Compute the radians angle from the segment length.

        Args:
            lengthA (float): The length of the BoneA.
            lengthB (float): The length of the BoneB.
            lengthC (float): The length of the BoneC.

            Return:
            (float) : The radians angle.
        '''
        return math.acos((lengthA * lengthA + lengthB * lengthB - lengthC * lengthC) / (2 * lengthA * lengthB))

    def compute(self, pPlug, pDataBlock):

        # Check if the output plug is connected.
        if(pPlug == self.outTransformBoneA and self.outTransformBoneB):

            # Get the input and output handle.
            inPositionBoneAHandle   = pDataBlock.inputValue(self.inPositionBoneA)
            inPositionBoneBHandle   = pDataBlock.inputValue(self.inPositionBoneB)
            inPositionBoneCHandle   = pDataBlock.inputValue(self.inPositionBoneC)

            outTransformBoneAHandle = pDataBlock.outputValue(self.outTransformBoneA)
            outTransformBoneBHandle = pDataBlock.outputValue(self.outTransformBoneB)

            # Get the input connection values.
            positionBoneA           = OpenMaya.MVector(inPositionBoneAHandle.asFloat3())
            positionBoneB           = OpenMaya.MVector(inPositionBoneBHandle.asFloat3())
            positionBoneC           = OpenMaya.MVector(inPositionBoneCHandle.asFloat3())

            # Compute the length between the BoneA and the BoneB.
            vectorBoneAB            = positionBoneB - positionBoneA
            boneALength             = vectorBoneAB.length()
            vectorBoneABNorm        = vectorBoneAB.normalize()

            # Compute the length between the BoneB and the BoneC.
            vectorBoneBC            = positionBoneC - positionBoneB
            ikLength                = vectorBoneBC.length()
            vectorBoneBCNorm        = vectorBoneBC.normalize()

            # Compute the vector between the BoneA and the BoneC.
            vectorBoneAC            = positionBoneC - positionBoneA
            boneBLength             = vectorBoneAC.length()
            vectorBoneACNorm        = vectorBoneAC.normalize()

            # Compute the ik boneA angle.
            ikAngle                = self.cosinusLaw(boneALength, ikLength, boneBLength)
            # Compute the displace rotation axis.
            rotAxis                 = vectorBoneABNorm ^ vectorBoneABNorm
            # Compute the displace rotation as quaternion.
            qRot                    = OpenMaya.MQuaternion(ikAngle, rotAxis)
            # Compute the BoneA direction.
            orientedVectorAB        = vectorBoneAB.rotateBy(qRot)
            orientBoneA             = orientedVectorAB.rotateTo(vectorBoneAB)
            
            # Compute the BoneB position.
            positionB               = positionBoneA + vectorBoneAB * boneALength
            positionC               = positionBoneB + vectorBoneBC * boneBLength

            # Create the BoneA matrix.
            transA                  = OpenMaya.MTransformationMatrix()
            transA.setTranslation(positionBoneA, OpenMaya.MSpace.kWorld)
            transA.setRotation(orientBoneA)

            # Create the BoneB matrix.
            transB                  = OpenMaya.MTransformationMatrix()
            transB.setTranslation(positionB, OpenMaya.MSpace.kWorld)

            # Update the output connection.
            outTransformBoneAHandle.setMMatrix(transA.asMatrix())
            outTransformBoneAHandle.setClean()
            outTransformBoneBHandle.setMMatrix(transB.asMatrix())
            outTransformBoneBHandle.setClean()

        else:
            return OpenMaya.MFn.kUnknown
            


    @staticmethod
    def nodeCreator():
        return IkNode()

    @staticmethod
    def nodeInitializer():
        
        # Init the numeric and matrix attribute builder.
        numFnAttrib             = OpenMaya.MFnNumericAttribute()
        matFnAttrib             = OpenMaya.MFnMatrixAttribute()

        # Define the input attribute.
        IkNode.inPositionBoneA    = numFnAttrib.create(
            'positionBoneA', 'posBoneA',
            OpenMaya.MFnNumericData.k3Float
        )
        numFnAttrib.writable  = True
        numFnAttrib.storable  = True
        numFnAttrib.hidden    = False
        numFnAttrib.keyable   = True
        IkNode.addAttribute(IkNode.inPositionBoneA)

        IkNode.inPositionBoneB   = numFnAttrib.create(
            'positionBoneB', 'posBoneB',
            OpenMaya.MFnNumericData.k3Float
        )
        numFnAttrib.writable  = True
        numFnAttrib.storable  = True
        numFnAttrib.hidden    = False
        numFnAttrib.keyable   = True
        IkNode.addAttribute(IkNode.inPositionBoneB)

        IkNode.inPositionBoneC   = numFnAttrib.create(
            'positionBoneC', 'posBoneC',
            OpenMaya.MFnNumericData.k3Float
        )
        numFnAttrib.writable  = True
        numFnAttrib.storable  = True
        numFnAttrib.hidden    = False
        numFnAttrib.keyable   = True
        IkNode.addAttribute(IkNode.inPositionBoneC)

        # Define the node output.
        IkNode.outTransformBoneA       = matFnAttrib.create(
            'transBoneA', 'trBoneA'
        )
        matFnAttrib.writable  = False
        matFnAttrib.storable  = False
        matFnAttrib.hidden    = False
        matFnAttrib.readable  = True
        IkNode.addAttribute(IkNode.outTransformBoneA)

        IkNode.outTransformBoneB       = matFnAttrib.create(
            'transBoneB', 'trBoneB'
        )
        matFnAttrib.writable  = False
        matFnAttrib.storable  = False
        matFnAttrib.hidden    = False
        matFnAttrib.readable  = True
        IkNode.addAttribute(IkNode.outTransformBoneB)

        # Define the node internal dependency.
        IkNode.attributeAffects(IkNode.inPositionBoneA, IkNode.outTransformBoneA)
        IkNode.attributeAffects(IkNode.inPositionBoneA, IkNode.outTransformBoneB)
        IkNode.attributeAffects(IkNode.inPositionBoneB, IkNode.outTransformBoneA)
        IkNode.attributeAffects(IkNode.inPositionBoneB, IkNode.outTransformBoneB)
        IkNode.attributeAffects(IkNode.inPositionBoneC, IkNode.outTransformBoneA)
        IkNode.attributeAffects(IkNode.inPositionBoneC, IkNode.outTransformBoneB)