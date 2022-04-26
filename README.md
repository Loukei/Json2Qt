# Json2Qt

A Qt code generator to automatically translate JSON to Qt class type.

## Introduction

JSON is a popular data format in many areas. 

Reading and writing the JSON file then convert to C++ struct/class is very painful and waste time, especially when JSON Data has dozens of attributes.

There were some tool in C++ to manage this task like [json2cpp.py],[autojsoncxx],[quicktype],[QtJsonSerializer] ... ,but its either not use Qt API or hard to install.

## How to use

``` bash
python Json2Qt.py -i user.json
```

or try [Json2Qt.exe](https://github.com/Loukei/Json2Qt/releases):

```bash
Json2Qt -i user.json
```

The json file:

![img](user_json.png)

will create to `user.h`:

![img](user_h.png)

and `user.cpp`:

![img](user_cpp.png)

1. Add the generated file `user.h` and `user.cpp` to your project.
2. Use `QJsonObject parseJsonFile(const QString& filename)` function to turn file into `QJsonObject`.
3. Use `User` object construct by `QJsonObject`.

- Turn object to `QJsonObject`, use `QJsonObject toQJsonObject() const` function.
- Save `User` to JSON file, use `QJsonDocument(user.toQJsonObject()).toJson()` [QJsonDocument]

``` c++
#include "user.h"

QJsonObject jsonObj = parseJsonFile("user.json");
auto user = User(jsonObj);
qDebug() << "User:" << user.toQJsonObject();
```

## Dependency

- Qt 5.0(or higher) for generated file.
- Python 3

**Check [Pipfile](https://github.com/Loukei/Json2Qt/blob/main/Pipfile) if you like pipenv**

## Bugs

I didn't process the variable name from the JSON file.
So the variable name like `{"image/jpeg":["application/vnd.google-apps.document"]}` will turn to `QString image/jpeg;`.

## Relate work

- [json2cpp](https://github.com/kcris/json2cpp)

**Qt Code Generator:**

- [Qface](https://github.com/Pelagicore/qface)
- [CppCodeGenerator](https://github.com/emloughl/CppCodeGenerator)
or any other IDL code generator support Qt.

**Template Engine:**

Using the string-based method to generate code is inflexible and hard to read.
- [Jinja 2](https://jinja.palletsprojects.com/en/2.11.x/)

## Reference

[JSON Support in Qt](https://doc.qt.io/qt-5/json.html)

[json2cpp.py]:      https://gist.github.com/soharu/5083914
[autojsoncxx]:      https://netheril96.github.io/autojsoncxx/
[quicktype]:        https://app.quicktype.io/
[QtJsonSerializer]: https://github.com/Skycoder42/QtJsonSerializer
[QJsonDocument]:    https://doc.qt.io/qt-5/qjsondocument.html#toJson-1
