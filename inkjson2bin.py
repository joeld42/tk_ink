#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys
import types
import codecs
import json
import pprint

def printIndented( indent, str ):
    indentStr = "    "* indent
    print indentStr + str

class InkValue( object ):
    ValueType_BASIC = 'basic'
    ValueType_DIVERT_TARGET = 'divert'
    ValueType_VARIABLE_POINTER = 'variable'

    def __init__(self, val, valType=ValueType_BASIC ):
        assert( isinstance( valType, basestring))
        self.valType = valType
        self.val = val
        self.ctx = None

    def prettyPrint(self, indent=0 ):
        valEscaped = str(self.val)
        valEscaped = valEscaped.replace( '\n', '\\n')
        printIndented( indent, "VALUE (%s): %s" % (self.valType, valEscaped))


class InkVoid( object ):
    
    def __init__(self):
        pass

    def prettyPrint(self, indent=0 ):
        printIndented( indent, "VOID"  )

class InkGlue( object ):

    GlueType_BIDIRECTIONAL = "bidirectional"
    GlueType_LEFT = "left"
    GlueType_RIGHT = "right"

    def __init__(self, glueType):
        self.glueType = glueType

    def prettyPrint(self, indent=0):
        printIndented( indent, "GLUE: " + self.glueType )

class InkControlCommand( object ):

    CommandType_EvalStart = "ev"
    CommandType_EvalOutput = "out"
    CommandType_EvalStart = "ev"
    CommandType_EvalOutput = "out"
    CommandType_EvalEnd = "/ev"
    CommandType_Duplicate = "du"
    CommandType_PopEvaluatedValue = "pop"
    CommandType_PopFunction = "~ret"
    CommandType_PopTunnel = "->->"
    CommandType_BeginString = "str"
    CommandType_EndString = "/str"
    CommandType_NoOp = "nop"
    CommandType_ChoiceCount = "choiceCnt"
    CommandType_TurnsSince = "turns"
    CommandType_ReadCount = "readc"
    CommandType_Random = "rnd"
    CommandType_SeedRandom = "srnd"
    CommandType_VisitIndex = "visit"
    CommandType_SequenceShuffleIndex = "seq"
    CommandType_StartThread = "thread"
    CommandType_Done = "done"
    CommandType_End = "end"
    CommandType_ListFromInt = "listInt"
    CommandType_ListRange = "range"

    nameLookup = {}

    def __init__(self, cmd ):
        # TODO: Assert that this is a valid cmd
        self.cmd = cmd

    def prettyPrint(self, indent=0):
        printIndented( indent, "CMD: %s ('%s')" % 
            ( self.commandStringFromName( self.cmd ), self.cmd) )

    @classmethod
    def makeCommandIfValid( cls, cmdstr ):
        if cls.commandStringFromName( cmdstr ):
            return InkControlCommand( cmdstr )
        else:            
            return None
        
    @classmethod
    def commandStringFromName( cls, cmdname ):
        if not cls.nameLookup:            
            for cname in dir(cls):
                if (cname.startswith("CommandType_")):
                    #print cls.__dict__[cname], cname
                    cls.nameLookup[cls.__dict__[cname]] = cname

        return cls.nameLookup.get( cmdname, None )
    
class InkNativeFunction( object ):

    nativeCallName = {}

    def __init__( self, funcName ):
        self.name = funcName

    @classmethod
    def makeNativeFuncIfValid( cls, funcName ):
        if nativeCallName.has_key( funcName ):
            return InkNativeFunction( funcName )
        return None

class InkContainer( object ):

    def __init__(self, contents ):
        self.contents = contents
        self.countFlags = 0
        self.name = ""
        self.namedOnlyContent = {} # WTF is this?

    def prettyPrint(self, indent= 0):
        printIndented( indent, "CONTAINER: %s (%d items)"  % (self.name, len(self.contents)) )
        if self.contents:
            printIndented( indent, "+-SUBITEMS:" );
            for subitem in self.contents:
                subitem.prettyPrint( indent+1 )

        if self.namedOnlyContent:
            for contentName, content in self.namedOnlyContent.iteritems():
                printIndented( indent, "+-NAMED CONTENT '%s':" % contentName );
                content.prettyPrint( indent+1 )


