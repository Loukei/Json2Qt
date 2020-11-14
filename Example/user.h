#ifndef USER_H
#define USER_H

// Code generate by Json2Qt.py https://github.com/Loukei/Json2Qt.git
// ## How to Use:
// QJsonObject jsonObj = parseJsonFile("test.json");
// auto user = User(jsonObj);
// ## Convert to json text
// auto jsonObj = user.toQJsonObject();
// QJsonDocument jsonDoc(jsonObj);
// qDebug() << jsonDoc.toJson();

#include <QFile>
#include <QDebug>
#include <QJsonDocument>
#include <QJsonParseError>
#include <QJsonObject>
#include <QJsonArray>

QJsonObject parseJsonFile(const QString& filename);

// class User
class User{
public:
    User() = default;
    User(const QJsonObject &jsonObj);
    QJsonObject toQJsonObject() const;
    int userid;
    QString username;
    bool verified;
    double weight;
    QList<int> items;
    QList<QString> games;
};

#endif // USER_H
