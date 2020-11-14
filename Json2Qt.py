'''
# Introduction

A Qt code generator to automatically translate JSON to Qt class type.

將JSON檔案轉成c++類別，並使用Qt的資料型態以及Qt的JSON模組轉換工具

https://github.com/Loukei/Json2Qt.git
'''
import argparse
import json
from typing import List
import sys
import os

class QtProperty:
    '''
    保存一個屬性，包含屬性名稱or容器型別(如果有)or參數類型

    ## 建構:
    QtProperty('name', str) = QString name;
    QtProperty('user',dict,True) = QList<User> user;
    QtProperty.formValue('items',[1,2,3]) = QList<int> items;

    ## 檢查:
    isQList() 是否為list
    isClass() 是否內部為Class型態，與isQList()不為互斥

    ## 
    typeStr() 回傳型別的字串，比如"QList<User>","QList<int>","User","double"等

    ## 靜態函數
    qtType(type) 將輸入的型別轉成Qt型別字串
    capitalStyle(value) 將輸入的變數名轉成開頭大寫，適合當作class名稱或函數名稱
    lowerStyle(value) 將輸入的變數轉成小寫，適合當作屬性名稱或變數名稱
    '''
    def __init__(self, name: str, baseType:type,islist:bool = False):
        self.name:str = name
        self.baseType:str = self.qtType(baseType) # bool/int/double/QString/{classname}
        self.islist:bool = islist
        pass

    def __repr__(self)->str:
        '回傳物件內部參數'
        return f'QtProperty(name:{self.name},baseType:{self.baseType},islist:{self.islist})'

    def isQList(self)->bool:
        '回傳是否為含有list容器型態'
        return self.islist
    
    def isClass(self)->bool:
        '回傳基底型別是否為class'
        return self.baseType == 'class'

    def typeStr(self)->str:
        '回傳屬性的型別(QList<int>,int,...)'
        baseTypeName = self.capitalStyle(self.name) if self.isClass() else self.baseType
        return f'QList<{baseTypeName}>' if self.islist else baseTypeName

    @staticmethod
    def formValue(name:str,value):
        '靜態建構子(static constructor)，value為任意輸入值，按照value的型別建構property'
        if value is None:
            raise Exception('Unvalid input')

        t = type(value)
        if t is dict:
            return QtProperty(name,dict) 
        elif t is list: 
            return QtProperty(name,type(value[0]),True)
        else:
            return QtProperty(name,t)

    @staticmethod
    def qtType(value:type) -> str:
        '''
        將輸入的型別轉為Qt類型字串
        '''
        if value is None:
            return 'NULL'
        elif value is bool:
            return 'bool'
        elif value is int:
            return 'int'
        elif value is float:
            return 'double'
        elif value is str:  # QString
            return 'QString'
        elif value is list: # Qlist
            return 'QList'
        elif value is dict: # class
            return 'class'
        else:
            return '0'

    @staticmethod
    def capitalStyle(value: str) -> str:
        return value.strip().replace(' ', '_').capitalize()

    @staticmethod
    def lowerStyle(value: str) -> str:
        return value.strip().replace(' ', '_').lower()

    @staticmethod
    def converterFunc(typeStr:str)->str:
        if typeStr == 'bool':
            return 'toBool()'
        elif typeStr == 'int':
            return 'toInt()'
        elif typeStr == 'double':
            return 'toDouble()'
        elif typeStr == 'QString':
            return 'toString()'
        elif typeStr == 'class':
            return 'toObject()'
        elif typeStr == 'array':
            return 'toArray()'

class QtClass:
    def __init__(self,name:str,attributes:list):
        self.name = QtProperty.capitalStyle(name)
        self.attributes = attributes
        pass
    
    def append(self,data):
        self.attributes.append(data)
        pass
    
    def __repr__(self)->str:
        return '{' + f'name: {self.name}, attributes: {self.attributes}' + '}'