class InkDivert( object ):

    PushPopType_FUNCTION = "function"
    PushPopType_TUNNEL = "tunnel"

    def __init__(self, targetPathString, pushesToStack=False, divPushType=PushPopType_FUNCTION):
        self.divPushType = divPushType
        self.pushesToStack = pushesToStack
        self.external = False
        self.externalArgs = []
        self.variableDivertName = None
        self.targetPathString = str(targetPathString)
        self.conditional = None

    def prettyPrint(self, indent= 0):
        targetStr = "???"
        if self.targetPathString:
            targetStr = self.targetPathString
        elif self.variableDivertName:
            targetStr = self.variableDivertName

        if (self.conditional):
            targetStr = targetStr + "COND: " + str(self.conditional)

        externalStr = ""
        if (self.external):
            externalStr = " EXTERNAL: [%s]" % str(self.externalArgs)

        printIndented( indent, "DIVERT: -> %s (%s) pushesToStack: %s%s"  % ( targetStr, self.divPushType, str(self.pushesToStack), externalStr ) )

class InkChoicePoint( object ):

    def __init__(self, choicePath, flags):
        self.choicePath = choicePath
        self.flags  = flags

    def prettyPrint(self, indent=0):
        printIndented( indent, "CHOICE: %s (flags: %d)" % ( self.choicePath, self.flags) )

class InkVarReference( object ):

    def __init__(self, varName="" ):
        self.varName = varName
        self.pathStringForCount = None

    def prettyPrint(self, indent=0):
        varNameStr = ""
        countStr = ""
        if self.varName:
            varNameStr = self.varName
            countStr = ""
        else:
            varNameStr = "COUNT"
            countStr = self.pathStringForCount

        printIndented( indent, "VAR REF: %s %s" % (varNameStr, countStr) )

class InkVarAssign( object ):

    def __init__(self, varName, isGlobal=True ):
        self.varName = varName
        self.isGlobal = isGlobal
        self.isNewDecl = True

    def prettyPrint(self, indent=0):
        globalStr = ""
        if self.isGlobal:
            globalStr = "Global"

        printIndented( indent, "VAR ASSIGN: %s %s" % (self.varName, globalStr) )

class InkTag( object ):
    def __init__(self, tagValue):
        self.tagValue = tagValue

    def prettyPrint(self, indent=0):
        printIndented( indent, "TAG: '%s'" % (self.tagValue)  )

class InkList( object ):

    def __init__(self):
        self.origins = []

    def prettyPrint(self, indent=0):
        printIndented( indent, "TAG: '%s'" % (self.tagValue)  )