class Generator:
    indent:str = ' '*4 # 縮排長度
    setFuncName:str = 'set' # ex: void setAge(const int &age);
    getFuncName:str = 'get' # ex: int getAge() const;

    def __init__(self,name:str,data:dict,isPrivateMember:bool = False):
        self.name:str = name.lower()
        self.classList:list = [] # the list of processed class
        # class use private data member, use getter() and setter() function if it's true
        self.isprivate:bool = isPrivateMember 
        # start process data
        self.processData([(name,data)])
        # reverse class list, subclass must declare ahead
        self.classList.reverse()
        pass

    def processData(self,unprocessedData:list):
        '''
        以遞迴的方式將json資料(事先轉為dict)分解轉換為classList與includeList的陣列
        如果為巢狀資料，則會將內容推入新的unprocessedData處理
        '''
        if len(unprocessedData) == 0:
            return None
        name, data = unprocessedData.pop()
        # generate Qt class
        qClass = QtClass(name,[])
        for k,v in data.items():
            if type(v) is dict:
                unprocessedData.append((QtProperty.capitalStyle(k),v))
            qClass.append(QtProperty.formValue(k,v))
        # push qClass into procssed list
        self.classList.append(qClass)
        # if still has none processed data, keep process data
        self.processData(unprocessedData)
        pass

    @staticmethod
    def declareProperty(prop:QtProperty):
        return f'{prop.typeStr()} {QtProperty.lowerStyle(prop.name)};\n'
    
    @staticmethod
    def declareSetFunc(prop:QtProperty):
        setFunc:str = Generator.setFuncName + QtProperty.capitalStyle(prop.name)
        return f'void {setFunc}(const {prop.typeStr()} &{QtProperty.lowerStyle(prop.name)});\n'

    @staticmethod
    def declareGetFunc(prop:QtProperty):
        getFunc:str = Generator.getFuncName + QtProperty.capitalStyle(prop.name)
        return f'{prop.typeStr()} {getFunc}() const;\n'
    
    @staticmethod
    def declareClassConstructor(classname:str):
        return Generator.indent + f'{classname}(const QJsonObject &jsonObj);\n'

    @staticmethod
    def declareClassQJsonObjectFunc():
        return Generator.indent + 'QJsonObject toQJsonObject() const;\n'

    @staticmethod
    def defineSetFunc(classname:str,prop:QtProperty):
        setFunc:str = Generator.setFuncName + QtProperty.capitalStyle(prop.name)
        ans:str = f'void {classname}::{setFunc}(const {prop.typeStr()} &{QtProperty.lowerStyle(prop.name)})\n'
        ans += '{\n'
        ans += Generator.indent + f'this->{QtProperty.lowerStyle(prop.name)} = {QtProperty.lowerStyle(prop.name)};\n'
        ans += '}\n'
        return ans
    
    @staticmethod
    def defineGetFunc(classname:str,prop:QtProperty):
        getFunc:str = Generator.getFuncName + QtProperty.capitalStyle(prop.name)
        ans = f'{prop.typeStr()} {classname}::{getFunc}() const\n'
        ans += '{\n'
        ans += Generator.indent + f'return this->{QtProperty.lowerStyle(prop.name)};\n'
        ans += '}\n'
        return ans

    @staticmethod
    def definePropertyConverter(prop:QtProperty):
        indent = Generator.indent
        ## add commit
        ans = indent + f'// parse {prop.typeStr()} {QtProperty.lowerStyle(prop.name)}\n'
        if prop.isQList():
            jsonArray = f'jsonObj["{prop.name}"].toArray()'
            arrayName = QtProperty.lowerStyle(prop.name) + 'Array'
            ans += indent + f'QJsonArray {arrayName} = {jsonArray};\n'
            ans += indent + f'for(auto i:{arrayName})' + '{\n'
            arrayItem = f'i.{QtProperty.converterFunc(prop.baseType)}'
            if prop.isClass():
                arrayItem = f'{QtProperty.capitalStyle(prop.name)}({arrayItem})'
            ans += indent*2 + f'this->{QtProperty.lowerStyle(prop.name)}.append({arrayItem});\n'
            ans += indent + '}\n'
        else:
            jsonValue = f'jsonObj["{prop.name}"].{QtProperty.converterFunc(prop.baseType)}'
            if prop.isClass(): # if jsonValue is Object, we need assign to class constructer
                jsonValue = f'{QtProperty.capitalStyle(prop.name)}({jsonValue})'
            ans += indent + f'this->{QtProperty.lowerStyle(prop.name)} = {jsonValue};\n'
        return ans

    @staticmethod
    def defineClassConstructor(qclass:QtClass):
        '建立目標類別的建構函式'
        # add commit
        ans = f'// construct {qclass.name} from QJsonObject,not \n'
        # add function declare
        ans += f'{qclass.name}::{qclass.name}(const QJsonObject &jsonObj)\n'
        ans += '{\n'
        # iterate all properties
        for qprop in qclass.attributes:
            ans += Generator.definePropertyConverter(qprop)
        ans += '}\n'
        return ans

    @staticmethod
    def defineClassQJsonObjectFunc(qclass:QtClass):
        '將類別轉換成QJsonObject資料'
        indent = Generator.indent
        ans = f'QJsonObject {qclass.name}::toQJsonObject() const\n'
        ans += '{\n'
        ans += indent + 'QJsonObject obj;\n'
        ## add propertys
        for qprop in qclass.attributes:
            propName:str = QtProperty.lowerStyle(qprop.name)
            if qprop.isQList():
                ans += indent + f'//fill {qprop.name}\n'
                jsonArray:str = f'{QtProperty.capitalStyle(qprop.name)}Array'
                ans += indent + f'QJsonArray {jsonArray};\n'
                ans += indent + f'for(auto i:this->{propName})' + '{\n'
                jsonValueItem:str = 'i.toQJsonObject()' if qprop.isClass() else 'i'
                ans += indent*2 + f'{jsonArray}.append({jsonValueItem});\n'
                ans += indent + '}\n'
                ans += indent + f'obj.insert("{qprop.name}",{jsonArray});\n'
            else:
                qjsonValue:str = propName + '.toQJsonObject()' if qprop.isClass() else propName
                ans += indent + f'obj.insert("{qprop.name}",this->{qjsonValue});\n'
        ans += indent + 'return obj;\n}\n'
        return ans

    @staticmethod
    def declareClass(qclass:QtClass,isPrivateMember:bool = False):
        'return class declare'
        ## add class commit
        ans = f'// class {qclass.name}\n'
        ans += f'class {qclass.name}' + '{\n'
        ans += 'public:\n'
        ## add class constructor
        ans += Generator.indent + f'{qclass.name}() = default;\n'
        ans += Generator.declareClassConstructor(qclass.name)
        ## declare class to QJsonObject function
        ans += Generator.declareClassQJsonObjectFunc()
        ## declare property and Read Write function 
        for qprop in qclass.attributes:
            if isPrivateMember:
                ans += f'\n\\Read and Write function to {qprop.name}'
                ans += Generator.indent + Generator.declareGetFunc(qprop)
                ans += Generator.indent + Generator.declareSetFunc(qprop)
            else:
                ans += Generator.indent + Generator.declareProperty(qprop)
        if isPrivateMember:
            ans += '\nprivate:\n'
            for qprop in qclass.attributes:
                ans += Generator.indent + Generator.declareProperty(qprop)
        ans += '};\n'
        return ans
    
    @staticmethod
    def defineClass(qclass:QtClass,isPrivateMember:bool = False):
        ans = Generator.defineClassConstructor(qclass) + '\n'
        ## declare class to QJsonObject function
        ans += Generator.defineClassQJsonObjectFunc(qclass) + '\n'
        if isPrivateMember:
            ans += '\n'
            for qprop in qclass.attributes:
                ans += Generator.defineGetFunc(qclass.name,qprop) + '\n'
                ans += Generator.defineSetFunc(qclass.name,qprop) + '\n'
        return ans + '\n'

    @staticmethod
    def defineJsonFileParseFunc()->str:
        indent = Generator.indent
        ans = 'QJsonObject parseJsonFile(const QString& filename)\n'
        ans += '{\n'
        ans += indent + 'QFile file(filename);\n'
        ans += indent + 'if(!file.open(QIODevice::ReadOnly)){\n'
        ans += indent*2 + 'auto msg = QString("File (%1) open fail: %2.").arg(filename,file.errorString());\n'
        ans += indent*2 + 'qFatal("%s",msg.toStdString().c_str());\n'
        ans += indent*2 + 'return QJsonObject();\n'
        ans += indent + '}\n\n'
        ans += indent + 'QJsonParseError jsonErr;\n'
        ans += indent + 'auto jsonDoc = QJsonDocument::fromJson(file.readAll(),&jsonErr);\n'
        ans += indent + 'if(jsonErr.error != QJsonParseError::NoError){\n'
        ans += indent*2 + 'auto msg = QString("File (%1) parse error: %2.").arg(filename,jsonErr.errorString());\n'
        ans += indent*2 + 'qFatal("%s",msg.toStdString().c_str());\n'
        ans += indent*2 + 'return QJsonObject();\n'
        ans += indent + '}\n'
        ans += indent + 'return jsonDoc.object();\n'
        ans += '}\n'
        return ans

    def buildHeader(self)->str:
        '產生Header file'
        # Preprocessor directives
        ans = f'#ifndef {self.name.upper()}_H\n#define {self.name.upper()}_H\n\n'
        # Add commit
        ans += f'// Code generate by Json2Qt.py https://github.com/Loukei/Json2Qt.git\n'
        ans += '// ## How to Use:\n'
        ans += '// QJsonObject jsonObj = parseJsonFile("test.json");\n'
        ans += f'// auto {self.name} = {self.name.capitalize()}(jsonObj);\n'
        ans += f'// ## Convert to json text\n'
        ans += f'// auto jsonObj = {self.name}.toQJsonObject();\n'
        ans += f'// QJsonDocument jsonDoc(jsonObj);\n'
        ans += f'// qDebug() << jsonDoc.toJson();\n\n'
        # Add include header
        ans += '#include <QFile>\n'
        ans += '#include <QDebug>\n'
        ans += '#include <QJsonDocument>\n'
        ans += '#include <QJsonParseError>\n'
        ans += '#include <QJsonObject>\n'
        ans += '#include <QJsonArray>\n\n'
        # declare Json file parse func
        ans += 'QJsonObject parseJsonFile(const QString& filename);\n'
        # declare classes
        ans += '\n'
        for qclass in self.classList:
            ans += self.declareClass(qclass,self.isprivate)
            ans += '\n'
        # endif
        ans += f'#endif // {self.name.upper()}_H\n'
        return ans

    def buildSource(self)->str:
        # Add include
        ans = f'#include "{self.name}.h"\n\n'
        # define json parse File function
        ans +=  Generator.defineJsonFileParseFunc()
        # define classes function
        ans += '\n'
        for qclass in self.classList:
            ans += Generator.defineClass(qclass,self.isprivate)
        return ans

def main(filename:str):
    # open file
    try:
        with open(filename) as f:
            content = f.read()
    except IOError:
        print("Can't open/read file.")
        return
    # use json module turn file to dict struct
    data:dict = json.loads(content)
    # get class name form file name
    classname = os.path.basename(filename).split('.')[0]
    # Use Generator turn data to QtClass list
    g = Generator(classname,data,False)
    # generate classname.h
    with open(classname + '.h', 'w') as headerFile:
        headerFile.write(g.buildHeader())
        headerFile.close()
    # generate classname.cpp
    with open(classname + '.cpp', 'w') as sourceFile:
        sourceFile.write(g.buildSource())
        sourceFile.close()
    pass

def validate_file(f):
    if not os.path.exists(f):
        # Argparse uses the ArgumentTypeError to give a rejection message like:
        # error: argument input: x does not exist
        raise argparse.ArgumentTypeError("{0} does not exist".format(f))
    return f

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Read file form Command line.")
    parser.add_argument("-i", "--input", dest="filename", required=True, type=validate_file,
                        help="input json file to serialize.", metavar="FILE")
    args = parser.parse_args()
    main(args.filename)
    pass