class InkBytecode( object ):

    def __init__( self, jsonData ):

        self.stringTable = {}
        self.inkVersion = jsonData["inkVersion"]
        print "--------------"
        self.root = self.jsonToInkObject( jsonData["root"])


    # More or less converted directly from ink runtime JTokenToRuntimeObject
    def jsonToInkObject(self, jtoken ):

        if isinstance(jtoken, int) or isinstance(jtoken, float):
            return InkValue( jtoken )
        elif isinstance(jtoken, basestring):
            if jtoken[0]=='^':
                print jtoken
                return InkValue( jtoken[1:] )
            elif jtoken=='\n':
                return InkValue( jtoken )

            # Glue ## ???
            elif jtoken == '<>':
                return InkGlue( InkGlue.GlueType_BIDIRECTIONAL )
            elif jtoken == 'G<':
                return InkGlue( InkGlue.GlueType_LEFT )
            elif jtoken == 'G>':
                return InkGlue( InkGlue.GlueType_RIGHT )

            # Control Commands
            cmd = InkControlCommand.makeCommandIfValid( jtoken )
            if cmd:
                return cmd

            # Native function?
            # Ink hack since ^ denotes storytext
            if jtoken=="L^":
                jtoken = "^"
            func = InkNativeFunction.makeNativeFuncIfValid( jtoken )
            if func:
                return func


            # NOTE: There is code to handle PopTunnel and Ret here but I think
            # it's covered by the ControlCommands case above

            # Void
            if jtoken=='void':
                return InkVoid()
                
            # Didn't expect this
            return InkValue("UNKNOWN (string '%s')" % jtoken )

        elif isinstance(jtoken, list):
            return self.jsonArrayToInkContainer( jtoken )

        elif isinstance(jtoken, dict):

            # Is it a divert target?
            divert = jtoken.get( "^->", None )
            if divert:
                val = InkValue( divert, InkValue.ValueType_DIVERT_TARGET )
                return val

            # Is it a variable pointer?
            varptr = jtoken.get( "^var", None)
            if varptr:
                val = InkValue( varptr, InkValue.ValueType_VARIABLE_POINTER )
                ctx = jtoken.get("ci", None)
                if ctx:
                    val.ctx = int(ctx)
                return val

            # Is it a divert?
            divert = None
            if jtoken.has_key( "->" ):
                divert = InkDivert( jtoken["->"] )
            elif jtoken.has_key( "f()"):
                divert = InkDivert( jtoken["f()"], True ) # PushPopType_FUNCTION
            elif jtoken.has_key( "->t->" ):
                divert = InkDivert( jtoken["->t->"], True, InkDivert.PushPopType_TUNNEL)
            elif jtoken.has_key( "x()"):
                divert = InkDivert( jtoken["x()"], False )
                divert.external = True

            if divert:
                divert.variableDivertName = jtoken.get( "var", None )
                # do we need to set targetPathString to None?

                divert.conditional = jtoken.has_key( "c" ) # discard value?

                if divert.external:
                    divert.externalArgs = int( jtoken.get( "exArgs", 0 ) )

                return divert

            # Choice
            choicePath = jtoken.get( "*", None )
            if choicePath:
                flags = int(jtoken.get("flg",0))
                choicePoint = InkChoicePoint( str(choicePath), flags)

                return choicePoint

            # Variable Reference
            varRef = None
            if jtoken.get( "VAR?", None):
                varRef = InkVarReference( jtoken["VAR?"] )
            elif jtoken.get( "CNT?", None ):
                varRef = InkVarReference()
                varRef.pathStringForCount = jtoken["CNT?" ]
            if varRef:
                return varRef

            # Variable Assign
            varAssign = None
            varAssignName = jtoken.get("VAR=", None )
            if varAssignName:
                varAssign = InkVarAssign( varAssignName, True )
            else:
                variableRef = jtoken.get("temp=", None )
                if variableRef:
                    varAssign = InkVarAssign( jtoken["temp="], False )

            if varAssign:
                isOldDecl = jtoken.get( "re", None )
                if isOldDecl:
                    varAssign.isNewDecl = False

                return varAssign


            # Tags
            if jtoken.get("#", None):
                tag = InkTag( jtoken["#"])
                return tag

            # Lists .. TODO

            # Didn't expect this
            return InkValue("UNKNOWN (dict '%s')" % jtoken )

        else:
            return InkValue("UNKNOWN")

    def jsonArrayToInkContainer(self, item ):

        contents = self.jsonArrayToInkObjectList( item[:-1])
        lastItem = item[-1] # Expect dictionary
        ctr = InkContainer( contents )

        # Lastitem may be "None", e.g. in a choice
        if lastItem:
            print "LastItem is ", lastItem
            for k, val in lastItem.iteritems():
                if k == "#f":
                    # Container Flags
                    ctr.countFlags = int(val)
                    print "it's countFlags", val
                elif k=="#n":
                    # Container Name
                    ctr.name = unicode(val)
                else:
                    # TODO: what is this for?
                    namedContentItem = self.jsonToInkObject( val )
                    print "It's namedContentItem..",
                    if isinstance( namedContentItem, InkContainer ):
                        print "It's a container", k
                        namedContentItem.name = k
                    ctr.namedOnlyContent[k] = namedContentItem

        return ctr;

    def jsonArrayToInkObjectList(self, items ):
        return list(map( self.jsonToInkObject, items ))




def readInkJson( filename ):

    with codecs.open(filename, 'r', 'utf-8-sig') as fd:
        jsonData = json.load(fd,'utf-8')

    return jsonData

if __name__=='__main__':

    if len(sys.argv) < 2:
        print "inkjson2bin <filename.json>"
        sys.exit(1)

    jsonData = readInkJson( sys.argv[1])
    ink = InkBytecode( jsonData )
    print "InkVersion", ink.inkVersion
    ink.root.prettyPrint()


